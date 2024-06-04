{% from "call_lib.jinja2" import call_pyilib with context %}

data modify storage {{DS.Temp}} join_str.obj_to_join set value []
$data modify storage {{DS.Temp}} join_str.obj_to_join append string entity $(selector) UUID[0]
$data modify storage {{DS.Temp}} join_str.obj_to_join append string entity $(selector) UUID[1]
$data modify storage {{DS.Temp}} join_str.obj_to_join append string entity $(selector) UUID[2]
$data modify storage {{DS.Temp}} join_str.obj_to_join append string entity $(selector) UUID[3]


{{call_pyilib("join_str {split: \"_\"}")}}
data modify storage {{DS.Temp}} selector2uuid.result set from storage {{DS.Temp}} join_str.result
data remove storage {{DS.Temp}} join_str
