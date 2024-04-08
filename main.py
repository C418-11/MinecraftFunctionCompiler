import ast
import json
import os
from itertools import zip_longest

with open("add.py", mode='r') as _:
    tree = ast.parse(_.read())


func_args = {
    "python:built-in\\print": ['*', *['*' + str(i) for i in range(1, 10)]]
}

define_args = {}

DECIMAL_PRECISION = 3

SB_ARGS = "Args"
SB_TEMP = "Temp"


def file_path(namespace: str, filename: str):
    return os.path.join(namespace.split(":", 1)[1], filename)


def generate_code(node, namespace: str):
    namespace = os.path.normpath(namespace)
    os.makedirs(file_path(namespace, ''), exist_ok=True)

    if isinstance(node, ast.Module):
        with open(file_path(namespace, "module.mcfunction"), mode='w') as f:
            for statement in node.body:
                c = generate_code(statement, os.path.join(namespace, "module"))
                f.write(c)

        # with open(file_path(namespace, "init.mcfunction"), mode='w') as f:
        #     f.write(f"scoreboard objectives add {SB_ARGS} dummy\n")
        #     f.write(f"scoreboard objectives add {SB_TEMP} dummy\n")
        #
        #     for arg, value in define_args.items():
        #         if type(value) not in {int, float}:
        #             if not (type(value) is str and value.isdigit()):
        #                 raise Exception("无法解析的默认值")
        #             value = int(value)
        #         if type(value) is float:
        #             value = value * (10 ** DECIMAL_PRECISION)
        #
        #         # Minecraft的积分版只能使用整数
        #         f.write(f"scoreboard players set {arg} {SB_ARGS} {value}\n")

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
        func_args[namespace] = args

        for name, default in zip_longest(args[::-1], node.defaults, fillvalue=ast.Constant(value=0)):

            if isinstance(default, ast.Constant):
                default_value = default.value
            else:
                raise Exception("无法解析的默认值")

            define_args[f"{namespace}.{name}"] = default_value
        return ''

    if isinstance(node, ast.Name):
        return f"{node.id}"

    if isinstance(node, ast.Return):
        return generate_code(node.value, namespace)

    if isinstance(node, ast.BinOp):
        left = generate_code(node.left, namespace)
        right = generate_code(node.right, namespace)

        if isinstance(node.op, ast.Add):
            cmd = (
                f"scoreboard players operation {namespace}.*BinOp {SB_TEMP} = {namespace}.{left} {SB_ARGS}\n"
                f"scoreboard players operation {namespace}.*BinOp {SB_TEMP} += {namespace}.{right} {SB_ARGS}\n"
                f"scoreboard players operation {namespace}.?Result {SB_TEMP} = {namespace}.*BinOp {SB_TEMP}\n"
                f"scoreboard players reset {namespace}.*BinOp\n"
            )
            return cmd

        raise Exception(f"无法解析的运算符 {node.op}")

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

        for name, value in zip(this_func_args, node.args):
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
print(define_args)
