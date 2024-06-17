# -*- coding: utf-8 -*-
# cython: language_level = 3
"""
替换源码中的占位符
"""
import json
import os
import sys
from typing import Generator

from Configuration import GlobalConfiguration
from jinja2 import Environment, Undefined
from jinja2 import FileSystemLoader


def _has_value(value) -> bool:
    is_none = value is None
    is_undefined = isinstance(value, Undefined)
    return not (is_none or is_undefined)


translate_keys = {}


def _text_component_style(
        data: dict,
        *,
        color: str = None,
        font: str = None,
        bold: str = None,
        italic: bool = None,
        underlined: bool = None,
        strikethrough: bool = None,
        obfuscated: bool = None,
        insertion: str = None,
        click_event: str = None,
        hover_event: str = None,
):
    if _has_value(color):
        # 检查合法性
        if "#" in color:
            if len(color) != 7:
                raise ValueError(f"color \'{color}\' is invalid")
            try:
                int(color[1:], 16)
            except ValueError:
                raise ValueError(f"color \'{color}\' is invalid")

        default_colors = [
            "black", "dark_blue", "dark_green", "dark_aqua", "dark_red",
            "dark_purple", "gold", "gray", "dark_gray", "blue", "green",
            "aqua", "red", "light_purple", "yellow", "white",
        ]

        if color not in default_colors:
            raise ValueError(f"color \'{color}\' is invalid")

        data["color"] = color

    if _has_value(font):
        data["font"] = font

    if _has_value(bold):
        data["bold"] = bold

    if _has_value(italic):
        data["italic"] = italic

    if _has_value(underlined):
        data["underlined"] = underlined

    if _has_value(strikethrough):
        data["strikethrough"] = strikethrough

    if _has_value(obfuscated):
        data["obfuscated"] = obfuscated

    if _has_value(insertion):
        data["insertion"] = insertion

    if _has_value(click_event):
        data["clickEvent"] = json.loads(click_event)

    if _has_value(hover_event):
        data["hoverEvent"] = json.loads(hover_event)

    return data


def _translate(
        translate: str,
        fallback: str = None,
        with_txt: str | list = None,
        **kwargs,
):
    if not _has_value(translate):
        print(f"\"{translate}\"")
        raise ValueError("translate is required")

    translate = f"python_interpreter.{translate}"

    if not _has_value(fallback):
        fallback = "§4§lTranslation missing: §e§o{}".format(translate)

    if translate in translate_keys and translate_keys[translate] != fallback:
        old_fallback = translate_keys[translate]
        raise ValueError(f"translate \'{translate}\' has different fallback: {old_fallback} -> {fallback}")
    elif translate not in translate_keys:
        translate_keys[translate] = fallback

    data = {"type": "translatable", "translate": translate, "fallback": fallback}

    if _has_value(with_txt):
        if type(with_txt) is str:
            with_ls: list = json.loads(with_txt)
            if type(with_ls) is not list:
                raise ValueError("with_txt is invalid")
        elif type(with_txt) is list:
            with_ls = []
            for t in with_txt:
                with_ls.append(json.loads(t))
        else:
            raise ValueError("with_txt is invalid")

        data["with"] = with_ls

    data = _text_component_style(data, **kwargs)

    return json.dumps(data, ensure_ascii=False)


def _nbt(
        source: str,
        nbt: str = "",
        *,
        block: str = None,
        entity: str = None,
        storage: str = None,
        interpret: bool = None,
        **kwargs,
):
    data = {"type": "nbt", "nbt": nbt, "source": source}

    if not _has_value(source):
        raise ValueError("source is required")

    if source not in {"storage", "entity", "block"}:
        raise ValueError(f"source \'{source}\' is invalid")

    if source == "block":
        if not _has_value(block):
            raise ValueError("block is required when source is block")
        data["block"] = block

    if source == "entity":
        if not _has_value(entity):
            raise ValueError("entity is required when source is entity")
        data["entity"] = entity

    if source == "storage":
        if not _has_value(storage):
            raise ValueError("storage is required when source is storage")
        data["storage"] = storage

    if _has_value(interpret):
        data["interpret"] = interpret

    data = _text_component_style(data, **kwargs)

    return json.dumps(data, ensure_ascii=False)


def _score(
        name: str,
        objective: str,
        **kwargs,
):
    data = {"type": "score", "score": {"name": name, "objective": objective}}

    data = _text_component_style(data, **kwargs)

    return json.dumps(data)


def _run_command(command: str):
    if not _has_value(command):
        raise ValueError("command is required")

    if not command.startswith("/"):
        command = f"/{command}"
    return json.dumps({"action": "run_command", "value": command})


def _suggest_command(command: str):
    if not _has_value(command):
        raise ValueError("command is required")

    return json.dumps({"action": "suggest_command", "value": command})


def _show_text(text: str | list):
    if not _has_value(text):
        raise ValueError("text is required")

    if type(text) is str:
        raw_json = json.loads(text)
    elif type(text) is list:
        raw_json = []
        for t in text:
            raw_json.append(json.loads(t))
    else:
        raise ValueError("text must be str or list")
    return json.dumps({"action": "show_text", "contents": raw_json})


help_funcs = {
    "TextC": {
        "translate": _translate,
        "nbt": _nbt,
        "score": _score,
        "clickEvent": {
            "run_command": _run_command,
            "suggest_command": _suggest_command,
        },
        "hoverEvent": {
            "show_text": _show_text,
        },
    }
}


env = Environment(
    loader=FileSystemLoader("PythonInterpreter/jinja2"),
    trim_blocks=True,
)


def replace_placeholders(code: str, data: dict) -> str:
    """
    替换代码中的占位符

    :param code: 源码
    :type code: str
    :param data: 数据
    :type data: dict
    :return: 替换后的代码
    :rtype: str
    """
    template = env.from_string(code)

    # 渲染模板
    code = template.render(data)

    return code


def get_relative_path(a: str, b: str) -> str:
    """
    计算路径A相对于路径B的相对路径

    :param a: 路径A
    :type a: str
    :param b: 路径B
    :type b: str
    :return: 相对路径
    :rtype: str
    """
    # 获取路径A和B的绝对路径
    a = os.path.abspath(a)
    b = os.path.abspath(b)

    # 获取路径A和B的公共路径
    common_path = os.path.commonpath([a, b])

    # 计算路径A相对于公共路径的相对路径
    relative_a = os.path.relpath(a, common_path)

    # 计算路径B相对于公共路径的相对路径
    relative_b = os.path.relpath(b, common_path)

    # 如果路径A比路径B长,则返回路径A的相对路径
    if len(relative_a) > len(relative_b):
        return relative_a

    # 如果路径A和路径B一样长,则返回路径A的相对路径
    elif len(relative_a) == len(relative_b):
        return relative_a

    # 如果路径B比路径A长,则返回路径B的相对路径
    else:
        return relative_b


def get_files(base_path: str, root_dir: str) -> Generator[tuple[str, str, str], None, None]:
    """
    获取指定目录下的所有文件路径的生成器

    :param base_path: 基础路径
    :type base_path: str
    :param root_dir: 根目录
    :type root_dir: str
    :return: 文件路径
    :rtype: str
    """
    for root, dirs, files in os.walk(os.path.join(base_path, root_dir)):
        for file in files:
            relative_path = get_relative_path(os.path.join(base_path, root_dir), root)
            relative_path = os.path.normpath(os.path.join(root_dir, relative_path))

            yield os.path.normpath(os.path.join(root, file)), relative_path, file


def _dump_translate_keys(file_obj):
    import json
    json.dump(translate_keys, file_obj, indent=4, ensure_ascii=False, sort_keys=True)


def main():
    file_extensions = [".mcfunction", ".mcmeta"]
    # save_path = r"D:\game\Minecraft\.minecraft\versions\1.20.6-MCFC\saves\函数\datapacks"
    save_path = r".\.output"
    read_path = r".\PythonInterpreter"

    placeholder_map = GlobalConfiguration().__placeholder__()
    placeholder_map.update(help_funcs)

    for file_path, relative_path, file in get_files(r"", read_path):

        print(file_path, relative_path, file)
        print("-" * 50)
        print("Reading", file_path)

        with open(file_path, encoding="UTF-8", mode='r') as f:
            code: str = f.read()

        save_file: bool = True

        if file.lower().endswith(".jinja2"):
            real_ext = os.path.splitext(file[:-len(".jinja2")])[1]
            if real_ext in file_extensions:
                print("Renaming", file, "To", file[:-len(".jinja2")])
                file = file[:-len(".jinja2")]
            elif real_ext == '':
                print("Plain template files have been ignored")
                save_file = False
            else:
                print("No operation is performed because the file suffix is unknown", real_ext)

        ext = os.path.splitext(file)[1].lower()
        new_code: str = ''

        if ext in file_extensions:
            print("Processing", file_path)
            new_code = replace_placeholders(code, placeholder_map)
        elif ext == ".disable":
            print("Disabled", file_path)
            save_file = False
        else:
            print("No Processing", file_path)
            new_code = code

        if save_file:
            print("Saving", file_path, "To", os.path.join(save_path, relative_path, file))

            os.makedirs(os.path.join(save_path, relative_path), exist_ok=True)
            with open(os.path.join(save_path, relative_path, file), encoding="UTF-8", mode='w') as f:
                f.write(new_code)
        else:
            print("Skipping", file_path)

        print("Done.", file_path)
        print("-" * 50)
        print()
        print()

    print()
    _dump_translate_keys(sys.stdout)


if __name__ == "__main__":
    main()

__all__ = ("main",)
