from template.MinecraftSupport.builtin import tprint
from template.MinecraftSupport.builtin import tbreakpoint


def main():
    tbreakpoint()
    tprint("Hello, World!")
    return
    # noinspection PyUnreachableCode
    tprint("Back from return")


main()
