from enum import Enum
import pickle
import socket
import threading
import pygame
from client.core.game_renderer import GameRenderer
from client.core.tcp_client import TCPClient
from common.constants import ARENA_HEIGHT, ARENA_WIDTH, UDP_PORT
from common.game_state import GameState, PlayerInfo
from common.tcp_messages import ExitTestMessage, InputMessage, LobbyInfoMessage, Message, PlayerInfoMessage, StartMessage

ALLOWED_KEYS = [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_a, pygame.K_s, pygame.K_d,
                pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]


class ClientState(Enum):
    NOT_CONNECTED = 1
    IN_LOBBY = 2
    IN_GAME = 3
    IN_TEST = 4

class GameClient:
    
    def __init__(self):
        self.tcp_client = TCPClient(self._on_tcp_message, self._on_tcp_disconnect)
        self.renderer = GameRenderer()
        self.state: ClientState = ClientState.NOT_CONNECTED
        self.lobby_info: LobbyInfoMessage = None
        self.id = None
        
    def start(self):
        # Get info from user
        while self.id is None or len(self.id) == 0:
            self.id = input("Enter player id: ").strip()
            
        self.udp_port = input("UDP Port (6000): ")
        if len(self.udp_port) == 0:
            self.udp_port = "6000"
            
        # Setup udp socket
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(("0.0.0.0", int(self.udp_port)))
        threading.Thread(target=self._udp_listener, daemon=True).start()
        
        # Init pygame
        pygame.init()
        self.screen = pygame.display.set_mode((ARENA_WIDTH, ARENA_HEIGHT))
        pygame.display.set_caption(f"Robot Battle ({self.id})")
        self.clock = pygame.time.Clock()
        self.font_header = pygame.font.SysFont("Arial", 20)
        self.font_text = pygame.font.SysFont("Arial", 16)
        
        self.screen_center = (
            ARENA_WIDTH / 2,
            ARENA_HEIGHT / 2
        )
            
        self._run()
        
    def _on_tcp_message(self, message: Message):
        if isinstance(message, LobbyInfoMessage):
            self.lobby_info = message
            self.state = ClientState.IN_LOBBY
            
    def _on_tcp_disconnect(self):
        self.state = ClientState.NOT_CONNECTED
        self.lobby_info = None
        
    def _udp_listener(self):
        while True:
            data, _ = self.udp_socket.recvfrom(4096)
            # print(len(data))
            
            obj = pickle.loads(data)
            
            if isinstance(obj, GameState):
                self.renderer.state = obj
            elif isinstance(obj, PlayerInfo):
                if self.state == ClientState.IN_LOBBY:
                    self.state = ClientState.IN_GAME
                self.renderer.static_player_info = obj
    
    def _run(self):       
        self.running = True
        while self.running:
            for event in pygame.event.get():
                self._handle_event(event)
                    
            self.screen.fill((30, 30, 30))
            
            if self.state == ClientState.NOT_CONNECTED:
                self._render_not_connected()
            elif self.state == ClientState.IN_LOBBY:
                self._render_in_lobby()
            elif self.state == ClientState.IN_GAME or self.state == ClientState.IN_TEST:
                self.renderer.render(self.screen)
            
            pygame.display.flip()
            self.clock.tick(30)
            
        pygame.quit()
        self.tcp_client.close()
        self.udp_socket.close()

      
    def _handle_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            self.running = False
            
        elif self.state == ClientState.NOT_CONNECTED:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.tcp_client.connect()
                with open("client/my_robot.py") as f:
                    self.tcp_client.send(PlayerInfoMessage(self.id, int(self.udp_port), f.read()))
        elif self.state == ClientState.IN_LOBBY:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_KP_ENTER:
                self.tcp_client.send(StartMessage())
            if event.type == pygame.KEYDOWN and event.key == pygame.K_t:
                self.state = ClientState.IN_TEST
                self.tcp_client.send(StartMessage(is_test=True))
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
        center_x, center_y = self.screen_center
        
        self._render_text_center_at("NOT CONNECTED", center_x, center_y, self.font_header)
        self._render_text_center_at("Press 'Enter' to connect...", center_x, center_y + 35, self.font_text)
    
    def _render_in_lobby(self):
        self._render_text_top_left_at("Players:", 50, 50, self.font_header)
        
        player_spacing = self.font_text.get_height() + 10
        for i, id in enumerate(self.lobby_info.player_ids):
            self._render_text_top_left_at(f"- {id}", 75, 75 + i * player_spacing, self.font_text)
            
        self._render_text_bottom_right_at("KP Enter - Start", ARENA_WIDTH - 50, ARENA_HEIGHT - 114, self.font_text)
        self._render_text_bottom_right_at("T - Start Test", ARENA_WIDTH - 50, ARENA_HEIGHT - 82, self.font_text)
        self._render_text_bottom_right_at("Delete   - Disconnect", ARENA_WIDTH - 50, ARENA_HEIGHT - 50, self.font_text)
    
    def _render_text_center_at(self, text: str, x: float, y: float, font: pygame.font.Font):
        text_surface = font.render(text, True, (255, 255, 255))
        self.screen.blit(text_surface, (
            x - text_surface.get_width() / 2, 
            y - text_surface.get_height() / 2
        ))
        
    def _render_text_top_left_at(self, text: str, x: float, y: float, font: pygame.font.Font):
        text_surface = font.render(text, True, (255, 255, 255))
        self.screen.blit(text_surface, (x, y))
        
    def _render_text_bottom_right_at(self, text: str, x: float, y: float, font: pygame.font.Font):
        text_surface = font.render(text, True, (255, 255, 255))
        self.screen.blit(text_surface, (
            x - text_surface.get_width(), 
            y -text_surface.get_height() 
        ))
        