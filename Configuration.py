# -*- coding: utf-8 -*-
# cython: language_level = 3


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
            save_path: str = "./.output",
            *,
            debug_mode: bool = False
    ):
        self.base_namespace = base_namespace
        self.READ_PATH = read_path
        self.SAVE_PATH: str = save_path
        self.DEBUG_MODE = debug_mode


__all__ = (
    "CompileConfiguration",
    "GlobalConfiguration",
)
