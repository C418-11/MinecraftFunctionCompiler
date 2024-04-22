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
