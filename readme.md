# Running it
You must have a terminal in the root folder (same as this file).
Then have a python virtual environment. Run the following commands:
* `python -m venv venv`
* `.\venv\Scripts\activate`
* `pip install -r requirements.txt`

## Client
To run the client use the following command:
`python -m client.main`

### Settings
Ip and port settings for the server can be changed in _client/settings.json_.

## Server
To run the server use the following command:
`python -m server.main`
  
  

# Programming your robot
The entrypoint for programming your own robot is the _robots_ folder in the _client_ folder.

To create a new robot, create a new python file (the name of the file will be the name of the robot in the UI). The file must define a class using the following template:  
```python
class MyRobot(RobotInterface):

    def build_robot(self, builder: RobotBuilder) -> None:
        pass
    
    def apply_stats(self, stats: RobotStats) -> None:
        pass

    def do_ability(self, index: int, command_list: list[WeaponCommand], info: RobotInfo) -> None:
        pass
```

There is four parts to customizing your robot:
* [Parts](#parts)
* [Stats](#stats)
* [Abilities](#abilities)
* [GUI](#gui)

The parts determines some base stats and what is available to use in the abilities.  
The stats is extra customizable stat points put on top of the base stats.  
The abilities determines what happens when each of the six ability keys are pressed.

All the stats and ability cost and cooldown can be view in the UI after starting the client.

## Parts
The construction and what parts the robot consists of is determined in the __build_robot__ function.

### Hull
The hull of the robot determines the base stat for the robot.  
The hull can be set like this: `builder.hull = RobotHullType.Standard`  
  
The different hulls and their stats can be found in __common\robot_hull.py__.  
The different stats are explained in the stats section.

### Weapons
The weapons added to the robot, is those who can be fired using the [Abilities](#abilities).
  
A weapon can be added like this:  
`builder.weapons.append(WeaponConfig("id", 0.5, -0.5, 315, WeaponType.STANDARD))`

A weapon config takes the following parameters:
|Name             |Description                 |required    |
|-----------------|----------------------------|---------|
|id|The id of the weapon, used in the ability function to refer to the weapon. |True|
|x|The horizontal placement of the weapon within the bounding box. Range: 1 to -1.  |True|
|y|The vertical placement of the weapon within the bounding box. Range: 1 to -1. |True|
|angle|The direction the weapon is facing firing. NOTE: A player cannot hit itself. |True|
|type|The weapon type determining the weapons stats. The specific stats can be viewed in the _common/weapon.py_ file. Default: STANDARD |False|

OBS. the x and x will be limited to stay within the player body. 

## Stats
The following table explains each stat, that is currently available:

|Name             |Description                 |Scale    |Unit     |
|-----------------|----------------------------|---------|---------|
|max_health|How much max health the robot has. |5||
|max_energy|How much max energy the robot has. |5||
|energy_regen|How fast the energy regenerates per second. |0.01|energy/tick|
|move_speed|How fast the robot moves. |0.5|px/tick|
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
|move_speed|15 |1.5|
|turn_speed|10 |1|
|size|10 |1|


### Scaling
The formula for the final stat value for the robot is:  
`base + custom * scale`

__Example:__  
|Name|Base Stat|Custom Stat|Final Value|
|-|-|-|-|
|max_health|100|2|110|
|max_energy|100|4|120|
|energy_regen|0.01|0.5|0.015|
|move_speed|5|1.5|5.75|
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

The function gets a robot info as input, this class has the following properties:  
|Name             |Description                 |
|-----------------|----------------------------|
|hp|The current hp of the robot. |
|max_hp|The max hp the robot can have. |
|energy|The current energy of the robot. |
|max_energy|The max energy the robot can have. |
|cooldowns|A dictionary, where the keys are the weapon ids and the values is the cooldown for ach weapon in seconds. (float) |

### Firing a weapon
To fire a weapon, a weapon command can be added like this:
`command_list.append(WeaponCommand("id"))`  
The id must match a weapon configured in the _build_robot_ function.

The weapon command has the following parameters:
|Name             |Description                 |required    |
|-----------------|----------------------------|---------|
|id|An id of a weapon configred in the _build_robot_ function. |True|
|delay|How long after the ability is activated that the bullet should be fired.  |False|

### Energy Cost
The energy cost of a total ability is the sum of all weapon commands that is produced by calling the function with the given key index.  
  
The cost of a single weapon command is calculated like this:
`cost_of_command = weapon_base_cost * (weapon_consective_fire_increase ^ number_of_times_fired-1)`  
  
OBS. The cost of an ability is calculated differently in the stats UI and during a game.  
In the stats screen the cost is simply calculated for the initial state.  
During a game the cost of the ability is always calculated when the ability is activated.

__Example__  
The robot is configured like this:  
```python
class MyRobot(RobotInterface):

    def build_robot(self, builder: RobotBuilder) -> None:
        builder.weapons.append(WeaponConfig("w1", 1, 0, 0, WeaponType.STANDARD))
    
    def apply_stats(self, stats: RobotStats) -> None:
        pass

    def do_ability(self, index: int, command_list: list[WeaponCommand]) -> None:
        if index == 1:
            command_list.append(WeaponCommand("w1"))
            command_list.append(WeaponCommand("w1", delay=timedelta(milliseconds=100)))
            command_list.append(WeaponCommand("w1", delay=timedelta(milliseconds=200)))
```

For this example the standard weapon type has the following stats:  
- weapon_base_cost = 5  
- weapon_consective_fire_increase = 1.1 (10% increase per extra shot)  

Then the total cost for the q(1) ability is:  
`5 * (1.1 ^ 2) = 6.05`

### Cooldown
Before an ability can be activated all of the weapons must have cooled down. Meaning the max cooldown time for an ability is corresponding to the cooldown of the weapon with the longest cooldown time.

## GUI
Each robot cna render some custom gui. The rendered GUI is only rendered for its own player.

Custom GUI code is defined in the __draw_gui__ function.

It is also possible to get a custom state from the robot, to use in rendering the custom gui.

The variables, which is needed in the rendering function should be return in a dictionary in the __get_state__ function. The same object returned by the _get_state_ function is injected into the _draw_gui_ function.

### Example  
```python
def get_state(self) -> dict:
    return {
        "test": 50
    }
    
def draw_gui(self, screen: pygame.Surface, state: dict) -> None:
    pygame.draw.rect(screen, (0, 255, 0), (state["test"],0,100,100))
```