import pygame

# the presentation - animations, sounds, whatever you want
class Game:
    def __init__(self):
        print("game")
    
    # decouple the game from the server/client
    def set_tick_callback(self, run_once):
        self.run_once = run_once

    # this is the main loop, runs forever until the game is closed
    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((1280, 720))
        
        clock = pygame.time.Clock()
        dt = 0
        self.running = True

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            # process keys if needed?
            # keys = pygame.key.get_pressed()

            # draw stuff
            screen.fill("purple")


            # display it
            pygame.display.flip()

            # process all the server/client stuff that is queued up
            if self.run_once:
                self.run_once()

            # wait for the next frame
            dt = clock.tick(60)/1000


        pygame.quit()
