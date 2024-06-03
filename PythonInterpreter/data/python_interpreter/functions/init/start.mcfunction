execute unless data storage {{DS.Flags}} Inited run return run function python_interpreter:init/init
tellraw @a {"text": "", "color": "gold", "extra": [{{RAWJSON.Prefix}}, " ", {{TextC.translate("init.inited","已阻止重复初始化")}}], {{RAWJSON.HoverEvent.Author}}}
return fail
