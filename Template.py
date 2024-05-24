# -*- coding: utf-8 -*-
# cython: language_level = 3
"""
模版函数处理
"""

import ast
import functools
import importlib
import inspect
import sys
import traceback
from typing import Any
from typing import Callable
from typing import TypeVar

from Constant import ScoreBoards
from DebuggingTools import COMMENT
from ABC import ABCEnvironment
from Configuration import CompileConfiguration
from Configuration import GlobalConfiguration
from ScoreboardTools import SB_ASSIGN
from ScoreboardTools import SB_RESET
from ScoreboardTools import SB_Name2Code

template_funcs = {}


class ArgData:
    """
    用于传参指定计分目标
    """

    def __init__(self, name: str, objective: str) -> None:
        """
        初始化

        :param name: 计分目标名称
        :type name: str
        :param objective: 计分目标对象
        :type objective: str
        :return: None
        :rtype: None
        """
        self.name: str = name
        self.objective: str = objective

    @property
    def code(self) -> str:
        """
        获取计分目标的编码结果

        :return: 计分目标编码结果
        :rtype: str
        """
        return SB_Name2Code[self.objective][self.name]

    def toResult(self, name: str, objective: str) -> str:
        """
        生成将计分目标赋值给 name, objective 的指令

        :param name: 计分目标名称
        :type name: str
        :param objective: 计分目标对象
        :type objective: str
        :return: 生成的指令
        :rtype: str
        """
        return SB_ASSIGN(
            name, objective,
            self.name, self.objective
        )

    def toJson(self) -> dict:
        """
        生成计分目标的原始JSON文本

        :return: 生成的JSON文本
        :rtype: dict
        """
        return {"score": {"name": f"{self.code}", "objective": self.objective}}

    def ReSet(self) -> str:
        """
        生成将计分目标重置的指令

        :return: 生成的指令
        :rtype: str
        """
        return SB_RESET(
            self.name, self.objective
        )

    def __str__(self):
        return f"{type(self).__name__}({self.name=}, {self.objective=})"


def _parse_node(node: Any, namespace: str):
    """
    尝试把AST节点转换成包含NameNode的python类型

    :param node: AST节点
    :type node: ast.AST
    :param namespace: 调用者命名空间
    :type namespace: str
    :return: 转换后结果
    :rtype: Any
    """
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return ArgData(f"{namespace}.{node.id}", ScoreBoards.Vars)
    if isinstance(node, ast.Dict):
        dict_result = {}
        for key, value in zip(node.keys, node.values, strict=True):
            dict_result[_parse_node(key, namespace)] = _parse_node(value, namespace)
        return dict_result
    return node


Callable_T = TypeVar("Callable_T", bound=Callable)


def register_func(func_for_compile: Callable[..., str]) -> Callable[[Callable_T], Callable_T]:
    """
    用于注册模版函数的装饰器

    :param func_for_compile: 编译用函数
    :type func_for_compile: Callable[..., str]
    :return: 装饰器
    :rtype: Callable[[Callable_T], Callable_T]
    """
    parameter_set = set(inspect.signature(func_for_compile).parameters.keys())

    @functools.wraps(func_for_compile)
    def compile_func_wrapper(
            args: list | None,
            kwargs: dict | None,
            *,
            env,
            c_conf,
            g_conf,
            namespace: str,
            file_namespace: str
    ) -> str:
        """
        包装编译用函数, 对参数和返回值进行处理

        :param args: 函数参数列表
        :type args: list | None
        :param kwargs: 函数关键字参数
        :type kwargs: dict | None
        :param env: 运行环境
        :type env: Environment
        :param c_conf: 编译配置
        :type c_conf: CompilerConfiguration
        :param g_conf: 全局配置
        :type g_conf: GlobalConfiguration
        :param namespace: 调用者命名空间
        :type namespace: str
        :param file_namespace: 调用者文件命名空间
        :type file_namespace: str
        :return: 编译出的命令字符串 (末尾自带换行符)
        :rtype: str
        """

        data = {
            "namespace": namespace,
            "file_namespace": file_namespace,

            "env": env,
            "c_conf": c_conf,
            "g_conf": g_conf
        }

        optional_parameters = set(data.keys())
        required_parameters = parameter_set & optional_parameters

        required_kwargs = {k: data[k] for k in required_parameters}

        command = func_for_compile(*args, **kwargs, **required_kwargs)
        if command is None:
            command = '\n'

        if type(command) is not str:
            raise TypeError(f"invalid return type {type(command)}")

        if not command.endswith('\n'):
            command += '\n'

        return command

    def decorator(func_for_python: Callable_T) -> Callable_T:
        """
        以函数名称注册编译用函数, 不对函数进行任何处理

        :param func_for_python: python环境下的函数
        :type func_for_python: Callable_T
        :return: 原样返回函数
        :rtype: Callable_T
        """
        package_name = inspect.getmodule(func_for_python).__name__
        full_path = f"{package_name}\\module.{func_for_python.__name__}"
        template_funcs[full_path] = compile_func_wrapper

        return func_for_python

    return decorator


def check_template(file_path: str) -> bool:
    """
    检查文件是否为模板文件

    :param file_path: 要检查的文件路径
    :type file_path: str
    :return: 是否为模版文件
    :rtype: bool
    """
    import re
    c = re.compile(r"#\s*MCFC:\s*(.*)")

    with open(file_path, mode='r', encoding="utf-8") as f:
        for line in f:
            if not line.startswith("#"):
                continue

            res = c.match(line)
            if (res is not None) and (res.group(1).lower() == "template"):
                return True

    return False


def init_template(name: str, env: ABCEnvironment, c_conf: CompileConfiguration, g_conf: GlobalConfiguration) -> None:
    """
    初始化模板文件

    :param name: 访问模板文件的路径
    :type name: str
    :param env: 运行环境
    :type env: Environment
    :param c_conf: 编译配置
    :type c_conf: CompileConfiguration
    :param g_conf: 全局配置
    :type g_conf: GlobalConfiguration
    :return: None
    :rtype: None
    """
    module = importlib.import_module(name)
    try:
        module.init(env, c_conf, g_conf)
    except AttributeError:
        pass
    except Exception as err:
        traceback.print_exception(err)
        print(f"Template:模板 {name} 初始化失败", file=sys.stderr)


def call_template(
        env: ABCEnvironment,
        c_conf: CompileConfiguration,
        g_conf: GlobalConfiguration,
        template_func_name: str,
        node: ast.Call,
        namespace: str,
        file_namespace: str) -> str:
    """
    调用模板函数

    :param env: 运行环境
    :type env: Environment
    :param c_conf: 编译配置
    :type c_conf: CompileConfiguration
    :param g_conf: 全局配置
    :type g_conf: GlobalConfiguration
    :param template_func_name: 模板函数名称
    :type template_func_name: str
    :param node: 函数调用节点
    :type node: ast.Call
    :param namespace: 调用所在命名空间
    :type namespace: str
    :param file_namespace: 调用所在文件命名空间
    :type file_namespace: str
    :return: 生成的MCF
    :rtype: str
    """
    func = template_funcs[template_func_name]
    commands = ''
    commands += COMMENT(f"Template.Call:调用模板函数", func=template_func_name)

    args = []
    kwargs = {}

    def _parse(value_node: Any) -> tuple[str, ArgData]:
        if type(value_node) in {ast.Constant, ast.Dict, ast.Name}:
            return '', _parse_node(value_node, namespace)
        if type(value_node) not in env.code_generators:
            return '', _parse_node(value_node, namespace)
        cmd = COMMENT("Template.Call:计算参数值")
        cmd += env.generate_code(value_node, namespace, file_namespace)

        cmd += COMMENT("Template.Call:传递参数")
        process_id = env.newID("Template.Call.Arg")
        arg_ext = f".*TemplateCallArg{process_id}"
        cmd += SB_ASSIGN(
            f"{template_func_name}{arg_ext}", g_conf.SB_ARGS,
            f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP
        )

        cmd += SB_RESET(f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP)

        return cmd, ArgData(f"{template_func_name}{arg_ext}", g_conf.SB_ARGS)

    for arg in node.args:
        cmds, arg_data = _parse(arg)
        commands += cmds
        args.append(arg_data)

    for kwarg in node.keywords:
        if not isinstance(kwarg, ast.keyword):
            raise TypeError("kwargs must be keyword")

        cmds, arg_data = _parse(kwarg.value)
        commands += cmds
        kwargs[kwarg.arg] = arg_data

    commands += func(
        args, kwargs,
        env=env, c_conf=c_conf, g_conf=g_conf,
        namespace=namespace, file_namespace=file_namespace
    )
    commands += COMMENT(f"Template.Call:调用模版函数结束")
    for arg in args:
        if not isinstance(arg, ArgData):
            continue
        if arg.objective == g_conf.SB_ARGS:
            commands += arg.ReSet()
    for kwarg in kwargs:
        if not isinstance(kwargs[kwarg], ArgData):
            continue
        if kwargs[kwarg].objective == g_conf.SB_ARGS:
            commands += kwargs[kwarg].ReSet()
    return commands


class CommandResult:
    """
    python环境下模板函数返回值

    .. warning::
       即将弃用
    """

    def __init__(self, *other, success: bool, result: int = None):
        self.success = success
        if not success:
            result = 0
        elif result is None:
            # 如果执行成功就必须传入值
            raise ValueError("result must be set")
        self.result = result
        self.other = other

    def __str__(self):
        return f"{type(self).__name__}({self.success=}, {self.result=}, {self.other=})"


__all__ = (
    "ArgData",
    "template_funcs",
    "register_func",

    "check_template",
    "init_template",
    "call_template",

    "CommandResult",
)
