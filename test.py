import pygame


pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption(f"Robot Battle Test")
clock = pygame.time.Clock()

if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        else:
            print(event)
       
            
    pygame.display.flip()
    clock.tick(60)
    
pygame.quit()