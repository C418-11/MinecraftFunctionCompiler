from template.MinecraftSupport.builtin import tprint
from template.MinecraftSupport.scoreboard import get_score
from template.MinecraftSupport.EnvBuild import build_scoreboard


build_scoreboard(
    "num",
    {"value": 5}
)


def factorial(n):
    if n == 0:
        return 1
    else:
        # 不写在一行是因为当前底层实现方式BinOp嵌套会覆盖值
        result = factorial(n - 1)
        return n * result


# 测试
num = get_score("value", "num")
ret = factorial(num)
tprint(num, "的阶乘是: ", ret, sep='')
