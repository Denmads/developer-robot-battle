import pickle
import socket
import threading
import pygame
from client.core.game_renderer import GameRenderer
from client.core.tcp_client import TCPClient
from common.constants import ARENA_HEIGHT, ARENA_WIDTH, UDP_PORT
from common.game_state import GameState, PlayerColors
from common.tcp_messages import InputMessage, PlayerInfoMessage, StartMessage

ALLOWED_KEYS = [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_a, pygame.K_s, pygame.K_d,
                pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]


class GameClient:
    
    def __init__(self, playerId: str):
        self.id = playerId
        
        self.tcp_client = TCPClient()
        self.renderer = GameRenderer()
        self.running = False
        
    def start(self):
        pygame.init()
        self.screen = pygame.display.set_mode((ARENA_WIDTH, ARENA_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)
        
        udp = input("UDP Port (6000): ")
        if len(udp) == 0:
            udp = "6000"
        
        self.tcp_client.connect()
        with open("client/my_robot.py") as f:
            self.tcp_client.send(PlayerInfoMessage(self.id, int(udp), f.read()))
            
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(("0.0.0.0", int(udp)))
        threading.Thread(target=self._udp_listener, daemon=True).start()
            
        self._run()
        
    def _udp_listener(self):
        while True:
            data, _ = self.udp_socket.recvfrom(4096)
            # print(len(data))
            
            obj = pickle.loads(data)
            
            if isinstance(obj, GameState):
                self.renderer.state = obj
            elif isinstance(obj, PlayerColors):
                self.renderer.color_map = obj
    
    def _run(self):       
        self.running = True
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key in ALLOWED_KEYS:
                    self.tcp_client.send(InputMessage(self.id, event.key, 1))
                elif event.type == pygame.KEYUP and event.key in ALLOWED_KEYS:
                    self.tcp_client.send(InputMessage(self.id, event.key, 2))
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_KP_ENTER:
                    self.tcp_client.send(StartMessage())
                    
                    
            self.screen.fill((30, 30, 30))
            
            if self.renderer.state is None:
                start_text = self.font.render("Press 'KP Enter' to start...", True, (255, 255, 255))
                self.screen.blit(start_text, (ARENA_WIDTH / 2 - start_text.get_width() / 2, ARENA_HEIGHT / 2 - start_text.get_height() / 2))
            else:
                self.renderer.render(self.screen)
            
            pygame.display.flip()
            self.clock.tick(30)
            
        pygame.quit()
        self.tcp_client.close()
        self.udp_socket.close()

            
        