data remove storage python_interpreter:flags Inited
scoreboard objectives remove {{SB.State}}
function python_interpreter:config/clear
function python_interpreter:constant/clear

tellraw @a {"text": "", "color": "gold", "extra": [{{RAWJSON.Prefix}}, " ", {"translate": "python_interpreter.uninstall.finish", "fallback": "已清空解释器相关数据"}], {{RAWJSON.HoverEvent.Author}}}
