import pygame


class Visual(pygame.sprite.Sprite):
    """when using this class to make menus and screens, you should pass the image as "pygame.image.load("myimage.png").convert()" """

    def __init__(self, name, x, y, width, height, texture, draw_group):
        pygame.sprite.Sprite.__init__(self)
        self.name = name
        self.width = width
        self.height = height
        self.draw_group = draw_group
        self.draw_group.add(self)
        self.rect = pygame.Rect(x, y, width, height, center=(x, y))
        self.image = texture
        try:
            self.image.set_colorkey((0, 0, 0))
        except AttributeError:
            pass
        self.rect.x = x
        self.rect.y = y
        self.child = None
        self.child_x = 0
        self.child_y = 0

    def __str__(self):
        return self.name

    def parent(self, child):
        self.child = child
        self.child_x = child.rect.x - self.rect.x
        self.child_y = child.rect.y - self.rect.y

    def set_image(self, directory):
        self.image = pygame.image.load(directory).convert()
        try:
            self.image.set_colorkey((0, 0, 0))
        except AttributeError:
            pass

    def rotate(self, value):
        x, y = self.image.get_rect().center
        x += self.rect.x
        y += self.rect.y
        self.image = pygame.transform.rotate(self.image, value)
        self.rect = self.image.get_rect(center=(x, y))

    def hide(self):
        self.image = pygame.Surface([64, 32])
        self.image.fill((0, 0, 0))
        self.image.set_colorkey((0, 0, 0))

    def kill(self):
        if self.child is not None:
            self.child.kill()
        pygame.sprite.Sprite.kill(self)

    def update(self):
        pygame.sprite.Sprite.update(self)
        if self.child is not None:
            self.child.rect.x = self.rect.x + self.child_x
            self.child.rect.y = self.rect.y + self.child_y

class Button(Visual):

    def __init__(self, name, x, y, width, height, texture, draw_group, activation_message):
        Visual.__init__(self, name, x, y, width, height, texture, draw_group)
        self.activated = False
        self.activation_message = activation_message

    def action(self, event):
        """if event = click and mouse is over button, set self.activated to True"""


class Menu(Visual):

    def __init__(self, name, x, y, width, height, texture, draw_group):
        Visual.__init__(self, name, x, y, width, height, texture, draw_group)
        self.components = []
        self.component_locations = []

    def add(self, component):
        self.components.append(component)
        self.component_locations.append([component.rect.x, component.rect.y])
        self.draw_group.add(component)

    def remove(self, component):
        del self.component_locations[component]

        self.components[component].kill()
        del self.components[component]

    def update(self):
        for component in self.components:
            component.update()
            coordinates = self.component_locations[self.components.index(component)]
            component.rect.x = coordinates[0] + self.rect.x
            component.rect.y = coordinates[1] + self.rect.y

    def pressed(self):
        pressed_button_messages = []
        for component in self.components:
            if type(component) is Button and component.activated:
                pressed_button_messages.append(component.activation_message)
        return pressed_button_messages

    def kill(self):
        for component in self.components:
            component.kill()
        Visual.kill(self)


class Meter(Visual):

    def __init__(self, name, x, y, width, height, texture, maximum, bar_color, draw_group):
        Visual.__init__(self, name, x, y, width, height, texture, draw_group)
        self.max = maximum
        self.value = maximum
        self.bar_color = bar_color
        bar = pygame.Surface([width - 8, height - 8]).fill(self.bar_color)
        self.bar = Visual("bar", x + 4, y + 4, width - 8, height - 8, bar, draw_group)
        draw_group.add(self.bar)
        self.px_offset = 0
        self.py_offset = 21

    def kill(self):
        self.bar.kill()
        Visual.kill(self)

    def update(self):
        self.bar.image = pygame.Surface([self.value / self.max * (self.width - 8), self.height])
        self.bar.image.fill(self.bar_color)
        self.bar.update()


class Number(Visual):

    def __init__(self, name, x, y, draw_group):

        Visual.__init__(self, name, x, y, 20, 24, pygame.Surface([0, 0]), draw_group)
        self.value = 0
        self.previous_digit = None
        self.next_digit = None

        self.add(0)

    def kill(self):
        if self.next_digit is not None:
            self.next_digit.kill()
        Visual.kill(self)

    def add(self, value):
        if self.value + value > 9:
            self.value += value
            if self.next_digit is None:
                self.next_digit = Number("digit", 0, 0, self.draw_group)
                self.next_digit.value = self.value // 10
                self.next_digit.previous_digit = self
                self.next_digit.add(0)
                self.draw_group.add(self.next_digit)
            else:
                self.next_digit.add(self.value // 10)
            self.value = self.value % 10
        elif self.value + value >= 0:
            self.value += value
        elif self.value + value < 0:
            if self.previous_digit is None:
                self.value += value
                while self.value < 0:
                    self.next_digit.add(-1)
                    self.value += 10
        self.image = pygame.image.load("assets/numbers/" + str(self.value) + ".png")
        self.image.set_colorkey((0, 0, 0))

    def update(self):
        Visual.update(self)
        if self.next_digit is not None:
            self.next_digit.rect.x = self.rect.x - 20
            self.next_digit.rect.y = self.rect.y
        if self.next_digit is None and self.value == 0:
            self.kill()


