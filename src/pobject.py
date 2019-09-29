import pygame, math

terrain = []
friction = .1
elasticity = .4


def sign(value):
    if value < 0:
        return -1
    else:
        return 1


def to_angle(coordinates):
    x, y = coordinates
    return math.atan(y / x)


def to_xy(angle):
    x = math.cos(angle)
    y = math.sin(angle)
    return x, y


def rotate_xy(coordinates, rotation):
    angle = to_angle(coordinates)
    return to_xy(angle + rotation)


def radius(coordinates):
    x, y = coordinates
    return (x**2 + y**2)**.5


class pobject(pygame.sprite.Sprite):

    def __init__(self):

        pygame.sprite.Sprite.__init__(self)
        self.texture = pygame.image.load("assets/animations/example_player/0.png")
        # self.texture.fill((255, 255, 200))
        self.image = self.texture.copy()
        self.rect = self.texture.get_rect()
        self.x_velocity = 0
        self.y_velocity = 0
        self.rotational_velocity = 0
        self.rotation = math.pi / 4
        self.points = [(0, 0), (0, 40), (10, 0), (10, 40)]
        self.center = 5, 20

        self.rect.x, self.rect.y = 500, 400

    def colliding(self):

        for point in self.points:

            x, y = point
            center_x, center_y = self.center
            coordinates = x + center_x, y + center_y
            x, y = rotate_xy(coordinates, self.rotation)
            try:
                if terrain.world[int((self.rect.y - y) // 16 + 1)][int((self.rect.x + x) // 16)] != 0:
                    self.rect.y = self.rect.y // 16 * 16
                    angle = to_angle(coordinates) + self.rotation
                    magnitude = sign(x) * math.tan(angle) * radius((x, y))
                    horizontal_velocity = math.cos(angle) * self.rotational_velocity + self.x_velocity
                    vertical_velocity = self.rotational_velocity / math.sin(angle) + self.y_velocity
                    horizontal_rebound = horizontal_velocity * elasticity
                    vertical_rebound = vertical_velocity * elasticity
                    angular_rebound = -horizontal_velocity * friction / math.cos(angle) * elasticity
                    self.x_velocity = horizontal_rebound * (1 - friction)
                    self.y_velocity = -vertical_rebound
                    self.rotational_velocity = -angular_rebound
            except IndexError:
                pass
        if 0 <= x < len(terrain.world[0]) and 0 <= y < len(terrain.world) and terrain.world[int(y)][int(x)] != 0:
            print("colliding")
        """c = ""
        for each in terrain["top"]:
            for row in each:
                if row:
                    c = "w"
        print(c)"""

    def update(self):

        if -20 < self.y_velocity:
            self.y_velocity -= .2
        x, y = self.center
        print(math.degrees(self.rotation))
        self.image = pygame.transform.rotate(self.texture, math.degrees(self.rotation))
        self.colliding()
        self.rect.x += self.x_velocity
        self.rect.y -= self.y_velocity
        self.rotation += self.rotational_velocity
