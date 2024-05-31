$function python_interpreter:step/step_once {"pid": $(pid)}

$execute if data storage {{DS.State}} ExitStep_$(pid) run return run function python_interpreter:void

$execute if score StepPreCall {{SB.Config}} < 0 {{SB.Constant}} run scoreboard players set StepToRun_$(pid) {{SB.State}} 2

$scoreboard players remove StepToRun_$(pid) {{SB.State}} 1

$execute if score StepToRun_$(pid) {{SB.State}} < 1 {{SB.Constant}} run return run function python_interpreter:step/exit_step {"pid": $(pid)}

$function python_interpreter:step/step {"pid": $(pid)}
