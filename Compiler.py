# -*- coding: utf-8 -*-
# cython: language_level = 3
"""
处理并编译源代码
"""

import ast
import json
import os
import sys
import time
import traceback
from collections import OrderedDict
from typing import Any

from Environment import CompileFailedException
from Environment import Environment
from ScoreboardTools import SB_Name2Code
from Template import template_funcs


class Compiler:
    def __init__(self, environment: Environment) -> None:
        """
        初始化编译器

        :param environment: 编译环境
        :type environment: Environment
        :return: None
        :rtype: None
        """
        self.env = environment
        self.c_conf = environment.c_conf
        self.g_conf = environment.g_conf
        self._encoding = environment.c_conf.Encoding

        self._last_start_time: float | None = None
        self._last_end_time: float | None = None

    def compile(self, source_file: str):
        """
        编译源码文件

        :param source_file: 源码文件名
        :type source_file: str
        :return: None
        :rtype: None
        """
        self._last_start_time = time.time()

        with open(os.path.join(self.c_conf.READ_PATH, f"{source_file}.py"), mode='r', encoding=self._encoding) as _:
            tree = ast.parse(_.read())

        if self.c_conf.DEBUG_MODE:
            print(ast.dump(tree, indent=4))
            print()

        compile_success: bool = False
        try:
            self.env.generate_code(tree, self.env.ns_join_base(source_file), source_file)
            compile_success = True
        except CompileFailedException as err:
            traceback.print_exception(err.raw_exc)
            for tb in err.traceback:
                tb.init(self.env)

            print(file=sys.stderr)
            print("CompileTraceback (most recent compile first):", file=sys.stderr)
            for tb in err.traceback[::-1]:
                print(
                    f"  File \"{tb.source_file_path}\","
                    f" line {tb.lineno},"
                    f" ns \"{tb.namespace}\","
                    f" file_ns \"{tb.file_namespace}\"",
                    file=sys.stderr
                )
                for line in tb.code_lines:
                    print(f"    {line}", file=sys.stderr)
        self._last_end_time = time.time()
        if self.c_conf.DEBUG_MODE and compile_success:
            self.print_environment()

    def print_environment(self) -> None:
        # noinspection GrazieInspection
        """
        打印环境信息

        :return: None
        :rtype: None
        """

        print(f"[DEBUG] CompileTime={self._last_end_time - self._last_start_time}")
        print()

        def _debug_dump(v: dict):
            return json.dumps(_deep_sorted(v), indent=4)

        _func_args = OrderedDict()
        for func_ns, args in self.env.func_args.items():
            _func_args[func_ns] = OrderedDict()
            for arg in args:
                _func_args[func_ns][arg] = repr(args[arg])

        _dumped_func_args = _debug_dump(_func_args)
        print(f"[DEBUG] FunctionArguments={_dumped_func_args}")
        print()
        _template_func = OrderedDict()
        for name, func in template_funcs.items():
            _template_func[name] = repr(func)
        _dumped_template_func = _debug_dump(_template_func)
        print(f"[DEBUG] TemplateFunctions={_dumped_template_func}")
        print()
        _dumped_sb_name2code = _debug_dump(SB_Name2Code)
        print(f"[DEBUG] SB_Name2Code={_dumped_sb_name2code}")
        print()
        _dumped_ns_map = _debug_dump(self.env.namespace.namespace_tree)
        print(f"[DEBUG] NamespaceMap={_dumped_ns_map}")
        print()
        _dumped_temp_map = _debug_dump(self.env.namespace.temp_ns)
        print(f"[DEBUG] TemplateScoreboardVariableMap={_dumped_temp_map}")
        print()
        _dumped_file_map = _debug_dump(self.env.file_namespace.namespace_tree)
        print(f"[DEBUG] FileMap={_dumped_file_map}")
        print()


def _deep_sorted(value: Any) -> Any:
    """
    深度排序

    :param value: 需要排序的值
    :type value: Any
    :return: 排序后的值
    :rtype: Any
    """
    if type(value) is set:
        value = list(value)
    if type(value) in (list, tuple):
        _processed = []
        for item in value:
            _processed.append(_deep_sorted(item))
        _processed.sort()
        return type(value)(_processed)
    if type(value) is dict:
        value = OrderedDict(value)
    if type(value) is not OrderedDict:
        return value

    _sorted_dict = OrderedDict()
    for key in sorted(value.keys()):
        _sorted_dict[key] = _deep_sorted(value[key])
    return _sorted_dict


__all__ = (
    "Compiler",
)
