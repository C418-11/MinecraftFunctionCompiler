# -*- coding: utf-8 -*-
# cython: language_level = 3
"""
计分板相关工具函数
"""
__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"



from Constant import ScoreBoards

SB_Name2Code: dict[str, dict[str, str]] = {}
SB_Code2Name: dict[str, dict[str, str]] = {}


def init_objective(objective: str) -> None:
    """
    初始化计分项

    :param objective: 计分项id
    """
    if objective not in SB_Name2Code:
        SB_Name2Code[objective] = {}
        SB_Code2Name[objective] = {}


def init_name(name: str, objective: str) -> None:
    """
    初始化计分目标

    :param name: 目标

    :param objective: 计分项
    """
    init_objective(objective)
    SB_Name2Code[objective][name] = name
    SB_Code2Name[objective][name] = name


def _init_flags(name: str, objective: str) -> None:
    """
    如果是标记位计分项，则初始化计分目标

    :param name: 目标

    :param objective: 计分项
    """
    if objective == ScoreBoards.Flags:
        init_name(name, objective)


IgnoreEncode: bool = False

_SB_ID = 0


def gen_code(name: str, objective: str) -> str:
    """
    编码计分目标 (Flag计分项不会被编码)

    :param name: 目标

    :param objective: 计分项

    :return: 编码后的计分目标
    """
    global _SB_ID

    init_objective(objective)

    if name in SB_Name2Code[objective]:
        return SB_Name2Code[objective][name]

    if objective == ScoreBoards.Flags:
        _init_flags(name, objective)
        return name

    if IgnoreEncode:
        init_name(name, objective)
        return name

    _SB_ID += 1
    code = hex(_SB_ID)
    SB_Name2Code[objective][name] = code
    SB_Code2Name[objective][code] = name

    return code


class SBCheckType:
    """
    计分检查模式
    """
    IF = "if"
    UNLESS = "unless"


class SBCompareType:
    """
    计分比较模式
    """
    EQUAL = "="

    LESS = "<"
    MORE = ">"

    LESS_EQUAL = "<="
    MORE_EQUAL = ">="


def CHECK_SB(
        check_type: str,
        a_name: str, a_objective: str,
        compare_op: str,
        b_name: str, b_objective: str,
        cmd: str,
        *,
        line_break: bool = True
) -> str:
    """
    如果检查条件成立, 就执行cmd

    :param check_type: 检查类型 (SBCheckType)

    :param a_name: 目标A

    :param a_objective: 计分项A

    :param compare_op: 比较类型 (SBCompareType)

    :param b_name: 目标B

    :param b_objective: 计分项B

    :param cmd: 要执行的命令

    :param line_break: 是否进行换行

    :return: 生成的命令
    """
    count_line = cmd.count('\n')
    if (count_line > 1) or (count_line == 1 and (not cmd.endswith('\n'))):
        raise ValueError("cmd can't have more than one line")

    if cmd.endswith("\n"):
        cmd = cmd[:-1]

    _init_flags(b_name, b_objective)
    command = (
        f"execute {check_type} score "
        f"{SB_Name2Code[a_objective][a_name]} {a_objective} "
        f"{compare_op} "
        f"{SB_Name2Code[b_objective][b_name]} {b_objective} "
        f"run {cmd}"
    )
    if line_break:
        command += "\n"

    return command


def SB_ASSIGN(to_name: str, to_objective: str, from_name: str, from_objective: str, *, line_break: bool = True) -> str:
    """
    将from_name的值赋给to_name

    :param to_name: 目标计分目标

    :param to_objective: 目标计分项

    :param from_name: 源计分目标

    :param from_objective: 源计分项

    :param line_break: 是否进行换行

    :return: 生成的命令
    """
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
    """
    计分操作类型
    """
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
        selector: str, objective: str,
        *,
        line_break: bool = True
) -> str:
    """
    对两个计分目标做任意支持的操作

    :param operation: 操作类型 (SBOperationType)

    :param target_name: 目标

    :param target_objective: 目标记分项

    :param selector: 选择器

    :param objective: 记分项

    :param line_break: 是否进行换行

    :return: 生成的命令
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


def SB_RESET(name: str, objective: str, *, line_break: bool = True) -> str:
    """
    重置计分目标

    :param name: 目标

    :param objective: 计分项

    :param line_break: 是否进行换行

    :return: 生成的命令
    """
    init_objective(objective)
    command = f"scoreboard players reset {SB_Name2Code[objective][name]} {objective}"
    if line_break:
        command += "\n"

    return command


def SB_CONSTANT(name: str, objective: str, value: int, *, line_break: bool = True) -> str:
    """
    将计分目标设置为常量

    :param name: 目标

    :param objective: 计分项

    :param value: 常量值

    :param line_break: 是否换行

    :return: 生成的命令
    """
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
