import pygame
import random

# static reference
materials = ["dirt", "dirt2", "dirt3", "grass", "sand"]
block_attributes = []


class Block(pygame.sprite.Sprite):
    """base block"""

    def __init__(self, material, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        x *= 16
        y *= 16
        self.image = block_attributes[material]
        self.rect = self.image.get_rect()
        width, self.height = self.rect.size

        if self.height == 16:
            offset = 0
        else:
            offset = -8
        self.rect = self.image.get_rect()
        
        self.rect.x = x
        self.rect.y = y + offset

    def kill(self):
        self.rect = pygame.Rect((0, 0), (0, 0))
        pygame.sprite.Sprite.kill(self)


class World:
    """contains blocks and manages them"""

    def __init__(self, length, height, blocks):

        for material in range(len(materials)):
            texture = pygame.image.load("assets/blocks/" + materials[material - 1] + ".png").convert()
            if material == 4:
                texture.set_colorkey((0, 0, 0))
            block_attributes.append(texture)

        self.world = []
        self.blocks = blocks
        self.collision_bounds = {}
        self.length = length
        self.height = height

    """def calculate_collision_bounds(self):
        top = []
        bottom = []
        left = []
        right = []
        for row in range(self.height):
            top_row = []
            bottom_row = []
            left_row = []
            right_row = []
            for column in range(self.length):
                is_block = self.world[row][column] != 0
                if row > 0 and self.world[row - 1][column] == 0:
                    top_row.append(is_block)
                else:
                    top_row.append(False)
                if row < self.height - 1 and self.world[row + 1][column] == 0:
                    bottom_row.append(is_block)
                else:
                    bottom_row.append(False)
                if column > 0 and self.world[row][column - 1] == 0:
                    left_row.append(is_block)
                else:
                    left_row.append(False)
                if column < self.length - 1 and self.world[row][column + 1] == 0:
                    right_row.append(is_block)
                else:
                    right_row.append(False)

            top.append(top_row)
            bottom.append(bottom_row)
            left.append(left_row)
            right.append(right_row)

        self.collision_bounds["top"] = top
        self.collision_bounds["bottom"] = bottom
        self.collision_bounds["left"] = left
        self.collision_bounds["right"] = right
        print("calculated collision bounds")"""

    def load(self, filename):
        """loads an existing file into the self.world matrix"""

        save = open(filename + ".txt", "r").read().split(" ")
        index = 0

        # for each row
        for each in range(self.height):
            column = 0
            row = []

            # typecast the value to an int and decode it
            while column < self.length:
                value = int(save[index])
                index += 1

                # values greater than 10 stand in for multiple of the same block in a row
                if value < 10:
                    row.append(value)
                    column += 1
                else:
                    length = value // 100
                    material = value % (length * 100)
                    for block in range(length):
                        row.append(material)
                        column += 1
            self.world.append(row)

    def generate(self, smoothness):
        """generates the self.world matrix, which manages the terrain"""

        # generation of height map vertices
        points = []
        peaks = []
        horizontal = 0
        while horizontal < self.length:
            points.append(horizontal)
            peaks.append(random.randint(3, 20))
            horizontal += random.randint(1, smoothness)
        if points[len(points) - 1] != self.length - 1:
            points.append(self.length - 1)
            peaks.append(random.randint(3, 10))

        # extrapolation of full height map
        heights = []
        for point in range(len(points) - 1):
            distance = points[point + 1] - points[point]
            delta = (peaks[point + 1] - peaks[point]) / distance
            for index in range(distance + 1):
                heights.append(self.height - (int(delta * index) + peaks[point]))

        # generation of world using height map
        for level in range(self.height):
            row = []
            for column in range(self.length):
                surface = heights[column]
                if level > surface:
                    row.append(random.randint(1, 3))
                elif level == surface:
                    row.append(4)
                else:
                    row.append(0)
            self.world.append(row)

    def initialize(self):
        """uses the self.world matrix to create Block sprites accordingly"""

        for x in range(self.height):
            for y in range(self.length):
                material = self.world[x][y]
                if material != 0:
                    new_block = Block(material, y, x)
                    self.blocks.add(new_block)
        # self.calculate_collision_bounds()

    def destroy(self, x, y, guarantee_radius, secondary_radius):
        """with x, y at the center, guarantee radius is the radius in blocks that are always destroyed
        secondary radius is a larger radius where blocks have a chance to be destroyed"""

        x = x // 16
        y = y // 16

        if 0 <= y < self.height and 0 <= x < self.length:
            broken = self.world[y][x] != 0
        else:
            broken = False

        # checking through block objects and comparing their relative coordinates to determine if they should be destroyed
        for block in self.blocks:
            if (x - guarantee_radius) < (block.rect.x // 16) < (x + guarantee_radius) \
                    and (y - guarantee_radius) < (block.rect.y // 16) < (y + guarantee_radius):

                try:
                    self.world[round((block.rect.y + 4) / 16)][block.rect.x // 16] = 0
                except KeyError or IndexError:
                    pass

                block.kill()

            elif (x - secondary_radius) < (block.rect.x // 16) < (x + secondary_radius) and \
                    (y - secondary_radius) < round((block.rect.y + 4) / 16) < (y + secondary_radius):

                if random.randint(0, 2) != 0:
                    try:
                        self.world[round((block.rect.y + 4) / 16)][block.rect.x // 16] = 0
                    except KeyError or IndexError:
                        pass

                    block.kill()

        # self.calculate_collision_bounds()

        return broken  # informing the caller whether or not any blocks were broken

    def place(self, x, y):
        # add block objects to the scene
        x = x // 16
        y = y // 16
        if self.world[y][x] == 0:
            self.world[y][x] = 1
            block = Block(1, x, y)
            self.blocks.add(block)
            # self.calculate_collision_bounds()
            return True
        else:
            return False
