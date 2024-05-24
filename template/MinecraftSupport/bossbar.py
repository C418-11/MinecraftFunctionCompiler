# -*- coding: utf-8 -*-
# cython: language_level = 3
# MCFC: Template
"""
对bossbar操作的支持
"""
import json

from Constant import DECIMAL_PRECISION
from Constant import ScoreBoards
from MinecraftColorString import ColorString
from Template import CommandResult
from Template import ArgData
from Template import register_func

BossBar_Map = {}


def _CheckId(_id: str) -> str:
    if not isinstance(_id, str):
        raise TypeError("id must be str")
    if '\n' in _id:
        raise ValueError("id must not contain '\\n'")
    if ':' not in _id:
        _id = f"minecraft:{_id}"

    return _id


def _CheckName(name) -> ColorString:
    if isinstance(name, (dict, str)):
        return ColorString.from_dict(name)
    else:
        raise TypeError("name must be dict or str")


def _add(_id: str, name: dict | str):
    _id = _CheckId(_id)
    json_name = json.dumps(_CheckName(name).to_dict())

    return f"bossbar add {_id} {json_name}\n"


@register_func(_add)
def add(_id: str, name: dict | str):
    _id = _CheckId(_id)
    if _id in BossBar_Map:
        return CommandResult(success=False)

    name = _CheckName(name)
    BossBar_Map[_id] = {"name": json.dumps(name.to_dict())}
    print(name.to_ansi() + "\033[0m")
    return CommandResult(success=True, result=len(BossBar_Map))


def _get(_id: str):
    _id = _CheckId(_id)

    return f"bossbar get {_id}\n"


@register_func(_get)
def get(_id: str):
    _id = _CheckId(_id)
    try:
        return CommandResult(success=True, result=len(BossBar_Map[_id]["players"]))
    except KeyError:
        return CommandResult(success=False)


def _remove(_id: str):
    _id = _CheckId(_id)

    return f"bossbar remove {_id}\n"


@register_func(_remove)
def remove(_id: str):
    _id = _CheckId(_id)
    try:
        BossBar_Map.pop(_id)
    except KeyError:
        return CommandResult(success=False)
    return CommandResult(success=True, result=len(BossBar_Map))


def _set_players(_id: str, players: str):
    _id = _CheckId(_id)

    return f"bossbar set {_id} players {players}\n"


@register_func(_set_players)
def set_players(_id: str, players: str):
    _id = _CheckId(_id)

    try:
        if BossBar_Map[_id]["players"] == players:
            return CommandResult(success=False)
    except KeyError:
        return CommandResult(success=False)

    BossBar_Map[_id]["players"] = players

    return CommandResult(success=True, result=len(players))


def _get_players(_id: str):
    _id = _CheckId(_id)

    return f"bossbar get {_id} players\n"


@register_func(_get_players)
def get_players(_id: str):
    _id = _CheckId(_id)

    try:
        return CommandResult(success=True, result=len(BossBar_Map[_id]["players"]))
    except KeyError:
        return CommandResult(success=False)


def _CheckValue(value: int | float):
    if isinstance(value, float):
        value = int(value * (10 ** DECIMAL_PRECISION))

    if not isinstance(value, int):
        raise TypeError("value must be int or float")

    if value < 0:
        raise ValueError("value must be positive")

    return value


def _set_value(_id: str, value: int | float | ArgData):
    _id = _CheckId(_id)

    if isinstance(value, ArgData):
        command = (
            f"execute store result bossbar {_id} value "
            f"run scoreboard players get {value.code} {ScoreBoards.Vars}\n"
        )
        return command

    value = _CheckValue(value)

    return f"bossbar set {_id} value {value}\n"


@register_func(_set_value)
def set_value(_id: str, value: int | float):
    _id = _CheckId(_id)
    value = _CheckValue(value)

    try:
        if BossBar_Map[_id]["value"] == value:
            return CommandResult(success=False)
    except KeyError:
        return CommandResult(success=False)

    BossBar_Map[_id]["value"] = value
    return CommandResult(success=True, result=value)


def _get_value(_id: str):
    _id = _CheckId(_id)

    return f"bossbar get {_id} value\n"


@register_func(_get_value)
def get_value(_id: str):
    _id = _CheckId(_id)

    try:
        return CommandResult(success=True, result=BossBar_Map[_id]["value"])
    except KeyError:
        return CommandResult(success=False)


def _set_max(_id: str, _max: int | float | ArgData):
    _id = _CheckId(_id)

    if isinstance(_max, ArgData):
        command = (
            f"execute store result bossbar {_id} max "
            f"run scoreboard players get {_max.code} {ScoreBoards.Vars}\n"
        )
        return command

    _max = _CheckValue(_max)

    return f"bossbar set {_id} max {_max}\n"


@register_func(_set_max)
def set_max(_id: str, _max: int | float):
    _id = _CheckId(_id)
    _max = _CheckValue(_max)

    try:
        if BossBar_Map[_id]["max"] == _max:
            return CommandResult(success=False)
    except KeyError:
        return CommandResult(success=False)
    BossBar_Map[_id]["max"] = _max


def _get_max(_id: str):
    _id = _CheckId(_id)

    return f"bossbar get {_id} max\n"


@register_func(_get_max)
def get_max(_id: str):
    _id = _CheckId(_id)

    try:
        return CommandResult(success=True, result=BossBar_Map[_id]["max"])
    except KeyError:
        return CommandResult(success=False)


def _set_visible(_id: str, visible: bool):
    _id = _CheckId(_id)

    return f"bossbar set {_id} visible {visible}\n"


@register_func(_set_visible)
def set_visible(_id: str, visible: bool):
    _id = _CheckId(_id)
    try:
        BossBar_Map[_id]["visible"] = visible
    except KeyError:
        return CommandResult(success=False)
    return CommandResult(success=True, result=visible)


def _get_visible(_id: str):
    _id = _CheckId(_id)

    return f"bossbar get {_id} visible\n"


@register_func(_get_visible)
def get_visible(_id: str):
    _id = _CheckId(_id)

    try:
        return CommandResult(success=True, result=BossBar_Map[_id]["visible"])
    except KeyError:
        return CommandResult(success=False)


def _set_name(_id: str, name: dict | str):
    _id = _CheckId(_id)

    return f"bossbar set {_id} name {json.dumps(_CheckName(name).to_dict())}\n"


@register_func(_set_name)
def set_name(_id: str, name: dict | str):
    _id = _CheckId(_id)
    name = _CheckName(name)
    try:
        BossBar_Map[_id]["name"] = json.dumps(name.to_dict())
    except KeyError:
        return CommandResult(success=False)
    print(name.to_ansi() + "\033[0m")
    return CommandResult(success=True, result=0)


allow_color = "blue|green|pink|purple|red|white|yellow".split("|")


def _CheckColor(color: str):
    if color not in allow_color:
        raise ValueError(f"color must be in {allow_color}")

    return color


def _set_color(_id: str, color: str):
    _id = _CheckId(_id)
    color = _CheckColor(color)
    return f"bossbar set {_id} color {color}\n"


@register_func(_set_color)
def set_color(_id: str, color: str):
    _id = _CheckId(_id)
    color = _CheckColor(color)
    try:
        BossBar_Map[_id]["color"] = color
    except KeyError:
        return CommandResult(success=False)
    return CommandResult(success=True, result=0)


allow_style = "notched_6|notched_10|notched_12|notched_20|progress".split("|")


def _CheckStyle(style: str | int):
    if isinstance(style, int):
        style = f"notched_{style}"

    if style not in allow_style:
        raise ValueError(f"style must be in {allow_style}")

    return style


def _set_style(_id: str, style: str | int):
    _id = _CheckId(_id)
    style = _CheckStyle(style)

    return f"bossbar set {_id} style {style}\n"


@register_func(_set_style)
def set_style(_id: str, style: str | int):
    _id = _CheckId(_id)
    style = _CheckStyle(style)

    try:
        BossBar_Map[_id]["style"] = style
    except KeyError:
        return CommandResult(success=False)
    return CommandResult(success=True, result=0)


__all__ = (
    "add",
    "get",
    "remove",

    "set_players",
    "get_players",
    "set_value",
    "get_value",
    "set_max",
    "get_max",
    "set_visible",
    "get_visible",

    "set_name",
    "set_color",
    "set_style",
)
