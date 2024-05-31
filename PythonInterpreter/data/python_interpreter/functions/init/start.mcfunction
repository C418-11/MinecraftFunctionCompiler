execute unless data storage {{DS.Flags}} Inited run return run function python_interpreter:init/init
tellraw @a {"text": "", "color": "gold", "extra": [{{RAWJSON.Prefix}}, " ", {"translate": "python_interpreter.init.inited", "fallback": "已阻止重复初始化"}], {{RAWJSON.HoverEvent.Author}}}
return fail
