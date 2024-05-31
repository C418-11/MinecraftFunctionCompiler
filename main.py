# -*- coding: utf-8 -*-
from Compiler import Compiler
from Configuration import CompileConfiguration
from Environment import Environment


def main():
    save_path = "./.output/"
    # save_path = r"D:\game\Minecraft\.minecraft\versions\1.16.5投影\saves\函数\datapacks\函数测试\data\source_code\functions"

    read_path = "./tests"
    file_name = "var_add"

    compile_configuration = CompileConfiguration("source_code:", read_path, save_path, debug_mode=True)
    environment = Environment(compile_configuration)

    compiler = Compiler(environment)
    compiler.compile(file_name)


if __name__ == "__main__":
    main()
