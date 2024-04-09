tellraw @a { "text": "" , "extra": [ ${RAWJSON:Prefix}, { "text": " ${CHAT:ClearingData}" }], "color": "gold", ${RAWJSON.HoverEvent.Author} }
scoreboard objectives remove ${SB:Args}
scoreboard objectives remove ${SB:Temp}
scoreboard objectives remove ${SB:Flags}
tellraw @a { "text": "" , "extra": [ ${RAWJSON:Prefix}, { "text": " ${CHAT:DataClearingComplete}" }], "color": "gold", ${RAWJSON.HoverEvent.Author} }