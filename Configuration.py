# -*- coding: utf-8 -*-
# cython: language_level = 3
"""
定义了一些配置文件
"""
import json


class GlobalConfiguration:
    DECIMAL_PRECISION: int = 3
    ResultExt: str = ".?Result"

    class _ScoreBoards:
        """
        这个类存储了必要计分项的名称
        """

        State = "PyI.State"
        Config = "PyI.Config"
        Constant = "PyI.Constant"

        Args = "Py.Args"
        Temp = "Py.Temp"
        Flags = "Py.Flags"
        Input = "Py.Input"
        Vars = "Py.Vars"
        FuncResult = "Py.FuncResult"

        def __placeholder__(self):
            data = {
                "State": self.State,
                "Config": self.Config,
                "Constant": self.Constant,

                "Args": self.Args,
                "Temp": self.Temp,
                "Flags": self.Flags,
                "Input": self.Input,
                "Vars": self.Vars,
                "FuncResult": self.FuncResult,
            }
            return data

    class _Flags:
        """
        这个类存储了一些常用的标记位名称
        """
        TRUE = "True"
        FALSE = "False"
        NEG = "Neg"

        DEBUG = "DEBUG"

        def __placeholder__(self):
            data = {
                "TRUE": self.TRUE,
                "FALSE": self.FALSE,
                "NEG": self.NEG,

                "DEBUG": self.DEBUG,
            }
            return data

    class _DataStorages:
        """
        这个类存储了必要 data storage 的名称
        """
        NameSpace = "python_interpreter"
        Root = "python"

        Temp = "temporary"
        LocalVars = "LocalVars"
        LocalTemp = "LocalTemp"

        def __init__(self):
            self.Flags = f"{self.NameSpace}:flags"
            self.Config = f"{self.NameSpace}:config"
            self.State = f"{self.NameSpace}:state"

        def __placeholder__(self):
            data = {
                "NS": self.NameSpace,
                "Flags": self.Flags,
                "Config": self.Config,
                "State": self.State,

                "Root": self.Root,

                "Temp": self.Temp,
                "LocalVars": self.LocalVars,
                "LocalTemp": self.LocalTemp,
            }
            return data

    class _RawJsons:
        """
        这个类存储了一些常用的原始JSON文本
        """
        Prefix = {
            "text": "[Python]",

            "clickEvent": {
                "action": "open_url", "value": "https://github.com/C418-11/MinecraftFunctionCompiler"
            },
            "hoverEvent": {
                "action": "show_text", "value": "GitHub"
            },

            "color": "gold",

            "bold": False,
            "italic": False,
            "underlined": False,
            "strikethrough": False,
            "obfuscated": False,

            "font": "minecraft:default",
        }

        def __placeholder__(self):
            data = {
                "Prefix": json.dumps(self.Prefix),
                "HoverEvent": self.HoverEvents.__placeholder__(),
            }
            return data

        class _HoverEvents:
            """
            这个类存储了一些常用的hoverEvent原始JSON
            """
            Author = {
                "hoverEvent": {"action": "show_text", "value": "Made By: C418____11"}
            }

            def __placeholder__(self):
                data = {
                    "Author": json.dumps(self.Author)[1:-1],
                }
                return data

        HoverEvents = _HoverEvents()

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

        self.RawJsons = self._RawJsons()

    def __placeholder__(self):
        data = {
            "SB": self.ScoreBoards.__placeholder__(),
            "FLAGS": self.Flags.__placeholder__(),
            "DS": self.DataStorages.__placeholder__(),
            "RAWJSON": self.RawJsons.__placeholder__(),
        }
        return data


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
