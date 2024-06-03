{% from "call_lib.jinja2" import call_pyilib with context %}

data modify storage {{DS.Temp}} join_str.result set value ""
${{ call_pyilib("_join_str {split: \"$(split)\"}") }}
data remove storage {{DS.Temp}} join_str.obj_to_join
data remove storage {{DS.Temp}} join_str.join_args
