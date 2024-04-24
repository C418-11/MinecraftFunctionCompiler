from template.MinecraftSupport.EnvBuild import build_scoreboard
from template.MinecraftSupport.builtin import tprint
from template.MinecraftSupport.scoreboard import get_score
from template.MinecraftSupport.scoreboard import write_score

build_scoreboard("points", {"player": 100})

x = get_score("player", "points")
tprint("Value is", x)

x_multiplied = x * 2
write_score("x", "points", x_multiplied)
y = get_score("x", "points")
tprint("(player * 2) =", y)

tprint('Comparing values...')

if x == 100:
    tprint("==100")

if x != 100:
    tprint("!=100")

# if x > 100:
#     tprint(">100")
#
# if x < 100:
#     tprint("<100")
#
#
# if x >= 100:
#     tprint(">=100")
#
# if x <= 100:
#     tprint("<=100")
