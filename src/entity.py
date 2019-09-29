import pygame
import random
import math
from src import display

# constants
friction = .2
walk_speed = 5
run_speed = 12
walk_accel = .5
run_accel = 1
gravity = -1
fall_limit = -40

volume = {"soft_land": .15, "hard_land": .5, "slash": 2, "crate_hit": .5, "equip_trowel": .25, "trowel_dig": .5,  "trowel_fail": .5}
terrain = None


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


class Entity(pygame.sprite.Sprite):

    def __init__(self, x, y, width, height, health, volume):

        # basic sprite setup
        pygame.sprite.Sprite.__init__(self)
        self.rect = pygame.Rect((x, y), (width, height), center=(x, y))

        self.rect.x = x
        self.rect.y = y

        self.hitbox_x = int(width / 2)
        self.hitbox_y = int(height / 2)

        # custom properties
        self.real_x = self.rect.x
        self.real_y = self.rect.y

        self.vel_x = 0.0
        self.vel_y = 0.0

        self.animation = 0
        self.right = True

        self.health = health

        self.source = None

        self.volume = volume

        # collisions
        self.entities = []

        self.parachute = None

    def engage_parachute(self, visual_draw_group):
        """for parachuting crates"""
        self.push(5, -5)
        texture = pygame.image.load("assets/animations/parachute/0.png").convert()
        self.parachute = display.Visual("parachute", self.rect.x, self.rect.y, 41, 64, texture, visual_draw_group)

    def push(self, x_impulse, y_impulse):
        self.vel_x += x_impulse
        self.vel_y += y_impulse

    def damage(self, amount, source):
        self.health += amount
        self.source = source

    def update_collisions(self):
        """handles any collisions with Block sprites"""

        # handles collisions with blocks on the left
        if self.colliding("-x") and self.vel_x < 0:
            y = self.real_y + 0
            dy = 0
            while self.colliding("-x") and dy < 8:
                self.real_y += 1
                dy += 1
            self.real_y = y
            if dy == 8:
                self.vel_x = int(-.25 * self.vel_x)
                self.real_x = math.ceil((self.rect.x + self.hitbox_x) / 16) * 16 - 2 * self.hitbox_x - 1

        # handles collisions with blocks on the right
        if self.colliding("+x") and self.vel_x > 0:
            y = self.real_y + 0
            dy = 0
            while self.colliding("+x") and dy < 8:
                self.real_y += 1
                dy += 1
            self.real_y = y
            if dy == 8:
                self.vel_x = int(-.25 * self.vel_x)
                self.real_x = math.ceil((self.rect.x + self.hitbox_x) / 16) * 16 - 2 * self.hitbox_x + 1

        # handles falling
        if self.colliding("-y") and self.vel_y < 0:
            if self.vel_y < -30:
                play_sound("hard_land", self.volume)
                self.damage(int(self.vel_y + 30), None)
            else:
                play_sound("soft_land", self.volume)
            self.vel_y = 0
            self.real_y -= (self.real_y + self.hitbox_y) % 16 - 1
            if self.hitbox_y < 16:
                self.real_y += 16 - self.hitbox_y
        elif not self.colliding("-y") and self.vel_y > fall_limit:
            self.vel_y += gravity

        # handles collisions with blocks above
        if self.colliding("+y") and self.vel_y > 0:
            self.vel_y = -.5 * self.vel_y
            self.real_y = math.floor(self.rect.y / 16) * 16 + self.hitbox_y

        if self.colliding("-x") and self.vel_x < 0:
            self.vel_x = int(-.25 * self.vel_x)
        if self.colliding("+x") and self.vel_x > 0:
            self.vel_x = int(-.25 * self.vel_x)

    def colliding(self, direction):
        """tests for collisions against blocks in specific orientations"""

        lower_x = (self.rect.x - self.hitbox_x + 8) // 16
        upper_x = (self.rect.x + self.hitbox_x + 7) // 16
        lower_y = int((self.rect.y + 2 * self.hitbox_y) // 16)
        upper_y = self.rect.y // 16
        try:
            if direction == "+x":
                return terrain.world[lower_y - 1][upper_x] != 0 or terrain.world[upper_y][upper_x] != 0
            elif direction == "-x":
                return terrain.world[lower_y - 1][lower_x] != 0 or terrain.world[upper_y][lower_x] != 0
            elif direction == "+y":
                return terrain.world[upper_y][lower_x] != 0 or terrain.world[upper_y][upper_x] != 0
            elif direction == "-y":
                return terrain.world[lower_y][lower_x] != 0 or terrain.world[lower_y][upper_x] != 0
        except IndexError:
            return False

    def friction(self):

        if self.vel_x > 0:
            self.vel_x -= friction
        elif self.vel_x < 0:
            self.vel_x += friction

    def update_position(self):
        """updates the virtual and display coordinates"""

        self.update_collisions()

        self.real_x += (self.vel_x / 10)
        self.rect.x = int(self.real_x)
        self.real_y -= (self.vel_y / 5)
        self.rect.y = int(self.real_y)

        if abs(self.vel_x) < .5:
            self.vel_x = 0

    def update(self):

        self.friction()

        self.update_position()

        try:
            if self.parachute is not None:
                self.push(.2, 1)
                self.parachute.rect.x = self.rect.x - 12
                self.parachute.rect.y = self.rect.y - 64
            if self.colliding("-y"):
                self.parachute.kill()
                self.parachute = None
        except AttributeError:
            pass


class Player(Entity):

    def __init__(self, x, y, health, draw_groups, hotbar_x, hotbar_y, skin, world, volume):
        # basic sprite setup
        Entity.__init__(self, x, y, 16, 30, health, volume)

        # custom properties
        self.accel_x = 0
        self.speed_limit = walk_speed
        self.accel_limit = walk_accel
        self.skin = skin
        self.terrain = world
        self.alive = True

        # setting up ground particles
        self.particle_draw_group = draw_groups[0]
        self.particles = Particles(self, [(200, 150, 100), (60, 140, 60), (150, 100, 100)], self.particle_draw_group)
        self.px_offset = 8
        self.py_offset = 30

        # setting up health bar
        self.visual_draw_group = draw_groups[1]
        texture = pygame.image.load("assets/displays/health.png").convert()
        bar_color = (150, 30, 30)
        self.health_bar = display.Meter("health_bar", hotbar_x + 40, hotbar_y + 40, 408, 42, texture, self.health, bar_color, self.visual_draw_group)
        self.health_bar_particles = Particles(self.health_bar, [(150, 30, 30)], self.particle_draw_group)

        self.force_group = draw_groups[2]

        # inventory
        self.items = []
        self.quantities = {}
        self.item_mode = 0
        self.selected = 0
        self.charge = 0
        self.cooldown = 0
        self.projectile_aim = 0
        self.place_aim = 0
        self.trowel_capacity = 0
        self.trowel_digging = True
        self.adjusting_greater = False
        self.adjusting_lower = False
        self.natural_regeneration = 0
        self.damage_indicator_timer = 0

        # inventory visuals
        texture = pygame.image.load("assets/displays/hotbar.png").convert()
        self.hotbar = display.Menu("hotbar", hotbar_x + 40, hotbar_y + 100, 364, 50, texture, self.visual_draw_group)
        texture = pygame.image.load("assets/displays/selected_slot.png").convert()
        self.hotbar.add(display.Visual("selected_slot", 372, 0, 64, 64, texture, self.visual_draw_group))
        texture = pygame.image.load("assets/displays/selection_arrow.png").convert()
        self.hotbar.add(display.Visual("selection_arrow", 0, 0, 48, 24, texture, self.visual_draw_group))

        self.reselect_item(0)

        texture = pygame.Surface([64, 32])
        texture.fill((0, 0, 0))
        self.guide = display.Visual("guide", self.rect.x, self.rect.y, 64, 32, texture, self.visual_draw_group)
        self.indicator = display.Visual("indicator", self.rect.x, self.rect.y - 20, 17, 12, texture, self.visual_draw_group)
        self.item_type = {"sword": "melee",
                          "arrows": "projectile",
                          "explosive_arrows": "projectile",
                          "trowel": "trowel",
                          "dirt": "trowel",
                          "dynamite": "throwable",
                          "rubber_arrows": "projectile",
                          "fireworks": "throwable",
                          "pebbles": "throwable",
                          "log": "throwable"}

        self.add_items("sword", 1)
        self.add_items("trowel", 1)
        self.add_items("arrows", 8)
        self.add_items("explosive_arrows", 3)

        # keybindings
        self.binding = {"left": "a", "right": "d", "up": "w", "sprint": "LSHIFT", "use": "f", "adjust_greater": "e", "adjust_lower": "q", "escape": "r"}

    def kill(self):
        self.particles.kill()
        self.health_bar.bar.kill()
        self.health_bar.kill()
        self.health_bar_particles.kill()
        self.hotbar.kill()
        self.indicator.kill()
        self.guide.kill()
        if self.parachute is not None:
            self.parachute.kill()
        Entity.kill(self)

    def action(self, event):
        """responds to events collected by the event loop"""

        def key(value):
            return event.key == getattr(pygame, "K_" + self.binding[value])

        if event.type == pygame.KEYDOWN:
            if key("left"):
                self.right = False
                self.accel_x -= walk_accel
            elif key("right"):
                self.right = True
                self.accel_x += walk_accel
            elif key("up"):
                if self.colliding("-y"):
                    self.vel_y = abs(self.vel_x) * .7 + 14
                    self.particles.spawn(4, (2, 2), 12, 4, True)
            elif key("sprint"):
                self.speed_limit = run_speed
                self.accel_limit = run_accel
            elif key("use"):
                item_type = self.item_type[self.items[self.selected]]
                if item_type == "melee" or item_type == "throwable":
                    self.use_item()
                elif item_type == "trowel":
                    if self.item_mode == 0:
                        play_sound("equip_trowel", self.volume)
                        self.item_mode = 1
                    elif self.item_mode == 1:
                        self.use_item()
                elif item_type == "projectile":
                    if self.item_mode == 0:
                        self.item_mode = 1
                    elif self.item_mode == 1:
                        self.item_mode = 2
                        self.charge = 1
            elif key("escape"):
                self.item_mode = 0
            if self.item_mode == 0:
                if key("adjust_greater"):
                    self.reselect_item(1)
                elif key("adjust_lower"):
                    self.reselect_item(-1)
            else:
                if key("adjust_lower"):
                    self.adjusting_greater = True
                elif key("adjust_greater"):
                    self.adjusting_lower = True
                    return

        elif event.type == pygame.KEYUP:
            if key("left"):
                self.accel_x += walk_accel
            elif key("right"):
                self.accel_x -= walk_accel
            elif key("sprint"):
                self.speed_limit = walk_speed
                self.accel_limit = walk_accel
            elif self.item_mode > 0:
                if self.item_type[self.items[self.selected]] == "projectile" and key("use") and self.item_mode == 2:
                    self.use_item()
                    self.charge = 0
                    self.item_mode = 1
                    self.guide.hide()
                elif key("adjust_lower"):
                    self.adjusting_greater = False
                elif key("adjust_greater"):
                    self.adjusting_lower = False

    def use_item(self):
        """initiates the appropriate response when the player successful uses an item"""

        item = self.items[self.selected]
        if item == "sword":
            if self.cooldown == 0:
                play_sound("slash", self.volume)
                self.cooldown = -15
                x = self.rect.x + 8
                if self.right:
                    x += 10
                else:
                    x -= 10
                self.force_group.add(Force(x, self.rect.y + 18, self, 12, 10, False, True, self.right, 12, 12, self))
            else:
                play_sound("trowel_fail", self.volume * .5)
        elif item == "arrows":
            self.force_group.add(Arrow(self.rect.x, self.rect.y + 16, self.projectile_aim, (self.charge / 2) + 20, self.force_group, self))
            self.add_items("arrows", -1)
        elif item == "explosive_arrows":
            self.force_group.add(ExplosiveArrow(self.rect.x, self.rect.y + 16, self.projectile_aim, (self.charge / 2) + 20, self.force_group, self.particle_draw_group, self.terrain, self))
            self.add_items("explosive_arrows", -1)
        elif item == "rubber_arrows":
            self.force_group.add(RubberArrow(self.rect.x, self.rect.y + 16, self.projectile_aim, (self.charge / 2) + 20, self.force_group, self))
            self.add_items("rubber_arrows", -1)
        elif item == "dynamite":
            self.force_group.add(Dynamite(self.rect.x, self.rect.y, self.right, self.particle_draw_group, self.force_group, self.terrain, self))
            self.add_items("dynamite", -1)
        elif item == "fireworks":
            self.force_group.add(Fireworks(self.rect.x, self.rect.y, self.right, self.particle_draw_group, self.force_group, self))
            self.add_items("fireworks", -1)
        elif item == "log":
            self.force_group.add(Log(self.rect.x, self.rect.y, self.right, self))
            self.add_items("log", -1)
        elif self.item_type[item] == "trowel":
            if 15 < self.projectile_aim < 60:
                offset = (20, 0)
            elif 60 <= self.projectile_aim < 135:
                offset = (0, -12)
            elif 135 <= self.projectile_aim < 165:
                offset = (-20, 0)
            elif 165 <= self.projectile_aim < 240:
                offset = (-20, 15)
            elif 240 <= self.projectile_aim < 300:
                offset = (0, 24)
            else:
                offset = (20, 15)
            dx, dy = offset
            if item == "trowel":
                if terrain.destroy(self.rect.x + dx + 8, self.rect.y + dy + 8, 1, 1):
                    play_sound("trowel_dig", self.volume)
                    self.trowel_capacity += 1
                    if self.trowel_capacity == 4:
                        self.hotbar.components[self.items.index("trowel") + 2].set_image("assets/items/dirt.png")
                        self.items[self.items.index("trowel")] = "dirt"
                else:
                    play_sound("trowel_fail", self.volume)
            else:
                if terrain.place(self.rect.x + dx + 8, self.rect.y + dy + 8):
                    play_sound("place_block", self.volume)
                    self.trowel_capacity -= 1
                    if self.trowel_capacity == 0:
                        self.hotbar.components[self.items.index("dirt") + 2].set_image("assets/items/trowel.png")
                        self.items[self.items.index("dirt")] = "trowel"

    def reselect_item(self, change):
        play_sound("click", self.volume * .1)
        self.selected += change
        if self.selected < 0:
            self.selected = len(self.items)-1
        elif self.selected > len(self.items)-1:
            self.selected = 0
        self.hotbar.component_locations[1] = (self.selected * 45 - 3, -5)

    def add_items(self, item, quantity):
        if item in self.items and self.quantities[item] + quantity >= 0:
            self.quantities[item] += quantity
            self.hotbar.components[self.items.index(item) + 2].child.add(quantity)
            if self.quantities[item] == 0:
                for each in range(self.items.index(item) + 3, len(self.hotbar.component_locations)):
                    self.hotbar.component_locations[each][0] -= 45
                self.hotbar.remove(self.items.index(item) + 2)
                self.items.remove(item)
                del self.quantities[item]
                self.reselect_item(-1)

        elif len(self.items) < 8 and quantity > 0:
            self.items.append(item)
            self.quantities[item] = quantity
            texture = pygame.image.load("assets/items/" + item + ".png")
            item_visual = display.Visual(item, (len(self.items) - 1) * 45 - 7, -7, 32, 32, texture, self.visual_draw_group)
            item_number = display.Number("item", (len(self.items) - 1) * 45 + 24, 56, self.visual_draw_group)
            item_number.add(quantity)
            item_visual.parent(item_number)

            self.hotbar.add(item_visual)

    def damage(self, amount, source):
        self.health += amount
        if self.health < 1:
            self.health = 0

        self.health_bar.value = self.health
        self.health_bar.px_offset = self.health_bar.value / self.health_bar.max * (self.health_bar.width - 8)
        if amount < 0:
            self.health_bar_particles.spawn(20, (2, 2), 20, 4, False)
            self.damage_indicator_timer = -24
            play_sound("damage", self.volume)
        else:
            self.damage_indicator_timer = 24
        if self.health == 0:
            self.alive = False
            self.despawn = 300

    def update_movement_particles(self):
        if ((self.vel_x > 0) != (self.accel_x > 0)) and self.accel_x != 0 and abs(self.vel_x) < 1 and self.colliding("-y"):
            self.particles.spawn(3, (2, 2), 16, 4, True)

        if self.colliding("-y") and self.vel_y < 0:
            self.particles.spawn(int((abs(self.vel_y) - 5) / 4), (2, 2), int((abs(self.vel_y)) / 2), 4, True)

    def update_item_state(self):
        """keeps track of the visuals of using items"""

        item_type = self.item_type[self.items[self.selected]]

        self.guide.rect.x = self.rect.x - 24
        self.guide.rect.y = self.rect.y

        # icons when the player uses an item
        if self.item_mode > 0:
            if item_type == "projectile":
                self.guide.set_image("assets/displays/icons/bow/" + str(self.charge // 15) + ".png")
                self.guide.rotate(self.projectile_aim)
            elif item_type == "trowel":
                self.guide.set_image("assets/displays/icons/trowel/" + self.items[self.selected] + ".png")
                self.guide.rotate(self.projectile_aim)
        elif self.cooldown < 0:
            self.guide.set_image("assets/displays/icons/sword/" + str((self.cooldown + 15)//3) + ".png")
            if not self.right:
                self.guide.image = pygame.transform.flip(self.guide.image, True, False)
        else:
            self.guide.hide()

        indicator_offset = 34 - abs(self.damage_indicator_timer)

        # indicators for the player
        if self.damage_indicator_timer > 0:
            self.indicator.set_image("assets/displays/indicators/healing_indicator.png")
        elif self.damage_indicator_timer < 0:
            self.indicator.set_image("assets/displays/indicators/damage_indicator.png")
        elif self.item_mode > 0:
            self.indicator.set_image("assets/displays/indicators/rotation_indicator.png")
            indicator_offset = 20
        else:
            self.indicator.hide()

        self.indicator.rect.x = self.rect.x
        self.indicator.rect.y = self.rect.y - indicator_offset

        # trowel aim and usage
        if item_type == "projectile" or item_type == "trowel":
            if self.adjusting_greater:
                self.projectile_aim += 4
            if self.adjusting_lower:
                self.projectile_aim -= 4
            if self.projectile_aim > 360:
                self.projectile_aim = 4
            if self.projectile_aim < 0:
                self.projectile_aim = 356

        # bow charge
        if 0 < self.charge < 89:
            self.charge += 1

        # sword cooldown
        if self.cooldown == -1:
            self.cooldown = 60
        elif self.cooldown > 0:
            self.cooldown -= 1
        elif self.cooldown < 0:
            self.cooldown += 1

        if self.damage_indicator_timer > 0:
            self.damage_indicator_timer -= 1
        elif self.damage_indicator_timer < 0:
            self.damage_indicator_timer += 1

    def update_animation(self):
        """manages the animation of the player depending on location and movement"""

        self.animation += 1
        if self.animation == 28:
            self.animation = 0
        if not self.colliding("-y"):
            mode = 3
        elif abs(self.vel_x) < 2:
            mode = 0
        elif abs(self.vel_x) < 7:
            mode = 1
        elif abs(self.vel_x) > 6:
            mode = 2
        frame = self.animation // 7

        self.image = pygame.image.load("assets/animations/" + self.skin + "/" + str(frame + (mode * 4)) + ".png").convert()
        if not self.right:
            self.image = pygame.transform.flip(self.image, True, False)
        self.image.set_colorkey((0, 0, 0))

    def update(self):

        # instant kill if the player falls into the void
        if self.rect.y > 2000 and self.alive:
            self.damage(-100, self)

        # friction is applied if the Player stops accelerating or if velocity is over the current limit
        if self.accel_x == 0 or (abs(self.vel_x) > abs(self.speed_limit + self.accel_limit)):
            self.friction()

        # the Player is accelerated if velocity is not yet at its limit or if acceleration is in the opposite direction
        if (abs(self.vel_x) < abs(self.speed_limit)) or ((self.vel_x > 0) != (self.accel_x > 0)):
            self.vel_x += self.accel_x

        self.update_movement_particles()

        self.update_position()

        if self.alive:

            self.natural_regeneration += 1
            if self.natural_regeneration > 320:
                if self.health < 100:
                    self.damage(1, self)
                self.natural_regeneration = 0

            self.update_item_state()

            self.update_animation()
        else:
            self.despawn -= 1
            if self.despawn == 0:

                self.kill()


class Crate(Entity):
    """creates random items for players to use once broken"""

    def __init__(self, x, y, visual_draw_group, volume):

        Entity.__init__(self, x, y, 20, 21, 30, volume)
        self.loot_table = [("arrows", 12), ("rubber_arrows", 6), ("explosive_arrows", 5), ("log", 1),
                           ("dynamite", 5), ("fireworks", 10)]
        self.engage_parachute(visual_draw_group)
        self.decay = 0

    def kill(self):
        if self.parachute is not None:
            self.parachute.kill()
        Entity.kill(self)

    def damage(self, amount, source):
        Entity.damage(self, amount, source)
        if amount < -6:
            play_sound("crate_hit", self.volume)
            self.decay = -600

    def update(self):
        Entity.update(self)
        self.decay += 1
        if self.decay > 100:
            self.decay = 0
            self.damage(-1, self)
        if self.health < 0:
            item, quantity = self.loot_table[random.randint(0, len(self.loot_table) - 1)]
            try:
                self.source.add_items(item, random.randint(1, quantity))
            except AttributeError:
                pass
            if self.parachute is not None:
                self.parachute.kill()
                self.parachute = None
            self.kill()
            return
        self.image = pygame.image.load("assets/animations/crate/" + str(int((30 - self.health) // 8)) + ".png")


class Arrow(Entity):

    def __init__(self, x, y, angle, force, force_group, source):

        Entity.__init__(self, x, y, 14, 3, 8, 1)
        self.source = source
        self.angle = angle
        self.force_group = force_group
        self.image = pygame.image.load("assets/animations/arrow.png")
        self.push(force * math.cos(math.radians(angle)), force * math.sin(math.radians(angle)))
        self.life = 1000

    def hit(self):
        self.force_group.add(
            Force(self.rect.x, self.rect.y, self, 12, 12, False, True, math.cos(self.angle) > 0, 16, 24, self.source))
        self.kill()

    def update(self):
        # the arrow has a short grace period so it doesn't strike the shooter

        if self.life > 0:
            self.life -= 1
        else:
            self.kill()
        if not(self.colliding("+x") or self.colliding("-x") or self.colliding("+y") or self.colliding("-y")):
            Entity.update(self)
            if self.life < 990 and len(self.entities) > 1:
                hit = False
                for entity in self.entities:
                    if type(entity) != Arrow:
                        hit = True
                if hit:
                    self.hit()

            # manage visual rotation
            x, y = self.image.get_rect().center
            x += self.rect.x
            y += self.rect.y

            try:
                self.image = pygame.transform.rotate(pygame.image.load("assets/animations/arrow.png"), math.degrees(math.atan(self.vel_y/self.vel_x)))
                self.rect = self.image.get_rect(center=(x, y))
            except ZeroDivisionError:
                pass


class RubberArrow(Arrow):

    def __init__(self, x, y, angle, force, force_group, source):

        Arrow.__init__(self, x, y, angle, force, force_group, source)

    def hit(self):
        self.force_group.add(
            Force(self.rect.x, self.rect.y, self, 12, 12, False, True, math.cos(self.angle) > 0, 30, 24, self.source))
        self.kill()


class Log(Entity):

    def __init__(self, x, y, right, source):

        Entity.__init__(self, x, y, 14, 14, 60, 1)
        self.source = source
        self.image = pygame.image.load("assets/animations/log.png")
        self.life = 1000
        if right:
            x = 10
        else:
            x = -10
        self.push(x, 10)

    def update(self):
        Entity.update(self)
        if self.vel_x > 0:
            x = .25
        else:
            x = -.25
        self.push(x, 0)
        self.life -= 1
        if self.life < 980:
            for entity in self.entities:
                if entity is not self:
                    if type(entity) is Log:
                        if entity.rect.x > self.rect.x:
                            self.rect.x = entity.rect.x - 14
                            self.push(-3, 4)
                        else:
                            self.rect.x = entity.rect.x + 14
                            self.push(3, 4)
                    else:
                        entity.damage(-1, self.source)
                        if self.vel_x > 0:
                            x = 3
                        else:
                            x = -3
                        entity.push(x, 2)
        if self.life < 0:
            self.kill()


class Explosive(Entity):
    """base class for explosives; handles explosion visuals and force"""

    def __init__(self, x, y, width, height, particle_group, force_group, source):

        Entity.__init__(self, x, y, width, height, 100, 1)
        self.source = source
        self.fuse = 0
        self.particle_group = particle_group
        self.force_group = force_group
        self.sparks = Particles(self, [(255, 255, 255), (255, 255, 0), (255, 150, 0)], particle_group)
        self.explosion = Particles(self, [(255, 255, 255), (200, 200, 200), (160, 160, 160), (125, 125, 125), (100, 100, 100), (255, 255, 0)], self.particle_group)

    def detonate(self, p_num, s_num, p_size, s_size, p_force, s_force, force_size, destructive, knockback, damage):
        play_sound("explosion", self.volume)
        self.explosion.spawn(p_num, (p_size, p_size), p_force, p_force, True)
        self.explosion.spawn(s_num, (s_size, s_size), s_force, s_force, True)
        self.force_group.add(Force(self.rect.x, self.rect.y, self, force_size, force_size, destructive, False, False, knockback, damage, self.source))

    def kill(self):
        self.sparks.kill()
        self.explosion.kill()
        Entity.kill(self)


class ExplosiveArrow(Arrow, Explosive):
    """uses the Arrow class for majority but uses the explosion from the Explosive class"""

    def __init__(self, x, y, angle, force, force_group, particle_group, terrain, source):

        Arrow.__init__(self, x, y, angle, force, force_group, source)
        self.terrain = terrain
        self.px_offset = 0
        self.py_offset = 0
        self.force_group = force_group
        self.particle_group = particle_group
        self.sparks = Particles(self, [(255, 255, 255), (255, 255, 0), (255, 150, 0)], self.particle_group)
        self.explosion = Particles(self, [(255, 255, 255), (200, 200, 200), (160, 160, 160), (125, 125, 125), (100, 100, 100), (255, 255, 0)], self.particle_group)

    def hit(self):
        self.py_offset = 32
        self.detonate(15, 40, 3, 2, 20, 40, 150, False, 30, 20)
        terrain.destroy(self.rect.x, self.rect.y, 2, 3)
        self.kill()

    def update(self):
        Arrow.update(self)
        if self.colliding("+x") or self.colliding("-x") or self.colliding("+y") or self.colliding("-y"):
            self.hit()
        self.sparks.spawn(1, (2, 2), 8, 4, True)


class Dynamite(Explosive):

    def __init__(self, x, y, right, particle_group, force_group, terrain, source):

        Explosive.__init__(self, x, y, 11, 30, particle_group, force_group, source)
        x = 20
        if not right:
            x = -20
        self.image = pygame.image.load("assets/animations/dynamite/0.png")
        self.push(x, 10)
        self.px_offset = 0
        self.py_offset = -8
        self.terrain = terrain

    def update(self):
        if self.fuse == 208:
            self.py_offset = 32
            self.detonate(15, 40, 3, 2, 20, 40, 150, True, 40, 40)
            terrain.destroy(self.rect.x, self.rect.y, 2, 3)
            self.kill()
        else:
            Entity.update(self)
            self.image = pygame.image.load("assets/animations/dynamite/" + str(self.fuse // 8) + ".png")
            self.sparks.spawn(1, (2, 2), 8, 4, True)
            self.fuse += 1


class Fireworks(Explosive):
    """is an explosive itself but also creates more explosives"""

    def __init__(self, x, y, right, particle_group, force_group, source):

        Explosive.__init__(self, x, y, 22, 15, particle_group, force_group, source)
        self.source = source
        x = 10
        if not right:
            x = -10
        self.push(x, 10)
        self.image = pygame.image.load("assets/animations/fireworks/0.png")
        self.px_offset = -6
        self.py_offset = 0
        self.explosion.colors = [(255, 140, 0), (255, 255, 255), (0, 0, 255)]

    def update(self):
        Entity.update(self)
        if self.fuse < 272:
            self.image = pygame.image.load("assets/animations/fireworks/" + str(self.fuse // 8) + ".png")
        elif self.fuse == 280:
            self.image = pygame.image.load("assets/animations/fireworks/34.png")
            self.force_group.add(Firework(self.rect.x + 8, self.rect.y - 8, "red_firework", 20, 30, self.particle_group, self.force_group, self.source))
        elif self.fuse == 310:
            self.image = pygame.image.load("assets/animations/fireworks/35.png")
            self.force_group.add(Firework(self.rect.x + 8, self.rect.y - 8, "green_firework", -10, 50, self.particle_group, self.force_group, self.source))
        elif self.fuse == 345:
            self.image = pygame.image.load("assets/animations/fireworks/36.png")
            self.force_group.add(Firework(self.rect.x + 8, self.rect.y - 8, "blue_firework", -30, 40, self.particle_group, self.force_group, self.source))
        elif self.fuse == 450:
            self.image = pygame.image.load("assets/animations/fireworks/37.png")
            self.px_offset = 16
            self.py_offset = 32
            self.detonate(10, 20, 3, 2, 10, 20, 60, False, 15, 10)
        elif self.fuse > 520:
            self.kill()
        self.fuse += 1


class Firework(Explosive):

    def __init__(self, x, y, name, angle, duration, particle_group, force_group, source):

        Explosive.__init__(self, x, y, 5, 15, particle_group, force_group, source)
        self.push(-angle, 60)
        self.image = pygame.transform.rotate(pygame.image.load("assets/animations/fireworks/" + name + ".png"), angle)
        self.name = name
        self.fuse = duration
        self.px_offset = 0
        self.py_offset = 8

    def update(self):
        Entity.update(self)
        self.fuse -= 1
        if self.fuse == 0:
            if self.name == "red_firework":
                colors = [(255, 0, 0), (255, 70, 70), (255, 255, 255)]
            elif self.name == "green_firework":
                colors = [(60, 255, 160), (200, 255, 200), (255, 255, 255)]
            else:
                colors = [(40, 190, 255), (255, 255, 255)]
            self.explosion.colors = colors
            self.detonate(20, 40, 3, 2, 20, 40, 100, False, 15, 10)
            self.kill()
        self.sparks.spawn(1, (2, 2), 0, 4, True)


class Particles(Entity):
    """source of particles for visual effect"""

    def __init__(self, parent, colors, draw_group):

        Entity.__init__(self, 0, 0, 2, 2, 0, 0)
        self.rect = pygame.Rect((0, 0), (10, 10), center=(0, 0))
        self.image = pygame.Surface([0, 0])

        self.parent = parent
        self.colors = colors
        self.draw_group = draw_group

    def spawn(self, number, size, force, variance, vertical):
        """spawns number particles of size with randomized velocities and directions based on parameters"""

        self.goto()

        force_range = force - 4, force + 4

        # randomized locations and forces
        if vertical:
            xl, xu = int(-8 + self.rect.x), int(8 + self.rect.x)
            yl, yu = int(-2 + self.rect.y), int(2 + self.rect.y)
            xfl, xfu = int(-1.5 * force), int(1.5 * force)
            yfl, yfu = int(force - variance), int(force + variance)
        else:
            xl, xu = int(-2 + self.rect.x), int(2 + self.rect.x)
            yl, yu = int(-4 + self.rect.y), int(12 + self.rect.y)
            xfl, xfu = int(force - variance), int(force + variance)
            yfl, yfu = int(force), int(2 * force)

        for each in range(number):
            self.draw_group.add(Particle(self.colors[random.randint(0, len(self.colors) - 1)], random.randint(xl, xu), random.randint(yl, yu), random.randint(xfl, xfu), random.randint(yfl, yfu), size))

    def goto(self):
        self.rect.x = self.parent.rect.x + self.parent.px_offset
        self.rect.y = self.parent.rect.y + self.parent.py_offset


class Particle(Entity):
    def __init__(self, color, x, y, x_force, y_force, size):
        Entity.__init__(self, x, y, 2, 2, 1, 0)
        self.rect = pygame.Rect((x, y), size, center=(x, y))
        self.image = pygame.Surface(size)
        self.image.fill(color)
        self.push(x_force, y_force)
        self.life = 60

    def update(self):
        Entity.update(self)
        self.life -= 1
        if self.life < 0:
            self.kill()


class Force(Entity):
    """manipulates entities it collides with"""

    def __init__(self, x, y, immune, width, height, destructive, directional, right, knockback, damage_value, source):
        Entity.__init__(self, x, y, width, height, 1000, 0)
        self.source = source
        self.rect = pygame.Rect((x - width/2, y - height/2), (width, height), center=(x, y))
        self.image = pygame.Surface([width, height])
        self.image.fill((0, 0, 0))
        self.image.set_colorkey((0, 0, 0))
        self.immune = immune
        self.width = width
        self.height = height
        self.destructive = destructive
        self.directional = directional
        self.right = right
        self.knockback = knockback
        self.damage_value = damage_value

    def update(self):
        """uses many factors to determine appropriate knockback and damage for entity, including distance"""

        for entity in self.entities:
            if self.immune != entity:
                dx = entity.rect.x - self.rect.x
                if dx > 0:
                    dx = 2 - dx / (self.width/2)
                elif dx < 0:
                    dx = 2 + dx / (self.width/2)
                else:
                    dx = 1
                dy = (self.rect.y + self.height/2 - entity.rect.y) / (self.height/2) + .2
                if dy > 0:
                    dy = 1 - dy
                else:
                    dy = -1 - dy
                if self.directional:
                    dx = abs(dx)
                    if not self.right:
                        dx = -dx
                    kbx = self.knockback * dx
                    kby = self.knockback * dy
                else:
                    distance = (dx**2 + dy**2)**.5 + .1
                    kbx = dx / distance * self.knockback
                    kby = dy / distance * self.knockback

                entity.push(kbx, kby)
                entity.damage(self.damage_value * -abs(dx), self.source)
        self.kill()


        







