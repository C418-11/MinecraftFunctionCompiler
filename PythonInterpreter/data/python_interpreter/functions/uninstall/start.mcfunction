data remove storage {{DS.Flags}} Inited
data remove storage {{DS.EntityData}} player_data
data remove storage {{DS.Temp}} jinja2

scoreboard objectives remove {{SB.State}}
scoreboard objectives remove {{SB.Temp}}

function python_interpreter:config/clear
function python_interpreter:constant/clear

tellraw @a {"text": "", "color": "gold", "extra": [{{RAWJSON.Prefix}}, " ", {{TextC.translate("uninstall.finish","已清空解释器相关数据")}}], {{RAWJSON.HoverEvent.Author}}}
