from datetime import datetime
from enum import Enum
import glob
import queue
import threading
import time
import pygame
from client.core.game_renderer import GameRenderer
from client.core.tcp_client import TCPClient
from client.core.udp_client import UDPClient
from common.calculations import calculate_ability_cooldown, calculate_ability_energy_cost
from common.robot import Robot, RobotInfo, parse_robot_config_from_string
from common.udp_message import GameStateMessage, PlayerStaticInfoMessage, UDPMessage
from common.tcp_messages import ExitTestMessage, InputMessage, LobbyInfoMessage, LobbyJoinedMessage, Message, PlayerInfoMessage, RoundEndedMessage, RoundStartedMessage, StartRoundMessage

ALLOWED_KEYS = [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_a, pygame.K_s, pygame.K_d,
                pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]


MENU_SIZE = (800, 600)

class ClientState(Enum):
    NOT_CONNECTED = 1
    IN_LOBBY = 2
    IN_GAME = 3
    IN_TEST = 4

class GameClient:
    
    def __init__(self):
        self.tcp_client = TCPClient(self._on_tcp_message, self._on_tcp_disconnect)
        self.state: ClientState = ClientState.NOT_CONNECTED
        self.main_thread_tasks = queue.Queue()
        
        self.all_robots = glob.glob("client\\robots\\*.py")
        self.current_selected_robot: int = 0
        self._create_robot()
        
        self.renderer = GameRenderer()
        self.lobby_info: LobbyInfoMessage = None
        
        self.id = None
        
    def _create_robot(self):
        with open(self.all_robots[self.current_selected_robot]) as f:
            config = parse_robot_config_from_string(f.read())
        
        self.robot = Robot.create(
            config, 0, 0, 0
        )
        
    def start(self):
        if len(self.all_robots) == 0:
            print("No robots to use. Add a robot configuration to 'client/robots'!")
            exit()
        
        # Get info from user
        while self.id is None or len(self.id) == 0:
            self.id = input("Enter player id: ").strip()
            
        self.udp_port = input("UDP Port (6000): ")
        if len(self.udp_port) == 0:
            self.udp_port = "6000"
            
        # Setup udp socket
        self.udp_client = UDPClient(int(self.udp_port), self._on_udp_message)
        
        # Init pygame
        pygame.init()
        self.screen = pygame.display.set_mode(MENU_SIZE)
        pygame.display.set_caption(f"Robot Battle ({self.id})")
        self.clock = pygame.time.Clock()
        self.font_header = pygame.font.SysFont("Arial", 20)
        self.font_text = pygame.font.SysFont("Arial", 16)
        
        self.screen_center = (
            MENU_SIZE[0] / 2,
            MENU_SIZE[1] / 2
        )
            
        self._run()
        
    def _on_tcp_message(self, message: Message):
        if isinstance(message, LobbyInfoMessage):
            self.lobby_info = message
        if isinstance(message, LobbyJoinedMessage):
            self.state = ClientState.IN_LOBBY
        elif isinstance(message, RoundStartedMessage):
            self.renderer.round_start_time = datetime.fromisoformat(message.begin_time)
            self.renderer.arena_size = (message.arena_width, message.arena_height)
            self.main_thread_tasks.put(("resize", (message.arena_width, message.arena_height)))
        elif isinstance(message, RoundEndedMessage):
            if len(message.winner_id) > 0:
                self.renderer.round_winner = message.winner_id 
                threading.Timer(3.0, self._go_to_lobby).start()
            else:
                self._go_to_lobby()
          
    def _go_to_lobby(self):
        self.state = ClientState.IN_LOBBY
        self.renderer.round_winner = None
        self.main_thread_tasks.put(("resize", MENU_SIZE))
            
    def _on_tcp_disconnect(self):
        self.state = ClientState.NOT_CONNECTED
        self.lobby_info = None
        
    def _on_udp_message(self, message: UDPMessage):
        if isinstance(message, GameStateMessage):
            self.renderer.add_new_state(message)
        elif isinstance(message, PlayerStaticInfoMessage):
            if self.state == ClientState.IN_LOBBY:
                self.state = ClientState.IN_GAME
            self.renderer.static_player_info = {p.idx: p for p in message.player_info}
    
    def _run(self):       
        self.running = True
        last_update: datetime = datetime.now()
        while self.running:
            while not self.main_thread_tasks.empty():
                task, data = self.main_thread_tasks.get()
                if task == "resize":
                    width, height = data
                    self.screen = pygame.display.set_mode((width, height))
            
            for event in pygame.event.get():
                self._handle_event(event)
                    
            self.screen.fill((30, 30, 30))
            
            if self.state == ClientState.NOT_CONNECTED:
                self._render_not_connected()
            elif self.state == ClientState.IN_LOBBY:
                self._render_in_lobby()
            elif self.state == ClientState.IN_GAME or self.state == ClientState.IN_TEST:
                self.renderer.render(self.screen, datetime.now() - last_update)
                
            last_update = datetime.now()
            pygame.display.flip()
            self.clock.tick(60)
            
        pygame.quit()
        self.tcp_client.close()
        self.udp_client.close()

      
    def _handle_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            self.running = False
            
        elif self.state == ClientState.NOT_CONNECTED:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.tcp_client.connect()
                with open(self.all_robots[self.current_selected_robot]) as f:
                    self.tcp_client.send(PlayerInfoMessage(self.id, int(self.udp_port), f.read()))
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
                self.current_selected_robot = max(0, self.current_selected_robot - 1)
                self._create_robot()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
                self.current_selected_robot = min(len(self.all_robots)-1, self.current_selected_robot + 1)
                self._create_robot()
        elif self.state == ClientState.IN_LOBBY:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_KP_ENTER:
                self.tcp_client.send(StartRoundMessage())
            if event.type == pygame.KEYDOWN and event.key == pygame.K_t:
                self.state = ClientState.IN_TEST
                self.tcp_client.send(StartRoundMessage(is_test=True))
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_DELETE:
                self.tcp_client.close()
                self.state = ClientState.NOT_CONNECTED
        elif self.state == ClientState.IN_GAME or self.state == ClientState.IN_TEST:
            if event.type == pygame.KEYDOWN and event.key in ALLOWED_KEYS:
                self.tcp_client.send(InputMessage(self.id, event.key, 1))
            elif event.type == pygame.KEYUP and event.key in ALLOWED_KEYS:
                self.tcp_client.send(InputMessage(self.id, event.key, 2))
            elif self.state == ClientState.IN_TEST and event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
                self.tcp_client.send(ExitTestMessage())
            
    def _render_not_connected(self):
        # Robot selection
        self._render_text_top_left_at("Robots:", 50, 50, self.font_header)
        
        robot_spacing = self.font_text.get_height() + 10
        text_left_margin = 75
        selector_spacing = 10
        selected_color = (255, 193, 7)
        for i, file_path in enumerate(self.all_robots):
            file_name = file_path.split("\\")[-1]
            text = f"{file_name.rstrip('.py')}"
            text_y = 75 + i * robot_spacing
            color = selected_color if i == self.current_selected_robot else (255, 255, 255)
            name_w, _ = self._render_text_top_left_at(text, text_left_margin, text_y, self.font_text, color)
            
            if i == self.current_selected_robot:
                w, _ = self.font_text.size(">")
                self._render_text_top_left_at(">", text_left_margin - selector_spacing - w, text_y, self.font_text, color)
                self._render_text_top_left_at("<", text_left_margin + name_w + selector_spacing, text_y, self.font_text, color)
        
        # Robot stats
        min_x = MENU_SIZE[0]
        max_x = 0
        max_y = 0
        
        right_margin = MENU_SIZE[0] - 325
        top_margin = 118
        stat_spacing = self.font_text.get_height() + 10
        stats = {
            "Hp": round(self.robot.max_hp, 2),
            "Energy": round(self.robot.max_energy, 2),
            "Size": round(self.robot.size, 2),
            "Energy Regen": round(self.robot.energy_regen, 2),
            "Move Speed": round(self.robot.move_speed, 2),
            "Turn speed": round(self.robot.turn_speed, 2)
        }
        
        stat_texts = [
            f"{stat_name}: {value}"
            for stat_name, value in stats.items()
        ]
        
        for i, stat in enumerate(stat_texts):
            w, h = self._render_text_top_right_at(stat, right_margin, top_margin + i * stat_spacing, self.font_text)
            if right_margin - w < min_x:
                min_x = right_margin - w
            if top_margin + i * stat_spacing + h > max_y:
                max_y = top_margin + i * stat_spacing + h
        
        # ability costs
        ability_stats = {}
        for i, key in enumerate(["q", "w", "e", "a", "s", "d"]):
            commands = []
            self.robot.ability_func(i+1, commands, RobotInfo(
                self.robot.hp,
                self.robot.max_hp,
                self.robot.energy,
                self.robot.max_energy,
                {
                    w.id: w.cooldown_time_left
                    for w in self.robot.weapons.values()
                }
            ))
            ability_stats[key] = {
                "cost": round(calculate_ability_energy_cost(self.robot, commands), 1),
                "cooldown": round(calculate_ability_cooldown(self.robot, commands), 2)
            }
        
        right_ability_margin = right_margin + 100
        for i, (key, ability_stats) in enumerate(ability_stats.items()):
            self._render_text_top_right_at(f"{key}:", right_ability_margin, top_margin + i * stat_spacing, self.font_text)
            self._render_text_top_right_at(f"{ability_stats['cost']}", right_ability_margin + 50, top_margin + i * stat_spacing, self.font_text)
            w, h = self._render_text_top_right_at(f"{ability_stats['cooldown']}", right_ability_margin + 125, top_margin + i * stat_spacing, self.font_text)
            
            if right_ability_margin + 125 + w > max_x:
                max_x = right_ability_margin + 125 + w 
            if top_margin + i * stat_spacing + h > max_y:
                max_y = top_margin + i * stat_spacing + h
        
        padding = 15
        pygame.draw.rect(self.screen, (255, 255, 255), (min_x - padding, top_margin - padding - 20, (max_x + padding * 2) - min_x, (max_y + padding * 2 + 20) - top_margin), 2)
        self._render_text_top_right_at("E", right_ability_margin + 50, top_margin - self.font_text.get_height() - 5, self.font_text)
        self._render_text_top_right_at("C", right_ability_margin + 125, top_margin - self.font_text.get_height() - 5, self.font_text)
        
        self._render_text_top_left_at("Stats", min_x - padding, top_margin - padding - 20 - self.font_header.get_height() - 10, self.font_header)
        
        self._render_text_bottom_right_at("Press 'Enter' to connect...", MENU_SIZE[0] - 50, MENU_SIZE[1] - 50, self.font_text)
        
        
    
    def _render_in_lobby(self):
        self._render_text_top_left_at("Players:", 50, 50, self.font_header)
        
        player_spacing = self.font_text.get_height() + 10
        for i, (id, color) in enumerate(self.lobby_info.players.items()):
            self._render_text_top_left_at(f"- {id}", 75, 75 + i * player_spacing, self.font_text, color)
            
        self._render_text_bottom_right_at("KP Enter - Start", MENU_SIZE[0] - 50, MENU_SIZE[1] - 114, self.font_text)
        self._render_text_bottom_right_at("T - Start Test", MENU_SIZE[0] - 50, MENU_SIZE[1] - 82, self.font_text)
        self._render_text_bottom_right_at("Delete   - Disconnect", MENU_SIZE[0] - 50, MENU_SIZE[1] - 50, self.font_text)
    
    def _render_text_center_at(self, text: str, x: float, y: float, font: pygame.font.Font, color: tuple[int, int, int] = (255, 255, 255)) -> tuple[int, int]:
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, (
            x - text_surface.get_width() / 2, 
            y - text_surface.get_height() / 2
        ))
        return (text_surface.get_width(), text_surface.get_height())
        
    def _render_text_top_left_at(self, text: str, x: float, y: float, font: pygame.font.Font, color: tuple[int, int, int] = (255, 255, 255)) -> tuple[int, int]:
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))
        return (text_surface.get_width(), text_surface.get_height())
        
    def _render_text_bottom_left_at(self, text: str, x: float, y: float, font: pygame.font.Font, color: tuple[int, int, int] = (255, 255, 255)) -> tuple[int, int]:
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, (
            x, 
            y - text_surface.get_height()
        ))
        return (text_surface.get_width(), text_surface.get_height())
    
    def _render_text_top_right_at(self, text: str, x: float, y: float, font: pygame.font.Font, color: tuple[int, int, int] = (255, 255, 255)) -> tuple[int, int]:
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, (
            x - text_surface.get_width(), 
            y 
        ))
        return (text_surface.get_width(), text_surface.get_height())
        
    def _render_text_bottom_right_at(self, text: str, x: float, y: float, font: pygame.font.Font, color: tuple[int, int, int] = (255, 255, 255)) -> tuple[int, int]:
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, (
            x - text_surface.get_width(), 
            y - text_surface.get_height() 
        ))
        return (text_surface.get_width(), text_surface.get_height())
    
        