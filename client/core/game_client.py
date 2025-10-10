from datetime import datetime
import json
import queue
import sys
import threading
import pygame
from client.core.renderers.connect_menu_renderer import ConnectMenuStateRenderer
from client.core.renderers.game_renderer import GameStateRenderer
from client.core.renderers.lobby_menu_renderer import LobbyMenuStateRenderer
from client.core.state_renderer import ClientState, SharedState
from client.core.tcp_client import TCPClient
from client.core.udp_client import UDPClient
from common.udp_message import GameStateMessage, PlayerStaticInfoMessage, RobotStateMessage, UDPMessage
from common.tcp_messages import LobbyInfoMessage, LobbyJoinedMessage, Message, RoundEndedMessage, RoundStartedMessage

ALLOWED_KEYS = [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_a, pygame.K_s, pygame.K_d,
                pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]


class GameClient:
    
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.path = "."
        else:
            self.path = "client"
        
        with open(self.path + "\\settings.json", "r") as f:
            settings = json.loads(f.read())
        
        self.tcp_client = TCPClient(self._on_tcp_message, self._on_tcp_disconnect, settings["ip"], settings["port"])
        self.main_thread_tasks = queue.Queue()
        
    def start(self):
        # Get info from user
        id: str = None
        while id is None or len(id) < 5 or len(id) > 30:
            id = input("Enter player id: ").strip()
            id = id.strip()
            
            if len(id) < 5 or len(id) > 30:
                print("Must be between 5 and 30 characters!")
            
        udp_port = ""
        if len(sys.argv) > 1 and sys.argv[1] == "-dev":
            udp_port = input("UDP Port (6000): ")
            udp_port = udp_port.strip()
            
        if len(udp_port) == 0:
            udp_port = "6000"
            
        # Setup renderers
        pygame.init()
        self.shared_state = SharedState(
            self.path,
            player_id=id,
            menu_size=(800, 600),
            client_state=ClientState.NOT_CONNECTED,
            tcp=self.tcp_client,
            udp_port=int(udp_port),
            font_header=pygame.font.SysFont("Arial", 20),
            font_text=pygame.font.SysFont("Arial", 16)
        )
        
        self.connect_menu_renderer = ConnectMenuStateRenderer(self.shared_state)
        self.lobby_menu_renderer = LobbyMenuStateRenderer(self.shared_state)
        self.game_renderer = GameStateRenderer(self.shared_state)
            
        # Setup udp socket
        self.udp_client = UDPClient(self.shared_state.udp_port, self._on_udp_message)
        
        # Init pygame window
        self.screen = pygame.display.set_mode(self.shared_state.menu_size)
        pygame.display.set_caption(f"Robot Battle ({self.shared_state.player_id})")
        self.clock = pygame.time.Clock()
            
        self._run()
        
    def _on_tcp_message(self, message: Message):
        if isinstance(message, LobbyInfoMessage):
            self.lobby_menu_renderer.latest_lobby_info = message
        if isinstance(message, LobbyJoinedMessage):
            self.shared_state.client_state = ClientState.IN_LOBBY
        elif isinstance(message, RoundStartedMessage):
            self.game_renderer.start_round(message)
            self.main_thread_tasks.put(("resize", (message.arena_width, message.arena_height)))
        elif isinstance(message, RoundEndedMessage):
            if len(message.winner_id) > 0:
                self.game_renderer.set_winner(message.winner_id)
                threading.Timer(3.0, self._go_to_lobby).start()
            else:
                self._go_to_lobby()
          
    def _go_to_lobby(self):
        self.shared_state.client_state = ClientState.IN_LOBBY
        self.game_renderer.set_winner(None)
        self.main_thread_tasks.put(("resize", self.shared_state.menu_size))
            
    def _on_tcp_disconnect(self):
        self.shared_state.client_state = ClientState.NOT_CONNECTED
        self.lobby_menu_renderer.latest_lobby_info = None
        
    def _on_udp_message(self, message: UDPMessage):
        if isinstance(message, GameStateMessage):
            self.game_renderer.add_new_state(message)
        elif isinstance(message, PlayerStaticInfoMessage):
            if self.shared_state.client_state == ClientState.IN_LOBBY:
                self.shared_state.client_state = ClientState.IN_GAME
            self.game_renderer.static_player_info = {p.idx: p for p in message.player_info}
        elif isinstance(message, RobotStateMessage):
            self.game_renderer.robot_state = message.state
    
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
                if event.type == pygame.QUIT:
                    self.running = False
                if self.shared_state.client_state == ClientState.NOT_CONNECTED:
                    self.connect_menu_renderer.on_event(event)
                elif self.shared_state.client_state == ClientState.IN_LOBBY:
                    self.lobby_menu_renderer.on_event(event)
                elif self.shared_state.client_state == ClientState.IN_GAME or self.shared_state.client_state == ClientState.IN_TEST:
                    self.game_renderer.on_event(event)
                    
            self.screen.fill((30, 30, 30))
            
            delta = datetime.now() - last_update
            if self.shared_state.client_state == ClientState.NOT_CONNECTED:
                self.connect_menu_renderer.render(self.screen, delta)
            elif self.shared_state.client_state == ClientState.IN_LOBBY:
                self.lobby_menu_renderer.render(self.screen, delta)
            elif self.shared_state.client_state == ClientState.IN_GAME or self.shared_state.client_state == ClientState.IN_TEST:
                self.game_renderer.render(self.screen, delta)
                
            last_update = datetime.now()
            pygame.display.flip()
            self.clock.tick(60)
            
        pygame.quit()
        self.tcp_client.close()
        self.udp_client.close()
    
        