# -*- coding: utf-8 -*-
# cython: language_level = 3
# MCFC: Template

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"


from Constant import ResultExt
from Constant import ScoreBoards
from Constant import Flags
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


def _get_score(name: str, objective: str):
    return _get_default(SB_MAP[objective], name, 0)


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

    command += (
        f"scoreboard players operation "
        f"{namespace}{ResultExt} {ScoreBoards.Temp} "
        f"= "
        f"{name} {objective}\n"
    )

    return command


__all__ = (
    "SB_MAP",
    "get_score",
)
