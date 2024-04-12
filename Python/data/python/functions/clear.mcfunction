tellraw @a { "text": "" , "extra": [ ${RAWJSON:Prefix}, { "text": " ${CHAT:ClearingData}" }], "color": "gold", ${RAWJSON.HoverEvent:Author} }
scoreboard objectives remove ${SB:Args}
scoreboard objectives remove ${SB:Temp}
scoreboard objectives remove ${SB:Flags}
scoreboard objectives remove ${SB:Input}
scoreboard objectives remove ${SB:Vars}
tellraw @a { "text": "" , "extra": [ ${RAWJSON:Prefix}, { "text": " ${CHAT:DataClearingComplete}" }], "color": "gold", ${RAWJSON.HoverEvent:Author} }