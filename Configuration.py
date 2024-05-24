# -*- coding: utf-8 -*-
# cython: language_level = 3
"""
定义了一些配置文件
"""


class GlobalConfiguration:
    DECIMAL_PRECISION: int = 3
    ResultExt: str = ".?Result"

    class _ScoreBoards:
        """
        这个类存储了必要计分项的名称
        """
        Args = "Py.Args"
        Temp = "Py.Temp"
        Flags = "Py.Flags"
        Input = "Py.Input"
        Vars = "Py.Vars"
        FuncResult = "Py.FuncResult"

    class _Flags:
        """
        这个类存储了一些常用的标记位名称
        """
        TRUE = "True"
        FALSE = "False"
        NEG = "Neg"

        DEBUG = "DEBUG"

    class _DataStorages:
        """
        这个类存储了必要 data storage 的名称
        """
        Root = "python"

        Temp = "temporary"
        LocalVars = "LocalVars"
        LocalTemp = "LocalTemp"

    def __init__(self):
        self.Flags = self._Flags()

        self.ScoreBoards = self._ScoreBoards()
        self.SB_ARGS = self.ScoreBoards.Args
        self.SB_TEMP = self.ScoreBoards.Temp
        self.SB_FLAGS = self.ScoreBoards.Flags
        self.SB_INPUT = self.ScoreBoards.Input
        self.SB_VARS = self.ScoreBoards.Vars
        self.SB_FUNC_RESULT = self.ScoreBoards.FuncResult

        self.DataStorages = self._DataStorages()
        self.DS_ROOT = self.DataStorages.Root
        self.DS_TEMP = self.DataStorages.Temp
        self.DS_LOCAL_VARS = self.DataStorages.LocalVars
        self.DS_LOCAL_TEMP = self.DataStorages.LocalTemp


class CompileConfiguration:
    Encoding = "utf-8"
    TEMPLATE_PATH = "./template"

    def __init__(
            self,
            base_namespace: str,
            read_path: str,
            save_path: str = "./.output",
            *,
            debug_mode: bool = False,
            generate_comments: bool = True,
    ) -> None:
        self.base_namespace = base_namespace
        self.READ_PATH = read_path
        self.SAVE_PATH: str = save_path
        self.DEBUG_MODE = debug_mode
        self.GENERATE_COMMENTS = generate_comments


__all__ = (
    "CompileConfiguration",
    "GlobalConfiguration",
)
