# -*- coding: utf-8 -*-
# cython: language_level = 3
"""
命名空间处理工具函数
"""

import ast
from collections import OrderedDict
from typing import Any
from typing import Callable
from typing import override

from ABC import ABCFileNamespace
from ABC import ABCNamespace
from Configuration import GlobalConfiguration
from ScoreboardTools import SB_Name2Code


class Namespace(ABCNamespace):
    @override
    def split_base(self, namespace: str) -> tuple[str, str]:
        if namespace.startswith(self._base_ns):
            base_ns, ns = namespace.split(self._base_ns, 1)
            return base_ns, ns
        raise Exception(f"namespace '{namespace}' is not in base namespace '{self._base_ns}'")

    @override
    def join_base(self, namespace: str) -> str:
        if self._base_ns.endswith(':'):
            new_namespace = f"{self._base_ns}{namespace}"
        else:
            new_namespace = f"{self._base_ns}\\{namespace}"

        return new_namespace

    @override
    def init_temp(self, namespace: str) -> None:
        self.temp_ns[namespace] = []

    @override
    def append_temp(self, namespace: str, name: str) -> None:
        self.temp_ns[namespace].append(name)

    @override
    def remove_temp(self, namespace: str, name: str) -> None:
        self.temp_ns[namespace].remove(name)

    @override
    def init_root(self, namespace: str, ns_type: str) -> None:
        self.namespace_tree[namespace] = OrderedDict({
            ".__namespace__": namespace,
            ".__type__": ns_type
        })

    @override
    def setter(self, name: str, targe_namespace: str, namespace: str, ns_type: str = None) -> None:
        data = {
            name: {
                ".__namespace__": targe_namespace,
                ".__type__": ns_type
            }
        }

        last_map = self.namespace_tree
        for ns in namespace.split('\\'):
            try:
                last_map = last_map[ns]
            except KeyError:
                raise KeyError(f"Namespace {namespace} not found")

        last_map.update(data)

    @override
    def getter(self, name, namespace: str, ret_raw: bool = False) -> tuple[str | dict, str]:

        last_map: dict[str, dict[str, ...]] = self.namespace_tree
        last_result: dict | None = None

        ns_ls: list[str] = []
        last_ns: list[str] = []

        for ns_name in namespace.split('\\'):
            try:
                last_map = last_map[ns_name]
            except KeyError:
                raise KeyError(f"{name} not found in namespace {namespace}")
            if name in last_map:
                last_result = last_map[name]
                last_ns = ns_ls

            ns_ls.append(ns_name)

        if name in last_map:
            last_result = last_map[name]
            last_ns = ns_ls

        if last_result is None:
            raise KeyError(f"{name} not found in namespace {namespace}")

        if not ret_raw:
            last_result = last_result[".__namespace__"]

        return last_result, '\\'.join(last_ns)

    @override
    def node_to_namespace(
            self,
            node: Any,
            namespace: str,
            *,
            not_exists_ok: bool = False,
            ns_type: str | None = None
    ) -> tuple[str, str, str]:

        if isinstance(node, ast.Name):
            try:
                ns, base_ns = self.getter(node.id, namespace, ret_raw=True)
            except KeyError:
                if not not_exists_ok:
                    raise
                self.setter(node.id, f"{namespace}\\{node.id}", namespace, ns_type)
                ns, base_ns = self.getter(node.id, namespace, ret_raw=True)
            ns: dict[str, dict[str, ...] | str]
            full_ns: str = ns[".__namespace__"]
            if ns[".__type__"] == "attribute":
                target_ns, name = full_ns.rsplit("|", 1)
                return self.node_to_namespace(
                    ast.Name(id=name), target_ns, not_exists_ok=not_exists_ok, ns_type=ns_type
                )
            return node.id, full_ns, base_ns

        if isinstance(node, ast.Attribute):
            value_ns = self.node_to_namespace(node.value, namespace, not_exists_ok=not_exists_ok, ns_type=ns_type)[1]
            try:
                full_ns = self.getter(node.attr, value_ns)[0]
            except KeyError:
                if not not_exists_ok:
                    raise
                self.setter(node.attr, f"{value_ns}\\{node.attr}", value_ns, ns_type)
                full_ns = self.getter(node.attr, value_ns)[0]

            return (
                node.attr,
                full_ns,
                value_ns
            )

        raise Exception(f"暂时不支持的节点类型 '{type(node.value).__name__}'")

    @override
    def store_local(
            self,
            g_conf: GlobalConfiguration,
            comment_gen: Callable[[str], str],
            namespace: str
    ) -> tuple[str, str]:
        _ns, _name = namespace.rsplit('\\', 1)
        local_ns: dict[str, dict[str, ...]] = self.getter(_name, _ns, ret_raw=True)[0]

        ns_ls: list[str] = []

        for name in local_ns:
            if name.startswith("."):
                continue
            data = local_ns[name]
            if data[".__type__"] != "variable":
                continue
            ns_ls.append(data[".__namespace__"])

        def store() -> str:
            nonlocal ns_ls
            command = ''
            command += comment_gen("LocalVars.Store")
            for ns in ns_ls:
                command += (
                    f"execute store result storage "
                    f"{g_conf.DS_ROOT} {g_conf.DS_TEMP} "
                    f"int 1 "
                    f"run scoreboard players get {SB_Name2Code[g_conf.SB_VARS][ns]} {g_conf.SB_VARS}\n"
                )
                command += (
                    f"data modify storage "
                    f"{g_conf.DS_ROOT} {g_conf.DS_LOCAL_VARS} "
                    f"append from storage "
                    f"{g_conf.DS_ROOT} {g_conf.DS_TEMP}\n"
                )
            command += comment_gen("LocalTemp.Store")
            for ns in self.temp_ns[namespace]:
                command += (
                    f"execute store result storage "
                    f"{g_conf.DS_ROOT} {g_conf.DS_TEMP} "
                    f"int 1 "
                    f"run scoreboard players get {SB_Name2Code[g_conf.SB_TEMP][ns]} {g_conf.SB_TEMP}\n"
                )
                command += (
                    f"data modify storage "
                    f"{g_conf.DS_ROOT} {g_conf.DS_LOCAL_TEMP} "
                    f"append from storage "
                    f"{g_conf.DS_ROOT} {g_conf.DS_TEMP}\n"
                )

            return command

        def load() -> str:
            nonlocal ns_ls
            command = ''
            command += comment_gen("LocalVars.Load")
            for ns in ns_ls[::-1]:
                command += (
                    f"execute store result score "
                    f"{SB_Name2Code[g_conf.SB_VARS][ns]} {g_conf.SB_VARS} "
                    f"run data get storage "
                    f"{g_conf.DS_ROOT} {g_conf.DS_LOCAL_VARS}[-1] 1\n"
                )
                command += (
                    f"data remove storage "
                    f"{g_conf.DS_ROOT} {g_conf.DS_LOCAL_VARS}[-1]\n"
                )
            command += comment_gen("LocalTemp.Load")
            for ns in self.temp_ns[namespace][::-1]:
                command += (
                    f"execute store result score "
                    f"{SB_Name2Code[g_conf.SB_TEMP][ns]} {g_conf.SB_TEMP} "
                    f"run data get storage "
                    f"{g_conf.DS_ROOT} {g_conf.DS_LOCAL_TEMP}[-1] 1\n"
                )
                command += (
                    f"data remove storage "
                    f"{g_conf.DS_ROOT} {g_conf.DS_LOCAL_TEMP}[-1]\n"
                )

            return command

        return store(), load()


class FileNamespace(ABCFileNamespace):

    def init_root(self, file_namespace: str, level: str | None, file_ns_type: str, ns: str) -> None:
        self.namespace_tree[file_namespace] = OrderedDict({
            ".__file_namespace__": file_namespace,
            ".__level__": level,
            ".__type__": file_ns_type,
            ".__namespace__": ns,
        })

    def setter(
            self,
            name: str,
            targe_file_namespace: str,
            file_namespace: str,
            level: str | None,
            file_ns_type: str, ns: str
    ) -> None:
        data = {
            name: {
                ".__file_namespace__": targe_file_namespace,
                ".__level__": level,
                ".__type__": file_ns_type,
                ".__namespace__": ns,
            }
        }

        last_map = self.namespace_tree
        for ns_path in file_namespace.split('\\'):
            try:
                last_map = last_map[ns_path]
            except KeyError:
                raise KeyError(f"Namespace {file_namespace} not found")

        last_map.update(data)

    def getter(self, name: str, file_namespace: str, ret_raw: bool = False) -> tuple[str | dict, str]:
        last_map: dict[str, dict[str, ...]] = self.namespace_tree
        last_result: dict | None = None

        ns_ls: list[str] = []
        last_ns: list[str] = []

        for ns_name in file_namespace.split('\\'):
            try:
                last_map = last_map[ns_name]
            except KeyError:
                raise KeyError(f"{name} not found in namespace {file_namespace}")
            if name in last_map:
                last_result = last_map[name]
                last_ns = ns_ls

            ns_ls.append(ns_name)

        if name in last_map:
            last_result = last_map[name]
            last_ns = ns_ls

        if last_result is None:
            raise KeyError(f"{name} not found in namespace {file_namespace}")

        if not ret_raw:
            last_result = last_result[".__file_namespace__"]

        return last_result, '\\'.join(last_ns)


def join_file_ns(path: str, *args: str) -> str:
    """
    连接文件命名空间

    :param path: 待连接的文件命名空间
    :type path: str
    :param args: 待连接的文件命名空间
    :type args: str
    :return: 连接后的文件命名空间
    :rtype: str
    """
    return path + '\\' + '\\'.join(args)


__all__ = (
    "Namespace",
    "FileNamespace",
    "join_file_ns",
)
