from template.MinecraftSupport.builtin import tbreakpoint
from template.MinecraftSupport.builtin import tprint


def main():
    tbreakpoint()
    tprint("Hello, World!")
    return
    # noinspection PyUnreachableCode
    tprint("Back from return")


main()
