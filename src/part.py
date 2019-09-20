from src import entity
import pygame

rotation_friction = 2

"""
CLACKLES:

I'm abandoning this class.

I was originally going to rebuild the entire character out of 
components with rotational physics, making the movements look more
realistic and flexible and making things like ragdoll physics possible,
but it seems to complicated for me to want to make it.

Settling for keyframed animation.

If you want to try to make it work, I suppose you could try,
but don't waste too much time on it. I don't know how to
calculate torque from collisions realistically.
"""


class Torso(entity.Entity):

    def __init__(self):

        entity.Entity.__init__(self, 500, 500, 20, 28, 100, 0)
        self.image = pygame.Surface([20, 28])
        self.image.fill((100, 100, 100))
        self.rotation = 0
        self.rotation_velocity = 0
        self.rotation_acceleration = 0

    def update_collisions(self):
        #p1
        return

    def update_position(self):

        entity.Entity.update_position(self)

        self.rotation += self.rotation_velocity
        if self.rotation_velocity > 0:
            self.rotation_velocity -= rotation_friction
        elif self.rotation_velocity < 0:
            self.rotation_velocity += rotation_friction
