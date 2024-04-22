# -*- coding: utf-8 -*-
# cython: language_level = 3
# MCFC: Template

import json

from Template import register_func
from Template import NameNode

print_end: bool = True


@register_func
def tprint(*objects, sep: str = ' ', end: str = '\n'):
    global print_end

    if isinstance(sep, NameNode):
        sep = sep.toJson()
    if not isinstance(sep, str):
        raise TypeError("sep must be str")

    if not isinstance(end, str):
        raise TypeError("end must be str")

    obj_json: list[dict] = []
    if not print_end:
        obj_json.append({"text": '↪'})

    for obj in objects:
        if isinstance(obj, NameNode):
            raw_json = obj.toJson()
        else:
            raw_json = {"text": str(obj)}
        obj_json.append(raw_json)
        obj_json.append({"text": sep})
    obj_json.pop()

    if print_end:
        safe_end = end.replace('\n', '')
        obj_json.append({"text": safe_end})
    else:
        obj_json.append({"text": '↩'})
        print_end = True

    json_text = json.dumps({"text": '', "extra": obj_json})
    command = f"tellraw @a {json_text}\n"

    if '\n' in end:
        print_end = True

    return command
