# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

import json

from Constant import Flags
from Constant import RawJsons
from Constant import ScoreBoards


def IF_FLAG(flag: str, cmd: str) -> str:
    """
    行尾 **没有** 换行符
    """
    return f"execute if score {flag} {ScoreBoards.Flags} = {Flags.TRUE} {ScoreBoards.Flags} run {cmd}"


ENABLE_DEBUGGING: bool = False


def DEBUG_OBJECTIVE(
        raw_json: dict = None, *,
        objective: str, name: str,
        from_objective: str = None, from_name: str = None
) -> str:
    """
    行尾 **有** 换行符
    """
    if not ENABLE_DEBUGGING:
        return ''

    if raw_json is None:
        raw_json = {"text": ""}

    if (from_objective is not None) ^ (from_name is not None):
        raise Exception("from_objective 和 from_name 必须同时传入")

    from_details: list[dict] = []

    if from_objective is not None:
        from_details.append({"text": " --From: ", "bold": True, "color": "gold"})
        from_details.append({"text": from_objective, "color": "dark_purple"})
        from_details.append({"text": " | ", "bold": True, "color": "gold"})
        from_details.append({"text": from_name, "color": "dark_aqua"})
        from_details.append({"text": " | ", "bold": True, "color": "gold"})
        from_details.append({"score": {"name": from_name, "objective": from_objective}, "color": "green"})

    debug_prefix = RawJsons.Prefix
    debug_prefix["italic"] = True
    debug_prefix["color"] = "gray"

    json_txt = json.dumps({
        "text": "",
        "extra": [
            debug_prefix,
            {"text": " "},
            {"text": "[DEBUG]", "color": "gray", "italic": True},
            {"text": " "},
            raw_json,
            {"text": objective, "color": "dark_purple"},
            {"text": " | ", "bold": True, "color": "gold"},
            {"text": name, "color": "dark_aqua"},
            {"text": " | ", "bold": True, "color": "gold"},
            {"score": {"name": name, "objective": objective}, "color": "green"},
            *from_details
        ]
    })
    return f'{IF_FLAG(Flags.DEBUG, f"tellraw @a {json_txt}")}\n'


def DEBUG_TEXT(*raw_json: dict) -> str:
    """
    行尾 **有** 换行符
    """
    if not ENABLE_DEBUGGING:
        return ''

    json_txt = json.dumps({
        "text": "",
        "extra": [
            RawJsons.Prefix,
            {"text": " "},
            {"text": "[DEBUG]", "color": "gray", "italic": True},
            {"text": " "},
            *raw_json,
        ]
    })
    return f'{IF_FLAG(Flags.DEBUG, f"tellraw @a {json_txt}")}\n'


class DebugTip:
    Reset = {"text": "重置: ", "color": "gold", "bold": True}
    Set = {"text": "设置: ", "color": "gold", "bold": True}
    Calc = {"text": "计算: ", "color": "gold", "bold": True}
    Result = {"text": "结果: ", "color": "gold", "bold": True}
    DelArg = {"text": "删除参数: ", "color": "gold", "bold": True}
    Assign = {"text": "赋值: ", "color": "gold", "bold": True}
    SetArg = {"text": "传参: ", "color": "gold", "bold": True}

    Call = {"text": "调用: ", "color": "gold", "bold": True}
    Init = {"text": "初始化: ", "color": "gold", "bold": True}

    CallTemplate = {"text": "调用模板: ", "color": "gold", "bold": True}


GENERATE_COMMENTS: bool = True


def FORCE_COMMENT(*texts: str, **kv_texts) -> str:
    nor_text = ' '.join(texts)
    kv_text = '\n'.join(f"{k} = {v}" for k, v in kv_texts.items())

    txt_ls = []
    if nor_text:
        txt_ls.extend(nor_text.split('\n'))
    if kv_text:
        txt_ls.extend(kv_text.split('\n'))

    ret = '\n# '.join(txt_ls)

    if ret:
        ret = f"# {ret}\n"

    return ret


def COMMENT(*texts: str, **kv_texts) -> str:
    if not GENERATE_COMMENTS:
        return ''

    return FORCE_COMMENT(*texts, **kv_texts)


__all__ = (
    "DEBUG_OBJECTIVE",
    "DEBUG_TEXT",
    "DebugTip",
    "FORCE_COMMENT",
    "COMMENT",
    "ENABLE_DEBUGGING",
    "GENERATE_COMMENTS"
)
