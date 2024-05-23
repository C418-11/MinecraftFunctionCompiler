# -*- coding: utf-8 -*-
# cython: language_level = 3
"""
处理函数调用参数类型
"""
import ast
from abc import ABC


class ABCParameter(ABC):
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name=})"


class ABCDefaultParameter(ABCParameter):
    def __init__(self, name: str, default):
        super().__init__(name)
        self.default = default

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name=}, {self.default=})"


class ABCVariableLengthParameter(ABCParameter):
    ...


class ABCArgument(ABCParameter):
    def __init__(self, name: str, pos_only: bool | None):
        ABCParameter.__init__(self, name)
        self.pos_only = pos_only

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name=}, {self.pos_only=})"


class ABCKeyword(ABCParameter):
    ...


class ArgParameter(ABCArgument):
    def __init__(self, name: str, pos_only: bool):
        super().__init__(name, pos_only)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name=}, {self.pos_only=})"


class DefaultArgParameter(ABCArgument, ABCDefaultParameter):
    def __init__(self, name: str, default, pos_only: bool):
        ABCArgument.__init__(self, name, pos_only)
        ABCDefaultParameter.__init__(self, name, default)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name=}, {self.default=}, {self.pos_only=})"


class VarArgParameter(ABCArgument, ABCVariableLengthParameter):
    def __init__(self, name: str):
        ABCArgument.__init__(self, name, None)
        ABCVariableLengthParameter.__init__(self, name)


class KWParameter(ABCKeyword):
    def __init__(self, name: str):
        super().__init__(name)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name=})"


class DefaultKWParameter(ABCKeyword, ABCDefaultParameter):
    def __init__(self, name: str, default):
        ABCKeyword.__init__(self, name)
        ABCDefaultParameter.__init__(self, name, default)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name=}, {self.default=})"


class VarKWParameter(ABCKeyword, ABCVariableLengthParameter):
    def __init__(self, name: str):
        super().__init__(name)


def parse_arguments(arg_node: ast.arguments):
    arguments = []

    for arg in arg_node.posonlyargs:
        arguments.append(ArgParameter(arg.arg, True))

    for arg in arg_node.args:
        arguments.append(ArgParameter(arg.arg, False))

    for i, default_arg in enumerate(arg_node.defaults[::-1], start=1):
        arg_data = arguments[-i]
        new_arg = DefaultArgParameter(arg_data.name, default_arg, arg_data.pos_only)
        arguments[-i] = new_arg

    if arg_node.vararg:
        arguments.append(VarArgParameter(arg_node.vararg.arg))

    for arg in arg_node.kwonlyargs:
        arguments.append(KWParameter(arg.arg))

    for i, default_arg in enumerate(arg_node.kw_defaults[::-1], start=1):
        if default_arg is None:
            continue
        kw_data = arguments[-i]
        new_arg = DefaultKWParameter(kw_data.name, default_arg)
        arguments[-i] = new_arg

    if arg_node.kwarg:
        arguments.append(VarKWParameter(arg_node.kwarg.arg))

    return arguments


__all__ = (
    "ABCParameter",
    "ABCDefaultParameter",
    "ABCVariableLengthParameter",
    "ABCArgument",
    "ABCKeyword",

    "ArgParameter",
    "DefaultArgParameter",
    "VarArgParameter",
    "KWParameter",
    "DefaultKWParameter",
    "VarKWParameter",

    "parse_arguments",
)
