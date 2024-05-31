tellraw @a {"text": "", "color": "gold", "extra": [{{RAWJSON.Prefix}}, " ", {"translate": "python_interpreter.init.start", "fallback": "正在初始化解释器"}], {{RAWJSON.HoverEvent.Author}}}

scoreboard objectives add {{SB.State}} dummy
function python_interpreter:constant/init
function python_interpreter:config/init

data modify storage {{DS.Flags}} Inited set value true
tellraw @a {"text": "", "color": "gold", "extra": [{{RAWJSON.Prefix}}, " ", {"translate": "python_interpreter.init.finish", "fallback": "解释器初始化结束"}], {{RAWJSON.HoverEvent.Author}}}
