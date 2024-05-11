# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

import ast
from collections import OrderedDict
from typing import Any

from Constant import DataStorageRoot
from Constant import DataStorages
from Constant import ScoreBoards
from DebuggingTools import COMMENT
from ScoreboardTools import SB_Name2Code

SB_TEMP: str = ScoreBoards.Temp
SB_FLAGS: str = ScoreBoards.Flags
SB_VARS: str = ScoreBoards.Vars

DS_ROOT: str = DataStorageRoot
DS_TEMP: str = DataStorages.Temp
DS_LOCAL_VARS: str = DataStorages.LocalVars
DS_LOCAL_TEMP: str = DataStorages.LocalTemp


def root_namespace(namespace: str) -> str:
    return namespace.split(":", 1)[1].split('\\')[0]


ns_map: OrderedDict[str, OrderedDict[str, ...]] = OrderedDict()


def ns_setter(name: str, targe_namespace: str, namespace: str, ns_type: str = None) -> None:
    data = {
        name: {
            ".__namespace__": targe_namespace,
            ".__type__": ns_type
        }
    }

    try:
        last_ns, last_name = namespace.rsplit('\\', 1)
    except ValueError:
        ns_map[namespace].update(data)
    else:
        ns_map[last_ns][last_name].update(data)


def ns_getter(name, namespace: str, ret_raw: bool = False) -> tuple[str | dict, str]:
    """

    :param name: 需要寻找的名称
    :param namespace: 在那个命名空间下进行寻找
    :param ret_raw: 是否直接返回源字典
    :return: 当ret_raw为True时直接返回源字典，否则返回所找到的完整命名空间
    """

    last_map: dict[str, dict[str, ...]] = ns_map
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
        node: Any,
        namespace: str,
        *,
        not_exists_ok: bool = False,
        ns_type: str | None = None
) -> tuple[str, str, str]:
    """
    :param node: AST节点
    :param namespace: 当前命名空间
    :param not_exists_ok: 名称不存在时在当前命名空间下生成
    :param ns_type: 自动生成时填入的命名空间类型
    :return: (name, full_namespace, root_namespace)
    """

    if isinstance(node, ast.Name):
        try:
            ns, base_ns = ns_getter(node.id, namespace, ret_raw=True)
        except KeyError:
            if not not_exists_ok:
                raise
            ns_setter(node.id, f"{namespace}\\{node.id}", namespace, ns_type)
            ns, base_ns = ns_getter(node.id, namespace, ret_raw=True)
        ns: dict[str, dict[str, ...] | str]
        full_ns: str = ns[".__namespace__"]
        if ns[".__type__"] == "attribute":
            target_ns, name = full_ns.split("|", 1)
            return node_to_namespace(
                ast.Name(id=name), target_ns, not_exists_ok=not_exists_ok, ns_type=ns_type
            )
        return node.id, full_ns, base_ns

    if isinstance(node, ast.Attribute):
        value_ns = node_to_namespace(node.value, namespace, not_exists_ok=not_exists_ok, ns_type=ns_type)[1]
        try:
            full_ns = ns_getter(node.attr, value_ns)[0]
        except KeyError:
            if not not_exists_ok:
                raise
            ns_setter(node.attr, f"{value_ns}\\{node.attr}", value_ns, ns_type)
            full_ns = ns_getter(node.attr, value_ns)[0]

        return (
            node.attr,
            full_ns,
            value_ns
        )

    raise Exception(f"暂时不支持的节点类型 '{type(node.value).__name__}'")


temp_map: OrderedDict[str, list[str]] = OrderedDict()


def store_local(namespace: str) -> tuple[str, str]:
    _ns, _name = namespace.split('\\', 1)
    local_ns: dict[str, dict[str, ...]] = ns_getter(_name, _ns, ret_raw=True)[0]

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
        for ns in temp_map[namespace]:
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
        for ns in temp_map[namespace][::-1]:
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


__all__ = (
    "ns_map",
    "temp_map",

    "root_namespace",
    "ns_setter",
    "ns_getter",
    "node_to_namespace",
    "store_local",
)
