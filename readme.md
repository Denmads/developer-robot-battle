# Running it
You must have a terminal in the root folder (same as this file).
Then have a python virtual environment. Run the following commands:
* `python -m venv venv`
* `.\venv\Scripts\activate`
* `pip install -r requirements.txt`

## Client
To run the client use the following command:
`python -m client.main`

## Server
To run the server use the following command:
`python -m server.main`
  
  

# Programming your robot
The entrypoint for programming your own robot is the __my_robot.py__ in the _client_ folder.

There is three parts to customizing your robot:
* Parts
* Stats
* Abilities

The parts determines some base stats and what is available to use in the abilities.  
The stats is extra customizable stat points put on top of the base stats.  
The abilities determines what happens when each of the six ability keys are pressed.

## Parts
The construction and what parts the robot consists of is determined in the __build_robot__ function.

### Hull
The hull of the robot determines the base stat for the robot.  
The hull can be set like this: `builder.hull = RobotHullType.Standard`  
  
The different hulls and their stats can be found in __common\robot_hull.py__.  
The different stats are explained in the stats section.


## Stats
The following table explains each stat, that is currently available:

|Name             |Description                 |Scale    |Unit     |
|-----------------|----------------------------|---------|---------|
|max_health|How much max health the robot has. |5||
|max_energy|How much max energy the robot has. |5||
|energy_regen|How fast the energy regenerates per second. |0.01|energy/tick|
|speed|How fast the robot moves. |0.5|px/tick|
|turn_speed|How fast the robot turns. |0.02|rad/tick|
|size|How large the robot is. |-1|px|

  
Stats are set in the __apply_stats__ function.  
Stats are set like this: `stats.speed = 10`
  
The stats set are always normalized to total up to 10.  
__Example:__  
|Name|Set Stat|Normalized Stat|
|-|-|-|
|max_health|20|2|
|max_energy|40|4|
|energy_regen|5|0.5|
|speed|15 |1.5|
|turn_speed|10 |1|
|size|10 |1|


### Scaling
The formula for the final stat value for the robot is:  
`base + custom * scale`
  
_Exceptions_  
size: `base - custom`

__Example:__  
|Name|Base Stat|Custom Stat|Final Value|
|-|-|-|-|
|max_health|100|2|110|
|max_energy|100|4|120|
|energy_regen|0.01|0.5|0.015|
|speed|5|1.5|5.75|
|turn_speed|0.01|1|0.03|
|size|25|1|24|


## Abilities
There are six ability keys:
|Index|Key|
|-|-|
|1|q|
|2|w|
|3|e|
|4|a|
|5|s|
|6|d|

Logic for abilities are implmented in the __do_ability__ function.