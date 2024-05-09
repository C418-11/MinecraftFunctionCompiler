tellraw @a { "text": "" , "extra": [ ${RAWJSON:Prefix}, { "text": " ${CHAT:ClearingData}" }], "color": "gold", ${RAWJSON.HoverEvent:Author} }
scoreboard objectives remove ${SB:Args}
scoreboard objectives remove ${SB:Temp}
scoreboard objectives remove ${SB:Flags}
scoreboard objectives remove ${SB:Input}
scoreboard objectives remove ${SB:Vars}
scoreboard objectives remove ${SB:FuncResult}
data remove storage ${DS:Root} ${DS:Temp}
data remove storage ${DS:Root} ${DS:LocalVars}
data remove storage ${DS:Root} ${DS:LocalTemp}
tellraw @a { "text": "" , "extra": [ ${RAWJSON:Prefix}, { "text": " ${CHAT:DataClearingComplete}" }], "color": "gold", ${RAWJSON.HoverEvent:Author} }