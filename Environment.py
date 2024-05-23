# -*- coding: utf-8 -*-
# cython: language_level = 3

import ast
import json
import os
import warnings
from typing import Any
from typing import override

from BreakPointTools import SplitBreakPoint
from Configuration import CompileConfiguration
from Configuration import GlobalConfiguration
from DebuggingTools import COMMENT
from DefaultCodeGenerators import DefaultCodeGenerators
from NamespaceTools import join_file_ns
from ABC import ABCEnvironment


class Environment(ABCEnvironment):
    """
    编译环境
    """

    def __init__(self, c_conf: CompileConfiguration, g_conf: GlobalConfiguration = None):
        super().__init__(c_conf, g_conf)
        self.code_generators = DefaultCodeGenerators.copy()

    @override
    def generate_code(self, node: Any, namespace: str, file_namespace: str) -> str:

        try:
            generator_info = self.code_generators[type(node)]
        except KeyError:
            warnings.warn(f"无法解析的节点: {namespace}.{type(node).__name__}", UserWarning)
            err_msg = json.dumps({"text": f"无法解析的节点: {namespace}.{type(node).__name__}", "color": "red"})
            return f"tellraw @a {err_msg}\n" + COMMENT("无法解析的节点:") + COMMENT(ast.dump(node, indent=4))

        code_generator = generator_info["func"]
        params_data = {
            "namespace": namespace,
            "file_namespace": file_namespace,
            "node": node,
            "env": self,
            "c_conf": self.c_conf,
            "g_conf": self.g_conf
        }

        required_params = generator_info["params"] & set(params_data.keys())
        required_data = {k: params_data[k] for k in required_params}

        try:
            result = code_generator(**required_data)
        except CompileFailedException as err:
            if not hasattr(node, "lineno"):
                raise
            c_traceback = _build_compile_traceback(self.c_conf, namespace, file_namespace, node)
            err.add_traceback(c_traceback)
            raise
        except Exception as err:
            new_exception = CompileFailedException(err)
            if hasattr(node, "lineno"):
                c_traceback = _build_compile_traceback(self.c_conf, namespace, file_namespace, node)
                new_exception.add_traceback(c_traceback)
            raise new_exception

        if result is None:
            result = ''

        return result

    @override
    def ns_split_base(self, namespace: str) -> tuple[str, str]:
        return self.namespace.split_base(namespace)

    @override
    def ns_join_base(self, name: str) -> str:
        return self.namespace.join_base(name)

    @override
    def ns_from_node(
            self,
            node: Any,
            namespace: str,
            *,
            not_exists_ok: bool = False,
            ns_type: str | None = None
    ) -> tuple[str, str, str]:
        return self.namespace.node_to_namespace(node, namespace, not_exists_ok=not_exists_ok, ns_type=ns_type)

    @override
    def ns_init(self, namespace: str, ns_type: str) -> None:
        self.namespace.init_root(namespace, ns_type)

    @override
    def ns_setter(self, name: str, targe_namespace: str, namespace: str, ns_type: str) -> None:
        self.namespace.setter(name, targe_namespace, namespace, ns_type)

    @override
    def ns_getter(self, name, namespace: str, ret_raw: bool = False) -> tuple[str | dict, str]:
        return self.namespace.getter(name, namespace, ret_raw)

    @override
    def ns_store_local(self, namespace: str) -> tuple[str, str]:
        return self.namespace.store_local(namespace)

    @override
    def temp_ns_init(self, namespace: str) -> None:
        self.namespace.init_temp(namespace)

    @override
    def temp_ns_append(self, namespace: str, name: str) -> None:
        self.namespace.append_temp(namespace, name)

    @override
    def temp_ns_remove(self, namespace: str, name: str) -> None:
        self.namespace.remove_temp(namespace, name)

    @override
    def file_ns_init(self, file_namespace: str, level: str | None, file_ns_type: str, ns: str) -> None:
        self.file_namespace.init_root(file_namespace, level, file_ns_type, ns)

    @override
    def file_ns_setter(
            self,
            name: str,
            targe_file_namespace: str,
            file_namespace: str,
            level: str | None,
            file_ns_type: str, ns: str
    ) -> None:
        self.file_namespace.setter(name, targe_file_namespace, file_namespace, level, file_ns_type, ns)

    @override
    def file_ns_getter(self, name, file_namespace: str, ret_raw: bool = False) -> tuple[str | dict, str]:
        return self.file_namespace.getter(name, file_namespace, ret_raw)

    @override
    def file_ns2path(self, path: str, *args) -> str:
        """
        将文件命名空间转换为路径

        :param path: 文件命名空间
        :type path: str
        :param args: 需要拼接的路径
        :type args: str
        :return: 拼接后的路径
        :rtype: str
        """
        return os.path.normpath(os.path.join(self.c_conf.SAVE_PATH, path, *args))

    @override
    def mkdirs_file_ns(self, file_namespace: str, *args):
        f_ns = join_file_ns(file_namespace, *args)
        os.makedirs(self.file_ns2path(f_ns), exist_ok=True)

    @override
    def writeable_file_namespace(self, file_namespace: str, namespace: str):
        class SBPWrapper(SplitBreakPoint):

            @override
            def open(self) -> None:
                super().open()
                self._write2file(COMMENT(f"Generated by MCFC"))
                self._write2file(COMMENT(f"Github: https://github.com/C418-11/MinecraftFunctionCompiler"))
                self._write2file(COMMENT(f"================================================================="))

        return SBPWrapper(
            self,
            self.c_conf,
            self.g_conf,
            self.file_ns2path(file_namespace),
            namespace,
            encoding=self.c_conf.Encoding
        )


class CompileTraceback:
    def __init__(self, source_file_path, lineno, end_lineno, col_offset, end_col_offset, namespace, file_namespace):
        self.source_file_path = source_file_path
        self.lineno = lineno
        self.end_lineno = end_lineno
        self.col_offset = col_offset
        self.end_col_offset = end_col_offset

        self.namespace = namespace
        self.file_namespace = file_namespace

        self.code_lines: list[str] = []
        self.code_columns: list[str] = []

    def init(self, env: Environment):
        code_lines = ''
        with open(self.source_file_path, mode='r', encoding=env.c_conf.Encoding) as f:
            for i, line in enumerate(f, start=1):
                if (i < self.lineno) or (i > self.end_lineno):
                    continue
                code_lines += line

        self.code_lines = code_lines.split('\n')[:-1]
        self.code_columns = code_lines[self.col_offset:self.end_col_offset].split('\n')


def _file_namespace2source_file(c_conf: CompileConfiguration, file_namespace: str) -> str:
    root_f_ns = file_namespace.split('\\', 1)[0]
    source_file_path = os.path.join(c_conf.READ_PATH, root_f_ns)
    source_file = f"{source_file_path}.py"
    abs_source_file = os.path.abspath(source_file)
    return abs_source_file


def _build_compile_traceback(
        c_conf: CompileConfiguration, namespace, file_namespace: str, node: Any) -> CompileTraceback:
    source_file_path = _file_namespace2source_file(c_conf, file_namespace)
    c_traceback = CompileTraceback(
        source_file_path,

        node.lineno,
        node.end_lineno,
        node.col_offset,
        node.end_col_offset,

        namespace,
        file_namespace,
    )
    return c_traceback


class CompileFailedException(Exception):
    def __init__(self, raw_exc):
        self._raw_exc = raw_exc
        self.traceback: list[CompileTraceback] = []

    @property
    def raw_exc(self):
        return self._raw_exc

    def add_traceback(self, _traceback: CompileTraceback):
        self.traceback.append(_traceback)


__all__ = (
    "CompileTraceback",
    "CompileFailedException",
    "Environment",
)
