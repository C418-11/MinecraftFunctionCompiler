# -*- coding: utf-8 -*-


import ast
import json
import os
import time
import warnings
from collections import OrderedDict
from itertools import zip_longest
from typing import Any

from BreakPointTools import BreakPointFlag
from BreakPointTools import SplitBreakPoint
from BreakPointTools import raiseBreakPoint
from BreakPointTools import register_processor
from BreakPointTools import updateBreakPoint
from Constant import Flags
from Constant import ResultExt
from Constant import ScoreBoards
from DebuggingTools import COMMENT
from DebuggingTools import DEBUG_OBJECTIVE
from DebuggingTools import DEBUG_TEXT
from DebuggingTools import DebugTip
from DebuggingTools import FORCE_COMMENT
from NamespaceTools import file_ns_getter
from NamespaceTools import file_ns_init
from NamespaceTools import file_ns_map
from NamespaceTools import file_ns_setter
from NamespaceTools import join_file_ns
from NamespaceTools import node_to_namespace
from NamespaceTools import ns_getter
from NamespaceTools import ns_init
from NamespaceTools import ns_map
from NamespaceTools import ns_setter
from NamespaceTools import root_namespace
from NamespaceTools import store_local
from NamespaceTools import temp_map
from ParameterTypes import ArgType
from ParameterTypes import DefaultArgType
from ParameterTypes import UnnecessaryParameter
from ParameterTypes import func_args
from ScoreboardTools import CHECK_SB
from ScoreboardTools import SBCheckType
from ScoreboardTools import SBCompareType
from ScoreboardTools import SBOperationType
from ScoreboardTools import SB_ASSIGN
from ScoreboardTools import SB_CONSTANT
from ScoreboardTools import SB_Name2Code
from ScoreboardTools import SB_OP
from ScoreboardTools import SB_RESET
from ScoreboardTools import gen_code
from ScoreboardTools import init_name
from Template import check_template
from Template import init_template
from Template import template_funcs

SB_ARGS: str = ScoreBoards.Args
SB_TEMP: str = ScoreBoards.Temp
SB_FLAGS: str = ScoreBoards.Flags
SB_VARS: str = ScoreBoards.Vars
SB_FUNC_RESULT: str = ScoreBoards.FuncResult

SAVE_PATH: None | str = None
READ_PATH: None | str = None
TEMPLATE_PATH: None | str = None
BASE_NAMESPACE: None | str = None


def is_parent_path(path1, path2):
    path1 = os.path.abspath(path1)
    path2 = os.path.abspath(path2)
    return os.path.commonpath([path1, path2]) == path1


def join_base_ns(path: str) -> str:
    if BASE_NAMESPACE.endswith(':'):
        new_namespace = f"{BASE_NAMESPACE}{path}"
    else:
        new_namespace = f"{BASE_NAMESPACE}\\{path}"

    return new_namespace


def namespace_path(namespace: str, path: str) -> str:
    base_path = os.path.join(namespace.split(':', 1)[1], path)
    return os.path.join(SAVE_PATH, base_path)


def remove_base_ns(namespace: str) -> str:
    if not namespace.startswith(BASE_NAMESPACE):
        raise Exception(f"namespace '{namespace}' is not in base namespace '{BASE_NAMESPACE}'")
    return namespace[len(BASE_NAMESPACE):]


GlobalId = 0


def newUid() -> str:
    global GlobalId
    GlobalId += 1
    return hex(GlobalId)[2:]


def alive_import(import_path: str, base: str = '') -> tuple[str | None, bool | None]:
    package_local_path = import_path.replace(".", "\\")

    full_path = os.path.normpath(os.path.join(base, package_local_path))
    if os.path.isfile(f"{full_path}.py"):
        return f"{full_path}.py", True
    if os.path.isdir(full_path):
        return full_path, False
    return None, None


loaded_modules = {}


def import_as(name: str, as_name: str | None, namespace: str, *, register_ns: bool = True) -> tuple[str, bool]:
    package_local_path = name.replace(".", "\\")

    safe_as_name = as_name or name

    is_template: bool = False
    sourcefile_path, is_file = alive_import(name, READ_PATH)
    if sourcefile_path is None:

        base_path = TEMPLATE_PATH
        if is_parent_path(TEMPLATE_PATH, package_local_path):
            base_path = ''

        sourcefile_path, is_file = alive_import(name, base_path)
        if sourcefile_path is None:
            raise Exception(f"无法导入 '{name}', {package_local_path}")
        is_template = True

    if (not is_template) and check_template(sourcefile_path):
        is_template = True

    command = ''

    if is_file and not is_template:
        new_namespace = join_base_ns(name)
        if register_ns:
            ns_setter(safe_as_name, f"{new_namespace}\\module", namespace, "module")

        def _load():
            nonlocal command
            start_t = time.time()
            with open(sourcefile_path, mode='r', encoding="utf-8") as f:
                tree = ast.parse(f.read())

            print("------------导入文件-----------")
            print(sourcefile_path)
            print(ast.dump(tree, indent=4))
            print("------------------------------")

            generate_code(tree, new_namespace, name)
            end_t = time.time()
            print(f"编译导入模块 {sourcefile_path}, 耗时{end_t - start_t}秒")

            command += f"function {new_namespace}/.__module\n"

        if sourcefile_path not in loaded_modules:
            _load()
            loaded_modules[sourcefile_path] = True
        else:
            print(f"重复导入模块 {sourcefile_path}")

    if is_file and is_template:
        init_template(name)
        ns_init(join_base_ns(name), "module")
        ns_setter("module", f"{join_base_ns(name)}\\module", join_base_ns(name), "module")
    elif is_template:
        ns_init(join_base_ns(name), "package")

    return command, is_file


def mkdirs(path: str, *, exist_ok: bool = False):
    os.makedirs(path, exist_ok=exist_ok)


@register_processor("return")
def sbp_return(func_path: str, level: str, *, name: str, objective: str):
    """
    处理return语句的断点
    :param func_path: 断点切断后恢复执行需要调用的函数
    :param level: 文件命名空间层级名
    :param name: 标记位目标
    :param objective: 标记位计分项
    """
    def _process_raise() -> tuple[str, bool]:
        command = ''
        keep_raise: bool = True
        if level in ["module", "function"]:
            command += COMMENT("BP:Return.Reset")
            command += SB_RESET(name, objective)
            keep_raise = False
        else:
            command += FORCE_COMMENT(BreakPointFlag(
                "return",
                name=name,
                objective=objective
            ))
        return command, keep_raise

    def _process_split() -> str:
        command = ''
        command += COMMENT("BP:Return.Split")
        command += CHECK_SB(
            SBCheckType.UNLESS,
            name, objective,
            SBCompareType.EQUAL,
            Flags.TRUE, SB_FLAGS,
            f"function {func_path}"
        )

        return command

    if func_path is None:
        return _process_raise()

    if level is None:
        return _process_split()


def file_ns_path(path: str, *args) -> str:
    """
    将文件命名空间转换为路径
    :param path: 文件命名空间
    :param args: 需要拼接的路径
    :return: 拼接后的路径
    """
    return os.path.normpath(os.path.join(SAVE_PATH, path, *args))


def generate_code(node, namespace: str, file_ns: str) -> str:
    """
    递归生成命令
    :param node: 需要被处理的AST节点
    :param namespace: 当前的命名空间
    :param file_ns: 当前的文件命名空间
    :return: 生成的命令字符串
    """
    if node is None:
        return SB_ASSIGN(
            f"{namespace}{ResultExt}", SB_TEMP,
            Flags.FALSE, SB_FLAGS,
        )

    if isinstance(node, ast.Module):
        ns_init(f"{namespace}", "file")
        temp_map[f"{namespace}\\module"] = []

        # 注册路径
        mkdirs(file_ns_path(file_ns), exist_ok=True)
        file_ns_init(file_ns, None, "folder", namespace)
        mkdirs(file_ns_path(file_ns, "module"), exist_ok=True)
        ns_setter("module", f"{namespace}\\module", namespace, "module")
        file_ns_setter(
            "module.mcfunction", join_file_ns(file_ns, "module.mcfunction"), file_ns,
            "module", "mcfunction", namespace
        )
        file_ns_setter(
            "module", join_file_ns(file_ns, "module"), file_ns,
            "module", "folder", namespace
        )

        # 生成并写入
        with SplitBreakPoint(file_ns_path(file_ns, "module.mcfunction"), namespace, encoding="utf-8") as f:
            f.write(COMMENT(f"Generated by MCFC"))
            f.write(COMMENT(f"Github: https://github.com/C418-11/MinecraftFunctionCompiler"))
            f.write('\n')
            for statement in node.body:
                c = generate_code(statement, f"{namespace}\\module", join_file_ns(file_ns, "module"))
                f.write(c)
            f.write(updateBreakPoint(f"{file_ns}\\module"))

        return ''

    if isinstance(node, ast.Import):
        command = ''
        for n in node.names:
            if not isinstance(n, ast.alias):
                raise Exception("Import 暂时只支持 alias")

            if n.name.startswith("."):
                raise Exception("暂时不支持相对导入")

            command += import_as(n.name, n.asname, namespace)[0]

        return command

    if isinstance(node, ast.ImportFrom):
        command, is_file = import_as(node.module, None, namespace, register_ns=False)
        for n in node.names:
            if not isinstance(n, ast.alias):
                raise Exception("ImportFrom 暂时只支持 alias")

            safe_as_name = n.asname or n.name

            ns_setter(safe_as_name, f"{join_base_ns(node.module)}\\module|{n.name}", namespace, "attribute")

            if is_file:
                continue
            command += import_as(f"{node.module}.{n.name}", None, namespace, register_ns=False)[0]
            ns_setter(safe_as_name, f"{join_base_ns(node.module)}.{n.name}", join_base_ns(node.module), "module")

        return command

    if isinstance(node, ast.FunctionDef):
        # 注册路径
        new_file_ns = join_file_ns(file_ns, f"{node.name}")
        mkdirs(file_ns_path(new_file_ns), exist_ok=True)
        file_ns_setter(
            f"{node.name}", new_file_ns, file_ns,
            "function", "folder", namespace
        )
        file_ns_setter(
            f"{node.name}.mcfunction", join_file_ns(file_ns, f"{node.name}.mcfunction"), file_ns,
            "function", "mcfunction", namespace
        )

        # 生成并写入
        with SplitBreakPoint(file_ns_path(file_ns, f"{node.name}.mcfunction"), namespace, encoding="utf-8") as f:
            ns_setter(node.name, f"{namespace}\\{node.name}", namespace, "function")
            temp_map[f"{namespace}\\{node.name}"] = []

            f.write(COMMENT(f"FunctionDef:函数头"))
            args = generate_code(node.args, f"{namespace}\\{node.name}", new_file_ns)
            f.write(args)
            f.write(COMMENT(f"FunctionDef:函数体"))
            for statement in node.body:
                body = generate_code(statement, f"{namespace}\\{node.name}", new_file_ns)
                f.write(body)
        return ''

    if isinstance(node, ast.Global):
        for n in node.names:
            target_ns = ns_getter(n, namespace)[0]
            ns_setter(n, target_ns, namespace, "variable")
        return ''

    if isinstance(node, ast.If):
        block_uid = newUid()

        base_namespace = f"{namespace}\\.if"

        # 如果父级不是if块，则创建一个if块
        f_ns, f_name = file_ns.rsplit('\\', maxsplit=1)
        f_father_ns = file_ns_getter(f_name, f_ns, ret_raw=True)[0]
        if f_father_ns[".__level__"] != "if":
            file_ns_setter(
                ".if", join_file_ns(file_ns, ".if"),
                file_ns,
                "if", "folder", namespace
            )
            new_file_ns = join_file_ns(file_ns, ".if")
            mkdirs(file_ns_path(new_file_ns), exist_ok=True)
        else:
            new_file_ns = file_ns
        # 注册路径
        if_block_ns = join_file_ns(new_file_ns, f"{block_uid}.mcfunction")
        file_ns_setter(
            f"{block_uid}.mcfunction", if_block_ns,
            new_file_ns,
            "if", "mcfunction", namespace
        )
        else_block_ns = join_file_ns(new_file_ns, f"{block_uid}-else.mcfunction")
        file_ns_setter(
            f"{block_uid}-else.mcfunction", else_block_ns,
            new_file_ns,
            "if", "mcfunction", namespace
        )
        # 生成并写入if块
        with SplitBreakPoint(file_ns_path(if_block_ns), namespace, encoding="utf-8") as f:
            f.write(DEBUG_OBJECTIVE({"text": "进入True分支"}, objective=SB_TEMP, name=f"{namespace}{ResultExt}"))
            for statement in node.body:
                body = generate_code(statement, namespace, new_file_ns)
                f.write(body)
            f.write(updateBreakPoint(file_ns))
        # 生成并写入else块
        with SplitBreakPoint(file_ns_path(else_block_ns), namespace, encoding="utf-8") as f:
            f.write(DEBUG_OBJECTIVE({"text": "进入False分支"}, objective=SB_TEMP, name=f"{namespace}{ResultExt}"))
            for statement in node.orelse:
                body = generate_code(statement, namespace, new_file_ns)
                f.write(body)
            f.write(updateBreakPoint(file_ns))

        command = ''
        func_path = f"{base_namespace}\\{block_uid}".replace('\\', '/')

        command += generate_code(node.test, namespace, file_ns)

        command += COMMENT(f"IF:检查条件")
        command += CHECK_SB(
            SBCheckType.UNLESS,
            f"{namespace}{ResultExt}", SB_TEMP,
            SBCompareType.EQUAL,
            Flags.FALSE, SB_FLAGS,
            f"function {func_path}"
        )
        command += CHECK_SB(
            SBCheckType.IF,
            f"{namespace}{ResultExt}", SB_TEMP,
            SBCompareType.EQUAL,
            Flags.FALSE, SB_FLAGS,
            f"function {func_path}-else"
        )

        command += DEBUG_OBJECTIVE(
            DebugTip.Reset,
            objective=SB_TEMP, name=f"{namespace}{ResultExt}"
        )
        command += SB_RESET(f"{namespace}{ResultExt}", SB_TEMP)

        return command

    if isinstance(node, ast.arguments):
        args = [arg.arg for arg in node.args]

        if namespace in func_args:
            warnings.warn(
                f"函数命名空间 {namespace} 已经存在, 可能覆盖之前的定义",
                UserWarning,
                stacklevel=0
            )

        args_dict = OrderedDict()
        command = ''

        command += COMMENT(f"arguments:处理参数")

        # 反转顺序以匹配默认值
        for name, default in zip_longest(reversed(args), reversed(node.defaults), fillvalue=None):

            if default is None:
                args_dict[name] = ArgType(name)
            elif isinstance(default, ast.Constant):
                default_value = default.value
                args_dict[name] = DefaultArgType(name, default_value)
            else:
                raise Exception("无法解析的默认值")

            gen_code(f"{namespace}.{name}", SB_ARGS)
            ns_setter(name, f"{namespace}.{name}", namespace, "variable")
            command += SB_ASSIGN(
                f"{namespace}.{name}", SB_VARS,
                f"{namespace}.{name}", SB_ARGS
            )

            command += SB_RESET(f"{namespace}.{name}", SB_ARGS)

            command += DEBUG_OBJECTIVE(
                DebugTip.Set,
                objective=SB_VARS, name=f"{namespace}.{name}",
                from_objective=SB_ARGS, from_name=f"{namespace}.{name}"
            )

        # 将最终顺序反转回来
        args_dict = OrderedDict([(k, v) for k, v in reversed(args_dict.items())])

        func_args[namespace] = args_dict

        return command

    if isinstance(node, ast.Name):
        assert isinstance(node.ctx, ast.Load)
        command = ''
        command += COMMENT(f"Name:读取变量", name=node.id)
        target_ns = ns_getter(node.id, namespace)[0]
        command += SB_ASSIGN(
            f"{namespace}{ResultExt}", SB_TEMP,
            f"{target_ns}", SB_VARS
        )
        return command

    if isinstance(node, ast.Attribute):
        assert isinstance(node.ctx, ast.Load)
        if not isinstance(node.value, ast.Name):
            raise Exception("暂时无法解析的值")

        base_namespace = ns_getter(node.value.id, namespace)[0]
        attr_namespace = ns_getter(node.attr, base_namespace)[0]

        command = ''
        command += COMMENT(f"Attribute:读取属性", base_ns=base_namespace, attr=node.attr)

        print(json.dumps(ns_map, indent=4))
        command += SB_ASSIGN(
            f"{namespace}{ResultExt}", SB_TEMP,
            f"{attr_namespace}", SB_VARS
        )

        return command

    if isinstance(node, ast.Return):
        command = ''
        command += COMMENT("Return:计算返回值")

        command += generate_code(node.value, namespace, file_ns)

        command += COMMENT("Return:保存返回值")

        ns, name = namespace.rsplit('\\', 1)
        func_map: dict = ns_getter(name, ns, ret_raw=True)[0]
        if func_map[".__type__"] != "function":
            raise Exception("返回语句不在函数内")

        func_name = func_map[".__namespace__"]

        command += SB_ASSIGN(
            f"{func_name}", SB_FUNC_RESULT,
            f"{namespace}{ResultExt}", SB_TEMP
        )

        command += DEBUG_OBJECTIVE(
            DebugTip.Result,
            objective=SB_FUNC_RESULT, name=f"{func_name}{ResultExt}",
            from_objective=SB_TEMP, from_name=f"{namespace}{ResultExt}"
        )
        command += DEBUG_OBJECTIVE(DebugTip.Reset, objective=SB_TEMP, name=f"{namespace}{ResultExt}")

        command += SB_RESET(f"{namespace}{ResultExt}", SB_TEMP)

        command += COMMENT("BP:Return.Enable")
        breakpoint_id = f"breakpoint_return_{newUid()}"
        command += SB_ASSIGN(
            f"{breakpoint_id}", SB_TEMP,
            Flags.TRUE, SB_FLAGS
        )

        command += FORCE_COMMENT(BreakPointFlag(
            "return",
            name=breakpoint_id,
            objective=SB_TEMP
        ))
        raiseBreakPoint(file_ns, "return", name=breakpoint_id, objective=SB_TEMP)

        return command

    if isinstance(node, ast.BinOp):
        command = ''
        command += COMMENT(f"BinOp:二进制运算", op=type(node.op).__name__)

        command += COMMENT(f"BinOp:处理左值")
        command += generate_code(node.left, namespace, file_ns)

        process_uid = newUid()

        process_ext = f".*BinOp{process_uid}"

        command += SB_ASSIGN(
            f"{namespace}{process_ext}", SB_TEMP,
            f"{namespace}{ResultExt}", SB_TEMP
        )
        temp_map[namespace].append(f"{namespace}{process_ext}")
        command += SB_RESET(f"{namespace}{ResultExt}", SB_TEMP)

        command += COMMENT(f"BinOp:处理右值")
        command += generate_code(node.right, namespace, file_ns)

        if isinstance(node.op, ast.Add):
            command += SB_OP(
                SBOperationType.ADD,
                f"{namespace}{process_ext}", SB_TEMP,
                f"{namespace}{ResultExt}", SB_TEMP
            )
        elif isinstance(node.op, ast.Sub):
            command += SB_OP(
                SBOperationType.SUBTRACT,
                f"{namespace}{process_ext}", SB_TEMP,
                f"{namespace}{ResultExt}", SB_TEMP
            )
        elif isinstance(node.op, ast.Mult):
            command += SB_OP(
                SBOperationType.MULTIPLY,
                f"{namespace}{process_ext}", SB_TEMP,
                f"{namespace}{ResultExt}", SB_TEMP
            )
        elif isinstance(node.op, ast.Div):
            command += SB_OP(
                SBOperationType.DIVIDE,
                f"{namespace}{process_ext}", SB_TEMP,
                f"{namespace}{ResultExt}", SB_TEMP
            )
        else:
            raise Exception(f"无法解析的运算符 {node.op}")

        command += SB_RESET(f"{namespace}{ResultExt}", SB_TEMP)

        command += COMMENT(f"BinOp:传递结果")
        command += SB_ASSIGN(
            f"{namespace}{ResultExt}", SB_TEMP,
            f"{namespace}{process_ext}", SB_TEMP
        )

        command += DEBUG_OBJECTIVE(DebugTip.Calc, objective=SB_TEMP, name=f"{namespace}{ResultExt}")
        command += DEBUG_OBJECTIVE(DebugTip.Reset, objective=SB_TEMP, name=f"{namespace}{process_ext}")

        command += SB_RESET(f"{namespace}{process_ext}", SB_TEMP)
        temp_map[namespace].remove(f"{namespace}{process_ext}")

        return command

    if isinstance(node, ast.UnaryOp):
        command = ''

        command += COMMENT(f"UnaryOp:一元操作", op=type(node.op).__name__)
        command += generate_code(node.operand, namespace, file_ns)

        if isinstance(node.op, ast.Not):
            command += COMMENT(f"UnaryOp:运算", op="Not(not)")
            command += CHECK_SB(
                SBCheckType.UNLESS,
                f"{namespace}{ResultExt}", SB_TEMP,
                SBCompareType.EQUAL,
                Flags.FALSE, SB_FLAGS,
                SB_ASSIGN(
                    f"{namespace}.*UnaryOp", SB_TEMP,
                    Flags.FALSE, SB_FLAGS,
                    line_break=False
                )
            )

            command += CHECK_SB(
                SBCheckType.IF,
                f"{namespace}{ResultExt}", SB_TEMP,
                SBCompareType.EQUAL,
                Flags.FALSE, SB_FLAGS,
                SB_ASSIGN(
                    f"{namespace}.*UnaryOp", SB_TEMP,
                    Flags.TRUE, SB_FLAGS,
                    line_break=False
                )
            )

        elif isinstance(node.op, ast.USub):
            command += COMMENT(f"UnaryOp:运算", op="USub(-)")
            command += SB_ASSIGN(
                f"{namespace}.*UnaryOp", SB_TEMP,
                f"{namespace}{ResultExt}", SB_TEMP
            )
            command += SB_OP(
                SBOperationType.MULTIPLY,
                f"{namespace}.*UnaryOp", SB_TEMP,
                Flags.NEG, SB_FLAGS
            )
        else:
            raise Exception(f"暂时无法解析的UnaryOp运算 {node.op}")

        command += SB_RESET(f"{namespace}{ResultExt}", SB_TEMP)

        command += COMMENT(f"UnaryOp:传递结果")
        command += SB_ASSIGN(
            f"{namespace}{ResultExt}", SB_TEMP,
            f"{namespace}.*UnaryOp", SB_TEMP
        )

        command += DEBUG_OBJECTIVE(DebugTip.Calc, objective=SB_TEMP, name=f"{namespace}{ResultExt}")
        command += DEBUG_OBJECTIVE(DebugTip.Reset, objective=SB_TEMP, name=f"{namespace}.*UnaryOp")

        command += SB_RESET(f"{namespace}.*UnaryOp", SB_TEMP)

        return command

    if isinstance(node, ast.Compare):
        command = ''
        command += COMMENT(f"Compare:比较操作", **{
            f"op{i}": type(cmp).__name__ for i, cmp in enumerate(node.comparators)
        })

        command += COMMENT(f"Compare:处理左值")
        command += generate_code(node.left, namespace, file_ns)

        command += SB_ASSIGN(
            f"{namespace}.*CompareLeft", SB_TEMP,
            f"{namespace}{ResultExt}", SB_TEMP
        )

        command += SB_RESET(f"{namespace}{ResultExt}", SB_TEMP)

        if len(node.ops) > 1:
            raise Exception("暂时无法解析多个比较符")

        command += SB_ASSIGN(
            f"{namespace}.*CompareResult", SB_TEMP,
            Flags.FALSE, SB_FLAGS
        )

        for i, op in enumerate(node.ops):
            command += COMMENT(f"Compare:提取左值")
            command += SB_ASSIGN(
                f"{namespace}.*CompareCalculate", SB_TEMP,
                f"{namespace}.*CompareLeft", SB_TEMP
            )

            command += COMMENT(f"Compare:处理右值")
            command += generate_code(node.comparators[i], namespace, file_ns)

            if isinstance(op, ast.Eq):
                command += COMMENT(f"Compare:比较", op="Eq(==)")
                check_type = SBCheckType.IF
                check_op = SBCompareType.EQUAL
            elif isinstance(op, ast.NotEq):
                command += COMMENT(f"Compare:比较", op="NotEq(!=)")
                check_type = SBCheckType.UNLESS
                check_op = SBCompareType.EQUAL
            elif isinstance(op, ast.Gt):
                command += COMMENT(f"Compare:比较", op="Gt(>)")
                check_type = SBCheckType.IF
                check_op = SBCompareType.MORE
            elif isinstance(op, ast.Lt):
                command += COMMENT(f"Compare:比较", op="Lt(<)")
                check_type = SBCheckType.IF
                check_op = SBCompareType.LESS
            elif isinstance(op, ast.GtE):
                command += COMMENT(f"Compare:比较", op="GtE(>=)")
                check_type = SBCheckType.IF
                check_op = SBCompareType.MORE_EQUAL
            elif isinstance(op, ast.LtE):
                command += COMMENT(f"Compare:比较", op="LtE(<=)")
                check_type = SBCheckType.IF
                check_op = SBCompareType.LESS_EQUAL
            else:
                raise Exception(f"无法解析的比较符 {op}")

            command += CHECK_SB(
                check_type,
                f"{namespace}.*CompareCalculate", SB_TEMP,
                check_op,
                f"{namespace}{ResultExt}", SB_TEMP,
                SB_ASSIGN(
                    f"{namespace}.*CompareResult", SB_TEMP,
                    Flags.TRUE, SB_FLAGS,
                    line_break=False
                )
            )
            command += SB_RESET(f"{namespace}.*CompareCalculate", SB_TEMP)

        command += SB_RESET(f"{namespace}.*CompareLeft", SB_TEMP)

        command += COMMENT(f"Compare:传递结果")
        command += SB_ASSIGN(
            f"{namespace}{ResultExt}", SB_TEMP,
            f"{namespace}.*CompareResult", SB_TEMP
        )

        command += SB_RESET(f"{namespace}.*CompareResult", SB_TEMP)

        return command

    if isinstance(node, ast.Expr):
        command = generate_code(node.value, namespace, file_ns)
        try:
            cmd = SB_RESET(f"{namespace}{ResultExt}", SB_TEMP)
        except KeyError:
            warnings.warn(
                (
                    "The expression unexpectedly has no return value. The reset return value is ignored. "
                    f"namespace=\"{namespace}{ResultExt}\""
                ),
                UserWarning
            )
        else:
            command += COMMENT(f"Expr:清除表达式返回值")
            command += cmd
        return command

    if isinstance(node, ast.Constant):
        value = node.value

        if type(value) is bool:
            value = 1 if value else 0

        if not isinstance(node.value, int):
            raise Exception(f"无法解析的常量 {node.value}")

        command = ''
        command += COMMENT(f"Constant:读取常量", value=value)
        command += SB_CONSTANT(f"{namespace}{ResultExt}", SB_TEMP, value)

        command += DEBUG_OBJECTIVE(DebugTip.Set, objective=SB_TEMP, name=f"{namespace}{ResultExt}")

        return command

    if isinstance(node, ast.Assign):
        command = generate_code(node.value, namespace, file_ns)
        from_namespace = f"{namespace}{ResultExt}"

        for t in node.targets:
            name, _, root_ns = node_to_namespace(t, namespace, not_exists_ok=True, ns_type="variable")

            target_namespace = f"{root_ns}.{name}"

            command += COMMENT(f"Assign:将结果赋值给变量", name=name)
            ns_setter(name, target_namespace, namespace, "variable")
            command += SB_ASSIGN(
                target_namespace, SB_VARS,
                from_namespace, SB_TEMP
            )

            command += DEBUG_OBJECTIVE(
                DebugTip.Assign,
                objective=SB_VARS, name=f"{target_namespace}",
                from_objective=SB_TEMP, from_name=f"{from_namespace}"
            )
            command += DEBUG_OBJECTIVE(DebugTip.Reset, objective=SB_TEMP, name=f"{from_namespace}")

            command += SB_RESET(f"{from_namespace}", SB_TEMP)

        return command

    if isinstance(node, ast.Call):
        is_builtin: bool = False
        if isinstance(node.func, ast.Name) and node.func.id in dir(__builtins__):
            raise Exception("暂不支持python内置函数")
            # is_builtin = True
            # func_name = node.func.id
            # func_ns = f"python:built-in\\{func_name}"
            # ns = "python:built-in"
        else:
            func_name, func_ns, ns = node_to_namespace(node.func, namespace, not_exists_ok=True, ns_type="function")

        commands: str = ''
        commands += COMMENT(f"Call:调用函数")

        # 如果是模版函数，则调用模版函数
        template_func_name = f"{ns.split(':', maxsplit=1)[1]}.{func_name}"
        if template_func_name in template_funcs:
            func_ns = template_funcs[template_func_name]
            commands += COMMENT(f"Template.Call:调用模板函数", func=template_func_name)
            commands += DEBUG_TEXT(
                DebugTip.CallTemplate,
                {"text": f"{func_ns.__name__}", "color": "dark_purple"},
                {"text": f"  "},
                {"text": f"{root_namespace(ns)}", "color": "gray"}
            )
            commands += func_ns(node.args, node.keywords, namespace=namespace, file_namespace=file_ns)
            commands += COMMENT(f"Template.Call:调用模版函数结束")
            return commands

        try:
            this_func_args = func_args[func_ns]
        except KeyError:
            raise Exception(f"未注册过的函数: {func_ns}")

        for name, value in zip_longest(this_func_args, node.args, fillvalue=None):
            if name is None:
                json_value = ast.dump(value)
                raise SyntaxError(f"函数 {func_ns} 在调用时传入了额外的值 {json_value}")

            # 如果参数未提供值，且不是默认值，则报错
            # 否者，使用默认值
            if value is None:
                if not isinstance(this_func_args[name], DefaultArgType):
                    raise SyntaxError(f"函数 {func_ns} 的参数 {name} 未提供值")

                default_value = this_func_args[name].default

                if isinstance(default_value, UnnecessaryParameter):
                    commands += COMMENT(f"Call:忽略参数", name=name)
                    continue

                commands += COMMENT(f"Call:使用默认值", name=name, value=default_value)
                value = ast.Constant(value=this_func_args[name].default)

            commands += COMMENT("Call:计算参数值")
            commands += generate_code(value, namespace, file_ns)

            commands += COMMENT("Call:传递参数", name=name)
            if is_builtin:
                init_name(f"{func_ns}.{name}", SB_ARGS)
            commands += SB_ASSIGN(
                f"{func_ns}.{name}", SB_ARGS,
                f"{namespace}{ResultExt}", SB_TEMP
            )

            commands += DEBUG_OBJECTIVE(
                DebugTip.SetArg,
                objective=SB_ARGS, name=f"{func_ns}.{name}",
                from_objective=SB_TEMP, from_name=f"{namespace}{ResultExt}"
            )
            commands += DEBUG_OBJECTIVE(DebugTip.Reset, objective=SB_TEMP, name=f"{namespace}{ResultExt}")

            commands += SB_RESET(f"{namespace}{ResultExt}", SB_TEMP)

        func_path = func_ns.replace('\\', '/')

        commands += DEBUG_TEXT(DebugTip.Call, {"text": f"{func_path}", "color": "dark_purple"})

        file_ns_setter(
            f"{func_name}.mcfunction$link", func_ns.split(':', maxsplit=1)[1], file_ns,
            "function", "$link", namespace
        )

        # 当在函数中调用函数时
        if namespace != join_base_ns(root_namespace(namespace)) + "\\module":
            store, load = store_local(namespace)
            commands += store
            commands += f"function {func_path}\n"
            commands += load
        else:
            commands += f"function {func_path}\n"

        gen_code(f"{func_ns}", SB_FUNC_RESULT)
        commands += SB_ASSIGN(
            f"{namespace}{ResultExt}", SB_TEMP,
            f"{func_ns}", SB_FUNC_RESULT
        )
        commands += SB_RESET(f"{func_ns}", SB_FUNC_RESULT)

        return commands

    warnings.warn(f"无法解析的节点: {namespace}.{type(node).__name__}", UserWarning)
    err_msg = json.dumps({"text": f"无法解析的节点: {namespace}.{type(node).__name__}", "color": "red"})
    return f"tellraw @a {err_msg}\n" + COMMENT("无法解析的节点:") + COMMENT(ast.dump(node, indent=4))


def _deep_sorted(d: dict | OrderedDict) -> OrderedDict | Any:
    """
    深度排序
    :param d: 需要排序的值
    :return: 排序后的值
    """
    if type(d) is set:
        d = list(d)
    if type(d) in (list, tuple):
        _processed = []
        for item in d:
            _processed.append(_deep_sorted(item))
        _processed.sort()
        return type(d)(_processed)
    if type(d) is dict:
        d = OrderedDict(d)
    if type(d) is not OrderedDict:
        return d

    _sorted_dict = OrderedDict()
    for key in sorted(d.keys()):
        _sorted_dict[key] = _deep_sorted(d[key])
    return _sorted_dict


def main():
    global SAVE_PATH
    global READ_PATH
    global TEMPLATE_PATH
    global BASE_NAMESPACE

    SAVE_PATH = "./.output/"
    # SAVE_PATH = r"D:\game\Minecraft\.minecraft\versions\1.16.5投影\saves\函数\datapacks\函数测试\data\source_code\functions"
    READ_PATH = "./tests"
    TEMPLATE_PATH = "./template"

    BASE_NAMESPACE = "source_code:"
    file_name = "breakpoint_test"

    start_t = time.time()
    with open(os.path.join(READ_PATH, f"{file_name}.py"), mode='r', encoding="utf-8") as _:
        tree = ast.parse(_.read())

    print(ast.dump(tree, indent=4))
    print()

    generate_code(tree, join_base_ns(file_name), file_name)
    end_t = time.time()

    print(f"[DEBUG] TimeUsed={end_t - start_t}")
    print()

    def _debug_dump(v: dict):
        return json.dumps(_deep_sorted(v), indent=4)

    _func_args = OrderedDict()
    for func_ns, args in func_args.items():
        _func_args[func_ns] = OrderedDict()
        for arg in args:
            _func_args[func_ns][arg] = repr(args[arg])

    _dumped_func_args = _debug_dump(_func_args)
    print(f"[DEBUG] FunctionArguments={_dumped_func_args}")
    print()
    _template_func = OrderedDict()
    for name, func in template_funcs.items():
        _template_func[name] = repr(func)
    _dumped_template_func = _debug_dump(_template_func)
    print(f"[DEBUG] TemplateFunctions={_dumped_template_func}")
    print()
    _dumped_sb_name2code = _debug_dump(SB_Name2Code)
    print(f"[DEBUG] SB_Name2Code={_dumped_sb_name2code}")
    print()
    _dumped_ns_map = _debug_dump(ns_map)
    print(f"[DEBUG] NamespaceMap={_dumped_ns_map}")
    print()
    _dumped_temp_map = _debug_dump(temp_map)
    print(f"[DEBUG] TemplateScoreboardVariableMap={_dumped_temp_map}")
    print()
    _dumped_file_map = _debug_dump(file_ns_map)
    print(f"[DEBUG] FileMap={_dumped_file_map}")
    print()


if __name__ == "__main__":
    main()
