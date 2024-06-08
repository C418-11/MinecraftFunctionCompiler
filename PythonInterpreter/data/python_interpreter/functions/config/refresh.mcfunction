scoreboard objectives add {{SB.Config}} dummy
execute store result score StepPerCall {{SB.Config}} run data get storage {{DS.Config}} StepPerCall 1

tellraw @a {"text": "", "color": "gold", "extra": [{{RAWJSON.Prefix}}, " ", {{TextC.translate("config.refresh","正在刷新解释器配置")}}]}
