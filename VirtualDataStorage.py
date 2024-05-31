# -*- coding: utf-8 -*-
# cython: language_level = 3


from ABCTypes import ABCEnvironment
from abc import ABC


class VClass(ABC):
    def __init__(self):
        pass

    def v__init__(self):
        pass

    def v__str__(self):
        pass


class VirtualDataStorage:
    def __init__(self, env: ABCEnvironment):
        self.env = env

    def set_static(self, vtarget: str, value: VClass) -> str:
        pass

    def assign_variable(self, vtarget: str, from_vtarget: str) -> str:
        pass

    def remove_variable(self, vtarget: str) -> str:
        pass

    def from_scoreboard(self, vtarget: str, from_selector: str, from_objective: str) -> str:
        pass


__all__ = ("main",)
