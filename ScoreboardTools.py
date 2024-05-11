# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

from Constant import ScoreBoards

SB_Name2Code: dict[str, dict[str, str]] = {}
SB_Code2Name: dict[str, dict[str, str]] = {}


def init_objective(objective):
    if objective not in SB_Name2Code:
        SB_Name2Code[objective] = {}
        SB_Code2Name[objective] = {}


def init_name(name, objective):
    init_objective(objective)
    SB_Name2Code[objective][name] = name
    SB_Code2Name[objective][name] = name


def _init_flags(name, objective):
    if objective == ScoreBoards.Flags:
        init_name(name, objective)


IgnoreEncode: bool = False

_UID = 0


def gen_code(name, objective):
    global _UID

    init_objective(objective)

    if name in SB_Name2Code[objective]:
        return SB_Name2Code[objective][name]

    if objective == ScoreBoards.Flags:
        _init_flags(name, objective)
        return name

    if IgnoreEncode:
        init_name(name, objective)
        return name

    _UID += 1
    code = hex(_UID)
    SB_Name2Code[objective][name] = code
    SB_Code2Name[objective][code] = name

    return code


class SBCheckType:
    IF = "if"
    UNLESS = "unless"


class SBCompareType:
    EQUAL = "="

    LESS = "<"
    MORE = ">"

    LESS_EQUAL = "<="
    MORE_EQUAL = ">="


def CHECK_SB(
        t: str,
        a_name: str, a_objective: str,
        op: str,
        b_name: str, b_objective: str,
        cmd: str
):
    """
    行尾 **有** 换行符

    :param t: SBCheckType
    :param a_name:
    :param a_objective:
    :param op: SBCompareType
    :param b_name:
    :param b_objective:
    :param cmd:
    """
    _init_flags(b_name, b_objective)
    return (
        f"execute {t} score "
        f"{SB_Name2Code[a_objective][a_name]} {a_objective} "
        f"{op} "
        f"{SB_Name2Code[b_objective][b_name]} {b_objective} "
        f"run {cmd}\n"
    )


def SB_ASSIGN(to_name: str, to_objective: str, from_name: str, from_objective: str, *, line_break: bool = True):
    _init_flags(from_name, from_objective)
    command = (
        f"scoreboard players operation "
        f"{gen_code(to_name, to_objective)} {to_objective} "
        f"= "
        f"{SB_Name2Code[from_objective][from_name]} {from_objective}"
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

    _init_flags(selector, objective)
    if selector in SB_Name2Code[objective]:
        selector = SB_Name2Code[objective][selector]

    command = (
        f"scoreboard players operation "
        f"{gen_code(target_name, target_objective)} {target_objective} "
        f"{operation} "
        f"{selector} {objective}"
    )
    if line_break:
        command += "\n"

    return command


def SB_RESET(name: str, objective: str, *, line_break: bool = True):
    init_objective(objective)
    command = f"scoreboard players reset {SB_Name2Code[objective][name]} {objective}"
    if line_break:
        command += "\n"

    return command


def SB_CONSTANT(name: str, objective: str, value: int, *, line_break: bool = True):
    command = f"scoreboard players set {gen_code(name, objective)} {objective} {value}"
    if line_break:
        command += "\n"

    return command


__all__ = (
    "SBCheckType",
    "SBCompareType",

    "CHECK_SB",
    "SB_ASSIGN",
    "SBOperationType",
    "SB_OP",
    "SB_RESET",
    "SB_CONSTANT",

    "IgnoreEncode",

    "SB_Name2Code",
    "SB_Code2Name",

    "init_objective",
    "init_name",
    "gen_code",
)
