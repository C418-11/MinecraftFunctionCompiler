# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

import json
import re
import os
import warnings
from typing import Callable
from NamespaceTools import file_ns_getter

Processor = Callable[[str | None, str | None, ...], str | None | tuple[str, bool]]

BreakPointProcessor: dict[str | None, Processor] = {}


BreakPointLevels: list[str] = ["module", "function", "if"]


def BreakPointFlag(func: str | None, *args, **kwargs):
    flag_str = "&Flag: BreakPoint"
    flag_str += f"&func={func}" if func else ""
    flag_str += f"&args={json.dumps(args)}" if args else ""
    flag_str += f"&kwargs={json.dumps(kwargs)}" if kwargs else ""
    return flag_str


def register_processor(name: str | None):
    def decorator(func: Processor):
        if name in BreakPointProcessor:
            warnings.warn(
                f"{name} already registered, it will be replaced",
                UserWarning,
                stacklevel=2
            )
        BreakPointProcessor[name] = func
        return func

    return decorator


_BP_ID: int = 0


def raiseBreakPoint(file_namespace: str, func: str | None, *func_args, **func_kwargs):
    global _BP_ID
    f_ns, f_name = file_namespace.rsplit('\\', maxsplit=1)
    target_f_ns: dict = file_ns_getter(f_name, f_ns, ret_raw=True)[0]

    if ":breakpoints" not in target_f_ns:
        target_f_ns[":breakpoints"] = {}

    data = {
        "id": _BP_ID,
        "func": func,
        "args": func_args,
        "kwargs": func_kwargs,
    }
    target_f_ns[":breakpoints"][_BP_ID] = data
    _BP_ID += 1


def updateBreakPoint(file_namespace: str):

    f_ns, f_name = file_namespace.rsplit('\\', maxsplit=1)
    target_f_ns: dict[str, dict[str, ...] | str] = file_ns_getter(f_name, f_ns, ret_raw=True)[0]

    level: str = target_f_ns[".__level__"]

    if level not in BreakPointLevels:
        raise Exception(f"SBP: Unknown level: \'{level}\', please check if it is registered in the code.")

    if ":breakpoints" not in target_f_ns:
        target_f_ns[":breakpoints"] = {}

    command = ''

    for file_name in target_f_ns:
        if not file_name.endswith("$link"):
            continue

        raw_f_namespace = target_f_ns[file_name][".__path__"]
        rf_ns, rf_name = raw_f_namespace.rsplit('\\', maxsplit=1)
        raw_f_ns = file_ns_getter(rf_name, rf_ns, ret_raw=True)[0]

        if ":breakpoints" not in raw_f_ns:
            continue

        for bp_id, bp_data in raw_f_ns[":breakpoints"].items():
            keep_raise = False
            try:
                processor = BreakPointProcessor[bp_data["func"]]
            except KeyError:
                warnings.warn(
                    f"SBP: Unknown function: \'{bp_data['func']}\', please check if it is registered in the code.",
                    UserWarning,
                    stacklevel=2
                )
            else:
                cmd, keep_raise = processor(None, level, *bp_data["args"], **bp_data["kwargs"])
                command += cmd

            if keep_raise:
                raiseBreakPoint(f_name, f_ns, bp_data["func"], *bp_data["args"], **bp_data["kwargs"])

    return command


class SplitBreakPoint:
    def __init__(self, file_path, namespace, encoding: str = "utf-8"):
        self._namespace = namespace
        self._encoding = encoding

        self._is_comment = False
        self._last_char = '\n'
        self._comment_line_cache: str = ''

        self._writing_dir = os.path.dirname(file_path)
        self._writing_name = os.path.basename(file_path)
        self._pb_id: int = 1
        self._open_file = open(file_path, mode='w', encoding=self._encoding)
        self.closed: bool = False

        self._flag_pattern = re.compile(r"#\s*&+Flag:\s*([^&\s]+).*")

        self._func_pattern = re.compile(r".*&func=([^&]+).*")
        self._args_pattern = re.compile(r".*&args=(\[[^&]*]).*")
        self._kwargs_pattern = re.compile(r".*&kwargs=({[^&]*}).*")

    def _parse_comment(self, text: str):
        matches = self._flag_pattern.findall(text)
        if not matches or matches[0] != "BreakPoint":
            self._write2file(text)
            return

        name, ext = os.path.splitext(self._writing_name)
        id_name = f"{name}_{hex(self._pb_id)[2:]}"
        writing_name = f"{id_name}{ext}"

        match_func = self._func_pattern.findall(text)
        match_args = self._args_pattern.findall(text)
        match_kwargs = self._kwargs_pattern.findall(text)

        func_key = match_func[0] if match_func else None
        match_args = match_args[0] if match_args else "[]"
        match_kwargs = match_kwargs[0] if match_kwargs else "{}"

        try:
            func = BreakPointProcessor[func_key]
        except KeyError:
            raise Exception(f"SBP: Unknown function: \'{func_key}\', please check if it is registered in the code.")

        try:
            args = json.loads(match_args)
            kwargs = json.loads(match_kwargs)
        except json.JSONDecodeError:
            raise Exception("SBP: Arguments are not valid json format.")

        ns_path = f"{self._namespace}/{id_name}"
        result = func(ns_path, None, *args, **kwargs)

        result = '' if result is None else result

        self._write2file(result)

        self._pb_id += 1
        self._open_file.close()
        self._open_file = open(os.path.join(self._writing_dir, writing_name), mode='w', encoding='utf-8')

    def write(self, text: str):
        if self.closed:
            raise Exception("File is closed")

        if not text:
            self._write2file(text)
            return

        for line in text.splitlines(keepends=True):
            if self._process_comment(line):
                continue

            if not self._is_comment_line(line):
                self._last_char = line[-1]
                self._write2file(line)
                continue
            self._is_comment = True

            if self._process_comment(line):
                continue

            raise Exception("Unknown error")

    def _write2file(self, text: str):
        self._open_file.write(text)

    def _is_comment_line(self, txt: str) -> bool:
        if '#' not in txt:
            return False
        last_char = self._last_char
        if txt.index('#') != 0:
            last_char = txt[txt.index('#') - 1]

        if last_char != '\n':
            return False
        return True

    def _process_comment(self, txt: str) -> bool:
        if self._is_comment:
            self._comment_line_cache += txt
            self._last_char = txt[-1]
            if '\n' in txt:
                self._parse_comment(self._comment_line_cache)
                self._comment_line_cache = ''
                self._is_comment = False
            return True
        return False

    def close(self):
        if not self.closed:
            self._open_file.close()
            self.closed = True

    def __enter__(self):
        if self.closed:
            raise Exception("File is closed")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.closed = True
        return self._open_file.__exit__(exc_type, exc_val, exc_tb)


__all__ = (
    "BreakPointFlag",

    "raiseBreakPoint",
    "updateBreakPoint",

    "register_processor",
    "SplitBreakPoint",
)
