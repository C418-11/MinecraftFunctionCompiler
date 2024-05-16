# -*- coding: utf-8 -*-
# cython: language_level = 3
# MCFC: Template

import json

from Constant import Flags, ScoreBoards, RawJsons
from ScoreboardTools import SB_RESET, CHECK_SB, SBCheckType, SBCompareType, SB_ASSIGN
from Template import NameNode
from Template import register_func
from BreakPointTools import register_processor
from BreakPointTools import raiseBreakPoint
from BreakPointTools import BreakPointFlag
from DebuggingTools import FORCE_COMMENT, COMMENT


SB_TEMP = ScoreBoards.Temp
SB_FLAGS = ScoreBoards.Flags


print_end: bool = True


def _tprint(*objects, sep: str = ' ', end: str = '\n'):
    global print_end

    if not isinstance(sep, str):
        raise TypeError("sep must be str")

    if not isinstance(end, str):
        raise TypeError("end must be str")

    obj_str: list[str] = []
    if not print_end:
        obj_str.append('↳')

    for obj in objects:
        obj_str.append(str(obj))
        safe_sep = sep.replace('\n', '')
        obj_str.append(safe_sep)

    if obj_str:
        obj_str.pop()

    if '\n' not in end:
        obj_str.append('↴')
        print_end = False
    else:
        safe_end = end.replace('\n', '')
        obj_str.append(safe_end)

    print(''.join(obj_str))


@register_func(_tprint)
def tprint(*objects, sep: str = ' ', end: str = '\n'):
    global print_end

    if not isinstance(sep, str):
        raise TypeError("sep must be str")

    if not isinstance(end, str):
        raise TypeError("end must be str")

    obj_json: list[dict] = []
    if not print_end:
        obj_json.append({"text": '↳'})

    for obj in objects:
        if isinstance(obj, NameNode):
            raw_json = obj.toJson()
        else:
            raw_json = {"text": str(obj)}

        obj_json.append(raw_json)
        safe_sep = sep.replace('\n', '')
        obj_json.append({"text": safe_sep})
    obj_json.pop()

    if '\n' not in end:
        obj_json.append({"text": '↴'})
        print_end = False
    else:
        safe_end = end.replace('\n', '')
        obj_json.append({"text": safe_end})

    json_text = json.dumps({"text": '', "extra": obj_json})
    if '\n' in json_text:
        raise Exception("json text must not contain '\\n'")
    command = f"tellraw @a {json_text}\n"

    return command


@register_processor("breakpoint")
def _sbp_breakpoint(func_path, level, *, name, objective):
    def _process_raise():
        command = ''
        keep_raise = True
        command += FORCE_COMMENT(BreakPointFlag(
            "breakpoint",
            name=name,
            objective=objective
        ))
        if level == "module":
            command += COMMENT("BP:breakpoint.Reset")
            command += SB_RESET(name, objective)
            keep_raise = False

        return command, keep_raise

    def _process_split():
        command = ''
        command += COMMENT("BP:breakpoint.Split")
        command += CHECK_SB(
            SBCheckType.UNLESS,
            name, objective,
            SBCompareType.EQUAL,
            Flags.TRUE, SB_FLAGS,
            f"function {func_path}"
        )
        continue_json = {
            "text": '',
            "extra": [
                RawJsons.Prefix,
                {"text": ' '},
                {"text": "[调用栈]", "color": "gray", "italic": True, "underlined": True},
                {
                    "text": f"{func_path}",
                    "color": "green",
                    "hoverEvent": {
                        "action": "show_text",
                        "value": {"text": "点击以继续执行", "color": "green"}
                    },
                    "clickEvent": {
                        "action": "run_command",
                        "value": f"/function {func_path}"
                    }
                },
            ]
        }

        # command += f"tellraw @s {json.dumps(details_json)}\n"
        command += f"tellraw @a {json.dumps(continue_json)}\n"
        return command

    if func_path is None:
        return _process_raise()

    if level is None:
        return _process_split()


def _tbreakpoint(*args, **kwargs):
    breakpoint(*args, **kwargs)


_BP_ID: int = 0


@register_func(_tbreakpoint)
def tbreakpoint(*, file_namespace: str):
    global _BP_ID

    command = ''

    breakpoint_id = f"BreakPoint:{file_namespace}\\{_BP_ID}"
    _BP_ID += 1

    command += COMMENT("BP:breakpoint.Enable")
    command += SB_ASSIGN(
        breakpoint_id, SB_TEMP,
        Flags.TRUE, SB_FLAGS
    )
    command += FORCE_COMMENT(BreakPointFlag(
        "breakpoint",
        name=breakpoint_id,
        objective=SB_TEMP
    ))
    raiseBreakPoint(file_namespace, "breakpoint", name=breakpoint_id, objective=SB_TEMP)

    return command


__all__ = (
    "tprint",
    "tbreakpoint",
)
