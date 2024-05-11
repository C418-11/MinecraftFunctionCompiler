from template.MinecraftSupport.EnvBuild import build_scoreboard
from template.MinecraftSupport.builtin import tprint
from template.MinecraftSupport.scoreboard import get_score

build_scoreboard(
    "num",
    {"value": 5}
)


def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)


# 测试
num = get_score("value", "num")
ret = factorial(num)
tprint(num, "的阶乘是: ", ret, sep='')
