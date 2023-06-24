# imports
import pygame
import neat
import time
import os
import random

pygame.font.init()

# screen dimensions
WIN_WIDTH = 500
WIN_HEIGHT = 800

GEN = 0

# load the images from imgs file
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

# sets fonts
STAT_FONT = pygame.font.SysFont("comicsans", 50)


# Bird class represents the bird moving
class Bird:
    # constant variables
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    # (x ,y) represents starting position of the bird
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # how much bird image is tilted
        self.tilt = 0
        # regarding the physics of the bird
        self.tick_count = 0
        # velocity starts at 0(not moving)
        self.vel = 0
        self.height = self.y
        # gives us current which image we are showing of the bird
        self.img_count = 0
        # the actual bird image
        self.img = self.IMGS[0]

    # what we call when we want the bird to jump
    def jump(self):
        # bird image moves at a -10.5 velocity(up) when jump is called
        self.vel = -10.5
        # keeps track of when we last jumped
        self.tick_count = 0
        # keeps track of where the bird last jumped from, where it originally started moving from
        self.height = self.y

    # is called every single frame to move the bird image
    def move(self):
        # adds a tick per frame to keep track of how many times we moved sense the last jump
        self.tick_count += 1

        # equation regarding the spead and tilt of the bird relative to the last jump
        # forms an arc for the bird to follow when jump is called
        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2

        # makes sure that the velocity is no more than 16 so the bird doesn't drop too fast
        if d >= 16:
            d = 16

        # moving the bird a little higher up when jump is called fine-tunes the movement
        if d < 0:
            d -= 2

        # change y position based on displacement
        self.y = self.y + d

        # tilts the bird based off of its movement up or down
        # if bird is going up
        if d < 0 or self.y < self.height + 50:
            # makes sure that the bird won't tilt to far in a sertan direction
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        # if bird is going down
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        # keeps track of the amount of ticks the image has run for
        self.img_count += 1

        # changes the bird image based off of the animation time
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # if the bird id falling(tilt =< -80) it will stay one image to show the bird is no longer flapping wings
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            # when bird does jump it will start with image index 1
            self.img_count = self.ANIMATION_TIME * 2

        # rotates bird based/around the rotating point
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        # moves the rotating point to the center
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        # actually rotates the image
        win.blit(rotated_image, new_rect.topleft)

    # used for collision
    def get_mask(self):
        return pygame.mask.from_surface(self.img)


# pipe class
class Pipe:
    # constant variables
    # space inbetween the pipe
    GAP = 160
    # the speed the pipe is moving
    VEL = 5

    # x represents the position of the pipe and the height will be random
    def __init__(self, x):
        self.x = x
        self.height = 0

        # where the top of the pipe will be drawn
        self.top = 0
        # where the bottom of the pipe will be drawn
        self.bottom = 0
        # top pipe needs to be flipped
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        # Used for collision purposes for the ai
        self.passed = False
        self.set_height()

    # defines where the top and bottom pipe is and the gap
    def set_height(self):
        # sets height of pipe to a random amount
        self.height = random.randrange(40, 450)
        # sets the corresponding heights and gap for both pipes
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    # moves the pipe across the screen
    def move(self):
        # moves pipe to the left each tic according to the velocity
        self.x -= self.VEL

    # draws top and bottom pipes as one
    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    # to detect collision between the bird and pipe
    def collide(self, bird):
        # gets mask
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # calculate how close the two mask are from each other
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # the point of collision for the bottom pipe
        # if no collision it just returns None
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        # the point of collision for the top pipe
        t_point = bird_mask.overlap(top_mask, top_offset)

        # checks of b_point or t_point returns with a collision
        if t_point or b_point:
            return True

        return False


# class for the ground
class Base:
    # constant variables
    # the ground will be moving at the same spead of the pipes
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        # y will not change as the ground does not move up or down
        self.y = y
        # splits the ground img into two separate images
        self.x1 = 0
        self.x2 = self.WIDTH

    # moves the two imgs in correlation to make it look like the ground is moving
    # once one of the imgs is moved off of the screen it will then be cycled back to the right side of the screen
    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # once img 1 reaches a point, it will move to the right side of the screen
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        # once img 2 reaches a point, it will move to the right side of the screen
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    # draws ground img
    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


# shows bird img on top of the window to see what's happening
def draw_window(win, birds, pipes, base, score, gen):
    # shows background image
    win.blit(BG_IMG, (0, 0))
    # draws every pipe on the screen
    for pipe in pipes:
        pipe.draw(win)

    # draws the score
    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    text = STAT_FONT.render("Gen: " + str(gen), 1, (255, 255, 255))
    win.blit(text, (10, 10))

    # draws the base(ground)
    base.draw(win)
    for bird in birds:
        # shows the bird
        bird.draw(win)
    # refresh
    pygame.display.update()


# runs main loop
def eval_genomes(genomes, config):
    global GEN
    GEN += 1
    # list keeps track of each genome(neural network per bird)
    nets = []
    ge = []
    # makes birds object
    birds = []

    # sets up neural network for each genome
    for _, g in genomes:
        # sets initial fitness to be 0
        g.fitness = 0
        # add individual networks to the nets list that corresponds to the genomes and birds lists
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        # add bird to birds list and sets starting position
        birds.append(Bird(230, 350))
        ge.append(g)

    # makes base object and sets it to the bottom of the screen
    base = Base(730)
    # makes pipe object
    pipes = [Pipe(700)]
    # sets window veritable
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    # sets spead of main loop
    clock = pygame.time.Clock()
    # score variable
    score = 0

    # main loop for game
    run = True
    while run and len(birds) > 0:
        # sets loop to run 30 times a second
        clock.tick(30)
        # event loop
        for event in pygame.event.get():
            # ends loop when pygame signals QUIT
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        # pipe index
        pipe_ind = 0
        # defines if the bird has passed the first pipe on the screen so we can then focus on the second pipe for collision
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1

        # will add a little fitness to each bird that has made it this far in the loop
        # encourages the bird to keep moving
        # for every second the bird moves there fitness level will increase
        for x, bird in enumerate(birds):
            ge[x].fitness += 0.1
            bird.move()

            # activate a neural network with our input
            output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            # bird will jump if the output of the neural network gives anything more than 0.5
            if output[0] > 0.5:
                bird.jump()

        # calls bird
        # bird.move()
        # add_pipe is set to false till bird moves past a pipe
        add_pipe = False
        # removed pipe list
        rem = []
        # calls the pipe.move function for every pipe in the pipes list
        for pipe in pipes:
            for x, bird in enumerate(birds):
                # checks for collision with pipe.collide function
                if pipe.collide(bird):
                    # fitness score is lowered for birds that collide with pipe
                    ge[x].fitness -= 1
                    # removes the bird, network and genome associated with the bird
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                # will check if bird has passed the pipe
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            # checks position of the pipe if it's off the screen
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        # adds a new pipe to the pipe list
        if add_pipe:
            # adds a point to the score as the bird passes the pipe
            score += 1
            # increases fitness score for bird that passes the pipe
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))

        # removes the pipe that left the screen from the pipes list
        for r in rem:
            pipes.remove(r)
        for x, bird in enumerate(birds):
            # detects if bird has hit the floor or went too high
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                # removes the bird, network and genome associated with the bird
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)
        # calls the base.move function so the ground looks like its moving
        base.move()
        # calls the draw_window function
        draw_window(win, birds, pipes, base, score, GEN)


# loads in config file
def run(config_path):
    # defines the properties we are setting with the config_path
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)

    # generates a population(collection of bata points) based off of the config file
    p = neat.Population(config)

    # gives output to the counsel with statistics on each iteration
    # optional
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # sets the fitness function to iterate 50 times
    # calls fitness function 50 times and passes all the genomes
    winner = p.run(eval_genomes, 50)


if __name__ == "__main__":
    # gives path to current directory
    local_dir = os.path.dirname(__file__)
    # gives path to exact file
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    # passes path to run function
    run(config_path)
