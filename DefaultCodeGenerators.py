# -*- coding: utf-8 -*-
# cython: language_level = 3
"""
一堆默认的代码生成器
"""

import ast
import inspect
import os
import time
import warnings
from collections import OrderedDict
from itertools import zip_longest

from ABCTypes import ABCEnvironment
from BreakPointTools import BreakPointFlag
from BreakPointTools import raiseBreakPoint
from BreakPointTools import register_processor
from BreakPointTools import updateBreakPoint
from Configuration import CompileConfiguration
from Configuration import GlobalConfiguration
from DebuggingTools import FORCE_COMMENT
from NamespaceTools import join_file_ns
from ParameterTypes import ABCDefaultParameter
from ParameterTypes import ABCKeyword
from ParameterTypes import ABCVariableLengthParameter
from ParameterTypes import parse_arguments
from ScoreboardTools import CHECK_SB
from ScoreboardTools import SBCheckType
from ScoreboardTools import SBCompareType
from ScoreboardTools import SBOperationType
from ScoreboardTools import SB_ASSIGN
from ScoreboardTools import SB_CONSTANT
from ScoreboardTools import SB_OP
from ScoreboardTools import SB_RESET
from ScoreboardTools import gen_code
from Template import call_template
from Template import check_template
from Template import init_template
from Template import template_funcs

loaded_modules: dict[str, bool] = {}


def is_parent_path(path1, path2):
    path1 = os.path.abspath(path1)
    path2 = os.path.abspath(path2)
    return os.path.commonpath([path1, path2]) == path1


def is_import_alive(import_path: str, base: str = '') -> tuple[str | None, bool | None]:
    package_local_path = import_path.replace(".", "\\")

    full_path = os.path.normpath(os.path.join(base, package_local_path))
    if os.path.isfile(f"{full_path}.py"):
        return f"{full_path}.py", True
    if os.path.isdir(full_path):
        return full_path, False
    return None, None


def import_as(
        env: ABCEnvironment,
        c_conf: CompileConfiguration,
        g_conf: GlobalConfiguration,
        name: str, as_name: str | None, namespace: str, *, register_ns: bool = True) -> tuple[str, bool]:
    package_local_path = name.replace(".", "\\")

    safe_as_name = as_name or name

    is_template: bool = False
    sourcefile_path, is_file = is_import_alive(name, c_conf.READ_PATH)
    if sourcefile_path is None:

        base_path = c_conf.TEMPLATE_PATH
        if is_parent_path(c_conf.TEMPLATE_PATH, package_local_path):
            base_path = ''

        sourcefile_path, is_file = is_import_alive(name, base_path)
        if sourcefile_path is None:
            raise Exception(f"无法导入 '{name}', {package_local_path}")
        is_template = True

    if (not is_template) and check_template(sourcefile_path):
        is_template = True

    command = ''

    if is_file and not is_template:
        new_namespace = env.ns_join_base(name)
        if register_ns:
            env.ns_setter(safe_as_name, f"{new_namespace}\\module", namespace, "module")

        def _load():
            nonlocal command
            start_t = time.time()
            with open(sourcefile_path, mode='r', encoding="utf-8") as f:
                tree = ast.parse(f.read())

            if c_conf.DEBUG_MODE:
                print("------------导入文件-----------")
                print(sourcefile_path)
                print(ast.dump(tree, indent=4))
                print("------------------------------")

            env.generate_code(tree, new_namespace, name)
            end_t = time.time()

            if c_conf.DEBUG_MODE:
                print(f"编译导入模块 {sourcefile_path}, 耗时{end_t - start_t}秒")

            command += f"function {new_namespace}/.__module\n"

        if sourcefile_path not in loaded_modules:
            _load()
            loaded_modules[sourcefile_path] = True
        else:
            print(f"重复导入模块 {sourcefile_path}")

    if is_file and is_template:
        init_template(name, env, c_conf, g_conf)
        env.ns_init(env.ns_join_base(name), "module")
        env.ns_setter("module", f"{env.ns_join_base(name)}\\module", env.ns_join_base(name), "module")
    elif is_template:
        env.ns_init(env.ns_join_base(name), "package")

    return command, is_file


@register_processor("return")
def sbp_return(
        env: ABCEnvironment,
        g_conf: GlobalConfiguration,
        func_path: str, level: str, name: str, objective: str) -> tuple[str, bool] | str:
    """
    处理return语句的断点

    :param env: 运行环境
    :type env: ABCEnvironment
    :param g_conf: 全局配置
    :type g_conf: GlobalConfiguration
    :param func_path: 断点切断后恢复执行需要调用的函数
    :type func_path: str
    :param level: 文件命名空间层级名
    :type level: str
    :param name: 标记位目标
    :type name: str
    :param objective: 标记位计分项
    :type objective: str
    :returns: 生成的命令字符串, 是否继续抛出断点
    :rtype: tuple[str, bool] | str
    """

    def _process_raise() -> tuple[str, bool]:
        command = ''
        keep_raise: bool = True
        if level in ["module", "function"]:
            command += env.COMMENT("BP:Return.Reset")
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
        command += env.COMMENT("BP:Return.Split")
        command += CHECK_SB(
            SBCheckType.UNLESS,
            name, objective,
            SBCompareType.EQUAL,
            g_conf.Flags.TRUE, g_conf.SB_FLAGS,
            f"function {func_path}"
        )

        return command

    if func_path is None:
        return _process_raise()

    if level is None:
        return _process_split()


DefaultCodeGenerators: dict = {}


def register_default_gen(node_type):
    def decorator(func):
        parameters = set(inspect.signature(func).parameters.keys())
        DefaultCodeGenerators[node_type] = {"func": func, "params": parameters}
        return func

    return decorator


@register_default_gen(type(None))
def gen_none(g_conf: GlobalConfiguration, namespace: str) -> str:
    return SB_ASSIGN(
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
        g_conf.Flags.FALSE, g_conf.SB_FLAGS,
    )


@register_default_gen(ast.Module)
def gen_module(
        env: ABCEnvironment,
        c_conf: CompileConfiguration,
        g_conf: GlobalConfiguration,
        node: ast.Module, namespace: str, file_namespace: str) -> str:
    env.ns_init(f"{namespace}", "file")
    env.temp_ns_init(f"{namespace}\\module")

    # 注册路径
    env.mkdirs_file_ns(file_namespace)
    env.file_ns_init(file_namespace, None, "folder", namespace)
    env.mkdirs_file_ns(file_namespace, "module")
    env.ns_setter("module", f"{namespace}\\module", namespace, "module")
    env.file_ns_setter(  # 注册文件
        "module.mcfunction",
        join_file_ns(file_namespace, "module.mcfunction"),
        file_namespace,
        "module",
        "mcfunction",
        namespace
    )
    env.file_ns_setter(  # 注册文件夹
        "module",
        join_file_ns(file_namespace, "module"),
        file_namespace,
        "module",
        "folder",
        namespace
    )

    # 生成并写入
    with env.writeable_file_namespace(join_file_ns(file_namespace, "module.mcfunction"), namespace) as f:
        for statement in node.body:
            c = env.generate_code(statement, f"{namespace}\\module", join_file_ns(file_namespace, "module"))
            f.write(c)
        f.write(updateBreakPoint(env, c_conf, g_conf, f"{file_namespace}\\module"))

    return ''


@register_default_gen(ast.Name)
def gen_name(env: ABCEnvironment, g_conf: GlobalConfiguration, node: ast.Name, namespace: str) -> str:
    assert isinstance(node.ctx, ast.Load)
    command = ''
    command += env.COMMENT(f"Name:读取变量", name=node.id)
    target_ns = env.ns_getter(node.id, namespace)[0]
    command += SB_ASSIGN(
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
        f"{target_ns}", g_conf.SB_VARS
    )
    return command


@register_default_gen(ast.Call)
def gen_call(
        env: ABCEnvironment,
        c_conf: CompileConfiguration,
        g_conf: GlobalConfiguration, node, namespace: str, file_namespace: str) -> str:
    if isinstance(node.func, ast.Name) and node.func.id in dir(__builtins__):
        raise Exception("暂不支持python内置函数")
    else:
        func_name, func_ns, ns = env.ns_from_node(node.func, namespace, not_exists_ok=True, ns_type="function")

    commands: str = ''
    commands += env.COMMENT(f"Call:调用函数")

    # 如果是模版函数，则调用模版函数
    template_func_name = f"{ns.split(':', maxsplit=1)[1]}.{func_name}"
    if template_func_name in template_funcs:
        commands += call_template(env, c_conf, g_conf, template_func_name, node, namespace, file_namespace)
        return commands

    try:
        this_func_args = env.func_args[func_ns]
    except KeyError:
        raise Exception(f"未注册过的函数: {func_ns}")

    for name, value in zip_longest(this_func_args, node.args, fillvalue=None):
        if name is None:
            json_value = ast.dump(value)
            raise SyntaxError(f"函数 {func_ns} 在调用时传入了额外的值 {json_value}")

        # 如果参数未提供值，且不是默认值，则报错
        # 否者，使用默认值
        if value is None:
            argument = this_func_args[name]
            if not isinstance(argument, ABCDefaultParameter):
                raise SyntaxError(f"函数 {func_ns} 的参数 {name} 未提供值")

            default_value = argument.default

            commands += env.COMMENT(f"Call:使用默认值", name=name, value=default_value)
            value = ast.Constant(value=argument.default)

        commands += env.COMMENT("Call:计算参数值")
        commands += env.generate_code(value, namespace, file_namespace)

        commands += env.COMMENT("Call:传递参数", name=name)
        commands += SB_ASSIGN(
            f"{func_ns}.{name}", g_conf.SB_ARGS,
            f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP
        )

        commands += SB_RESET(f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP)

    func_path = func_ns.replace('\\', '/')

    env.file_ns_setter(
        f"{func_name}.mcfunction$link", func_ns.split(':', maxsplit=1)[1], file_namespace,
        "function", "$link", namespace
    )

    # 当在函数中调用函数时
    if namespace != env.ns_join_base(env.ns_split_base(namespace)[1]) + "\\module":
        store, load = env.ns_store_local(namespace)
        commands += store
        commands += f"function {func_path}\n"
        commands += load
    else:
        commands += f"function {func_path}\n"

    gen_code(f"{func_ns}", g_conf.SB_FUNC_RESULT)
    commands += SB_ASSIGN(
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
        f"{func_ns}", g_conf.SB_FUNC_RESULT
    )
    commands += SB_RESET(f"{func_ns}", g_conf.SB_FUNC_RESULT)

    return commands


@register_default_gen(ast.Constant)
def gen_constant(
        env: ABCEnvironment,
        g_conf: GlobalConfiguration, node: ast.Constant, namespace: str) -> str:
    value = node.value

    if type(value) is bool:
        value = 1 if value else 0

    if not isinstance(node.value, int):
        raise Exception(f"无法解析的常量 {node.value}")

    command = ''
    command += env.COMMENT(f"Constant:读取常量", value=value)
    command += SB_CONSTANT(f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP, value)

    return command


@register_default_gen(ast.Attribute)
def gen_attribute(env: ABCEnvironment, g_conf: GlobalConfiguration, node: ast.Attribute, namespace: str) -> str:
    assert isinstance(node.ctx, ast.Load)
    if not isinstance(node.value, ast.Name):
        raise Exception("暂时无法解析的值")

    base_namespace = env.ns_getter(node.value.id, namespace)[0]
    attr_namespace = env.ns_getter(node.attr, base_namespace)[0]

    command = ''
    command += env.COMMENT(f"Attribute:读取属性", base_ns=base_namespace, attr=node.attr)

    command += SB_ASSIGN(
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
        f"{attr_namespace}", g_conf.SB_VARS
    )

    return command


@register_default_gen(ast.Expr)
def gen_expr(
        env: ABCEnvironment,
        g_conf: GlobalConfiguration, node: ast.Expr, namespace: str, file_namespace: str) -> str:
    command = env.generate_code(node.value, namespace, file_namespace)
    try:
        cmd = SB_RESET(f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP)
    except KeyError:
        warnings.warn(
            (
                "The expression unexpectedly has no return value. The reset return value is ignored. "
                f"namespace=\"{namespace}{g_conf.ResultExt}\""
            ),
            UserWarning
        )
    else:
        command += env.COMMENT(f"Expr:清除表达式返回值")
        command += cmd
    return command


@register_default_gen(ast.BinOp)
def gen_bin_op(
        env: ABCEnvironment,
        g_conf: GlobalConfiguration, node: ast.BinOp, namespace: str, file_namespace: str) -> str:
    command = ''
    command += env.COMMENT(f"BinOp:二进制运算", op=type(node.op).__name__)

    command += env.COMMENT(f"BinOp:处理左值")
    command += env.generate_code(node.left, namespace, file_namespace)

    process_uid = env.newID("process")

    process_ext = f".*BinOp{process_uid}"

    command += SB_ASSIGN(
        f"{namespace}{process_ext}", g_conf.SB_TEMP,
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP
    )
    env.temp_ns_append(namespace, f"{namespace}{process_ext}")
    command += SB_RESET(f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP)

    command += env.COMMENT(f"BinOp:处理右值")
    command += env.generate_code(node.right, namespace, file_namespace)

    if isinstance(node.op, ast.Add):
        command += SB_OP(
            SBOperationType.ADD,
            f"{namespace}{process_ext}", g_conf.SB_TEMP,
            f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP
        )
    elif isinstance(node.op, ast.Sub):
        command += SB_OP(
            SBOperationType.SUBTRACT,
            f"{namespace}{process_ext}", g_conf.SB_TEMP,
            f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP
        )
    elif isinstance(node.op, ast.Mult):
        command += SB_OP(
            SBOperationType.MULTIPLY,
            f"{namespace}{process_ext}", g_conf.SB_TEMP,
            f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP
        )
    elif isinstance(node.op, ast.Div):
        command += SB_OP(
            SBOperationType.DIVIDE,
            f"{namespace}{process_ext}", g_conf.SB_TEMP,
            f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP
        )
    else:
        raise Exception(f"无法解析的运算符 {node.op}")

    command += SB_RESET(f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP)

    command += env.COMMENT(f"BinOp:传递结果")
    command += SB_ASSIGN(
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
        f"{namespace}{process_ext}", g_conf.SB_TEMP
    )

    command += SB_RESET(f"{namespace}{process_ext}", g_conf.SB_TEMP)
    env.temp_ns_remove(namespace, f"{namespace}{process_ext}")

    return command


@register_default_gen(ast.Assign)
def gen_assign(
        env: ABCEnvironment, g_conf: GlobalConfiguration, node: ast.Assign, namespace: str, file_namespace: str) -> str:
    command = env.generate_code(node.value, namespace, file_namespace)
    from_namespace = f"{namespace}{g_conf.ResultExt}"

    for t in node.targets:
        name, _, root_ns = env.ns_from_node(t, namespace, not_exists_ok=True, ns_type="variable")

        target_namespace = f"{root_ns}.{name}"

        command += env.COMMENT(f"Assign:将结果赋值给变量", name=name)
        env.ns_setter(name, target_namespace, namespace, "variable")
        command += SB_ASSIGN(
            target_namespace, g_conf.SB_VARS,
            from_namespace, g_conf.SB_TEMP
        )

        command += SB_RESET(f"{from_namespace}", g_conf.SB_TEMP)

    return command


@register_default_gen(ast.Import)
def gen_import(
        env: ABCEnvironment,
        c_conf: CompileConfiguration,
        g_conf: GlobalConfiguration,
        node: ast.Import, namespace: str) -> str:
    command = ''
    for n in node.names:
        if not isinstance(n, ast.alias):
            raise Exception("Import 暂时只支持 alias")

        if n.name.startswith("."):
            raise Exception("暂时不支持相对导入")

        command += import_as(env, c_conf, g_conf, n.name, n.asname, namespace)[0]

    return command


@register_default_gen(ast.ImportFrom)
def gen_import_from(
        env: ABCEnvironment,
        c_conf: CompileConfiguration,
        g_conf: GlobalConfiguration,
        node: ast.ImportFrom, namespace: str) -> str:
    command, is_file = import_as(env, c_conf, g_conf, node.module, None, namespace, register_ns=False)
    for n in node.names:
        if not isinstance(n, ast.alias):
            raise Exception("ImportFrom 暂时只支持 alias")

        safe_as_name = n.asname or n.name

        env.ns_setter(
            safe_as_name, f"{env.ns_join_base(node.module)}\\module|{n.name}", namespace, "attribute")

        if is_file:
            continue
        command += import_as(env, c_conf, g_conf, f"{node.module}.{n.name}", None, namespace, register_ns=False)[0]
        env.ns_setter(
            safe_as_name, f"{env.ns_join_base(node.module)}.{n.name}", env.ns_join_base(node.module), "module")

    return command


@register_default_gen(ast.FunctionDef)
def gne_func_def(
        env: ABCEnvironment,
        node: ast.FunctionDef, namespace: str, file_namespace: str) -> str:
    # 注册路径
    new_file_ns = join_file_ns(file_namespace, f"{node.name}")
    env.mkdirs_file_ns(new_file_ns)
    env.file_ns_setter(
        f"{node.name}", new_file_ns, file_namespace,
        "function", "folder", namespace
    )
    func_file_ns = join_file_ns(file_namespace, f"{node.name}.mcfunction")
    env.file_ns_setter(
        f"{node.name}.mcfunction", func_file_ns, file_namespace,
        "function", "mcfunction", namespace
    )

    # 生成并写入
    with env.writeable_file_namespace(func_file_ns, namespace) as f:
        env.ns_setter(node.name, f"{namespace}\\{node.name}", namespace, "function")
        env.temp_ns_init(f"{namespace}\\{node.name}")

        f.write(env.COMMENT(f"FunctionDef:函数头"))
        args = env.generate_code(node.args, f"{namespace}\\{node.name}", new_file_ns)
        f.write(args)
        f.write(env.COMMENT(f"FunctionDef:函数体"))
        for statement in node.body:
            body = env.generate_code(statement, f"{namespace}\\{node.name}", new_file_ns)
            f.write(body)
    return ''


@register_default_gen(ast.Global)
def gen_global(
        env: ABCEnvironment, node: ast.Global, namespace: str) -> str:
    for n in node.names:
        target_ns = env.ns_getter(n, namespace)[0]
        env.ns_setter(n, target_ns, namespace, "variable")
    return ''


@register_default_gen(ast.If)
def gen_if(
        env: ABCEnvironment,
        c_conf: CompileConfiguration,
        g_conf: GlobalConfiguration,
        node: ast.If, namespace: str, file_namespace: str) -> str:
    block_uid = env.newID("if-block")

    base_namespace = f"{namespace}\\.if"

    # 如果父级不是if块，则创建一个if块
    f_ns, f_name = file_namespace.rsplit('\\', maxsplit=1)
    f_father_ns = env.file_ns_getter(f_name, f_ns, ret_raw=True)[0]
    if f_father_ns[".__level__"] != "if":
        env.file_ns_setter(
            ".if", join_file_ns(file_namespace, ".if"),
            file_namespace,
            "if", "folder", namespace
        )
        new_file_ns = join_file_ns(file_namespace, ".if")
        env.mkdirs_file_ns(new_file_ns)
    else:
        new_file_ns = file_namespace
    # 注册路径
    if_block_ns = join_file_ns(new_file_ns, f"{block_uid}.mcfunction")
    env.file_ns_setter(
        f"{block_uid}.mcfunction", if_block_ns,
        new_file_ns,
        "if", "mcfunction", namespace
    )
    else_block_ns = join_file_ns(new_file_ns, f"{block_uid}-else.mcfunction")
    env.file_ns_setter(
        f"{block_uid}-else.mcfunction", else_block_ns,
        new_file_ns,
        "if", "mcfunction", namespace
    )
    # 生成并写入if块
    with env.writeable_file_namespace(if_block_ns, namespace) as f:
        for statement in node.body:
            body = env.generate_code(statement, namespace, new_file_ns)
            f.write(body)
        f.write(updateBreakPoint(env, c_conf, g_conf, file_namespace))
    # 生成并写入else块
    with env.writeable_file_namespace(else_block_ns, namespace) as f:
        for statement in node.orelse:
            body = env.generate_code(statement, namespace, new_file_ns)
            f.write(body)
        f.write(updateBreakPoint(env, c_conf, g_conf, file_namespace))

    command = ''
    func_path = f"{base_namespace}\\{block_uid}".replace('\\', '/')

    command += env.generate_code(node.test, namespace, file_namespace)

    command += env.COMMENT(f"IF:检查条件")
    command += CHECK_SB(
        SBCheckType.UNLESS,
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
        SBCompareType.EQUAL,
        g_conf.Flags.FALSE, g_conf.SB_FLAGS,
        f"function {func_path}"
    )
    command += CHECK_SB(
        SBCheckType.IF,
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
        SBCompareType.EQUAL,
        g_conf.Flags.FALSE, g_conf.SB_FLAGS,
        f"function {func_path}-else"
    )

    command += SB_RESET(f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP)

    return command


@register_default_gen(ast.Return)
def gen_return(
        env: ABCEnvironment,
        g_conf: GlobalConfiguration,
        node: ast.Return, namespace: str, file_namespace: str) -> str:
    command = ''
    command += env.COMMENT("Return:计算返回值")

    command += env.generate_code(node.value, namespace, file_namespace)

    command += env.COMMENT("Return:保存返回值")

    ns, name = namespace.rsplit('\\', 1)
    func_map: dict = env.ns_getter(name, ns, ret_raw=True)[0]
    if func_map[".__type__"] != "function":
        raise Exception("返回语句不在函数内")

    func_name = func_map[".__namespace__"]

    command += SB_ASSIGN(
        f"{func_name}", g_conf.SB_FUNC_RESULT,
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP
    )

    command += SB_RESET(f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP)

    command += env.COMMENT("BP:Return.Enable")
    breakpoint_id = f"breakpoint_return_{env.newID("return.breakpoint")}"
    command += SB_ASSIGN(
        f"{breakpoint_id}", g_conf.SB_TEMP,
        g_conf.Flags.TRUE, g_conf.SB_FLAGS
    )

    command += FORCE_COMMENT(BreakPointFlag(
        "return",
        name=breakpoint_id,
        objective=g_conf.SB_TEMP
    ))
    raiseBreakPoint(env, file_namespace, "return", name=breakpoint_id, objective=g_conf.SB_TEMP)

    return command


@register_default_gen(ast.Compare)
def gen_compare(
        env: ABCEnvironment,
        g_conf: GlobalConfiguration,
        node: ast.Compare, namespace: str, file_namespace: str) -> str:
    command = ''
    command += env.COMMENT(f"Compare:比较操作", **{
        f"op{i}": type(cmp).__name__ for i, cmp in enumerate(node.comparators)
    })

    command += env.COMMENT(f"Compare:处理左值")
    command += env.generate_code(node.left, namespace, file_namespace)

    command += SB_ASSIGN(
        f"{namespace}.*CompareLeft", g_conf.SB_TEMP,
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP
    )

    command += SB_RESET(f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP)

    if len(node.ops) > 1:
        raise Exception("暂时无法解析多个比较符")

    command += SB_ASSIGN(
        f"{namespace}.*CompareResult", g_conf.SB_TEMP,
        g_conf.Flags.FALSE, g_conf.SB_FLAGS
    )

    for i, op in enumerate(node.ops):
        command += env.COMMENT(f"Compare:提取左值")
        command += SB_ASSIGN(
            f"{namespace}.*CompareCalculate", g_conf.SB_TEMP,
            f"{namespace}.*CompareLeft", g_conf.SB_TEMP
        )

        command += env.COMMENT(f"Compare:处理右值")
        command += env.generate_code(node.comparators[i], namespace, file_namespace)

        if isinstance(op, ast.Eq):
            command += env.COMMENT(f"Compare:比较", op="Eq(==)")
            check_type = SBCheckType.IF
            check_op = SBCompareType.EQUAL
        elif isinstance(op, ast.NotEq):
            command += env.COMMENT(f"Compare:比较", op="NotEq(!=)")
            check_type = SBCheckType.UNLESS
            check_op = SBCompareType.EQUAL
        elif isinstance(op, ast.Gt):
            command += env.COMMENT(f"Compare:比较", op="Gt(>)")
            check_type = SBCheckType.IF
            check_op = SBCompareType.MORE
        elif isinstance(op, ast.Lt):
            command += env.COMMENT(f"Compare:比较", op="Lt(<)")
            check_type = SBCheckType.IF
            check_op = SBCompareType.LESS
        elif isinstance(op, ast.GtE):
            command += env.COMMENT(f"Compare:比较", op="GtE(>=)")
            check_type = SBCheckType.IF
            check_op = SBCompareType.MORE_EQUAL
        elif isinstance(op, ast.LtE):
            command += env.COMMENT(f"Compare:比较", op="LtE(<=)")
            check_type = SBCheckType.IF
            check_op = SBCompareType.LESS_EQUAL
        else:
            raise Exception(f"无法解析的比较符 {op}")

        command += CHECK_SB(
            check_type,
            f"{namespace}.*CompareCalculate", g_conf.SB_TEMP,
            check_op,
            f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
            SB_ASSIGN(
                f"{namespace}.*CompareResult", g_conf.SB_TEMP,
                g_conf.Flags.TRUE, g_conf.SB_FLAGS,
                line_break=False
            )
        )

        command += env.COMMENT(f"Compare:重置计算临时变量")
        command += SB_RESET(f"{namespace}.*CompareCalculate", g_conf.SB_TEMP)

    command += env.COMMENT(f"Compare:重置左值")
    command += SB_RESET(f"{namespace}.*CompareLeft", g_conf.SB_TEMP)

    command += env.COMMENT(f"Compare:传递结果")
    command += SB_ASSIGN(
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
        f"{namespace}.*CompareResult", g_conf.SB_TEMP
    )

    command += SB_RESET(f"{namespace}.*CompareResult", g_conf.SB_TEMP)

    return command


@register_default_gen(ast.arguments)
def gen_arguments(
        env: ABCEnvironment,
        g_conf: GlobalConfiguration,
        node: ast.arguments, namespace: str) -> str:
    if namespace in env.func_args:
        warnings.warn(
            f"函数命名空间 {namespace} 已经存在, 可能覆盖之前的定义",
            UserWarning,
            stacklevel=0
        )

    command = ''

    command += env.COMMENT(f"arguments:处理参数")

    arguments_dict = OrderedDict(((arg.name, arg) for arg in parse_arguments(node)))
    # 反转顺序以匹配默认值
    for name, argument in arguments_dict.items():
        if isinstance(argument, ABCDefaultParameter):
            raise Exception(f"函数参数 {name} 包含默认值, 暂时无法处理")
        if isinstance(argument, ABCKeyword):
            raise Exception(f"函数参数 {name} 包含关键字参数, 暂时无法处理")
        if isinstance(argument, ABCVariableLengthParameter):
            raise Exception(f"函数参数 {name} 包含*参数, 暂时无法处理")

        gen_code(f"{namespace}.{name}", g_conf.SB_ARGS)
        env.ns_setter(name, f"{namespace}.{name}", namespace, "variable")
        command += SB_ASSIGN(
            f"{namespace}.{name}", g_conf.SB_VARS,
            f"{namespace}.{name}", g_conf.SB_ARGS
        )

        command += SB_RESET(f"{namespace}.{name}", g_conf.SB_ARGS)

    env.func_args[namespace] = arguments_dict

    return command


@register_default_gen(ast.UnaryOp)
def gen_unary_op(
        env: ABCEnvironment,
        g_conf: GlobalConfiguration,
        node: ast.UnaryOp, namespace: str, file_namespace: str) -> str:
    command = ''

    command += env.COMMENT(f"UnaryOp:一元操作", op=type(node.op).__name__)
    command += env.generate_code(node.operand, namespace, file_namespace)

    if isinstance(node.op, ast.Not):
        command += env.COMMENT(f"UnaryOp:运算", op="Not(not)")
        command += CHECK_SB(
            SBCheckType.UNLESS,
            f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
            SBCompareType.EQUAL,
            g_conf.Flags.FALSE, g_conf.SB_FLAGS,
            SB_ASSIGN(
                f"{namespace}.*UnaryOp", g_conf.SB_TEMP,
                g_conf.Flags.FALSE, g_conf.SB_FLAGS,
                line_break=False
            )
        )

        command += CHECK_SB(
            SBCheckType.IF,
            f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
            SBCompareType.EQUAL,
            g_conf.Flags.FALSE, g_conf.SB_FLAGS,
            SB_ASSIGN(
                f"{namespace}.*UnaryOp", g_conf.SB_TEMP,
                g_conf.Flags.TRUE, g_conf.SB_FLAGS,
                line_break=False
            )
        )

    elif isinstance(node.op, ast.USub):
        command += env.COMMENT(f"UnaryOp:运算", op="USub(-)")
        command += SB_ASSIGN(
            f"{namespace}.*UnaryOp", g_conf.SB_TEMP,
            f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP
        )
        command += SB_OP(
            SBOperationType.MULTIPLY,
            f"{namespace}.*UnaryOp", g_conf.SB_TEMP,
            g_conf.Flags.NEG, g_conf.SB_FLAGS
        )
    else:
        raise Exception(f"暂时无法解析的UnaryOp运算 {node.op}")

    command += SB_RESET(f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP)

    command += env.COMMENT(f"UnaryOp:传递结果")
    command += SB_ASSIGN(
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
        f"{namespace}.*UnaryOp", g_conf.SB_TEMP
    )

    command += SB_RESET(f"{namespace}.*UnaryOp", g_conf.SB_TEMP)

    return command
