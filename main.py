import ast
import json
import os
from abc import ABC
from itertools import zip_longest
from collections import OrderedDict
from Constant import Flags
from Constant import ScoreBoards

import warnings

with open("test/add.py", mode='r') as _:
    tree = ast.parse(_.read())


class ABCParameterType(ABC):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name=})"


class ABCDefaultParameterType(ABCParameterType):
    def __init__(self, name, default):
        super().__init__(name)
        self.default = default

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name=}, {self.default=})"


class ArgType(ABCParameterType):
    pass


class DefaultArgType(ArgType, ABCDefaultParameterType):
    pass


class KwType(ABCParameterType):
    pass


class DefaultKwType(KwType, ABCDefaultParameterType):
    pass


class UnnecessaryParameter:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __repr__(self):
        return "<<UnnecessaryParameter>>"


print_args = OrderedDict([
    ('*', DefaultArgType('*', UnnecessaryParameter())),
    *[(('*' + str(i)), DefaultArgType('*' + str(i), UnnecessaryParameter())) for i in range(1, 10)]
])


func_args: dict[str, OrderedDict[str, ArgType | DefaultArgType]] = {
    "python:built-in\\int":  OrderedDict([
        ('x', DefaultArgType('x', UnnecessaryParameter())),
    ]),
    "python:built-in\\print": print_args,
    "python:built-in\\input": print_args,
}

SB_ARGS: str = ScoreBoards.Args
SB_TEMP: str = ScoreBoards.Temp
SB_FLAGS: str = ScoreBoards.Flags
SB_INPUT: str = ScoreBoards.Input

ENABLE_DEBUGGING: bool = True


SAVE_PATH = "./.output/"
# SAVE_PATH = r"D:\game\Minecraft\.minecraft\versions\1.16.5投影\saves\函数\datapacks\函数测试\data\source_code\functions"


def file_path(namespace: str, filename: str):
    base_path = os.path.join(namespace.split(":", 1)[1], filename)
    return os.path.join(SAVE_PATH, base_path)


def IF_FLAG(flag: str, cmd: str):
    return f"execute if score {flag} {SB_FLAGS} = {Flags.TRUE} {SB_FLAGS} run {cmd}\n"


def DEBUG_OBJECTIVE(objective: str, name: str):
    json_txt = json.dumps({
        "text": "",
        "extra": [
            {"text": "[DEBUG]", "color": "gray", "italic": True},
            {"text": " "},
            {"text": objective, "color": "dark_purple"},
            {"text": " | ", "bold": True, "color": "gold"},
            {"text": name, "color": "dark_aqua"},
            {"text": " | ", "bold": True, "color": "gold"},
            {"score": {"name": name, "objective": objective}, "color": "green"},
        ]
    })
    return IF_FLAG(Flags.DEBUG, f"tellraw @a {json_txt}\n")


def generate_code(node, namespace: str):
    namespace = os.path.normpath(namespace)
    os.makedirs(file_path(namespace, ''), exist_ok=True)

    if isinstance(node, ast.Module):
        with open(file_path(namespace, "module.mcfunction"), mode='w') as f:
            for statement in node.body:
                c = generate_code(statement, os.path.join(namespace, "module"))
                f.write(c)

        return ''

    if isinstance(node, ast.FunctionDef):
        with open(file_path(namespace, f"{node.name}.mcfunction"), mode='w') as f:
            args = generate_code(node.args, os.path.join(namespace, node.name))
            f.write(args)
            for statement in node.body:
                body = generate_code(statement, os.path.join(namespace, node.name))
                f.write(body)
        return ''

    if isinstance(node, ast.arguments):
        args = [arg.arg for arg in node.args]

        if namespace in func_args:
            warnings.warn(
                f"函数命名空间 {namespace} 已经存在, 可能覆盖之前的定义",
                UserWarning,
                stacklevel=0
            )

        args_dict = OrderedDict()

        # 反转顺序以匹配默认值
        for name, default in zip_longest(reversed(args), reversed(node.defaults), fillvalue=None):

            if default is None:
                args_dict[name] = ArgType(name)
            elif isinstance(default, ast.Constant):
                default_value = default.value
                args_dict[name] = DefaultArgType(name, default_value)
            else:
                raise Exception("无法解析的默认值")

        # 将最终顺序反转回来
        args_dict = OrderedDict([(k, v) for k, v in reversed(args_dict.items())])

        func_args[namespace] = args_dict

        return ''

    if isinstance(node, ast.Name):
        return f"{node.id}"

    if isinstance(node, ast.Return):
        return generate_code(node.value, namespace)

    if isinstance(node, ast.BinOp):
        left = generate_code(node.left, namespace)
        right = generate_code(node.right, namespace)

        command = f"scoreboard players operation {namespace}.*BinOp {SB_TEMP} = {namespace}.{left} {SB_ARGS}\n"

        if isinstance(node.op, ast.Add):
            command += f"scoreboard players operation {namespace}.*BinOp {SB_TEMP} += {namespace}.{right} {SB_ARGS}\n"
        else:
            raise Exception(f"无法解析的运算符 {node.op}")

        command += f"scoreboard players operation {namespace}.?Result {SB_TEMP} = {namespace}.*BinOp {SB_TEMP}\n"

        if ENABLE_DEBUGGING:
            command += DEBUG_OBJECTIVE(SB_TEMP, f"{namespace}.*BinOp")
        command += f"scoreboard players reset {namespace}.*BinOp {SB_TEMP}\n"

        return command

    if isinstance(node, ast.Expr):
        return generate_code(node.value, namespace)

    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Call):
        func = generate_code(node.func, namespace)
        # 如果是python内置函数，则不需要加上命名空间
        if func not in dir(__builtins__):
            func = f"{namespace}\\{func}"
        else:
            func = f"python:built-in\\{func}"

        commands: str = ''
        del_args: str = ''

        try:
            this_func_args = func_args[func]
        except KeyError:
            raise Exception(f"未注册过的函数: {func}")

        for name, value in zip_longest(this_func_args, node.args, fillvalue=None):
            if name is None:
                json_value = ast.dump(value)
                raise SyntaxError(f"函数 {func} 在调用时传入了额外的值 {json_value}")

            # 如果参数未提供值，且不是默认值，则报错
            if value is None:
                if not isinstance(this_func_args[name], DefaultArgType):
                    raise SyntaxError(f"函数 {func} 的参数 {name} 未提供值")

                default_value = this_func_args[name].default

                if isinstance(default_value, UnnecessaryParameter):
                    continue
                value = ast.Constant(value=this_func_args[name].default)

            if ENABLE_DEBUGGING:
                del_args += DEBUG_OBJECTIVE(SB_ARGS, f"{func}.{name}")
            del_args += f"scoreboard players reset {func}.{name} {SB_ARGS}\n"

            if isinstance(value, ast.Call):
                # 拿到value的namespace
                commands += generate_code(value, namespace)

                func_result = f"{namespace}\\{generate_code(value.func, namespace)}"

                commands += (
                    f"scoreboard players operation "
                    f"{func}.{name} {SB_ARGS} "  # To
                    f"= "  # 运算符
                    f"{func_result}.?Result {SB_TEMP}\n"  # From
                )
                if ENABLE_DEBUGGING:
                    del_args += DEBUG_OBJECTIVE(SB_ARGS, f"{func_result}.?Result")
                del_args += f"scoreboard players reset {func_result}.?Result {SB_TEMP}\n"

            elif isinstance(value, ast.Constant):
                commands += f"scoreboard players set {func}.{name} {SB_ARGS} {value.value}\n"

            else:
                raise Exception(f"无法解析的参数 {type(value).__name__}")

        func = func.replace('\\', '/')
        commands += f"function {func}\n"
        commands += del_args

        return commands

    err_msg = json.dumps({"text": f"无法解析的节点: {namespace}.{type(node).__name__}", "color": "red"})
    return f"tellraw @a {err_msg}\n"


print(ast.dump(tree, indent=4))
print(generate_code(tree, "source_code:add"))
print(f"[DEBUG] {func_args=}")
