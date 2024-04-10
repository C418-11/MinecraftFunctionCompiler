# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

import json


DECIMAL_PRECISION: int = 3


class ScoreBoards:
    Args = "Python.Args"
    Temp = "Python.Temp"
    Flags = "Python.Flags"
    Input = "Python.Input"


class RawJsons:
    Prefix = json.dumps({
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
    })

    class HoverEvents:
        Author = json.dumps({
            "hoverEvent": {"action": "show_text", "value": "Made By: C418____11"}
        })[1:-1]


class Flags:
    TRUE = "True"
    FALSE = "False"

    DEBUG = "DEBUG"


SCOREBOARDS_PLACEHOLDER_MAP = {
    "SB:Args": ScoreBoards.Args,
    "SB:Temp": ScoreBoards.Temp,
    "SB:Flags": ScoreBoards.Flags,
    "SB:Input": ScoreBoards.Input,
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

    "RAWJSON:Prefix": RawJsons.Prefix,
    "RAWJSON.HoverEvent:Author": RawJsons.HoverEvents.Author,
}


PLACEHOLDER_MAP = {
    **SCOREBOARDS_PLACEHOLDER_MAP,
    **BUILTIN_PLACEHOLDER_MAP,
    **CHAT_PLACEHOLDER_MAP,
    **RAWJSON_PLACEHOLDER_MAP,
}

__all__ = (
    "ScoreBoards",
    "RawJsons",
    "Flags",
    "PLACEHOLDER_MAP",
)
