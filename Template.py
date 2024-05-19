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

from Constant import ResultExt
from Constant import ScoreBoards
from ScoreboardTools import SB_ASSIGN
from ScoreboardTools import SB_Name2Code

template_funcs = {}


class NameNode:
    """
    用于传参指定计分目标
    """

    def __init__(self, name: str, *, namespace: str) -> None:
        """
        初始化

        :param name: 计分目标名称
        :type name: str
        :param namespace: 调用者命名空间
        :type namespace: str
        :return: None
        :rtype: None
        """
        self.name: str = name
        self.namespace: str = namespace

    @property
    def code(self) -> str:
        """
        获取计分目标的编码结果

        :return: 计分目标编码结果
        :rtype: str
        """
        return SB_Name2Code[ScoreBoards.Vars][f"{self.namespace}.{self.name}"]

    def toResult(self) -> str:
        """
        生成将计分目标赋值给 {namespace}{ResultExt} 的指令

        :return: 生成的指令
        :rtype: str
        """
        return SB_ASSIGN(
            f"{self.namespace}{ResultExt}", ScoreBoards.Temp,
            f"{self.namespace}.{self.name}", ScoreBoards.Vars
        )

    def toJson(self) -> dict:
        """
        生成计分目标的原始JSON文本

        :return: 生成的JSON文本
        :rtype: dict
        """
        return {"score": {"name": f"{self.code}", "objective": ScoreBoards.Vars}}

    def __str__(self):
        return f"{type(self).__name__}({self.name=}, {self.namespace=})"


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
        return NameNode(node.id, namespace=namespace)
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
            namespace: str,
            file_namespace: str
    ) -> str:
        """
        包装编译用函数, 对参数和返回值进行处理

        :param args: 函数参数列表
        :type args: list | None
        :param kwargs: 函数关键字参数
        :type kwargs: dict | None
        :param namespace: 调用者命名空间
        :type namespace: str
        :param file_namespace: 调用者文件命名空间
        :type file_namespace: str
        :return: 编译出的命令字符串 (末尾自带'\n')
        :rtype: str
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = []

        if not isinstance(args, list):
            raise TypeError("args must be list")
        if not isinstance(kwargs, list):
            raise TypeError("kwargs must be list")

        new_args = []
        for arg in args:
            new_args.append(_parse_node(arg, namespace))

        new_kwargs = {}
        for kwarg in kwargs:
            if not isinstance(kwarg, ast.keyword):
                raise TypeError("kwargs must be keyword")
            new_kwargs[kwarg.arg] = _parse_node(kwarg.value, namespace)

        data = {
            "namespace": namespace,
            "file_namespace": file_namespace
        }

        optional_parameters = set(data.keys())
        required_parameters = parameter_set & optional_parameters

        required_kwargs = {k: data[k] for k in required_parameters}

        command = func_for_compile(*new_args, **new_kwargs, **required_kwargs)
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


def init_template(name: str) -> None:
    """
    初始化模板文件

    :param name: 访问模板文件的路径
    :type name: str
    :return: None
    :rtype: None
    """
    module = importlib.import_module(name)
    try:
        module.init()
    except AttributeError:
        pass
    except Exception as err:
        traceback.print_exception(err)
        print(f"Template:模板 {name} 初始化失败", file=sys.stderr)


class CommandResult:
    """
    临时的东西, 后面大概率弃用

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
    "NameNode",
    "template_funcs",
    "register_func",

    "check_template",
    "init_template",

    "CommandResult",
)
