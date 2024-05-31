scoreboard objectives add {{SB.Config}} dummy
execute store result score StepPreCall {{SB.Config}} run data get storage {{DS.Config}} StepPreCall 1
