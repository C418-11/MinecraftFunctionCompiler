import ast
import json
import os
from abc import ABC
from itertools import zip_longest
from collections import OrderedDict
from Constant import Flags
from Constant import ScoreBoards
from Constant import RawJsons

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
    "python:built-in\\int": OrderedDict([
        ('x', DefaultArgType('x', UnnecessaryParameter())),
    ]),
    "python:built-in\\print": print_args,
    # todo "python:built-in\\input": print_args,
}

SB_ARGS: str = ScoreBoards.Args
SB_TEMP: str = ScoreBoards.Temp
SB_FLAGS: str = ScoreBoards.Flags
SB_INPUT: str = ScoreBoards.Input
SB_VARS: str = ScoreBoards.Vars

ENABLE_DEBUGGING: bool = True


SAVE_PATH = "./.output/"
# SAVE_PATH = r"D:\game\Minecraft\.minecraft\versions\1.16.5投影\saves\函数\datapacks\函数测试\data\source_code\functions"

ResultExt = ".?Result"


def namespace_path(namespace: str, path: str):
    base_path = os.path.join(namespace.split(":", 1)[1], path)
    return os.path.join(SAVE_PATH, base_path)


def IF_FLAG(flag: str, cmd: str):
    """
    行尾 **没有** 换行符
    """
    return f"execute if score {flag} {SB_FLAGS} = {Flags.TRUE} {SB_FLAGS} run {cmd}"


class SBCheckType:
    IF = "if"
    UNLESS = "unless"


def CHECK_SB(t: str, a_name: str, a_objective: str, b_name: str, b_objective: str, cmd: str):
    """
    行尾 **没有** 换行符
    """
    return f"execute {t} score {a_name} {a_objective} = {b_name} {b_objective} run {cmd}"


def DEBUG_OBJECTIVE(
        raw_json: dict = None, *,
        objective: str, name: str,
        from_objective: str = None, from_name: str = None
):
    """
    行尾 **有** 换行符
    """

    if raw_json is None:
        raw_json = {"text": ""}

    if (from_objective is not None) ^ (from_name is not None):
        raise Exception("from_objective 和 from_name 必须同时传入")

    from_details: list[dict] = []

    if from_objective is not None:
        from_details.append({"text": " --From: ", "bold": True, "color": "gold"})
        from_details.append({"text": from_objective, "color": "dark_purple"})
        from_details.append({"text": " | ", "bold": True, "color": "gold"})
        from_details.append({"text": from_name, "color": "dark_aqua"})
        from_details.append({"text": " | ", "bold": True, "color": "gold"})
        from_details.append({"score": {"name": from_name, "objective": from_objective}, "color": "green"})

    debug_prefix = RawJsons.Prefix
    debug_prefix["italic"] = True
    debug_prefix["color"] = "gray"

    json_txt = json.dumps({
        "text": "",
        "extra": [
            debug_prefix,
            {"text": " "},
            {"text": "[DEBUG]", "color": "gray", "italic": True},
            {"text": " "},
            raw_json,
            {"text": objective, "color": "dark_purple"},
            {"text": " | ", "bold": True, "color": "gold"},
            {"text": name, "color": "dark_aqua"},
            {"text": " | ", "bold": True, "color": "gold"},
            {"score": {"name": name, "objective": objective}, "color": "green"},
            *from_details
        ]
    })
    return f'{IF_FLAG(Flags.DEBUG, f"tellraw @a {json_txt}")}\n'


class NameNodeGenType:
    RS = "RawStr"
    SB = "ScoreBoard"


def generate_name_node(node, namespace, generate_type):
    if not isinstance(node, ast.Name):
        raise Exception("节点不是 Name 类型")

    if generate_type == NameNodeGenType.RS:
        return f"{node.id}"
    elif generate_type == NameNodeGenType.SB:
        return (
            f"scoreboard players operation "
            f"{namespace}{ResultExt} {SB_TEMP} "
            f"= {namespace}.{node.id} {SB_VARS}\n"
        )
    else:
        raise Exception("未知的生成类型")


class DebugTip:
    Reset = {"text": "重置: ", "color": "gold", "bold": True}
    Set = {"text": "设置: ", "color": "gold", "bold": True}
    Calc = {"text": "计算: ", "color": "gold", "bold": True}


Uid = 9


def newUid():
    global Uid
    Uid += 1
    return hex(Uid)[2:]


def generate_code(node, namespace: str):
    namespace = os.path.normpath(namespace)
    os.makedirs(namespace_path(namespace, ''), exist_ok=True)

    if isinstance(node, ast.Module):
        with open(namespace_path(namespace, "module.mcfunction"), mode='w') as f:
            for statement in node.body:
                c = generate_code(statement, os.path.join(namespace, "module"))
                f.write(c)

        return ''

    if isinstance(node, ast.FunctionDef):
        with open(namespace_path(namespace, f"{node.name}.mcfunction"), mode='w') as f:
            args = generate_code(node.args, os.path.join(namespace, node.name))
            f.write(args)
            for statement in node.body:
                body = generate_code(statement, os.path.join(namespace, node.name))
                f.write(body)
        return ''

    if isinstance(node, ast.If):
        block_uid = newUid()

        base_namespace = f"{namespace}\\.if"
        base_path = namespace_path(base_namespace, '')
        os.makedirs(base_path, exist_ok=True)

        with open(os.path.join(base_path, f"{block_uid}.mcfunction"), mode='w') as f:
            f.write('tellraw @a {"text": "进入True分支"}\n')
            for statement in node.body:
                body = generate_code(statement, namespace)
                f.write(body)
        with open(os.path.join(base_path, f"{block_uid}-else.mcfunction"), mode='w') as f:
            f.write('tellraw @a {"text": "进入False分支"}\n')
            for statement in node.orelse:
                body = generate_code(statement, namespace)
                f.write(body)

        command = []
        del_temp = ''
        func_path = f"{base_namespace}\\{block_uid}".replace('\\', '/')

        if isinstance(node.test, ast.Constant):
            if node.test.value:
                test_name, test_objective = Flags.TRUE, SB_FLAGS
            else:

                test_name, test_objective = Flags.FALSE, SB_FLAGS
        elif isinstance(node.test, ast.Name):
            command.append(generate_name_node(node.test, namespace, NameNodeGenType.SB)[:-1])  # 去除换行符
            if ENABLE_DEBUGGING:
                command.append(DEBUG_OBJECTIVE(DebugTip.Reset, objective=SB_TEMP, name=f"{namespace}{ResultExt}"))
            del_temp += f"scoreboard players reset {namespace}{ResultExt} {SB_TEMP}\n"
            test_name, test_objective = f"{namespace}{ResultExt}", SB_TEMP
        else:
            raise Exception("无法解析的测试")

        command.append(CHECK_SB(
            SBCheckType.IF,
            test_name, test_objective,
            Flags.TRUE, SB_FLAGS,
            f"function {func_path}"
        ))
        command.append(CHECK_SB(
            SBCheckType.UNLESS,
            test_name, test_objective,
            Flags.TRUE, SB_FLAGS,
            f"function {func_path}-else"
        ))

        cmd = '\n'.join(command) + '\n' + del_temp

        return cmd

    if isinstance(node, ast.arguments):
        args = [arg.arg for arg in node.args]

        if namespace in func_args:
            warnings.warn(
                f"函数命名空间 {namespace} 已经存在, 可能覆盖之前的定义",
                UserWarning,
                stacklevel=0
            )

        args_dict = OrderedDict()
        command = ''

        # 反转顺序以匹配默认值
        for name, default in zip_longest(reversed(args), reversed(node.defaults), fillvalue=None):

            if default is None:
                args_dict[name] = ArgType(name)
            elif isinstance(default, ast.Constant):
                default_value = default.value
                args_dict[name] = DefaultArgType(name, default_value)
            else:
                raise Exception("无法解析的默认值")

            command += (
                f"scoreboard players operation "
                f"{namespace}.{name} {SB_VARS} "
                f"= "
                f"{namespace}.{name} {SB_ARGS}\n"
            )
            if ENABLE_DEBUGGING:
                command += DEBUG_OBJECTIVE(
                    DebugTip.Set,
                    objective=SB_VARS, name=f"{namespace}.{name}",
                    from_objective=SB_ARGS, from_name=f"{namespace}.{name}"
                )

        # 将最终顺序反转回来
        args_dict = OrderedDict([(k, v) for k, v in reversed(args_dict.items())])

        func_args[namespace] = args_dict

        return command

    if isinstance(node, ast.Name):
        return f"{node.id}"

    if isinstance(node, ast.Return):
        command = ''
        if isinstance(node.value, ast.Name):
            command += generate_name_node(node.value, namespace, NameNodeGenType.SB)
            if ENABLE_DEBUGGING:
                command += DEBUG_OBJECTIVE(DebugTip.Reset, objective=SB_TEMP, name=f"{namespace}{ResultExt}")
        else:
            command += generate_code(node.value, namespace)

        return command

    if isinstance(node, ast.BinOp):
        left = generate_code(node.left, namespace)
        right = generate_code(node.right, namespace)

        command = f"scoreboard players operation {namespace}.*BinOp {SB_TEMP} = {namespace}.{left} {SB_VARS}\n"

        if isinstance(node.op, ast.Add):
            command += f"scoreboard players operation {namespace}.*BinOp {SB_TEMP} += {namespace}.{right} {SB_VARS}\n"
        else:
            raise Exception(f"无法解析的运算符 {node.op}")

        command += f"scoreboard players operation {namespace}{ResultExt} {SB_TEMP} = {namespace}.*BinOp {SB_TEMP}\n"

        if ENABLE_DEBUGGING:
            command += DEBUG_OBJECTIVE(DebugTip.Calc, objective=SB_TEMP, name=f"{namespace}{ResultExt}")
            command += DEBUG_OBJECTIVE(DebugTip.Reset, objective=SB_TEMP, name=f"{namespace}.*BinOp")
        command += f"scoreboard players reset {namespace}.*BinOp {SB_TEMP}\n"

        return command

    if isinstance(node, ast.Expr):
        return generate_code(node.value, namespace)

    if isinstance(node, ast.Constant):
        value = node.value

        if type(value) is bool:
            value = 1 if value else 0

        if not isinstance(node.value, int):
            raise Exception(f"无法解析的常量 {node.value}")

        command = (
            f"scoreboard players set "
            f"{namespace}{ResultExt} {SB_TEMP} "
            f"{value}\n"
        )

        if ENABLE_DEBUGGING:
            command += DEBUG_OBJECTIVE(DebugTip.Set, objective=SB_TEMP, name=f"{namespace}{ResultExt}")

        return command

    if isinstance(node, ast.Assign):
        command = generate_code(node.value, namespace)

        for t in node.targets:
            if not isinstance(t, ast.Name):
                raise Exception("暂时只能赋值Name节点")

            target = t.id

            command += (
                f"scoreboard players operation "
                f"{namespace}.{target} {SB_VARS} "
                f"= "
                f"{namespace}{ResultExt} {SB_TEMP}\n"
            )
            if ENABLE_DEBUGGING:
                command += DEBUG_OBJECTIVE(
                    DebugTip.Set,
                    objective=SB_VARS, name=f"{namespace}.{target}",
                    from_objective=SB_TEMP, from_name=f"{namespace}{ResultExt}"
                )
                command += DEBUG_OBJECTIVE(DebugTip.Reset, objective=SB_TEMP, name=f"{namespace}{ResultExt}")

            command += f"scoreboard players reset {namespace}{ResultExt} {SB_TEMP}\n"

        return command

    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            func = node.func.id
        else:
            raise Exception("暂时无法解析的函数名")

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
                del_args += DEBUG_OBJECTIVE(DebugTip.Reset, objective=SB_ARGS, name=f"{func}.{name}")
            del_args += f"scoreboard players reset {func}.{name} {SB_ARGS}\n"

            if isinstance(value, ast.Call):
                # 拿到value的namespace
                commands += generate_code(value, namespace)

                func_result = f"{namespace}\\{generate_code(value.func, namespace)}"

                commands += (
                    f"scoreboard players operation "
                    f"{func}.{name} {SB_ARGS} "  # To
                    "= "  # 运算符
                    f"{func_result}{ResultExt} {SB_TEMP}\n"  # From
                )
                if ENABLE_DEBUGGING:
                    commands += DEBUG_OBJECTIVE(
                        DebugTip.Set,
                        objective=SB_ARGS, name=f"{func}.{name}",
                        from_objective=SB_TEMP, from_name=f"{func_result}{ResultExt}"
                    )
                    del_args += DEBUG_OBJECTIVE(objective=SB_ARGS, name=f"{func_result}{ResultExt}")
                del_args += f"scoreboard players reset {func_result}{ResultExt} {SB_TEMP}\n"

            elif isinstance(value, ast.Constant):
                commands += f"scoreboard players set {func}.{name} {SB_ARGS} {value.value}\n"
            elif isinstance(value, ast.Name):
                commands += (
                    f"scoreboard players operation "
                    f"{func}.{name} {SB_ARGS} "
                    "= "
                    f"{namespace}.{value.id} {SB_VARS}\n")
                if ENABLE_DEBUGGING:
                    commands += DEBUG_OBJECTIVE(
                        DebugTip.Set,
                        objective=SB_ARGS, name=f"{func}.{name}",
                        from_objective=SB_VARS, from_name=f"{namespace}.{value.id}"
                    )
            else:
                raise Exception(f"无法解析的参数 {type(value).__name__}")

            if ENABLE_DEBUGGING:
                commands += DEBUG_OBJECTIVE(DebugTip.Set, objective=SB_ARGS, name=f"{func}.{name}")

        func = func.replace('\\', '/')
        commands += f"function {func}\n"
        commands += del_args

        return commands

    err_msg = json.dumps({"text": f"无法解析的节点: {namespace}.{type(node).__name__}", "color": "red"})
    return f"tellraw @a {err_msg}\n"


print(ast.dump(tree, indent=4))
print(generate_code(tree, "source_code:add"))
print(f"[DEBUG] {func_args=}")
