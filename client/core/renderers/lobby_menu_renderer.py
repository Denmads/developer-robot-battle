from datetime import timedelta
import pygame

from client.core.render_utils import render_text_bottom_right_at, render_text_top_left_at
from client.core.state_renderer import ClientState, SharedState, StateRenderer
from common.tcp_messages import LobbyInfoMessage, StartRoundMessage


class LobbyMenuStateRenderer(StateRenderer):
    
    def __init__(self, state: SharedState):
        super().__init__(state)
        self.latest_lobby_info: LobbyInfoMessage = None
        
        self.controller_connected: bool = pygame.joystick.get_count() > 0
    
    def on_event(self, event: pygame.event.Event):
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_KP_ENTER) or (event.type == pygame.JOYBUTTONDOWN and event.button == 0):
            self.state.tcp.send(StartRoundMessage())
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_t) or (event.type == pygame.JOYBUTTONDOWN and event.button == 2):
            self.state.client_state = ClientState.IN_TEST
            self.state.tcp.send(StartRoundMessage(is_test=True))
        elif (event.type == pygame.KEYDOWN and event.key == pygame.K_DELETE) or (event.type == pygame.JOYBUTTONDOWN and event.button == 1):
            self.state.tcp.close()
            self.state.client_state = ClientState.NOT_CONNECTED
            
    
    def render(self, screen: pygame.Surface, delta: timedelta):
        render_text_top_left_at(screen, "Players:", 50, 50, self.state.font_header)
        
        if self.latest_lobby_info is not None:
            player_spacing = self.state.font_text.get_height() + 10
            for i, (id, color) in enumerate(self.latest_lobby_info.players.items()):
                render_text_top_left_at(screen, f"- {id}", 75, 75 + i * player_spacing, self.state.font_text, color)
            
        render_text_bottom_right_at(screen, f"KP Enter{' / A' if self.controller_connected else ''} - Start", self.state.menu_size[0] - 50, self.state.menu_size[1] - 114, self.state.font_text)
        render_text_bottom_right_at(screen, f"T{' / X' if self.controller_connected else ''} - Start Test", self.state.menu_size[0] - 50, self.state.menu_size[1] - 82, self.state.font_text)
        render_text_bottom_right_at(screen, f"Delete{' / B' if self.controller_connected else ''}   - Disconnect", self.state.menu_size[0] - 50, self.state.menu_size[1] - 50, self.state.font_text)
    
    