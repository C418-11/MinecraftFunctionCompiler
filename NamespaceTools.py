# -*- coding: utf-8 -*-
# cython: language_level = 3
"""
命名空间处理工具函数
"""

import ast
from collections import OrderedDict
from typing import Any

from Constant import DataStorageRoot
from Constant import DataStorages
from Constant import ScoreBoards
from DebuggingTools import COMMENT
from ScoreboardTools import SB_Name2Code

SB_TEMP: str = ScoreBoards.Temp
SB_VARS: str = ScoreBoards.Vars

DS_ROOT: str = DataStorageRoot
DS_TEMP: str = DataStorages.Temp
DS_LOCAL_VARS: str = DataStorages.LocalVars
DS_LOCAL_TEMP: str = DataStorages.LocalTemp


class Namespace:
    """
    命名空间存储及其操作
    """
    def __init__(self, base_namespace) -> None:
        """
        初始化命名空间

        :param base_namespace: 基础命名空间
        """
        self._base_ns = base_namespace
        self.namespace_tree: OrderedDict[str, OrderedDict[str, ...]] = OrderedDict()
        self.temp_ns: OrderedDict[str, list[str]] = OrderedDict()

    def split_base(self, namespace: str) -> tuple[str, str]:
        """
        分割命名空间的基础命名空间

        :param namespace: 命名空间
        :type namespace: str
        :return: 基础命名空间和其余部分
        :rtype: tuple[str, str]
        """
        if namespace.startswith(self._base_ns):
            base_ns, ns = namespace.split(self._base_ns, 1)
            return base_ns, ns
        raise Exception(f"namespace '{namespace}' is not in base namespace '{self._base_ns}'")

    def join_base(self, namespace: str) -> str:
        """
        连接基础命名空间

        :param namespace: 命名空间
        :type namespace: str
        :return: 连接后的命名空间
        :rtype: str
        """
        if self._base_ns.endswith(':'):
            new_namespace = f"{self._base_ns}{namespace}"
        else:
            new_namespace = f"{self._base_ns}\\{namespace}"

        return new_namespace

    def init_temp(self, namespace: str) -> None:
        """
        初始化编译时临时命名空间存储

        :param namespace: 需要初始化的命名空间
        :type namespace: str
        :return: None
        :rtype: None
        """
        self.temp_ns[namespace] = []

    def append_temp(self, namespace: str, name: str) -> None:
        """
        添加MCF运行时临时命名空间

        :param namespace: 存储目标命名空间
        :type namespace: str
        :param name: MCF运行时临时命名空间
        :type name: str
        :return: None
        :rtype: None
        """
        self.temp_ns[namespace].append(name)

    def remove_temp(self, namespace: str, name: str) -> None:
        """
        移除MCF运行时临时命名空间

        :param namespace: 存储目标命名空间
        :type namespace: str
        :param name: MCF运行时临时命名空间
        :type name: str
        :return: None
        :rtype: None
        """
        self.temp_ns[namespace].remove(name)

    def init_root(self, namespace: str, ns_type: str) -> None:
        """
        初始化根命名空间

        :param namespace: 命名空间
        :type namespace: str
        :param ns_type: 命名空间类型
        :type ns_type: str
        :return: None
        :rtype: None
        """
        self.namespace_tree[namespace] = OrderedDict({
            ".__namespace__": namespace,
            ".__type__": ns_type
        })

    def setter(self, name: str, targe_namespace: str, namespace: str, ns_type: str = None) -> None:
        """
        在指定的命名空间下创建一个名称指向目标命名空间

        :param name: 名称
        :type name: str
        :param targe_namespace: 指向的命名空间
        :type targe_namespace: str
        :param namespace: 设置的命名空间
        :type namespace: str
        :param ns_type: 命名空间类型
        :type ns_type: str
        :return: None
        :rtype: None
        """
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

    def getter(self, name, namespace: str, ret_raw: bool = False) -> tuple[str | dict, str]:
        """
        在指定的命名空间下寻找名称，并返回所找到的值

        :param name: 寻找的名称
        :type name: str
        :param namespace: 寻找的命名空间
        :type namespace: str
        :param ret_raw: 是否直接返回源字典
        :type ret_raw: bool
        :returns: (完整命名空间 | 命名空间字典, 基础命名空间)
        :rtype: tuple[str | dict, str]
        """

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

    def node_to_namespace(
            self,
            node: Any,
            namespace: str,
            *,
            not_exists_ok: bool = False,
            ns_type: str | None = None
    ) -> tuple[str, str, str]:
        """
        将AST节点转换为命名空间

        :param node: AST节点
        :type node: ast.Name | ast.Attribute
        :param namespace: 当前命名空间
        :type namespace: str
        :param not_exists_ok: 名称不存在时在当前命名空间下生成
        :type not_exists_ok: bool
        :param ns_type: 不存在时生成填入的命名空间类型
        :type ns_type: str
        :returns: (name, full_namespace, root_namespace)
        :rtype: tuple[str, str, str]
        """

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

    def store_local(self, namespace: str) -> tuple[str, str]:
        """
        将当前命名空间下的所有变量和临时变量存储到data storage

        :param namespace: 目标命名空间
        :type namespace: str
        :returns: (保存用命令, 加载用命令)
        :rtype: tuple[str, str]
        """
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
            """
            计算需保存的变量

            :return: 保存用命令
            :rtype: str
            """
            nonlocal ns_ls
            command = ''
            command += COMMENT("LocalVars.Store")
            for ns in ns_ls:
                command += (
                    f"execute store result storage "
                    f"{DS_ROOT} {DS_TEMP} "
                    f"int 1 "
                    f"run scoreboard players get {SB_Name2Code[SB_VARS][ns]} {SB_VARS}\n"
                )
                command += (
                    f"data modify storage "
                    f"{DS_ROOT} {DS_LOCAL_VARS} "
                    f"append from storage "
                    f"{DS_ROOT} {DS_TEMP}\n"
                )
            command += COMMENT("LocalTemp.Store")
            for ns in self.temp_ns[namespace]:
                command += (
                    f"execute store result storage "
                    f"{DS_ROOT} {DS_TEMP} "
                    f"int 1 "
                    f"run scoreboard players get {SB_Name2Code[SB_TEMP][ns]} {SB_TEMP}\n"
                )
                command += (
                    f"data modify storage "
                    f"{DS_ROOT} {DS_LOCAL_TEMP} "
                    f"append from storage "
                    f"{DS_ROOT} {DS_TEMP}\n"
                )

            return command

        def load() -> str:
            """
            计算需加载的变量

            :return: 加载用命令
            :rtype: str
            """
            nonlocal ns_ls
            command = ''
            command += COMMENT("LocalVars.Load")
            for ns in ns_ls[::-1]:
                command += (
                    f"execute store result score "
                    f"{SB_Name2Code[SB_VARS][ns]} {SB_VARS} "
                    f"run data get storage "
                    f"{DS_ROOT} {DS_LOCAL_VARS}[-1] 1\n"
                )
                command += (
                    f"data remove storage "
                    f"{DS_ROOT} {DS_LOCAL_VARS}[-1]\n"
                )
            command += COMMENT("LocalTemp.Load")
            for ns in self.temp_ns[namespace][::-1]:
                command += (
                    f"execute store result score "
                    f"{SB_Name2Code[SB_TEMP][ns]} {SB_TEMP} "
                    f"run data get storage "
                    f"{DS_ROOT} {DS_LOCAL_TEMP}[-1] 1\n"
                )
                command += (
                    f"data remove storage "
                    f"{DS_ROOT} {DS_LOCAL_TEMP}[-1]\n"
                )

            return command

        return store(), load()


class FileNamespace:
    """
    文件命名空间存储及其操作
    """
    def __init__(self):
        """
        初始化文件命名空间
        """
        self.namespace_tree = OrderedDict()

    def init_root(self, file_namespace: str, level: str | None, file_ns_type: str, ns: str) -> None:
        """
        初始化根文件命名空间

        :param file_namespace: 文件命名空间
        :type file_namespace: str
        :param level: 文件层级名
        :type level: str | None
        :param file_ns_type: 文件命名空间类型
        :type file_ns_type: str
        :param ns: 文件命名空间所对应的普通命名空间
        :type ns: str
        :return: None
        :rtype: None
        """
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
        """
        在指定的文件命名空间下创建一个名称指向目标文件命名空间

        :param name: 名称
        :type name: str
        :param targe_file_namespace: 指向的文件命名空间
        :type targe_file_namespace: str
        :param file_namespace: 设置的文件命名空间
        :type file_namespace: str
        :param level: 文件层级名
        :type level: str | None
        :param file_ns_type: 文件命名空间类型
        :type file_ns_type: str
        :param ns: 文件命名空间所对应的普通命名空间
        :type ns: str
        :return: None
        :rtype: None
        """
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
        """
        在指定的文件命名空间下寻找名称，并返回所找到的值

        :param name: 寻找的名称
        :type name: str
        :param file_namespace: 寻找的文件命名空间
        :type file_namespace: str
        :param ret_raw: 是否返回源字典
        :type ret_raw: bool
        :returns: (完整文件命名空间 | 文件命名空间字典, 基础文件命名空间)
        :rtype: tuple[str | dict, str]
        """
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
