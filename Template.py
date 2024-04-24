# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"


import ast
import functools
import inspect
import re

from Constant import ScoreBoards
from ScoreboardTools import SB_Name2Code

template_funcs = {}


class NameNode:
    def __init__(self, name, *, namespace):
        self.name = name
        self.namespace = namespace

    def toJson(self):
        name = SB_Name2Code[f"{self.namespace}.{self.name}"]
        return {"score": {"name": f"{name}", "objective": ScoreBoards.Vars}}


def _parse_node(node, namespace: str):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return NameNode(node.id, namespace=namespace)
    return node


def register_func(python_func):

    def decorator(func):
        @functools.wraps(func)
        def wrapper(args, kwargs, *, namespace):

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

            try:
                return func(*new_args, **new_kwargs, namespace=namespace)
            except TypeError as e:
                cmp = re.compile(fr"{func.__name__}\(\)\sgot\san\sunexpected\skeyword\sargument\s'namespace'")
                if not cmp.match(str(e)):
                    raise

            return func(*new_args, **new_kwargs)

        package_name = inspect.getmodule(func).__name__
        full_path = f"{package_name}.{func.__name__}"

        template_funcs[full_path] = wrapper

        return python_func

    return decorator


__all__ = (
    "NameNode",
    "template_funcs",
    "register_func",
)
