# -*- coding: utf-8 -*-
# cython: language_level = 3
# MCFC: Template

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

from Template import register_func
from .scoreboard import SB_MAP


def _build_scoreboard(objective: str, value: dict):
    if objective not in SB_MAP:
        SB_MAP[objective] = value
    else:
        SB_MAP[objective].update(value)


@register_func(_build_scoreboard)
def build_scoreboard(_objective: str, _value: dict):
    return ''
