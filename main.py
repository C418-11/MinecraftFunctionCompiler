# -*- coding: utf-8 -*-

import ast
import inspect
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
from DebuggingTools import COMMENT
from DebuggingTools import FORCE_COMMENT
from NamespaceTools import FileNamespace
from NamespaceTools import Namespace
from NamespaceTools import join_file_ns
from ParameterTypes import ABCParameterType
from ParameterTypes import ArgType
from ParameterTypes import DefaultArgType
from ParameterTypes import UnnecessaryParameter
# from ParameterTypes import func_args
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
from Template import check_template, call_template
from Template import init_template
from Template import template_funcs


def is_parent_path(path1, path2):
    path1 = os.path.abspath(path1)
    path2 = os.path.abspath(path2)
    return os.path.commonpath([path1, path2]) == path1


GlobalId = 0


def newUid() -> str:
    global GlobalId
    GlobalId += 1
    return hex(GlobalId)[2:]


class GlobalConfiguration:

    ResultExt: str = ".?Result"

    SB_TEMP = "Py.Temp"
    SB_FLAGS = "Py.Flags"
    SB_VARS = "Py.Vars"
    SB_ARGS = "Py.Args"
    SB_FUNC_RESULT = "Py.FuncResult"

    class _Flags:
        TRUE = "True"
        FALSE = "False"
        NEG = "Neg"

    def __init__(self):
        self.Flags = self._Flags()


class CompileConfiguration:
    Encoding = "utf-8"
    TEMPLATE_PATH = "./template"

    def __init__(
            self,
            base_namespace: str,
            read_path: str,
            save_path: str = "./.output"
    ):
        self.base_namespace = base_namespace
        self.READ_PATH = read_path
        self.SAVE_PATH: str = save_path


class Environment:
    """
    编译环境
    """

    def __init__(self, c_conf: CompileConfiguration, g_conf: GlobalConfiguration = None):
        if g_conf is None:
            g_conf = GlobalConfiguration()
        self.code_generators = DefaultCodeGenerators.copy()
        self.c_conf: CompileConfiguration = c_conf
        self.g_conf: GlobalConfiguration = g_conf
        self.namespace = Namespace(self.c_conf.base_namespace)
        self.file_namespace = FileNamespace()
        self.func_args: dict[str, OrderedDict[str, ABCParameterType]] = {}

    def generate_code(self, node: Any, namespace: str, file_namespace: str) -> str:

        try:
            generator_info = self.code_generators[type(node)]
        except KeyError:
            warnings.warn(f"无法解析的节点: {namespace}.{type(node).__name__}", UserWarning)
            err_msg = json.dumps({"text": f"无法解析的节点: {namespace}.{type(node).__name__}", "color": "red"})
            return f"tellraw @a {err_msg}\n" + COMMENT("无法解析的节点:") + COMMENT(ast.dump(node, indent=4))

        code_generator = generator_info["func"]
        params_data = {
            "namespace": namespace,
            "file_namespace": file_namespace,
            "node": node,
            "env": self,
            "c_conf": self.c_conf,
            "g_conf": self.g_conf
        }

        required_params = generator_info["params"] & set(params_data.keys())
        required_data = {k: params_data[k] for k in required_params}

        result = code_generator(**required_data)
        if result is None:
            result = ''

        return result

    def ns_split_base(self, namespace: str) -> tuple[str, str]:
        return self.namespace.split_base(namespace)

    def ns_join_base(self, name: str) -> str:
        return self.namespace.join_base(name)

    def ns_from_node(
            self,
            node: Any,
            namespace: str,
            *,
            not_exists_ok: bool = False,
            ns_type: str | None = None
    ) -> tuple[str, str, str]:
        return self.namespace.node_to_namespace(node, namespace, not_exists_ok=not_exists_ok, ns_type=ns_type)

    def ns_init(self, namespace: str, ns_type: str) -> None:
        self.namespace.init_root(namespace, ns_type)

    def ns_setter(self, name: str, targe_namespace: str, namespace: str, ns_type: str) -> None:
        self.namespace.setter(name, targe_namespace, namespace, ns_type)

    def ns_getter(self, name, namespace: str, ret_raw: bool = False) -> tuple[str | dict, str]:
        return self.namespace.getter(name, namespace, ret_raw)

    def ns_store_local(self, namespace: str) -> tuple[str, str]:
        return self.namespace.store_local(namespace)

    def temp_ns_init(self, namespace: str) -> None:
        self.namespace.init_temp(namespace)

    def temp_ns_append(self, namespace: str, name: str) -> None:
        self.namespace.append_temp(namespace, name)

    def temp_ns_remove(self, namespace: str, name: str) -> None:
        self.namespace.remove_temp(namespace, name)

    def file_ns_init(self, file_namespace: str, level: str | None, file_ns_type: str, ns: str) -> None:
        self.file_namespace.init_root(file_namespace, level, file_ns_type, ns)

    def file_ns_setter(
            self,
            name: str,
            targe_file_namespace: str,
            file_namespace: str,
            level: str | None,
            file_ns_type: str, ns: str
    ) -> None:
        self.file_namespace.setter(name, targe_file_namespace, file_namespace, level, file_ns_type, ns)

    def file_ns_getter(self, name, file_namespace: str, ret_raw: bool = False) -> tuple[str | dict, str]:
        return self.file_namespace.getter(name, file_namespace, ret_raw)

    def file_ns2path(self, path: str, *args) -> str:
        """
        将文件命名空间转换为路径

        :param path: 文件命名空间
        :type path: str
        :param args: 需要拼接的路径
        :type args: str
        :return: 拼接后的路径
        :rtype: str
        """
        return os.path.normpath(os.path.join(self.c_conf.SAVE_PATH, path, *args))

    def mkdirs_file_ns(self, file_namespace: str, *args):
        f_ns = join_file_ns(file_namespace, *args)
        os.makedirs(self.file_ns2path(f_ns), exist_ok=True)

    def writeable_file_namespace(self, file_namespace: str, namespace: str):
        class SBPWrapper(SplitBreakPoint):
            def __enter__(self):
                f = super().__enter__()
                f.write(COMMENT(f"Generated by MCFC"))
                f.write(COMMENT(f"Github: https://github.com/C418-11/MinecraftFunctionCompiler"))
                return f
        return SBPWrapper(
            self,
            self.c_conf,
            self.g_conf,
            self.file_ns2path(file_namespace),
            namespace,
            encoding=self.c_conf.Encoding
        )


loaded_modules: dict[str, bool] = {}


def is_import_alive(import_path: str, base: str = '') -> tuple[str | None, bool | None]:
    package_local_path = import_path.replace(".", "\\")

    full_path = os.path.normpath(os.path.join(base, package_local_path))
    if os.path.isfile(f"{full_path}.py"):
        return f"{full_path}.py", True
    if os.path.isdir(full_path):
        return full_path, False
    return None, None


def import_as(
        env: Environment,
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

            print("------------导入文件-----------")
            print(sourcefile_path)
            print(ast.dump(tree, indent=4))
            print("------------------------------")

            env.generate_code(tree, new_namespace, name)
            end_t = time.time()
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
        g_conf: GlobalConfiguration,
        func_path: str, level: str, name: str, objective: str) -> tuple[str, bool] | str:
    """
    处理return语句的断点

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


@register_default_gen(None)
def gen_none(g_conf: GlobalConfiguration, namespace: str) -> str:
    return SB_ASSIGN(
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
        g_conf.Flags.FALSE, g_conf.SB_FLAGS,
    )


@register_default_gen(ast.Module)
def gen_module(
        env: Environment,
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
        f.write('\n')
        for statement in node.body:
            c = env.generate_code(statement, f"{namespace}\\module", join_file_ns(file_namespace, "module"))
            f.write(c)
        f.write(updateBreakPoint(env, c_conf, g_conf, f"{file_namespace}\\module"))

    return ''


@register_default_gen(ast.Name)
def gen_name(env: Environment, g_conf: GlobalConfiguration, node: ast.Name, namespace: str) -> str:
    assert isinstance(node.ctx, ast.Load)
    command = ''
    command += COMMENT(f"Name:读取变量", name=node.id)
    target_ns = env.ns_getter(node.id, namespace)[0]
    command += SB_ASSIGN(
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
        f"{target_ns}", g_conf.SB_FLAGS
    )
    return command


@register_default_gen(ast.Call)
def gen_call(
        env: Environment,
        c_conf: CompileConfiguration,
        g_conf: GlobalConfiguration, node, namespace: str, file_namespace: str) -> str:
    is_builtin: bool = False
    if isinstance(node.func, ast.Name) and node.func.id in dir(__builtins__):
        raise Exception("暂不支持python内置函数")
    else:
        func_name, func_ns, ns = env.ns_from_node(node.func, namespace, not_exists_ok=True, ns_type="function")

    commands: str = ''
    commands += COMMENT(f"Call:调用函数")

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
            if not isinstance(this_func_args[name], DefaultArgType):
                raise SyntaxError(f"函数 {func_ns} 的参数 {name} 未提供值")

            default_value = this_func_args[name].default

            if isinstance(default_value, UnnecessaryParameter):
                commands += COMMENT(f"Call:忽略参数", name=name)
                continue

            commands += COMMENT(f"Call:使用默认值", name=name, value=default_value)
            value = ast.Constant(value=this_func_args[name].default)

        commands += COMMENT("Call:计算参数值")
        commands += env.generate_code(value, namespace, file_namespace)

        commands += COMMENT("Call:传递参数", name=name)
        if is_builtin:
            init_name(f"{func_ns}.{name}", g_conf.SB_ARGS)
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
def gen_constant(g_conf: GlobalConfiguration, node: ast.Constant, namespace: str) -> str:
    value = node.value

    if type(value) is bool:
        value = 1 if value else 0

    if not isinstance(node.value, int):
        raise Exception(f"无法解析的常量 {node.value}")

    command = ''
    command += COMMENT(f"Constant:读取常量", value=value)
    command += SB_CONSTANT(f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP, value)

    return command


@register_default_gen(ast.Attribute)
def gen_attribute(env: Environment, g_conf: GlobalConfiguration, node: ast.Attribute, namespace: str) -> str:
    assert isinstance(node.ctx, ast.Load)
    if not isinstance(node.value, ast.Name):
        raise Exception("暂时无法解析的值")

    base_namespace = env.ns_getter(node.value.id, namespace)[0]
    attr_namespace = env.ns_getter(node.attr, base_namespace)[0]

    command = ''
    command += COMMENT(f"Attribute:读取属性", base_ns=base_namespace, attr=node.attr)

    command += SB_ASSIGN(
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
        f"{attr_namespace}", g_conf.SB_VARS
    )

    return command


@register_default_gen(ast.Expr)
def gen_expr(
        env: Environment,
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
        command += COMMENT(f"Expr:清除表达式返回值")
        command += cmd
    return command


@register_default_gen(ast.BinOp)
def gen_bin_op(
        env: Environment,
        g_conf: GlobalConfiguration, node: ast.BinOp, namespace: str, file_namespace: str) -> str:
    command = ''
    command += COMMENT(f"BinOp:二进制运算", op=type(node.op).__name__)

    command += COMMENT(f"BinOp:处理左值")
    command += env.generate_code(node.left, namespace, file_namespace)

    process_uid = newUid()

    process_ext = f".*BinOp{process_uid}"

    command += SB_ASSIGN(
        f"{namespace}{process_ext}", g_conf.SB_TEMP,
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP
    )
    env.temp_ns_append(namespace, f"{namespace}{process_ext}")
    command += SB_RESET(f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP)

    command += COMMENT(f"BinOp:处理右值")
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

    command += COMMENT(f"BinOp:传递结果")
    command += SB_ASSIGN(
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
        f"{namespace}{process_ext}", g_conf.SB_TEMP
    )

    command += SB_RESET(f"{namespace}{process_ext}", g_conf.SB_TEMP)
    env.temp_ns_remove(namespace, f"{namespace}{process_ext}")

    return command


@register_default_gen(ast.Assign)
def gen_assign(
        env: Environment, g_conf: GlobalConfiguration, node: ast.Assign, namespace: str, file_namespace: str) -> str:
    command = env.generate_code(node.value, namespace, file_namespace)
    from_namespace = f"{namespace}{g_conf.ResultExt}"

    for t in node.targets:
        name, _, root_ns = env.ns_from_node(t, namespace, not_exists_ok=True, ns_type="variable")

        target_namespace = f"{root_ns}.{name}"

        command += COMMENT(f"Assign:将结果赋值给变量", name=name)
        env.ns_setter(name, target_namespace, namespace, "variable")
        command += SB_ASSIGN(
            target_namespace, g_conf.SB_VARS,
            from_namespace, g_conf.SB_TEMP
        )

        command += SB_RESET(f"{from_namespace}", g_conf.SB_TEMP)

    return command


@register_default_gen(ast.Import)
def gen_import(
        env: Environment,
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
        env: Environment,
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
        env: Environment,
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

        f.write(COMMENT(f"FunctionDef:函数头"))
        args = env.generate_code(node.args, f"{namespace}\\{node.name}", new_file_ns)
        f.write(args)
        f.write(COMMENT(f"FunctionDef:函数体"))
        for statement in node.body:
            body = env.generate_code(statement, f"{namespace}\\{node.name}", new_file_ns)
            f.write(body)
    return ''


@register_default_gen(ast.Global)
def gen_global(
        env: Environment, node: ast.Global, namespace: str) -> str:
    for n in node.names:
        target_ns = env.ns_getter(n, namespace)[0]
        env.ns_setter(n, target_ns, namespace, "variable")
    return ''


@register_default_gen(ast.If)
def gen_if(
        env: Environment,
        c_conf: CompileConfiguration,
        g_conf: GlobalConfiguration,
        node: ast.If, namespace: str, file_namespace: str) -> str:
    block_uid = newUid()

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

    command += COMMENT(f"IF:检查条件")
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
        env: Environment,
        g_conf: GlobalConfiguration,
        node: ast.Return, namespace: str, file_namespace: str) -> str:
    command = ''
    command += COMMENT("Return:计算返回值")

    command += env.generate_code(node.value, namespace, file_namespace)

    command += COMMENT("Return:保存返回值")

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

    command += COMMENT("BP:Return.Enable")
    breakpoint_id = f"breakpoint_return_{newUid()}"
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
        env: Environment,
        g_conf: GlobalConfiguration,
        node: ast.Compare, namespace: str, file_namespace: str) -> str:
    command = ''
    command += COMMENT(f"Compare:比较操作", **{
        f"op{i}": type(cmp).__name__ for i, cmp in enumerate(node.comparators)
    })

    command += COMMENT(f"Compare:处理左值")
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
        command += COMMENT(f"Compare:提取左值")
        command += SB_ASSIGN(
            f"{namespace}.*CompareCalculate", g_conf.SB_TEMP,
            f"{namespace}.*CompareLeft", g_conf.SB_TEMP
        )

        command += COMMENT(f"Compare:处理右值")
        command += env.generate_code(node.comparators[i], namespace, file_namespace)

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
            f"{namespace}.*CompareCalculate", g_conf.SB_TEMP,
            check_op,
            f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
            SB_ASSIGN(
                f"{namespace}.*CompareResult", g_conf.SB_TEMP,
                g_conf.Flags.TRUE, g_conf.SB_FLAGS,
                line_break=False
            )
        )
        command += SB_RESET(f"{namespace}.*CompareCalculate", g_conf.SB_TEMP)

    command += SB_RESET(f"{namespace}.*CompareLeft", g_conf.SB_TEMP)

    command += COMMENT(f"Compare:传递结果")
    command += SB_ASSIGN(
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
        f"{namespace}.*CompareResult", g_conf.SB_TEMP
    )

    command += SB_RESET(f"{namespace}.*CompareResult", g_conf.SB_TEMP)

    return command


@register_default_gen(ast.arguments)
def gen_arguments(
        env: Environment,
        g_conf: GlobalConfiguration,
        node: ast.arguments, namespace: str) -> str:
    args = [arg.arg for arg in node.args]

    if namespace in env.func_args:
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

        gen_code(f"{namespace}.{name}", g_conf.SB_ARGS)
        env.ns_setter(name, f"{namespace}.{name}", namespace, "variable")
        command += SB_ASSIGN(
            f"{namespace}.{name}", g_conf.SB_VARS,
            f"{namespace}.{name}", g_conf.SB_ARGS
        )

        command += SB_RESET(f"{namespace}.{name}", g_conf.SB_ARGS)

    # 将最终顺序反转回来
    args_dict = OrderedDict([(k, v) for k, v in reversed(args_dict.items())])

    env.func_args[namespace] = args_dict

    return command


@register_default_gen(ast.UnaryOp)
def gen_unary_op(
        env: Environment,
        g_conf: GlobalConfiguration,
        node: ast.UnaryOp, namespace: str, file_namespace: str) -> str:
    command = ''

    command += COMMENT(f"UnaryOp:一元操作", op=type(node.op).__name__)
    command += env.generate_code(node.operand, namespace, file_namespace)

    if isinstance(node.op, ast.Not):
        command += COMMENT(f"UnaryOp:运算", op="Not(not)")
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
        command += COMMENT(f"UnaryOp:运算", op="USub(-)")
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

    command += COMMENT(f"UnaryOp:传递结果")
    command += SB_ASSIGN(
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
        f"{namespace}.*UnaryOp", g_conf.SB_TEMP
    )

    command += SB_RESET(f"{namespace}.*UnaryOp", g_conf.SB_TEMP)

    return command


def _deep_sorted(value: Any) -> Any:
    """
    深度排序

    :param value: 需要排序的值
    :type value: Any
    :return: 排序后的值
    :rtype: Any
    """
    if type(value) is set:
        value = list(value)
    if type(value) in (list, tuple):
        _processed = []
        for item in value:
            _processed.append(_deep_sorted(item))
        _processed.sort()
        return type(value)(_processed)
    if type(value) is dict:
        value = OrderedDict(value)
    if type(value) is not OrderedDict:
        return value

    _sorted_dict = OrderedDict()
    for key in sorted(value.keys()):
        _sorted_dict[key] = _deep_sorted(value[key])
    return _sorted_dict


def main():
    save_path = "./.output/"
    # save_path = r"D:\game\Minecraft\.minecraft\versions\1.16.5投影\saves\函数\datapacks\函数测试\data\source_code\functions"

    read_path = "./tests"
    file_name = "func_add"

    compile_configuration = CompileConfiguration("source_code:", read_path, save_path)
    environment = Environment(compile_configuration)

    start_t = time.time()
    with open(os.path.join(compile_configuration.READ_PATH, f"{file_name}.py"), mode='r', encoding="utf-8") as _:
        tree = ast.parse(_.read())

    print(ast.dump(tree, indent=4))
    print()

    environment.generate_code(tree, environment.ns_join_base(file_name), file_name)
    end_t = time.time()

    print(f"[DEBUG] TimeUsed={end_t - start_t}")
    print()

    def _debug_dump(v: dict):
        return json.dumps(_deep_sorted(v), indent=4)

    _func_args = OrderedDict()
    for func_ns, args in environment.func_args.items():
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
    _dumped_ns_map = _debug_dump(environment.namespace.namespace_tree)
    print(f"[DEBUG] NamespaceMap={_dumped_ns_map}")
    print()
    _dumped_temp_map = _debug_dump(environment.namespace.temp_ns)
    print(f"[DEBUG] TemplateScoreboardVariableMap={_dumped_temp_map}")
    print()
    _dumped_file_map = _debug_dump(environment.file_namespace.namespace_tree)
    print(f"[DEBUG] FileMap={_dumped_file_map}")
    print()


if __name__ == "__main__":
    main()
