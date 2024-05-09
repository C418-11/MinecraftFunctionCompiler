tellraw @a { "text": "" , "extra": [ ${RAWJSON:Prefix}, { "text": " ${CHAT:Initializing}" }], "color": "gold", ${RAWJSON.HoverEvent:Author} }
scoreboard objectives add ${SB:Args} dummy
scoreboard objectives add ${SB:Temp} dummy
scoreboard objectives add ${SB:Flags} dummy
scoreboard objectives add ${SB:Vars} dummy
scoreboard players set True ${SB:Flags} 1
scoreboard players set False ${SB:Flags} 0
scoreboard players set Neg ${SB:Flags} -1
scoreboard players set DEBUG ${SB:Flags} 0
scoreboard objectives add ${SB:Input} trigger
scoreboard objectives add ${SB:FuncResult} dummy
data modify storage ${DS:Root} ${DS:LocalVars} set value []
data modify storage ${DS:Root} ${DS:LocalTemp} set value []
tellraw @a { "text": "" , "extra": [ ${RAWJSON:Prefix}, { "text": " ${CHAT:InitializationComplete}" }], "color": "gold", ${RAWJSON.HoverEvent:Author} }