# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

from abc import ABC
from collections import OrderedDict


class ABCParameterType(ABC):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name=})"


class ABCDefaultParameterType(ABCParameterType):
    def __init__(self, name, default):
        super().__init__(name)
        self.default = default

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name=}, {self.default=})"


class ArgType(ABCParameterType):
    pass


class DefaultArgType(ArgType, ABCDefaultParameterType):
    pass


class KwType(ABCParameterType):
    pass


class DefaultKwType(KwType, ABCDefaultParameterType):
    pass


class UnnecessaryParameter:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __repr__(self):
        return "<<UnnecessaryParameter>>"


print_args = OrderedDict([
    ('*', DefaultArgType('*', UnnecessaryParameter())),
    *[(('*' + str(i)), DefaultArgType('*' + str(i), UnnecessaryParameter())) for i in range(1, 10)]
])

func_args: dict[str, OrderedDict[str, ArgType | DefaultArgType]] = {
    "python:built-in\\int": OrderedDict([
        ('x', DefaultArgType('x', UnnecessaryParameter())),
    ]),
    "python:built-in\\print": print_args,
}


__all__ = (
    "func_args",
    "ABCParameterType",
    "ABCDefaultParameterType",
    "ArgType",
    "DefaultArgType",
    "KwType",
    "DefaultKwType",
    "UnnecessaryParameter"
)
