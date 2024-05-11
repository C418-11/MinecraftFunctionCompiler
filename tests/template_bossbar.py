from template.MinecraftSupport import bossbar
from template.MinecraftSupport.EnvBuild import build_scoreboard
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
    bossbar.remove("test")
bossbar.add("test", {"text": "Test", "color": "gold"})
bossbar.set_players("test", "@a")

now_value = get_score("value", "bossbar")
bossbar.set_value("test", now_value)
now_max = get_score("max", "bossbar")
bossbar.set_max("test", now_max)

if now_value > now_max:
    bossbar.set_name("test", {"text": "Err", "color": "red"})
