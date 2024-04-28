from template.MinecraftSupport.EnvBuild import build_scoreboard
from template.MinecraftSupport.bossbar import add
from template.MinecraftSupport.bossbar import remove
from template.MinecraftSupport.bossbar import set_max
from template.MinecraftSupport.bossbar import set_name
from template.MinecraftSupport.bossbar import set_players
from template.MinecraftSupport.bossbar import set_value
from template.MinecraftSupport.scoreboard import get_score


build_scoreboard(
    "bossbar",
    {
        "value": 50,
        "max": 100,
        "remove": False
    }
)


if get_score("remove", "bossbar"):
    remove("test")
add("test",  {"text": "Test", "color": "gold"})
set_players("test", "@a")

now_value = get_score("value", "bossbar")
set_value("test", now_value)
now_max = get_score("max", "bossbar")
set_max("test", now_max)

if now_value > now_max:
    set_name("test", {"text": "Err", "color": "red"})
