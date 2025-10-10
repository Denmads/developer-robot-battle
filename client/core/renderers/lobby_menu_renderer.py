from datetime import timedelta
import pygame

from client.core.render_utils import render_text_bottom_right_at, render_text_top_left_at, render_text_top_right_at
from client.core.state_renderer import ClientState, SharedState, StateRenderer
from common.tcp_messages import LobbyInfoMessage, StartRoundMessage


class LobbyMenuStateRenderer(StateRenderer):
    
    def __init__(self, state: SharedState):
        super().__init__(state)
        self.latest_lobby_info: LobbyInfoMessage = None
    
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
                
        self._render_controls(screen)
            
        render_text_bottom_right_at(screen, f"KP Enter{' / A' if self.state.controller_connected else ''} - Start", self.state.menu_size[0] - 50, self.state.menu_size[1] - 114, self.state.font_text)
        render_text_bottom_right_at(screen, f"T{' / X' if self.state.controller_connected else ''} - Start Test", self.state.menu_size[0] - 50, self.state.menu_size[1] - 82, self.state.font_text)
        render_text_bottom_right_at(screen, f"Delete{' / B' if self.state.controller_connected else ''}   - Disconnect", self.state.menu_size[0] - 50, self.state.menu_size[1] - 50, self.state.font_text)
        
    def _render_controls(self, screen: pygame.Surface):
        max_x = 0
        max_y = 0
        
        right_margin = self.state.menu_size[0] - 350
        right_margin_abil = self.state.menu_size[0] - 150
        top_margin = 118
        control_spacing = 10
        move_controls = [
            f"Forward - up{' / LS ↑' if self.state.controller_connected else ''}",
            f"Back - down{' / LS ↓' if self.state.controller_connected else ''}",
            f"Turn Right - right{' / LS →' if self.state.controller_connected else ''}",
            f"Turn Left - left{' / LS ←' if self.state.controller_connected else ''}"
        ]
        
        _, h_mov = render_text_top_left_at(screen, "Movement", right_margin, top_margin, self.state.font_header, (255, 255, 255))
        max_y = top_margin + h_mov + 15
        for i, control in enumerate(move_controls):
            w, h = render_text_top_left_at(screen, control, right_margin, max_y, self.state.font_text, (235, 235, 235))
            # if right_margin + w > max_x:
            #     max_x = right_margin + w
                
            max_y += h + control_spacing
        
        ability_controls = [
            f"Q{' / L Trigger' if self.state.controller_connected else ''}",
            f"W{' / Y' if self.state.controller_connected else ''}",
            f"E{' / R Trigger' if self.state.controller_connected else ''}",
            f"A{' / X' if self.state.controller_connected else ''}",
            f"S{' / A' if self.state.controller_connected else ''}",
            f"D{' / B' if self.state.controller_connected else ''}"
        ]
        
        _, h_abil = render_text_top_left_at(screen, "Abilities", right_margin_abil, top_margin, self.state.font_header, (255, 255, 255))
        for i, control in enumerate(ability_controls):
            w, h = render_text_top_left_at(screen, control, right_margin_abil, top_margin + h_abil + 15 + i * (control_spacing + self.state.font_text.get_height()), self.state.font_text, (235, 235, 235))
            if right_margin_abil + w > max_x:
                max_x = right_margin_abil + w
                
            if top_margin + h_abil + 15 + i * (control_spacing + self.state.font_text.get_height()) + h > max_y:
                max_y = top_margin + h_abil + 15 + i * (control_spacing + self.state.font_text.get_height()) + h
        
        
        padding = 15
        pygame.draw.rect(screen, (255, 255, 255), (right_margin - padding, top_margin - padding, (max_x + padding * 2) - right_margin, (max_y + padding * 2 + 20) - top_margin), 2)
        
        render_text_top_left_at(screen, "Controls", right_margin - padding, top_margin - padding - self.state.font_header.get_height() - 10, self.state.font_header)
    
    