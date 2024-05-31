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

        def __placeholder__(self):
            data = {
                "SB:Args": self.Args,
                "SB:Temp": self.Temp,
                "SB:Flags": self.Flags,
                "SB:Input": self.Input,
                "SB:Vars": self.Vars,
                "SB:FuncResult": self.FuncResult,
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
                "FLAG:TRUE": self.TRUE,
                "FLAG:FALSE": self.FALSE,
                "FLAG:NEG": self.NEG,

                "FLAG:DEBUG": self.DEBUG,
            }
            return data

    class _DataStorages:
        """
        这个类存储了必要 data storage 的名称
        """
        Root = "python"

        Temp = "temporary"
        LocalVars = "LocalVars"
        LocalTemp = "LocalTemp"

        def __placeholder__(self):
            data = {
                "DS:Root": self.Root,

                "DS:Temp": self.Temp,
                "DS:LocalVars": self.LocalVars,
                "DS:LocalTemp": self.LocalTemp,
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
                "RAWJSON:Prefix": self.Prefix,
                "RAWJSON.HoverEvent:Author": self.HoverEvents.Author,
            }
            return data

        class HoverEvents:
            """
            这个类存储了一些常用的hoverEvent原始JSON
            """
            Author = {
                "hoverEvent": {"action": "show_text", "value": "Made By: C418____11"}
            }

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
            **self.ScoreBoards.__placeholder__(),
            **self.Flags.__placeholder__(),
            **self.DataStorages.__placeholder__(),
            **self.RawJsons.__placeholder__(),
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
