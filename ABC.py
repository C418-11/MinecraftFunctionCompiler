# -*- coding: utf-8 -*-
# cython: language_level = 3


from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import OrderedDict

from Configuration import CompileConfiguration
from Configuration import GlobalConfiguration
from NamespaceTools import Namespace
from NamespaceTools import FileNamespace
from ParameterTypes import ABCParameter


class ABCEnvironment(ABC):
    def __init__(self, c_conf: CompileConfiguration, g_conf: GlobalConfiguration = None):
        if g_conf is None:
            g_conf = GlobalConfiguration()
        self.c_conf: CompileConfiguration = c_conf
        self.g_conf: GlobalConfiguration = g_conf
        self.namespace = Namespace(self.c_conf.base_namespace)
        self.file_namespace = FileNamespace()

        self.func_args: dict[str, OrderedDict[str, ABCParameter]] = {}

    @abstractmethod
    def generate_code(self, node: Any, namespace: str, file_namespace: str) -> str:
        ...

    @abstractmethod
    def ns_split_base(self, namespace: str) -> tuple[str, str]:
        ...

    @abstractmethod
    def ns_join_base(self, name: str) -> str:
        ...

    @abstractmethod
    def ns_from_node(
            self,
            node: Any,
            namespace: str,
            *,
            not_exists_ok: bool = False,
            ns_type: str | None = None
    ) -> tuple[str, str, str]:
        ...

    @abstractmethod
    def ns_init(self, namespace: str, ns_type: str) -> None:
        ...

    @abstractmethod
    def ns_setter(self, name: str, targe_namespace: str, namespace: str, ns_type: str) -> None:
        ...

    @abstractmethod
    def ns_getter(self, name, namespace: str, ret_raw: bool = False) -> tuple[str | dict, str]:
        ...

    @abstractmethod
    def ns_store_local(self, namespace: str) -> tuple[str, str]:
        ...

    @abstractmethod
    def temp_ns_init(self, namespace: str) -> None:
        ...

    @abstractmethod
    def temp_ns_append(self, namespace: str, name: str) -> None:
        ...

    @abstractmethod
    def temp_ns_remove(self, namespace: str, name: str) -> None:
        ...

    @abstractmethod
    def file_ns_init(self, file_namespace: str, level: str | None, file_ns_type: str, ns: str) -> None:
        ...

    @abstractmethod
    def file_ns_setter(
            self,
            name: str,
            targe_file_namespace: str,
            file_namespace: str,
            level: str | None,
            file_ns_type: str, ns: str
    ) -> None:
        ...

    @abstractmethod
    def file_ns_getter(self, name, file_namespace: str, ret_raw: bool = False) -> tuple[str | dict, str]:
        ...

    @abstractmethod
    def file_ns2path(self, path: str, *args) -> str:
        ...

    @abstractmethod
    def mkdirs_file_ns(self, file_namespace: str, *args):
        ...

    @abstractmethod
    def writeable_file_namespace(self, file_namespace: str, namespace: str):
        ...
