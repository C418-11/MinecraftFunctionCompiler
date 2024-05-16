# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

import ast
import functools
import importlib
import inspect
import re
import sys
import traceback

from Constant import ResultExt
from Constant import ScoreBoards
from ScoreboardTools import SB_ASSIGN
from ScoreboardTools import SB_Name2Code

template_funcs = {}


class NameNode:
    def __init__(self, name, *, namespace):
        self.name = name
        self.namespace = namespace

    @property
    def code(self):
        return SB_Name2Code[ScoreBoards.Vars][f"{self.namespace}.{self.name}"]

    def toResult(self):
        return SB_ASSIGN(
            f"{self.namespace}{ResultExt}", ScoreBoards.Temp,
            f"{self.namespace}.{self.name}", ScoreBoards.Vars
        )

    def toJson(self):
        return {"score": {"name": f"{self.code}", "objective": ScoreBoards.Vars}}

    def __str__(self):
        return f"{type(self).__name__}({self.name=}, {self.namespace=})"


def _parse_node(node, namespace: str):
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


def register_func(func_for_compile):
    parameter_set = set(inspect.signature(func_for_compile).parameters.keys())

    @functools.wraps(func_for_compile)
    def compile_func_wrapper(args, kwargs, *, namespace, file_namespace):

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

    def decorator(func_for_python):
        package_name = inspect.getmodule(func_for_python).__name__
        full_path = f"{package_name}\\module.{func_for_python.__name__}"
        template_funcs[full_path] = compile_func_wrapper

        return func_for_python

    return decorator


def check_template(file_path: str) -> bool:
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
    module = importlib.import_module(name)
    try:
        module.init()
    except AttributeError:
        pass
    except Exception as err:
        traceback.print_exception(err)
        print(f"Template:模板 {name} 初始化失败", file=sys.stderr)


class CommandResult:
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
