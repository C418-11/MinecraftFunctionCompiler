{% from "call_lib.jinja2" import void, call_pyilib with context %}

execute store result score **join_str.length {{SB.Temp}} run data get storage {{DS.Temp}} join_str.obj_to_join
execute if score **join_str.length {{SB.Temp}} < 1 {{SB.Constant}} run return run {{void}}

data modify storage {{DS.Temp}} join_str.join_args.last set from storage {{DS.Temp}} join_str.result
data modify storage {{DS.Temp}} join_str.join_args.new set from storage {{DS.Temp}} join_str.obj_to_join[0]
data remove storage {{DS.Temp}} join_str.obj_to_join[0]

{% set call_join = call_pyilib("base_join_str with storage "+DS.Temp+" join_str.join_args") %}
{{ call_join }}

data modify storage {{DS.Temp}} join_str.join_args.last set from storage {{DS.Temp}} join_str.result
$data modify storage {{DS.Temp}} join_str.join_args.new set value "$(split)"

execute if score **join_str.length {{SB.Temp}} > 1 {{SB.Constant}} run {{ call_join }}

${{ call_pyilib("_join_str {split: \"$(split)\"}") }}
