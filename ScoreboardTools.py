# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"


SB_Name2Code: dict[str, str] = {}
SB_Code2Name: dict[str, str] = {}


_UID = 0


def _gen_code(name):
    global _UID
    if name in SB_Name2Code:
        return SB_Name2Code[name]

    _UID += 1
    code = hex(_UID)
    SB_Name2Code[name] = code
    SB_Code2Name[code] = name

    return code


class SBCheckType:
    IF = "if"
    UNLESS = "unless"


def CHECK_SB(t: str, a_name: str, a_objective: str, b_name: str, b_objective: str, cmd: str):
    """
    行尾 **有** 换行符
    """
    return (
        f"execute {t} score "
        f"{SB_Name2Code[a_name]} {a_objective} "
        f"= "
        f"{SB_Name2Code[b_name]} {b_objective} "
        f"run {cmd}\n"
    )


def SB_ASSIGN(to_name: str, to_objective: str, from_name: str, from_objective: str, *, line_break: bool = True):
    command = (
        f"scoreboard players operation "
        f"{_gen_code(to_name)} {to_objective} "
        f"= "
        f"{SB_Name2Code[from_name]} {from_objective}"
    )
    if line_break:
        command += "\n"

    return command


class SBOperationType:
    ADD = "+="
    SUBTRACT = "-="
    MULTIPLY = "*="
    DIVIDE = "/="
    MODULO = "%="

    ASSIGN = "="

    LESS = "<"
    MORE = ">"

    SWAP = "><"


def SB_OP(
        operation: str,
        target_name: str, target_objective: str,
        selector, objective,
        *,
        line_break: bool = True
) -> str:
    """
    :param operation: <操作>
    :param target_name: <目标>
    :param target_objective: <目标记分项>
    :param selector: <选择器>
    :param objective: <记分项>
    :param line_break: 是否进行换行
    """

    if selector in SB_Name2Code:
        selector = SB_Name2Code[selector]

    command = (
        f"scoreboard players operation "
        f"{_gen_code(target_name)} {target_objective} "
        f"{operation} "
        f"{selector} {objective}"
    )
    if line_break:
        command += "\n"

    return command


def SB_RESET(name: str, objective: str, *, line_break: bool = True):
    command = f"scoreboard players reset {SB_Name2Code[name]} {objective}"
    if line_break:
        command += "\n"

    return command


def SB_CONSTANT(name: str, objective: str, value: int, *, line_break: bool = True):
    command = f"scoreboard players set {_gen_code(name)} {objective} {value}"
    if line_break:
        command += "\n"

    return command


__all__ = (
    "SBCheckType",
    "CHECK_SB",
    "SB_ASSIGN",
    "SBOperationType",
    "SB_OP",
    "SB_RESET",
    "SB_CONSTANT",

    "SB_Name2Code",
    "SB_Code2Name",
)
