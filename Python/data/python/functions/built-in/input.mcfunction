function python:built-in/print
tellraw @a {"text":"", "extra":[${RAWJSON:Prefix}, {"text": "${BuiltIn:input.TIP}"}, ${RAWJSON.BuiltIn:input}], "color": "gray"}
