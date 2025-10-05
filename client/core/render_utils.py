import pygame


def render_text_center_at(screen: pygame.Surface, text: str, x: float, y: float, font: pygame.font.Font, color: tuple[int, int, int] = (255, 255, 255)) -> tuple[int, int]:
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (
        x - text_surface.get_width() / 2, 
        y - text_surface.get_height() / 2
    ))
    return (text_surface.get_width(), text_surface.get_height())
        
def render_text_top_left_at(screen: pygame.Surface, text: str, x: float, y: float, font: pygame.font.Font, color: tuple[int, int, int] = (255, 255, 255)) -> tuple[int, int]:
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))
    return (text_surface.get_width(), text_surface.get_height())
    
def render_text_bottom_left_at(screen: pygame.Surface, text: str, x: float, y: float, font: pygame.font.Font, color: tuple[int, int, int] = (255, 255, 255)) -> tuple[int, int]:
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (
        x, 
        y - text_surface.get_height()
    ))
    return (text_surface.get_width(), text_surface.get_height())

def render_text_top_right_at(screen: pygame.Surface, text: str, x: float, y: float, font: pygame.font.Font, color: tuple[int, int, int] = (255, 255, 255)) -> tuple[int, int]:
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (
        x - text_surface.get_width(), 
        y 
    ))
    return (text_surface.get_width(), text_surface.get_height())
    
def render_text_bottom_right_at(screen: pygame.Surface, text: str, x: float, y: float, font: pygame.font.Font, color: tuple[int, int, int] = (255, 255, 255)) -> tuple[int, int]:
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (
        x - text_surface.get_width(), 
        y - text_surface.get_height() 
    ))
    return (text_surface.get_width(), text_surface.get_height())