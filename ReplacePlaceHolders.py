# -*- coding: utf-8 -*-
# cython: language_level = 3
"""
替换源码中的占位符
"""

import os
import re

from Constant import PLACEHOLDER_MAP


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
    matches = re.findall(r'\$\{([^{}$]+)}', code)

    for match in matches:
        key = match.strip()
        if key in data:
            code = code.replace(f'${{{key}}}', data[key])
        else:
            raise KeyError(f'Key {key} not found in data')

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


def get_files(base_path: str, root_dir: str) -> str:
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


def main():
    file_extensions = [".mcfunction", ".mcmeta"]
    save_path = r".\.output"
    # save_path = r"D:\game\Minecraft\.minecraft\versions\1.16.5投影\saves\函数\datapacks""
    read_path = r".\Python"

    for file_path, relative_path, file in get_files(r"", read_path):

        print(file_path, relative_path, file)
        print("-" * 50)
        print("Reading", file_path)

        with open(file_path, encoding="UTF-8", mode='r') as f:
            code = f.read()

        ext = os.path.splitext(file)[1]
        if ext in file_extensions:
            print("Processing", file_path)
            new_code = replace_placeholders(code, PLACEHOLDER_MAP)
        else:
            print("No Processing", file_path)
            new_code = code

        print("Saving", file_path, "To", os.path.join(save_path, relative_path, file))

        os.makedirs(os.path.join(save_path, relative_path), exist_ok=True)
        with open(os.path.join(save_path, relative_path, file), encoding="UTF-8", mode='w') as f:
            f.write(new_code)

        print("Done.", file_path)
        print("-" * 50)
        print()
        print()


if __name__ == "__main__":
    main()

__all__ = ("main",)
