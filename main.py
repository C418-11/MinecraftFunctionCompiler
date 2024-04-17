import ast
import json
import os
import sys
import warnings
from abc import ABC
from collections import OrderedDict
from itertools import zip_longest

from Constant import Flags
from Constant import RawJsons
from Constant import ScoreBoards


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
}

SB_ARGS: str = ScoreBoards.Args
SB_TEMP: str = ScoreBoards.Temp
SB_FLAGS: str = ScoreBoards.Flags
SB_INPUT: str = ScoreBoards.Input
SB_VARS: str = ScoreBoards.Vars

SAVE_PATH: None | str = None
READ_PATH: None | str = None
BASE_NAMESPACE: None | str = None

ResultExt = ".?Result"


def join_base_ns(path: str) -> str:
    if BASE_NAMESPACE.endswith(":"):
        new_namespace = f"{BASE_NAMESPACE}{path}"
    else:
        new_namespace = f"{BASE_NAMESPACE}\\{path}"

    return new_namespace


def namespace_path(namespace: str, path: str) -> str:
    base_path = os.path.join(namespace.split(":", 1)[1], path)
    return os.path.join(SAVE_PATH, base_path)


def root_namespace(namespace: str) -> str:
    return namespace.split(":", 1)[1].split('\\')[0]


def IF_FLAG(flag: str, cmd: str) -> str:
    """
    行尾 **没有** 换行符
    """
    return f"execute if score {flag} {SB_FLAGS} = {Flags.TRUE} {SB_FLAGS} run {cmd}"


class SBCheckType:
    IF = "if"
    UNLESS = "unless"


def CHECK_SB(t: str, a_name: str, a_objective: str, b_name: str, b_objective: str, cmd: str):
    """
    行尾 **有** 换行符
    """
    return f"execute {t} score {a_name} {a_objective} = {b_name} {b_objective} run {cmd}\n"


ENABLE_DEBUGGING: bool = False


def DEBUG_OBJECTIVE(
        raw_json: dict = None, *,
        objective: str, name: str,
        from_objective: str = None, from_name: str = None
) -> str:
    """
    行尾 **有** 换行符
    """
    if not ENABLE_DEBUGGING:
        return ''

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


def DEBUG_TEXT(*raw_json: dict) -> str:
    """
    行尾 **有** 换行符
    """
    if not ENABLE_DEBUGGING:
        return ''

    json_txt = json.dumps({
        "text": "",
        "extra": [
            RawJsons.Prefix,
            {"text": " "},
            {"text": "[DEBUG]", "color": "gray", "italic": True},
            {"text": " "},
            *raw_json,
        ]
    })
    return f'{IF_FLAG(Flags.DEBUG, f"tellraw @a {json_txt}")}\n'


class DebugTip:
    Reset = {"text": "重置: ", "color": "gold", "bold": True}
    Set = {"text": "设置: ", "color": "gold", "bold": True}
    Calc = {"text": "计算: ", "color": "gold", "bold": True}
    Result = {"text": "结果: ", "color": "gold", "bold": True}
    DelArg = {"text": "删除参数: ", "color": "gold", "bold": True}
    Assign = {"text": "赋值: ", "color": "gold", "bold": True}
    SetArg = {"text": "传参: ", "color": "gold", "bold": True}

    Call = {"text": "调用: ", "color": "gold", "bold": True}
    Init = {"text": "初始化: ", "color": "gold", "bold": True}


Uid = 9


def newUid() -> str:
    global Uid
    Uid += 1
    return hex(Uid)[2:]


import_module_map: dict[str, dict[str, str]] = {}


def node_to_namespace(node, namespace: str) -> tuple[str, str, str]:
    if isinstance(node, ast.Name):
        return node.id, f"{namespace}\\{node.id}", namespace
    if isinstance(node, ast.Attribute):
        modules = import_module_map[root_namespace(namespace)]

        node_value = node_to_namespace(node.value, namespace)[0]

        if node_value not in modules:
            print(node_value, modules, file=sys.stderr)
            raise Exception("暂时无法解析的属性")

        return (
            f"{node_value}\\{node.attr}",
            join_base_ns(f"{modules[node_value]}\\{node.attr}"),
            join_base_ns(f"{modules[node_value]}")
        )

    raise Exception("暂时不支持的节点类型")


def generate_code(node, namespace: str) -> str:
    namespace = os.path.normpath(namespace)
    os.makedirs(namespace_path(namespace, ''), exist_ok=True)

    if isinstance(node, ast.Module):
        import_module_map[root_namespace(namespace)] = {}
        with open(namespace_path(namespace, "module.mcfunction"), mode='w', encoding="utf-8") as f:
            for statement in node.body:
                c = generate_code(statement, namespace)
                f.write(c)

        return ''

    if isinstance(node, ast.Import):
        command = ''
        for n in node.names:
            if not isinstance(n, ast.alias):
                raise Exception("当前版本只允许 Import 中有 alias")

            with open(os.path.join(READ_PATH, f"{n.name}.py"), mode='r', encoding="utf-8") as f:
                tree = ast.parse(f.read())

            print("------------导入文件-----------")
            print(os.path.normpath(os.path.join(READ_PATH, f"{n.name}.py")))
            print(ast.dump(tree, indent=4))
            print("------------------------------")

            new_namespace = join_base_ns(n.name)
            generate_code(tree, new_namespace)

            as_name = n.asname if n.asname is not None else n.name

            import_module_map[root_namespace(namespace)].update({as_name: n.name})

            command += DEBUG_TEXT(DebugTip.Init, {"text": f"导入 {n.name}"})
            command += f"function {new_namespace}/module\n"
        return command

    if isinstance(node, ast.FunctionDef):
        with open(namespace_path(namespace, f"{node.name}.mcfunction"), mode='w', encoding="utf-8") as f:
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

        with open(os.path.join(base_path, f"{block_uid}.mcfunction"), mode='w', encoding="utf-8") as f:
            f.write(DEBUG_OBJECTIVE({"text": "进入True分支"}, objective=SB_TEMP, name=f"{namespace}{ResultExt}"))
            for statement in node.body:
                body = generate_code(statement, namespace)
                f.write(body)
        with open(os.path.join(base_path, f"{block_uid}-else.mcfunction"), mode='w', encoding="utf-8") as f:
            f.write(DEBUG_OBJECTIVE({"text": "进入False分支"}, objective=SB_TEMP, name=f"{namespace}{ResultExt}"))
            for statement in node.orelse:
                body = generate_code(statement, namespace)
                f.write(body)

        command = ''
        del_temp = ''
        func_path = f"{base_namespace}\\{block_uid}".replace('\\', '/')

        command += generate_code(node.test, namespace)

        command += CHECK_SB(
            SBCheckType.UNLESS,
            f"{namespace}{ResultExt}", SB_TEMP,
            Flags.FALSE, SB_FLAGS,
            f"function {func_path}"
        )
        command += CHECK_SB(
            SBCheckType.IF,
            f"{namespace}{ResultExt}", SB_TEMP,
            Flags.FALSE, SB_FLAGS,
            f"function {func_path}-else"
        )

        command += DEBUG_OBJECTIVE(
            DebugTip.Reset,
            objective=SB_TEMP, name=f"{namespace}{ResultExt}"
        )
        command += f"scoreboard players reset {namespace}{ResultExt} {SB_TEMP}\n"

        cmd = command + del_temp

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
        assert isinstance(node.ctx, ast.Load)
        return (
            f"scoreboard players operation "
            f"{namespace}{ResultExt} {SB_TEMP} "
            f"= "
            f"{namespace}.{node.id} {SB_VARS}\n"
        )

    if isinstance(node, ast.Attribute):
        assert isinstance(node.ctx, ast.Load)
        if not isinstance(node.value, ast.Name):
            raise Exception("暂时无法解析的值")

        modules = import_module_map[root_namespace(namespace)]

        if node.value.id not in modules:
            print(node.value.id, modules)
            raise Exception("暂时无法解析的属性")

        attr_namespace = join_base_ns(f"{modules[node.value.id]}.{node.attr}")

        return (
            f"scoreboard players operation "
            f"{namespace}{ResultExt} {SB_TEMP} "
            f"= "
            f"{attr_namespace} {SB_VARS}\n"
        )

    if isinstance(node, ast.Return):
        command = generate_code(node.value, namespace)

        father_namespace = '\\'.join(namespace.split('\\')[:-1])

        command += (
            f"scoreboard players operation "
            f"{father_namespace}{ResultExt} {SB_TEMP} "
            f"= "
            f"{namespace}{ResultExt} {SB_TEMP}\n"
        )

        command += DEBUG_OBJECTIVE(
            DebugTip.Result,
            objective=SB_TEMP, name=f"{father_namespace}{ResultExt}",
            from_objective=SB_TEMP, from_name=f"{namespace}{ResultExt}"
        )
        command += DEBUG_OBJECTIVE(DebugTip.Reset, objective=SB_TEMP, name=f"{namespace}{ResultExt}")

        command += f"scoreboard players reset {namespace}{ResultExt} {SB_TEMP}\n"

        return command

    if isinstance(node, ast.BinOp):
        command = ''

        command += generate_code(node.left, namespace)

        command += f"scoreboard players operation {namespace}.*BinOp {SB_TEMP} = {namespace}{ResultExt} {SB_TEMP}\n"
        command += f"scoreboard players reset {namespace}{ResultExt} {SB_TEMP}\n"

        command += generate_code(node.right, namespace)

        if isinstance(node.op, ast.Add):
            command += \
                f"scoreboard players operation {namespace}.*BinOp {SB_TEMP} += {namespace}{ResultExt} {SB_TEMP}\n"
        elif isinstance(node.op, ast.Sub):
            command += \
                f"scoreboard players operation {namespace}.*BinOp {SB_TEMP} -= {namespace}{ResultExt} {SB_TEMP}\n"
        elif isinstance(node.op, ast.Mult):
            command += \
                f"scoreboard players operation {namespace}.*BinOp {SB_TEMP} *= {namespace}{ResultExt} {SB_TEMP}\n"
        elif isinstance(node.op, ast.Div):
            command += \
                f"scoreboard players operation {namespace}.*BinOp {SB_TEMP} /= {namespace}{ResultExt} {SB_TEMP}\n"
        else:
            raise Exception(f"无法解析的运算符 {node.op}")

        command += f"scoreboard players reset {namespace}{ResultExt} {SB_TEMP}\n"

        command += f"scoreboard players operation {namespace}{ResultExt} {SB_TEMP} = {namespace}.*BinOp {SB_TEMP}\n"

        command += DEBUG_OBJECTIVE(DebugTip.Calc, objective=SB_TEMP, name=f"{namespace}{ResultExt}")
        command += DEBUG_OBJECTIVE(DebugTip.Reset, objective=SB_TEMP, name=f"{namespace}.*BinOp")

        command += f"scoreboard players reset {namespace}.*BinOp {SB_TEMP}\n"

        return command

    if isinstance(node, ast.UnaryOp):
        command = ''

        command += generate_code(node.operand, namespace)

        if isinstance(node.op, ast.Not):
            command += CHECK_SB(
                SBCheckType.UNLESS,
                f"{namespace}{ResultExt}", SB_TEMP,
                Flags.FALSE, SB_FLAGS,
                (
                    f"scoreboard players operation "
                    f"{namespace}.*UnaryOp {SB_TEMP} "
                    f"= "
                    f"{Flags.FALSE} {SB_FLAGS}"
                )
            )

            command += CHECK_SB(
                SBCheckType.IF,
                f"{namespace}{ResultExt}", SB_TEMP,
                Flags.FALSE, SB_FLAGS,
                (
                    f"scoreboard players operation "
                    f"{namespace}.*UnaryOp {SB_TEMP} "
                    f"= "
                    f"{Flags.TRUE} {SB_FLAGS}"
                )
            )
        elif isinstance(node.op, ast.USub):
            command += (
                f"scoreboard players operation "
                f"{namespace}.*UnaryOp {SB_TEMP} "
                f"= "
                f"{namespace}{ResultExt} {SB_TEMP}\n"
            )
            command += (
                f"scoreboard players operation "
                f"{namespace}.*UnaryOp {SB_TEMP} "
                f"*= "
                f"{Flags.NEG} {SB_FLAGS}\n"
            )
        else:
            raise Exception(f"暂时无法解析的UnaryOp运算 {node.op}")

        command += f"scoreboard players reset {namespace}{ResultExt} {SB_TEMP}\n"

        command += f"scoreboard players operation {namespace}{ResultExt} {SB_TEMP} = {namespace}.*UnaryOp {SB_TEMP}\n"

        command += DEBUG_OBJECTIVE(DebugTip.Calc, objective=SB_TEMP, name=f"{namespace}{ResultExt}")
        command += DEBUG_OBJECTIVE(DebugTip.Reset, objective=SB_TEMP, name=f"{namespace}.*UnaryOp")

        command += f"scoreboard players reset {namespace}.*UnaryOp {SB_TEMP}\n"

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

            command += DEBUG_OBJECTIVE(
                DebugTip.Assign,
                objective=SB_VARS, name=f"{namespace}.{target}",
                from_objective=SB_TEMP, from_name=f"{namespace}{ResultExt}"
            )
            command += DEBUG_OBJECTIVE(DebugTip.Reset, objective=SB_TEMP, name=f"{namespace}{ResultExt}")

            command += f"scoreboard players reset {namespace}{ResultExt} {SB_TEMP}\n"

        return command

    if isinstance(node, ast.Call):
        func_name, func, ns = node_to_namespace(node.func, namespace)

        # 如果是python内置函数，则不需要加上命名空间
        if func_name in dir(__builtins__):
            func = f"python:built-in\\{func_name}"

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

            commands += generate_code(value, namespace)
            commands += (
                f"scoreboard players operation "
                f"{func}.{name} {SB_ARGS} "
                "= "
                f"{namespace}{ResultExt} {SB_TEMP}\n"
            )

            commands += DEBUG_OBJECTIVE(
                DebugTip.SetArg,
                objective=SB_ARGS, name=f"{func}.{name}",
                from_objective=SB_TEMP, from_name=f"{namespace}{ResultExt}"
            )
            commands += DEBUG_OBJECTIVE(DebugTip.Reset, objective=SB_TEMP, name=f"{namespace}{ResultExt}")

            commands += f"scoreboard players reset {namespace}{ResultExt} {SB_TEMP}\n"

            # 删除已经使用过的参数
            del_args += DEBUG_OBJECTIVE(DebugTip.DelArg, objective=SB_ARGS, name=f"{func}.{name}")
            del_args += f"scoreboard players reset {func}.{name} {SB_ARGS}\n"

        func = func.replace('\\', '/')

        commands += DEBUG_TEXT(DebugTip.Call, {"text": f"{func}", "color": "dark_purple"})
        commands += f"function {func}\n"
        commands += del_args

        # 如果根命名空间不一样，需要去额外处理返回值
        if ns != namespace:
            commands += (
                f"scoreboard players operation "
                f"{namespace}{ResultExt} {SB_TEMP} "
                f"= "
                f"{ns}{ResultExt} {SB_TEMP}\n"
            )

            commands += DEBUG_OBJECTIVE(
                DebugTip.Result,
                objective=SB_TEMP, name=f"{namespace}{ResultExt}",
                from_objective=SB_TEMP, from_name=f"{ns}{ResultExt}"
            )
            commands += DEBUG_OBJECTIVE(DebugTip.Reset, objective=SB_TEMP, name=f"{ns}{ResultExt}")

            commands += f"scoreboard players reset {ns}{ResultExt} {SB_TEMP}\n"

        return commands

    err_msg = json.dumps({"text": f"无法解析的节点: {namespace}.{type(node).__name__}", "color": "red"})
    return f"tellraw @a {err_msg}\n"


def main():
    global SAVE_PATH
    global READ_PATH
    global BASE_NAMESPACE

    SAVE_PATH = "./.output/"
    SAVE_PATH = r"D:\game\Minecraft\.minecraft\versions\1.16.5投影\saves\函数\datapacks\函数测试\data\source_code\functions"
    READ_PATH = "./tests/import_add"

    BASE_NAMESPACE = "source_code:"
    file_name = "caller"

    with open(os.path.join(READ_PATH, f"{file_name}.py"), mode='r', encoding="utf-8") as _:
        tree = ast.parse(_.read())

    print(ast.dump(tree, indent=4))
    print(generate_code(tree, join_base_ns(file_name)))
    print(f"[DEBUG] {func_args=}")
    print()
    print(f"[DEBUG] {import_module_map=}")


if __name__ == "__main__":
    main()
