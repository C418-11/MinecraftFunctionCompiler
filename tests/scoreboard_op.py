from template.MinecraftSupport.builtin import tprint
from template.MinecraftSupport.scoreboard import get_score
from template.MinecraftSupport.EnvBuild import build_scoreboard


build_scoreboard("points", {"player": 100})


x = get_score("player", "points")
tprint("Value is", x)


if x == 100:
    tprint("==100")

if get_score("player", "points") != 100:
    tprint("!=100")


# if get_score("player", "points") > 100:
#     tprint(">100")
#
# if get_score("player", "points") < 100:
#     tprint("<100")
#
#
# if get_score("player", "points") >= 100:
#     tprint(">=100")
#
# if get_score("player", "points") <= 100:
#     tprint("<=100")
