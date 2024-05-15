from template.MinecraftSupport.builtin import tprint


def main():
    tprint("生成出的文件目录不应该会在.if文件夹里面嵌套.if文件夹")


value = True

if value:
    if value:
        main()
