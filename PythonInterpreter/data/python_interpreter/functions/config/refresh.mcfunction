scoreboard objectives add {{SB.Config}} dummy
execute store result score StepPreCall {{SB.Config}} run data get storage {{DS.Config}} StepPreCall 1

tellraw @a {"text": "", "color": "gold", "extra": [{{RAWJSON.Prefix}}, " ", {{TextC.translate("config.refresh","正在刷新解释器配置")}}]}
