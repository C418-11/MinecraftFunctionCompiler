# -*- coding: utf-8 -*-
# cython: language_level = 3
# MCFC: Template
"""
对计分板操作的支持
"""

from Configuration import GlobalConfiguration
from ScoreboardTools import SB_ASSIGN
from ScoreboardTools import SB_CONSTANT
from ScoreboardTools import init_name
from Template import ArgData
from Template import register_func

SB_MAP: dict[str, dict[str, int]] = {}


def init(g_conf: GlobalConfiguration):
    global SB_MAP
    SB_MAP = {
        g_conf.SB_FLAGS: {
            g_conf.Flags.TRUE: 1,
            g_conf.Flags.FALSE: 0,

            g_conf.Flags.DEBUG: 0,
            g_conf.Flags.NEG: -1,
        },
        g_conf.SB_VARS: {},
        g_conf.SB_ARGS: {},
        g_conf.SB_TEMP: {},
    }


def _get_default(self: dict, key: str, default):
    if key in self:
        return self[key]
    else:
        return default


def _get_score(name: str, objective: str, *, g_conf: GlobalConfiguration, namespace: str = None):
    if namespace is None:
        raise ValueError("namespace is None")

    command = ''

    init_name(name, objective)
    command += SB_ASSIGN(
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
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


def _write_score(name: str, objective: str, value: int, *, g_conf: GlobalConfiguration, namespace: str):
    command = ''

    if isinstance(value, ArgData):
        command += value.toResult(f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP)
    elif isinstance(value, int):
        command += SB_CONSTANT(
            f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP,
            value
        )
    else:
        raise TypeError("value must be ArgData or int")

    init_name(name, objective)
    command += SB_ASSIGN(
        name, objective,
        f"{namespace}{g_conf.ResultExt}", g_conf.SB_TEMP
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
