# -*- coding: utf-8 -*-
# cython: language_level = 3
"""
这个文件存储了一些通用的常量
"""

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

import json

DECIMAL_PRECISION: int = 3
ResultExt = ".?Result"


class ScoreBoards:
    """
    这个类存储了必要计分项的名称
    """
    Args = "Py.Args"
    Temp = "Py.Temp"
    Flags = "Py.Flags"
    Input = "Py.Input"
    Vars = "Py.Vars"
    FuncResult = "Py.FuncResult"


DataStorageRoot = "python"


class DataStorages:
    """
    这个类存储了必要 data storage 的名称
    """
    Temp = "temporary"
    LocalVars = "LocalVars"
    LocalTemp = "LocalTemp"


class RawJsons:
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

    class HoverEvents:
        """
        这个类存储了一些常用的hoverEvent原始JSON
        """
        Author = {
            "hoverEvent": {"action": "show_text", "value": "Made By: C418____11"}
        }


class Flags:
    """
    这个类存储了一些常用的标记位名称
    """
    TRUE = "True"
    FALSE = "False"
    NEG = "Neg"

    DEBUG = "DEBUG"


SCOREBOARDS_PLACEHOLDER_MAP = {
    "SB:Args": ScoreBoards.Args,
    "SB:Temp": ScoreBoards.Temp,
    "SB:Flags": ScoreBoards.Flags,
    "SB:Input": ScoreBoards.Input,
    "SB:Vars": ScoreBoards.Vars,
    "SB:FuncResult": ScoreBoards.FuncResult,
}

DATA_STORAGES_PLACEHOLDER_MAP = {
    "DS:Root": DataStorageRoot,

    "DS:Temp": DataStorages.Temp,
    "DS:LocalVars": DataStorages.LocalVars,
    "DS:LocalTemp": DataStorages.LocalTemp,
}

BUILTIN_PLACEHOLDER_MAP = {
    "BuiltIn:print": "打印: ",
    "BuiltIn:input.TIP": "输入: ",
}

CHAT_PLACEHOLDER_MAP = {
    "CHAT:Initializing": "正在初始化...",
    "CHAT:InitializationComplete": "初始化完成!",

    "CHAT:ClearingData": "正在清空数据...",
    "CHAT:DataClearingComplete": "数据清空完成!",
}

RAWJSON_PLACEHOLDER_MAP = {
    "RAWJSON.BuiltIn:input": json.dumps({
        "text": "[点击输入]",

        "clickEvent": {
            "action": "suggest_command", "value": f"/trigger {ScoreBoards.Input} set "
        },
        "hoverEvent": {
            "action": "show_text", "value": "[点击自动补全指令]"
        },

        "color": "gold",

        "bold": False,
        "italic": False,
        "underlined": False,
        "strikethrough": False,
        "obfuscated": False,

        "font": "minecraft:default",
    }),

    "RAWJSON:Prefix": json.dumps(RawJsons.Prefix),
    "RAWJSON.HoverEvent:Author": json.dumps(RawJsons.HoverEvents.Author)[1:-1],
}

PLACEHOLDER_MAP = {
    **SCOREBOARDS_PLACEHOLDER_MAP,
    **DATA_STORAGES_PLACEHOLDER_MAP,
    **BUILTIN_PLACEHOLDER_MAP,
    **CHAT_PLACEHOLDER_MAP,
    **RAWJSON_PLACEHOLDER_MAP,
}

__all__ = (
    "DECIMAL_PRECISION",
    "ResultExt",
    "ScoreBoards",
    "DataStorageRoot",
    "DataStorages",
    "RawJsons",
    "Flags",
    "PLACEHOLDER_MAP",
)
