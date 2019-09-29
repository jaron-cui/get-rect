import pygame
from src import terrain, display, entity, part, pobject
import random

# global reference, static variables
volume = {"click": .5}
pygame.init()
system_info = pygame.display.Info()


def play_sound(sound, multiplier):
    if sound in volume:
        value = volume[sound]
    else:
        value = 1.0
    value *= multiplier
    effect = pygame.mixer.Sound("assets/sounds/" + sound + str(random.randint(0, 3)) + ".wav")
    effect.set_volume(value)
    if value > 0:
        effect.play()


class GUI:
    """handles the user interface"""

    def __init__(self):

        window = pygame.display.set_mode((system_info.current_w//2, system_info.current_h//2), pygame.RESIZABLE | pygame.DOUBLEBUF)
        background = Background()

        visuals = pygame.sprite.Group()

        music_volume = 1
        sfx_volume = 1

        texture = pygame.Surface([16, 64])
        texture.fill((255, 255, 255))

        music_slider = display.Visual("music_slider", 1340, 110, 16, 64, texture, visuals)
        sfx_slider = display.Visual("sfx_slider", 1340, 290, 16, 64, texture, visuals)

        pygame.mixer.music.load("assets/sounds/title.mp3")
        pygame.mixer.music.play(-1)

        done = False

        while not done:
            # screen is the current menu the user sees
            screen = background.screen

            # sound slider positioning
            music_slider.rect.x = music_volume * 540 + 800
            sfx_slider.rect.x = sfx_volume * 540 + 800

            # background uses volume to make sound when the user navigates
            background.volume = sfx_volume

            pygame.mixer.music.set_volume(music_volume * .5)

            # settings menu
            if screen == "settings1" or screen == "settings2":
                music_slider.image = texture
                sfx_slider.image = texture
            else:
                music_slider.hide()
                sfx_slider.hide()

            # user input
            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    done = True

                # up and down key presses are used to navigate
                elif event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_DOWN:
                        if screen == "title1":
                            background.goto("title2")
                        elif screen == "play1":
                            background.goto("play2")
                        elif screen == "settings1":
                            background.goto("settings2")

                    elif event.key == pygame.K_UP:

                        if screen == "title2":
                            background.goto("title1")
                        elif screen == "play2" or background.screen == "play404":
                            background.goto("play1")
                        elif screen == "settings2":
                            background.goto("settings1")

                    # right and left keys adjust sliders
                    elif event.key == pygame.K_RIGHT:

                        if screen == "settings1" and music_volume < 1:
                            play_sound("click", sfx_volume)
                            music_volume += .1
                        elif screen == "settings2" and sfx_volume < 1:
                            play_sound("click", sfx_volume)
                            sfx_volume += .1

                    elif event.key == pygame.K_LEFT:

                        if screen == "settings1" and music_volume > 0:
                            play_sound("click", sfx_volume)
                            music_volume -= .1
                        elif screen == "settings2" and sfx_volume > 0:
                            play_sound("click", sfx_volume)
                            sfx_volume -= .1

                    # escape always brings the user back to the main screen
                    elif event.key == pygame.K_ESCAPE:
                        background.goto("title1")

                    # enter is used to select buttons
                    elif event.key == pygame.K_RETURN:

                        if screen == "title1":
                            background.goto("play1")
                        elif screen == "title2":
                            background.goto("settings1")
                        elif screen == "play1":

                            # if the user presses generate, the music changes and the game starts
                            pygame.mixer.music.fadeout(1200)
                            pygame.mixer.music.load("assets/sounds/level.mp3")
                            pygame.mixer.music.play(-1)
                            game = Game(window, sfx_volume, visuals)
                            background.goto("title1")
                            pygame.mixer.music.load("assets/sounds/title.mp3")
                            pygame.mixer.music.play(-1)

            window.blit(background.image, background.rect)
            visuals.draw(window)
            pygame.display.update()


class Game:
    """runs the actual game aspect"""

    def __init__(self, window, volume, visuals):

        # entity objects
        particles = pygame.sprite.Group()
        real_entities = pygame.sprite.Group()

        # blocks
        blocks = pygame.sprite.Group()

        # generating the world
        world = terrain.World(system_info.current_w//32, system_info.current_h//32 - 10, blocks)
        world.generate(10)
        world.initialize()
        entity.terrain = world
        pobject.terrain = world

        # player 1 and 2 are spawned
        player1 = entity.Player(200, 0, 100, [particles, visuals, real_entities], 0, 0, "example_player", world, volume)
        player2 = entity.Player(1200, 0, 100, [particles, visuals, real_entities], 600, 0, "sisters_character", world, volume)

        # player 2 has a different keybinding set
        player2.binding = {"left": "LEFT", "right": "RIGHT", "up": "UP", "sprint": "RCTRL", "use": "KP5", "adjust_greater": "KP6", "adjust_lower": "KP4", "escape": "KP7"}

        real_entities.add(player1, player2)
        real_entities.add(part.Torso())
        visuals.add(pobject.pobject())

        # initial crate
        real_entities.add(entity.Crate(600, 0, visuals, volume))

        # message for when game ends
        texture = pygame.Surface([0, 0])
        end_message = display.Visual("end_message", 522, 300, 396, 174, texture, visuals)

        clock = pygame.time.Clock()

        # used to track the ending sequence
        end_counter = -1

        # time between crate spawns
        drop = 1000
        done = False
        player2.add_items("dynamite", 99)
        player2.add_items("fireworks", 99)
        player1.add_items("log", 99)
        player2.add_items("log", 99)
        while not done:
            clock.tick(60)

            # ending sequence
            if end_counter != -1:
                if end_counter == 2000:
                    if player1.alive:
                        message = "player_1.png"
                    else:
                        message = "player_2.png"
                    end_message.set_image("assets/displays/end_messages/" + message)
                    for x in range(100, 1400, 200):
                        real_entities.add(entity.Fireworks(x, 100, True, particles, real_entities, player1))
                elif end_counter == 1500:
                    end_message.set_image("assets/displays/end_messages/trophy.png")
                elif not (player1.alive or player2.alive):
                    if end_counter == 800:
                        end_message.set_image("assets/displays/end_messages/oh.png")
                    elif end_counter == 600:
                        pygame.mixer.music.load("assets/sounds/final.mp3")
                        pygame.mixer.music.play(1)
                        end_message.set_image("assets/displays/end_messages/tie.png")
                elif end_counter == 800:
                    end_message.hide()
                    for each in real_entities:
                        each.kill()
                    return
                if end_counter == 0:
                    end_message.hide()
                    for each in real_entities:
                        each.kill()
                    return
                end_counter -= 1

            drop -= 1

            # randomized drop times and locations
            if drop == 0 and end_counter < 0:
                drop = random.randint(240, 1000)
                real_entities.add(entity.Crate(random.randint(0, 1000), 0, visuals, volume))

            # initiate end sequence if a player dies
            if (player1.health <= 0 or player2.health <= 0) and end_counter == -1:
                end_counter = 2000
                pygame.mixer.music.fadeout(1200)
                pygame.mixer.music.load("assets/sounds/win.mp3")
                pygame.mixer.music.play()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    end_message.kill()
                    for each in real_entities:
                        each.kill()
                    return
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    for each in real_entities:
                        print(each.hitbox_y)

                # players are given the events if they are alive
                if player1.alive:
                    player1.action(event)
                if player2.alive:
                    player2.action(event)

            # collisions between blocks and entities passed to entities
            for hitbox in real_entities:
                try:
                    collisions = pygame.sprite.groupcollide(real_entities, real_entities, False, False)[hitbox]
                except KeyError:
                    collisions = []
                hitbox.entities = collisions

            # sky color

            window.fill((200, 255, 255))

            visuals.update()
            particles.update()
            real_entities.update()

            particles.draw(window)
            real_entities.draw(window)
            blocks.draw(window)
            visuals.draw(window)


            pygame.display.update()


class Background:
    """runs the background"""

    def __init__(self):
        self.image = pygame.image.load("assets/displays/menus/title1.png")
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = [0, 0]
        self.screen = "title1"
        self.volume = 1

    def goto(self, name):
        play_sound("click", self.volume)
        self.image = pygame.image.load("assets/displays/menus/" + name + ".png")
        self.screen = name


def main():
    main_window = GUI()


main()
