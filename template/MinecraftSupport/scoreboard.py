# -*- coding: utf-8 -*-
# cython: language_level = 3
# MCFC: Template

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

from Constant import ResultExt
from Constant import Flags
from Constant import ScoreBoards
from Template import register_func
from ScoreboardTools import SB_ASSIGN
from ScoreboardTools import SB_Name2Code
from ScoreboardTools import SB_Code2Name

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


def _get_score(name: str, objective: str):
    return _get_default(SB_MAP[objective], name, 0)


def _init_scoreboard(name, objective):
    if objective not in SB_Name2Code:
        SB_Name2Code[objective] = {}
        SB_Code2Name[objective] = {}
    SB_Name2Code[objective][name] = name
    SB_Code2Name[objective][name] = name


@register_func(_get_score)
def get_score(name: str, objective: str, *, namespace: str = None):
    """
    判断(变量|值) 是否等于指定计分板中的值

    :param name: 目标
    :param objective: 计分板
    :param namespace: 命名空间 !!!该值应当由编译器自动传入!!!
    """

    if namespace is None:
        raise ValueError("namespace is None")

    command = ''

    _init_scoreboard(name, objective)
    command += SB_ASSIGN(
        f"{namespace}{ResultExt}", ScoreBoards.Temp,
        name, objective
    )

    return command


__all__ = (
    "SB_MAP",
    "get_score",
)
