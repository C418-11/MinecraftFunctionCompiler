# -*- coding: utf-8 -*-
# cython: language_level = 3
# MCFC: Template
"""
在python环境中构建MC环境
"""

from Template import register_func
from .scoreboard import SB_MAP


def _build_scoreboard(_objective: str, _value: dict):
    return ''


@register_func(_build_scoreboard)
def build_scoreboard(objective: str, value: dict[str, int]) -> None:
    """
    在python环境中构建一个积分项并设置默认值

    :param objective: 积分项
    :type objective: str
    :param value: 默认值
    :type value: dict[str, int]
    :return: None
    :rtype: None
    """
    if objective not in SB_MAP:
        SB_MAP[objective] = value
    else:
        SB_MAP[objective].update(value)


__all__ = (
    "build_scoreboard",
)
