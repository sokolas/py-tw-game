import pygame

# the presentation - animations, sounds, whatever you want
class Game:
    def __init__(self, width=1280, height=720):
        print("game")
        self.width = width
        self.height = height
    
    # decouple the game from the server/client
    def set_tick_callback(self, run_once):
        self.run_once = run_once

    # this is the main loop, runs forever until the game is closed
    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        
        font = pygame.font.Font(pygame.font.get_default_font(), 90)

        clock = pygame.time.Clock()
        dt = 0
        self.running = True

        text_position = pygame.Vector2(self.width/3, self.height/4)
        text_speed = pygame.Vector2(100, 100)

        text_surface = font.render("DVD", True, pygame.Color("aquamarine"))
        text_size = pygame.Vector2(font.size("DVD"))
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            # process keys if needed?
            # keys = pygame.key.get_pressed()

            # move objects, etc
            text_position += text_speed * dt
            if text_position.x < 1:
                text_position.x = 1
                text_speed.x = -text_speed.x
            if text_position.x > self.width - text_size.x:
                text_position.x = self.width - text_size.x
                text_speed.x = -text_speed.x
            if text_position.y < 1:
                text_position.y = 1
                text_speed.y = -text_speed.y
            if text_position.y > self.height - text_size.y:
                text_position.y = self.height - text_size.y
                text_speed.y = -text_speed.y
            
            # draw stuff
            screen.fill("black")
            screen.blit(text_surface, dest=text_position)

            # display it
            pygame.display.flip()

            # process all the server/client stuff that is queued up
            if self.run_once:
                self.run_once()

            # wait for the next frame
            dt = clock.tick(60)/1000


        pygame.quit()
