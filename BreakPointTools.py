# -*- coding: utf-8 -*-
# cython: language_level = 3
"""
抛出, 更新, 处理断点
"""
import inspect
import json
import os
import re
import warnings
from typing import Callable
from typing import TypeVar

Processor = Callable[[str | None, str | None, ...], str | None | tuple[str, bool]]

BreakPointProcessor: dict[str | None, Processor] = {}

BreakPointLevels: set[str] = {"module", "function", "if"}


def BreakPointFlag(func: str | None, *args, **kwargs) -> str:
    """
    用于生成断点标记

    :param func: 断点处理函数注册名
    :type func: str | None
    :param args: 断点处理函数参数
    :type args: Any
    :param kwargs: 断点处理函数关键字参数
    :type kwargs: Any
    :return: 生成的断点标记
    :rtype: str
    """
    flag_str = "&Flag: BreakPoint"
    flag_str += f"&func={func}" if func else ""
    flag_str += f"&args={json.dumps(args)}" if args else ""
    flag_str += f"&kwargs={json.dumps(kwargs)}" if kwargs else ""
    return flag_str


Processor_T = TypeVar("Processor_T", bound=Processor)


def register_processor(name: str | None) -> Callable[[Processor_T], Processor_T]:
    """
    注册断点处理函数

    :param name: 注册名
    :type name: str | None
    :return: 用于注册的装饰器
    :rtype: Callable[[Processor_T], Processor_T]
    """

    def decorator(func: Processor_T) -> Processor_T:
        """
        注册断点处理函数

        :param func: 断点处理函数
        :type func: Processor_T
        :return: 原样返回所装饰的函数
        :rtype: Processor_T
        """
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


def raiseBreakPoint(env, file_namespace: str, func: str | None, *func_args, **func_kwargs) -> None:
    """
    抛出断点

    :param file_namespace: 抛出所在的文件命名空间
    :type file_namespace: str
    :param func: 断点处理函数注册名
    :type func: str | None
    :param func_args: 断点处理函数参数
    :type func_args: Any
    :param func_kwargs: 断点处理函数关键字参数
    :type func_kwargs: Any
    :return: None
    :rtype: None
    """
    global _BP_ID
    f_ns, f_name = file_namespace.rsplit('\\', maxsplit=1)
    target_f_ns: dict = env.file_ns_getter(f_name, f_ns, ret_raw=True)[0]

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


def updateBreakPoint(env, c_conf, g_conf, file_namespace: str) -> str:
    """
    更新断点

    :param file_namespace: 需要更新的文件命名空间
    :type file_namespace: str
    :return: 断点处理函数生成的命令
    :rtype: str
    """
    f_ns, f_name = file_namespace.rsplit('\\', maxsplit=1)
    target_f_ns: dict[str, dict[str, ...] | str] = env.file_ns_getter(f_name, f_ns, ret_raw=True)[0]

    level: str = target_f_ns[".__level__"]

    if level not in BreakPointLevels:
        raise Exception(f"SBP: Unknown level: \'{level}\', please check if it is registered in the code.")

    if ":breakpoints" not in target_f_ns:
        target_f_ns[":breakpoints"] = {}

    command = ''

    for file_name in target_f_ns:
        if not file_name.endswith("$link"):
            continue

        raw_f_namespace = target_f_ns[file_name][".__file_namespace__"]
        rf_ns, rf_name = raw_f_namespace.rsplit('\\', maxsplit=1)
        raw_f_ns = env.file_ns_getter(rf_name, rf_ns, ret_raw=True)[0]

        if ":breakpoints" not in raw_f_ns:
            continue

        params_data = {
            "func_path": None,
            "level": level,
            "env": env,
            "c_conf": c_conf,
            "g_conf": g_conf,
        }
        data_keys = set(params_data.keys())

        for bp_id, bp_data in raw_f_ns[":breakpoints"].items():
            try:
                processor = BreakPointProcessor[bp_data["func"]]
            except KeyError:
                warnings.warn(
                    f"SBP: Unknown function: \'{bp_data['func']}\', please check if it is registered in the code.",
                    UserWarning,
                    stacklevel=2
                )
                continue

            parameters = set(inspect.signature(processor).parameters.keys())
            required_params = parameters & data_keys
            required_data = {k: params_data[k] for k in required_params}
            cmd, keep_raise = processor(*bp_data["args"], **required_data, **bp_data["kwargs"])
            command += cmd

            if keep_raise:
                raiseBreakPoint(f_name, f_ns, bp_data["func"], *bp_data["args"], **bp_data["kwargs"])

    return command


class SplitBreakPoint:
    """
    用于分割断点的类
    """

    def __init__(self, env, c_conf, g_conf, file_path: str, file_namespace: str, encoding: str = "utf-8") -> None:
        """
        初始化

        :param file_path: 写入的文件路径
        :type file_path: str
        :param file_namespace: 当前的文件命名空间
        :type file_namespace: str
        :param encoding: 文件编码
        :type encoding: str
        :return: None
        :rtype: None
        """
        self._env = env
        self._c_conf = c_conf
        self._g_conf = g_conf

        self._namespace = file_namespace
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

    def _parse_comment(self, text: str) -> None:
        """
        解析注释 在断点标记处分割MCF

        :param text: 需要解析的注释文本
        :type text: str
        :return: None
        :rtype: None
        """
        matches = self._flag_pattern.findall(text)
        if not matches or matches[0] != "BreakPoint":
            self._write2file(text)
            return

        name, ext = os.path.splitext(self._writing_name)
        id_name = f"{name}-{hex(self._pb_id)[2:]}"
        writing_name = f"{id_name}{ext}"

        match_func = self._func_pattern.findall(text)
        match_args = self._args_pattern.findall(text)
        match_kwargs = self._kwargs_pattern.findall(text)

        func_key = match_func[0] if match_func else None
        match_args = match_args[0] if match_args else "[]"
        match_kwargs = match_kwargs[0] if match_kwargs else "{}"

        try:
            processor = BreakPointProcessor[func_key]
        except KeyError:
            raise Exception(f"SBP: Unknown function: \'{func_key}\', please check if it is registered in the code.")

        try:
            args = json.loads(match_args)
            kwargs = json.loads(match_kwargs)
        except json.JSONDecodeError:
            raise Exception("SBP: Arguments are not valid json format.")

        ns_path = f"{self._namespace}\\{id_name}".replace('\\', '/')

        params_data = {
            "func_path": ns_path,
            "level": None,
            "env": self._env,
            "c_conf": self._c_conf,
            "g_conf": self._g_conf,
        }
        data_keys = set(params_data.keys())

        required_params = set(inspect.signature(processor).parameters.keys()) & data_keys
        required_data = {k: params_data[k] for k in required_params}

        result = processor(*args, **required_data, **kwargs)

        result = '' if result is None else result

        self._write2file(result)

        self._pb_id += 1
        self._open_file.close()
        self._open_file = open(os.path.join(self._writing_dir, writing_name), mode='w', encoding='utf-8')

    def write(self, text: str) -> None:
        """
        写入文本

        :param text: 文本
        :type text: str
        :return: None
        :rtype: None
        """
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

    def _write2file(self, text: str) -> None:
        """
        写入文本到当前打开的文件

        :param text: 文本
        :type text: str
        :return: None
        :rtype: None
        """
        self._open_file.write(text)

    def _is_comment_line(self, txt: str) -> bool:
        """
        判断是否是注释行

        :param txt: 文本
        :type txt: str
        :return: 是否是注释行
        :rtype: bool
        """
        if '#' not in txt:
            return False
        last_char = self._last_char
        if txt.index('#') != 0:
            last_char = txt[txt.index('#') - 1]

        if last_char != '\n':
            return False
        return True

    def _process_comment(self, txt: str) -> bool:
        """
        处理注释行

        :param txt: 待处理文本
        :type txt: str
        :return: 是否处理了注释
        :rtype: bool
        """
        if self._is_comment:
            self._comment_line_cache += txt
            self._last_char = txt[-1]
            if '\n' in txt:
                self._parse_comment(self._comment_line_cache)
                self._comment_line_cache = ''
                self._is_comment = False
            return True
        return False

    def close(self) -> None:
        # noinspection GrazieInspection
        """
        关闭文件

        :return: None
        :rtype: None
        """
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
