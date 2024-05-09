import ast
import json
import os
import sys
import warnings
from collections import OrderedDict
from itertools import zip_longest

from Constant import DataStorageRoot
from Constant import DataStorages
from Constant import Flags
from Constant import ResultExt
from Constant import ScoreBoards
from DebuggingTools import COMMENT
from DebuggingTools import DEBUG_OBJECTIVE
from DebuggingTools import DEBUG_TEXT
from DebuggingTools import DebugTip
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
SB_INPUT: str = ScoreBoards.Input
SB_VARS: str = ScoreBoards.Vars
SB_FUNC_RESULT: str = ScoreBoards.FuncResult

DS_ROOT: str = DataStorageRoot
DS_TEMP: str = DataStorages.Temp
DS_LOCAL_VARS: str = DataStorages.LocalVars
DS_LOCAL_TEMP: str = DataStorages.LocalTemp

SAVE_PATH: None | str = None
READ_PATH: None | str = None
TEMPLATE_PATH: None | str = None
BASE_NAMESPACE: None | str = None


def is_parent_path(path1, path2):
    path1 = os.path.abspath(path1)
    path2 = os.path.abspath(path2)
    return os.path.commonpath([path1, path2]) == path1


def join_base_ns(path: str) -> str:
    if BASE_NAMESPACE.endswith(":"):
        new_namespace = f"{BASE_NAMESPACE}{path}"
    else:
        new_namespace = f"{BASE_NAMESPACE}\\{path}"

    return new_namespace


def namespace_path(namespace: str, path: str) -> str:
    base_path = os.path.join(namespace.split(":", 1)[1], path)
    return os.path.join(SAVE_PATH, base_path)


def root_namespace(namespace: str) -> str:
    return namespace.split(":", 1)[1].split('\\')[0]


Uid = 0


def newUid() -> str:
    global Uid
    Uid += 1
    return hex(Uid)[2:]


import_module_map: dict[str, dict[str, str]] = {}
from_import_map: dict[str, dict[str, tuple[str, str]]] = {}


def node_to_namespace(node, namespace: str) -> tuple[str, str | None, str | None]:
    """
    :param node: AST节点
    :param namespace: 当前命名空间
    :return: (name, full_namespace, root_namespace)
    """

    if type(node) is str:
        return node, None, None

    if isinstance(node, ast.Name):
        from_modules = from_import_map[root_namespace(namespace)]
        if node.id not in from_modules:
            return node.id, f"{namespace}\\{node.id}", namespace

        return node_to_namespace(
            ast.Attribute(
                value=from_modules[node.id][0],
                attr=from_modules[node.id][1],
                ctx=ast.Load()
            ),
            namespace
        )

    if isinstance(node, ast.Attribute):
        modules = import_module_map[root_namespace(namespace)]

        node_value = node_to_namespace(node.value, namespace)[0]

        if node_value not in modules:
            print(node_value, modules, file=sys.stderr)
            raise Exception("未导入模块")

        return (
            node.attr,
            join_base_ns(f"{modules[node_value]}\\{node.attr}"),
            join_base_ns(f"{modules[node_value]}")
        )

    raise Exception("暂时不支持的节点类型")


ns_map: OrderedDict[str, OrderedDict[str, ...]] = OrderedDict()


def ns_setter(name: str, targe_namespace: str, namespace: str, _type: str = None) -> None:

    data = {
        name: {
            ".__namespace__": targe_namespace,
            ".__type__": _type
        }
    }

    try:
        last_ns, last_name = namespace.rsplit('\\', 1)
    except ValueError:
        ns_map[namespace].update(data)
    else:
        ns_map[last_ns][last_name].update(data)


def ns_getter(name, namespace: str, ret_raw: bool = False) -> tuple[str | dict, str]:

    """

    :param name: 需要寻找的名称
    :param namespace: 在那个命名空间下进行寻找
    :param ret_raw: 是否直接返回源字典
    :return: 当ret_raw为True时直接返回源字典，否则返回所找到的完整命名空间
    """

    last_map: dict[str, dict[str, ...]] = ns_map
    last_result: dict | None = None

    ns_ls: list[str] = []
    last_ns: list[str] = []

    for ns_name in namespace.split('\\'):
        last_map = last_map[ns_name]
        if name in last_map:
            last_result = last_map[name]
            last_ns = ns_ls

        ns_ls.append(ns_name)

    if name in last_map:
        last_result = last_map[name]
        last_ns = ns_ls

    if last_result is None:
        raise Exception(f"未在命名空间找到 {name}")

    if not ret_raw:
        last_result = last_result[".__namespace__"]

    return last_result, '\\'.join(last_ns)


temp_map: OrderedDict[str, list[str]] = OrderedDict()


def store_local(namespace: str) -> tuple[str, str]:
    _ns, _name = namespace.split('\\', 1)
    local_ns: dict[str, dict[str, ...]] = ns_getter(_name, _ns, ret_raw=True)[0]

    ns_ls: list[str] = []

    for name in local_ns:
        if name.startswith("."):
            continue
        data = local_ns[name]
        if data[".__type__"] != "variable":
            continue
        ns_ls.append(data[".__namespace__"])

    def store() -> str:
        nonlocal ns_ls
        command = ''
        command += COMMENT("LocalVars.Store")
        for ns in ns_ls:
            command += (
                f"execute store result storage "
                f"{DS_ROOT} {DS_TEMP} "
                f"int 1 "
                f"run scoreboard players get {SB_Name2Code[SB_VARS][ns]} {SB_VARS}\n"
            )
            command += (
                f"data modify storage "
                f"{DS_ROOT} {DS_LOCAL_VARS} "
                f"append from storage "
                f"{DS_ROOT} {DS_TEMP}\n"
            )
        command += COMMENT("LocalTemp.Store")
        for ns in temp_map[namespace]:
            command += (
                f"execute store result storage "
                f"{DS_ROOT} {DS_TEMP} "
                f"int 1 "
                f"run scoreboard players get {SB_Name2Code[SB_TEMP][ns]} {SB_TEMP}\n"
            )
            command += (
                f"data modify storage "
                f"{DS_ROOT} {DS_LOCAL_TEMP} "
                f"append from storage "
                f"{DS_ROOT} {DS_TEMP}\n"
            )

        return command

    def load() -> str:
        nonlocal ns_ls
        command = ''
        command += COMMENT("LocalVars.Load")
        for ns in ns_ls[::-1]:
            command += (
                f"execute store result score "
                f"{SB_Name2Code[SB_VARS][ns]} {SB_VARS} "
                f"run data get storage "
                f"{DS_ROOT} {DS_LOCAL_VARS}[-1] 1\n"
            )
            command += (
                f"data remove storage "
                f"{DS_ROOT} {DS_LOCAL_VARS}[-1]\n"
            )
        command += COMMENT("LocalTemp.Load")
        for ns in temp_map[namespace][::-1]:
            command += (
                f"execute store result score "
                f"{SB_Name2Code[SB_TEMP][ns]} {SB_TEMP} "
                f"run data get storage "
                f"{DS_ROOT} {DS_LOCAL_TEMP}[-1] 1\n"
            )
            command += (
                f"data remove storage "
                f"{DS_ROOT} {DS_LOCAL_TEMP}[-1]\n"
            )

        return command

    return store(), load()


def generate_code(node, namespace: str) -> str:
    os.makedirs(namespace_path(namespace, ''), exist_ok=True)

    if isinstance(node, ast.Module):
        ns_map[namespace] = OrderedDict()
        import_module_map[root_namespace(namespace)] = {}
        from_import_map[root_namespace(namespace)] = {}
        with open(namespace_path(namespace, ".__module.mcfunction"), mode='w', encoding="utf-8") as f:
            f.write(COMMENT(f"Generated by MCFC"))
            f.write(COMMENT(f"Github: https://github.com/C418-11/MinecraftFunctionCompiler"))
            f.write('\n')
            for statement in node.body:
                c = generate_code(statement, namespace)
                f.write(c)

        return ''

    if isinstance(node, ast.Import):
        command = ''
        for n in node.names:
            if not isinstance(n, ast.alias):
                raise Exception("Import 暂时只支持 alias")

            if n.name.startswith("."):
                raise Exception("暂时不支持相对导入")

            pack_path = n.name.replace(".", "\\")
            file_path = os.path.join(READ_PATH, f"{pack_path}.py")

            as_name = n.asname if n.asname is not None else n.name

            if not os.path.exists(file_path):

                template_path = f"{pack_path}.py"
                if not is_parent_path(READ_PATH, file_path):
                    template_path = os.path.join(TEMPLATE_PATH, f"{pack_path}.py")

                res = check_template(template_path)
                if res:
                    import_module_map[root_namespace(namespace)].update({as_name: n.name})
                    init_template(n.name)
                    continue
                else:
                    raise Exception(f"未找到模板文件 {template_path}")

            with open(file_path, mode='r', encoding="utf-8") as f:
                tree = ast.parse(f.read())

            print("------------导入文件-----------")
            print(os.path.normpath(os.path.join(READ_PATH, f"{n.name}.py")))
            print(ast.dump(tree, indent=4))
            print("------------------------------")

            new_namespace = join_base_ns(n.name)
            generate_code(tree, new_namespace)

            if as_name in import_module_map[root_namespace(namespace)]:
                warnings.warn(
                    f"导入模块 {as_name} 已经存在, 可能覆盖之前的定义",
                    UserWarning
                )
            import_module_map[root_namespace(namespace)].update({as_name: n.name})
            ns_map[namespace].update({as_name: {".__namespace__": new_namespace, ".__type__": "module"}})

            command += COMMENT(f"Import:导入模块", name=n.name, as_name=as_name)
            command += DEBUG_TEXT(
                DebugTip.Init,
                {"text": f"导入 ", "color": "gold", "bold": True},
                {"text": f"{n.name}", "color": "dark_purple"},
                {"text": f" 用作 ", "color": "gold"},
                {"text": f"{as_name}", "color": "dark_purple"},
            )
            command += f"function {new_namespace}/.__module\n"
        return command

    if isinstance(node, ast.ImportFrom):
        for n in node.names:
            if not isinstance(n, ast.alias):
                raise Exception("ImportFrom 暂时只支持 alias")

            as_name = n.asname if n.asname is not None else n.name

            if as_name in import_module_map[root_namespace(namespace)]:
                warnings.warn(
                    f"导入模块 {as_name} 已经存在, 可能覆盖之前的定义",
                    UserWarning
                )
            from_import_map[root_namespace(namespace)].update({as_name: (node.module, n.name)})
            # ns_setter(as_name, f"{as_name}", namespace)

        return generate_code(ast.Import(names=[ast.alias(name=node.module, asname=None)]), namespace)

    if isinstance(node, ast.FunctionDef):
        with open(namespace_path(namespace, f"{node.name}.mcfunction"), mode='w', encoding="utf-8") as f:
            ns_setter(node.name, f"{namespace}\\{node.name}", namespace, "function")
            temp_map[f"{namespace}\\{node.name}"] = []

            f.write(COMMENT(f"FunctionDef:函数头"))
            args = generate_code(node.args, f"{namespace}\\{node.name}")
            f.write(args)
            f.write(COMMENT(f"FunctionDef:函数体"))
            for statement in node.body:
                body = generate_code(statement, f"{namespace}\\{node.name}")
                f.write(body)
        return ''

    if isinstance(node, ast.Global):
        root_ns = join_base_ns(root_namespace(namespace))
        for n in node.names:
            ns_setter(n, f"{root_ns}.{n}", namespace, "variable")
        return ''

    if isinstance(node, ast.If):
        block_uid = newUid()

        base_namespace = f"{namespace}\\.if"

        base_path = namespace_path(base_namespace, '')
        os.makedirs(base_path, exist_ok=True)

        with open(os.path.join(base_path, f"{block_uid}.mcfunction"), mode='w', encoding="utf-8") as f:
            f.write(DEBUG_OBJECTIVE({"text": "进入True分支"}, objective=SB_TEMP, name=f"{namespace}{ResultExt}"))
            for statement in node.body:
                body = generate_code(statement, namespace)
                f.write(body)
        with open(os.path.join(base_path, f"{block_uid}-else.mcfunction"), mode='w', encoding="utf-8") as f:
            f.write(DEBUG_OBJECTIVE({"text": "进入False分支"}, objective=SB_TEMP, name=f"{namespace}{ResultExt}"))
            for statement in node.orelse:
                body = generate_code(statement, namespace)
                f.write(body)

        command = ''
        func_path = f"{base_namespace}\\{block_uid}".replace('\\', '/')

        command += generate_code(node.test, namespace)

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

        command += SB_ASSIGN(
            f"{namespace}{ResultExt}", SB_TEMP,
            f"{attr_namespace}", SB_VARS
        )

        return command

    if isinstance(node, ast.Return):
        command = ''
        command += COMMENT("Return:计算返回值")
        command += generate_code(node.value, namespace)

        command += COMMENT("Return:保存返回值")

        ns, name = namespace.split('\\', 1)
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

        return command

    if isinstance(node, ast.BinOp):
        command = ''
        command += COMMENT(f"BinOp:二进制运算", op=type(node.op).__name__)

        command += COMMENT(f"BinOp:处理左值")
        command += generate_code(node.left, namespace)

        process_uid = newUid()

        process_ext = f".*BinOp{process_uid}"

        command += SB_ASSIGN(
            f"{namespace}{process_ext}", SB_TEMP,
            f"{namespace}{ResultExt}", SB_TEMP
        )
        temp_map[namespace].append(f"{namespace}{process_ext}")
        command += SB_RESET(f"{namespace}{ResultExt}", SB_TEMP)

        command += COMMENT(f"BinOp:处理右值")
        command += generate_code(node.right, namespace)

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
        command += generate_code(node.operand, namespace)

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
        command += generate_code(node.left, namespace)

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
            command += generate_code(node.comparators[i], namespace)

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
        return generate_code(node.value, namespace)

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
        command = generate_code(node.value, namespace)
        from_namespace = f"{namespace}{ResultExt}"

        for t in node.targets:
            name, _, root_ns = node_to_namespace(t, namespace)

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
        func_name, func_ns, ns = node_to_namespace(node.func, namespace)
        commands: str = ''

        # 如果是python内置函数，则不需要加上命名空间
        is_builtin: bool = False
        if func_name in dir(__builtins__):
            func_ns = f"python:built-in\\{func_name}"
            is_builtin = True

        # 如果是模版函数，则调用模版函数
        elif f"{root_namespace(ns)}.{func_name}" in template_funcs:
            func_ns = template_funcs[f"{root_namespace(ns)}.{func_name}"]
            commands += COMMENT(f"Template.Call:调用模板函数", func=func_ns.__name__, namespace=root_namespace(ns))
            commands += DEBUG_TEXT(
                DebugTip.CallTemplate,
                {"text": f"{func_ns.__name__}", "color": "dark_purple"},
                {"text": f"  "},
                {"text": f"{root_namespace(ns)}", "color": "gray"}
            )
            commands += func_ns(node.args, node.keywords, namespace=namespace)
            commands += COMMENT(f"Template.Call:调用模版函数结束")
            return commands
        else:
            func_ns, ns = ns_getter(func_name, ns)

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
            commands += generate_code(value, namespace)

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
        # 当在函数中调用函数时
        if namespace != join_base_ns(root_namespace(namespace)):
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

    err_msg = json.dumps({"text": f"无法解析的节点: {namespace}.{type(node).__name__}", "color": "red"})
    return f"tellraw @a {err_msg}\n" + COMMENT("无法解析的节点:") + COMMENT(ast.dump(node, indent=4))


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
    file_name = "recursive_call"

    with open(os.path.join(READ_PATH, f"{file_name}.py"), mode='r', encoding="utf-8") as _:
        tree = ast.parse(_.read())

    print(ast.dump(tree, indent=4))
    print(generate_code(tree, join_base_ns(file_name)))
    print(f"[DEBUG] {func_args=}")
    print()
    print(f"[DEBUG] {import_module_map=}")
    print()
    print(f"[DEBUG] {from_import_map=}")
    print()
    print(f"[DEBUG] {template_funcs=}")
    print()
    _dumped_sb_name2code = json.dumps(SB_Name2Code, indent=4)
    print(f"[DEBUG] SB_Name2Code={_dumped_sb_name2code}")
    print()
    _dumped_ns_map = json.dumps(ns_map, indent=4)
    print(f"[DEBUG] NamespaceMap={_dumped_ns_map}")
    print()
    _dumped_temp_map = json.dumps(temp_map, indent=4)
    print(f"[DEBUG] TemplateScoreboardVariableMap={_dumped_temp_map}")


if __name__ == "__main__":
    main()
