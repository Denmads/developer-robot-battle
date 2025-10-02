from datetime import datetime
from enum import Enum
import threading
import time
import pygame
from client.core.game_renderer import GameRenderer
from client.core.tcp_client import TCPClient
from client.core.udp_client import UDPClient
from common.constants import ARENA_HEIGHT, ARENA_WIDTH, UDP_PORT
from common.udp_message import GameStateMessage, PlayerStaticInfoMessage, UDPMessage
from common.tcp_messages import ExitTestMessage, InputMessage, LobbyInfoMessage, LobbyJoinedMessage, Message, PlayerInfoMessage, RoundEndedMessage, RoundStartedMessage, StartRoundMessage

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
        self.udp_client = UDPClient(int(self.udp_port), self._on_udp_message)
        
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
        if isinstance(message, LobbyJoinedMessage):
            self.state = ClientState.IN_LOBBY
        elif isinstance(message, RoundStartedMessage):
            self.renderer.round_start_time = datetime.fromisoformat(message.begin_time)
        elif isinstance(message, RoundEndedMessage):
            if len(message.winner_id) > 0:
                self.renderer.round_winner = message.winner_id 
                threading.Timer(3.0, self._go_to_lobby).start()
            else:
                self._go_to_lobby()
          
    def _go_to_lobby(self):
        self.state = ClientState.IN_LOBBY
        self.renderer.round_winner = None
            
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
                with open("client/my_robot.py") as f:
                    self.tcp_client.send(PlayerInfoMessage(self.id, int(self.udp_port), f.read()))
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
        center_x, center_y = self.screen_center
        
        self._render_text_center_at("NOT CONNECTED", center_x, center_y, self.font_header)
        self._render_text_center_at("Press 'Enter' to connect...", center_x, center_y + 35, self.font_text)
    
    def _render_in_lobby(self):
        self._render_text_top_left_at("Players:", 50, 50, self.font_header)
        
        player_spacing = self.font_text.get_height() + 10
        for i, (id, color) in enumerate(self.lobby_info.players.items()):
            self._render_text_top_left_at(f"- {id}", 75, 75 + i * player_spacing, self.font_text, color)
            
        self._render_text_bottom_right_at("KP Enter - Start", ARENA_WIDTH - 50, ARENA_HEIGHT - 114, self.font_text)
        self._render_text_bottom_right_at("T - Start Test", ARENA_WIDTH - 50, ARENA_HEIGHT - 82, self.font_text)
        self._render_text_bottom_right_at("Delete   - Disconnect", ARENA_WIDTH - 50, ARENA_HEIGHT - 50, self.font_text)
    
    def _render_text_center_at(self, text: str, x: float, y: float, font: pygame.font.Font, color: tuple[int, int, int] = (255, 255, 255)):
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, (
            x - text_surface.get_width() / 2, 
            y - text_surface.get_height() / 2
        ))
        
    def _render_text_top_left_at(self, text: str, x: float, y: float, font: pygame.font.Font, color: tuple[int, int, int] = (255, 255, 255)):
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))
        
    def _render_text_bottom_right_at(self, text: str, x: float, y: float, font: pygame.font.Font, color: tuple[int, int, int] = (255, 255, 255)):
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, (
            x - text_surface.get_width(), 
            y -text_surface.get_height() 
        ))
        