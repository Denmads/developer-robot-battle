from datetime import timedelta
import glob
import pygame

from client.core.render_utils import render_text_bottom_left_at, render_text_bottom_right_at, render_text_top_left_at, render_text_top_right_at
from client.core.state_renderer import SharedState, StateRenderer
from common.calculations import calculate_ability_cooldown, calculate_ability_energy_cost
from common.constants import MIN_AXIS_VALUE
from common.robot import Robot, RobotInfo, parse_robot_config_from_string
from common.tcp_messages import PlayerInfoMessage


class ConnectMenuStateRenderer(StateRenderer):
    
    def __init__(self, state: SharedState):
        super().__init__(state)
        
        self.all_robots = glob.glob(self.state.path + "\\robots\\*.py")
        self.current_selected_robot: int = 0
        
        self.controller_up_prev_active: bool = False
        self.controller_down_prev_active: bool = False
        self.controller_up_active: bool = False
        self.controller_down_active: bool = False
        
        self.failed_to_connect: bool = False
        
        if len(self.all_robots) == 0:
            print("No robots to use. Add a robot configuration to 'client/robots'!")
            exit()
            
        self._create_robot()
    
    def _create_robot(self):
        with open(self.all_robots[self.current_selected_robot]) as f:
            config = parse_robot_config_from_string(f.read())
        
        self.state.robot = Robot.create(
            config, 0, 0, 0
        )
    
    def on_event(self, event: pygame.event.Event):
        
        if event.type == pygame.JOYAXISMOTION and event.axis == 1:
            self.controller_up_prev_active = self.controller_up_active
            self.controller_down_prev_active = self.controller_down_active
        
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN) or (event.type == pygame.JOYBUTTONDOWN and event.button == 0):
            try:
                self.state.tcp.connect()
                with open(self.all_robots[self.current_selected_robot]) as f:
                    self.state.tcp.send(PlayerInfoMessage(self.state.player_id, int(self.state.udp_port), f.read()))
            except:
                self.failed_to_connect = True
        elif (event.type == pygame.KEYDOWN and event.key == pygame.K_UP) or (self.controller_up_active and not self.controller_up_prev_active):
            self.current_selected_robot = max(0, self.current_selected_robot - 1)
            self._create_robot()
        elif (event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN) or (self.controller_down_active and not self.controller_down_prev_active):
            self.current_selected_robot = min(len(self.all_robots)-1, self.current_selected_robot + 1)
            self._create_robot()
            
        if event.type == pygame.JOYAXISMOTION and event.axis == 1:
            self.controller_up_active = event.value < -1 * MIN_AXIS_VALUE
            self.controller_down_active = event.value > MIN_AXIS_VALUE
    
    
    
    def render(self, screen: pygame.Surface, delta: timedelta):
        self._render_robot_selector(screen)
        self._render_robot_stats(screen)
        
        render_text_bottom_right_at(screen, f"Press 'Enter'{' / A' if self.state.controller_connected else ''} to connect...", self.state.menu_size[0] - 50, self.state.menu_size[1] - 50, self.state.font_text)
        
        if self.failed_to_connect:
            render_text_bottom_left_at(screen, "Failed to connect to server!!!", 50, self.state.menu_size[1] - 50, self.state.font_text, (255, 155, 155))
        
    def _render_robot_selector(self, screen: pygame.Surface):
        render_text_top_left_at(screen, "Robots:", 50, 50, self.state.font_header)
        
        robot_spacing = self.state.font_text.get_height() + 10
        text_left_margin = 75
        selector_spacing = 10
        selected_color = (255, 193, 7)
        for i, file_path in enumerate(self.all_robots):
            file_name = file_path.split("\\")[-1]
            text = f"{file_name[:-3]}"
            text_y = 75 + i * robot_spacing
            color = selected_color if i == self.current_selected_robot else (255, 255, 255)
            name_w, _ = render_text_top_left_at(screen, text, text_left_margin, text_y, self.state.font_text, color)
            
            if i == self.current_selected_robot:
                w, _ = self.state.font_text.size(">")
                render_text_top_left_at(screen, ">", text_left_margin - selector_spacing - w, text_y, self.state.font_text, color)
                render_text_top_left_at(screen, "<", text_left_margin + name_w + selector_spacing, text_y, self.state.font_text, color)
                
    def _render_robot_stats(self, screen: pygame.Surface):
        min_x = self.state.menu_size[0]
        max_x = 0
        max_y = 0
        
        right_margin = self.state.menu_size[0] - 325
        top_margin = 118
        stat_spacing = self.state.font_text.get_height() + 10
        stats = {
            "Hp": round(self.state.robot.max_hp, 2),
            "Energy": round(self.state.robot.max_energy, 2),
            "Size": round(self.state.robot.size, 2),
            "Energy Regen": round(self.state.robot.energy_regen, 2),
            "Move Speed": round(self.state.robot.move_speed, 2),
            "Turn speed": round(self.state.robot.turn_speed, 2)
        }
        
        stat_texts = [
            f"{stat_name}: {value}"
            for stat_name, value in stats.items()
        ]
        
        for i, stat in enumerate(stat_texts):
            w, h = render_text_top_right_at(screen, stat, right_margin, top_margin + i * stat_spacing, self.state.font_text)
            if right_margin - w < min_x:
                min_x = right_margin - w
            if top_margin + i * stat_spacing + h > max_y:
                max_y = top_margin + i * stat_spacing + h
        
        # ability costs
        ability_stats = {}
        for i, key in enumerate(["q", "w", "e", "a", "s", "d"]):
            commands = []
            self.state.robot.ability_func(i+1, commands, RobotInfo(
                (0, 0),
                0,
                self.state.robot.hp,
                self.state.robot.max_hp,
                self.state.robot.energy,
                self.state.robot.max_energy,
                {
                    w.id: w.cooldown_time_left
                    for w in self.state.robot.weapons.values()
                },
                [(0, 0)],
                []
            ))
            ability_stats[key] = {
                "cost": round(calculate_ability_energy_cost(self.state.robot.weapons, commands), 1),
                "cooldown": round(calculate_ability_cooldown(self.state.robot, commands), 2)
            }
        
        right_ability_margin = right_margin + 100
        for i, (key, ability_stats) in enumerate(ability_stats.items()):
            render_text_top_right_at(screen, f"{key}:", right_ability_margin, top_margin + i * stat_spacing, self.state.font_text)
            render_text_top_right_at(screen, f"{ability_stats['cost']}", right_ability_margin + 50, top_margin + i * stat_spacing, self.state.font_text)
            w, h = render_text_top_right_at(screen, f"{ability_stats['cooldown']}", right_ability_margin + 125, top_margin + i * stat_spacing, self.state.font_text)
            
            if right_ability_margin + 125 + w > max_x:
                max_x = right_ability_margin + 125 + w 
            if top_margin + i * stat_spacing + h > max_y:
                max_y = top_margin + i * stat_spacing + h
        
        padding = 15
        pygame.draw.rect(screen, (255, 255, 255), (min_x - padding, top_margin - padding - 20, (max_x + padding * 2) - min_x, (max_y + padding * 2 + 20) - top_margin), 2)
        render_text_top_right_at(screen, "E", right_ability_margin + 50, top_margin - self.state.font_text.get_height() - 5, self.state.font_text)
        render_text_top_right_at(screen, "C", right_ability_margin + 125, top_margin - self.state.font_text.get_height() - 5, self.state.font_text)
        
        render_text_top_left_at(screen, "Stats", min_x - padding, top_margin - padding - 20 - self.state.font_header.get_height() - 10, self.state.font_header)