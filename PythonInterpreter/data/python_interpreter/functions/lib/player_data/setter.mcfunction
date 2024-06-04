$data modify storage {{DS.EntityData}} player_data.$(player_uuid).$(path) set from storage {{DS.Temp}} player_data.value
data remove storage {{DS.Temp}} player_data.value
