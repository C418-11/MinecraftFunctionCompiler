# -*- coding: utf-8 -*-
# cython: language_level = 3
# MCFC: Template
"""
对计分板操作的支持
"""

from Constant import Flags
from Constant import ResultExt
from Constant import ScoreBoards
from ScoreboardTools import SB_ASSIGN
from ScoreboardTools import SB_CONSTANT
from ScoreboardTools import init_name
from Template import ArgData
from Template import register_func

SB_MAP: dict[str, dict[str, int]] = {
    ScoreBoards.Flags: {
        Flags.TRUE: 1,
        Flags.FALSE: 0,

        Flags.DEBUG: 0,
        Flags.NEG: -1,
    },
    ScoreBoards.Vars: {},
    ScoreBoards.Args: {},
    ScoreBoards.Temp: {},
}


def _get_default(self: dict, key: str, default):
    if key in self:
        return self[key]
    else:
        return default


def _get_score(name: str, objective: str, *, namespace: str = None):
    if namespace is None:
        raise ValueError("namespace is None")

    command = ''

    init_name(name, objective)
    command += SB_ASSIGN(
        f"{namespace}{ResultExt}", ScoreBoards.Temp,
        name, objective
    )

    return command


@register_func(_get_score)
def get_score(name: str, objective: str):
    """
    从计分板中获取值

    :param name: 目标
    :param objective: 计分项
    """
    return _get_default(SB_MAP[objective], name, 0)


def _write_score(name: str, objective: str, value: int, *, namespace: str):
    command = ''

    if isinstance(value, ArgData):
        command += value.toResult(f"{namespace}{ResultExt}", ScoreBoards.Temp)
    elif isinstance(value, int):
        command += SB_CONSTANT(
            f"{namespace}{ResultExt}", ScoreBoards.Temp,
            value
        )
    else:
        raise TypeError("value must be ArgData or int")

    init_name(name, objective)
    command += SB_ASSIGN(
        name, objective,
        f"{namespace}{ResultExt}", ScoreBoards.Temp
    )

    return command


@register_func(_write_score)
def write_score(name: str, objective: str, value: int):
    """
    将值写入计分板

    :param name: 目标
    :param objective: 计分项
    :param value: 值
    """
    SB_MAP[objective][name] = value


__all__ = (
    "SB_MAP",
    "get_score",
    "write_score",
)
