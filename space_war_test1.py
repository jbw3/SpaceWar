# Space War Game

from livewires import games, color
import math, textx
pygame = games.pygame

games.init(900, 650, 50, "Space War")
games.screen.background = games.load_image("images\\gray_background.bmp", False)

class Jstick_check(games.Text):
    def __init__(self, game):
        self.game = game
        super(Jstick_check, self).__init__("No controllers plugged in", 75,
                                           color.red, x=games.screen.width/2,
                                           y=games.screen.height/2, interval=25)

    def tick(self):
        pygame.joystick.quit()
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.destroy()
            self.game.init_joysticks()
            self.game.setup()

class Laser(games.Sprite):
    SPEED = 10
    LIFETIME = 130
    def __init__(self, man, num, points, angle, x, y):
        self.man = man
        self.life = self.LIFETIME
        self.points = points
        self.is_solid = False
        super(Laser, self).__init__(games.load_image("images\\laser"+str(num)+".bmp"),
                                    angle, x, y,
                                    dx=self.SPEED * math.sin(math.radians(angle)),
                                    dy=self.SPEED * -math.cos(math.radians(angle)))

    def update(self):
        for sprite in self.overlapping_sprites:
            if issubclass(type(sprite), Woundable):
                sprite.wound(self.points)
            if sprite.is_solid:
                self.destroy()

        if self.life > 0:
            self.life -= 1
        else:
            self.destroy()

class Woundable(games.Sprite):
    def wound(self, points):
        pass

class Health(games.Sprite):
    COLOR = (255, 0, 0)
    meter_image = games.load_image("images\\health_meter.bmp", False)
    def __init__(self, top=None, bottom=None, left=None, right=None):
        super(Health, self).__init__(Health.meter_image.convert(), top=top,
                                     bottom=bottom, left=left, right=right,
                                     is_collideable=False)

    def update_image(self, health):
        health = max(0, health) # make sure health is not less than 0
        image = Health.meter_image.convert()
        for x in range(1, health+1):
            for y in range(1, self.height-1):
                image.set_at((x, y), Health.COLOR)
        self.image = image

class Arms(Woundable):
    def __init__(self, man, image, angle, x, y):
        super(Arms, self).__init__(image, angle, x, y)
        self.man = man
        self.is_solid = True

    def wound(self, points):
        self.man.wound(points)

class Man(Woundable):
    MAX_HEALTH = 100
    SPEED = 2
    LASER_DELAY = 20
    total = 0
    def __init__(self, game, controller, color, x, y):
        Man.total += 1
        self.game = game
        self.controller = controller
        self.arm_yshift = -11
        self.laser_wait = 0
        self.laser_pad = 25
        self.laser_angle = 13
        self.health = self.MAX_HEALTH
        self.is_solid = True
        super(Man, self).__init__(games.load_image("images\\"+color+"_man.bmp"),
                                  x=x, y=y)
        self.arms = Arms(self, games.load_image("images\\"+color+"_arms1.bmp"),
                         self.angle,
                         x + self.arm_yshift * math.cos(math.radians(self.angle + 90)),
                         y + self.arm_yshift * math.sin(math.radians(self.angle + 90)))
        if Man.total == 1:
            left = 10
            right = None
        elif Man.total == 2:
            left = None
            right = games.screen.width - 10
        self.meter = Health(top=10, left=left, right=right)
        self.meter.update_image(self.health)
        games.screen.add(self.meter)

    def update(self):
        # move
        if abs(self.controller.get_axis(2)) > .2 or abs(self.controller.get_axis(3)) > .2:
            self.angle = 90 + math.degrees(math.atan2(self.controller.get_axis(3), self.controller.get_axis(2)))
        if abs(self.controller.get_axis(0)) > .1 or abs(self.controller.get_axis(1)) > .1:
            speed = min(self.SPEED, self.SPEED * (self.controller.get_axis(0)**2 + self.controller.get_axis(1)**2)**.5)
            angle = math.pi/2 + math.atan2(self.controller.get_axis(1), self.controller.get_axis(0))
            self.move(speed, angle)

        # shoot
        if self.laser_wait > 0:
            self.laser_wait -= 1
        else:
            if self.controller.get_button(5):
                laser = Laser(self, 1, 45, self.angle,
                              self.x + self.laser_pad * math.sin(math.radians(self.angle+self.laser_angle)),
                              self.y + self.laser_pad * -math.cos(math.radians(self.angle+self.laser_angle)))
                games.screen.add(laser)
                self.laser_wait = self.LASER_DELAY

        # update arms
        self.arms.angle = self.angle
        self.arms.x = self.x + self.arm_yshift * math.cos(math.radians(self.angle+90))
        self.arms.y = self.y + self.arm_yshift * math.sin(math.radians(self.angle+90))

    def move(self, speed, angle):
        self.x += speed * math.sin(angle)
        self.y += speed * -math.cos(angle)
        for sprite in self.overlapping_sprites:
            if sprite.is_solid and sprite != self.arms:
                if self.top < sprite.bottom:
                    self.top = sprite.bottom
                if self.bottom > sprite.top:
                    self.bottom = sprite.top
                if self.left < sprite.right:
                    self.left = sprite.right
                if self.right > sprite.left:
                    self.right = sprite.left

##                if self.top < sprite.bottom and (270 < angle < 360 or 0 <= angle < 90):
##                    self.top = sprite.bottom
##                if self.bottom > sprite.top and 90 < angle < 270:
##                    self.bottom = sprite.top
##                if self.left < sprite.right and 180 < angle < 360:
##                    self.left = sprite.right
##                if self.right > sprite.left and 0 < angle < 180:
##                    self.right = sprite.left
##
##                if 315 < angle < 360 or 0 <= angle <= 45:
##                    self.top = sprite.bottom
##                elif 45 < angle <= 135:
##                    self.right = sprite.left
##                elif 135 < angle <= 225:
##                    self.bottom = sprite.top
##                elif 225 < angle <= 315:
##                    self.left = sprite.right

    def wound(self, points):
        self.health -= points
        self.meter.update_image(self.health)
        if self.health <= 0:
            self.die()

    def die(self):
        Man.total -= 1
        self.arms.destroy()
        self.destroy()

class Game(object):
    def __init__(self):
        if pygame.joystick.get_count() == 0:
            text = Jstick_check(self)
            games.screen.add(text)
        else:
            self.init_joysticks()
            self.setup()

    def init_joysticks(self):
        self.joysticks = []
        for i in range(pygame.joystick.get_count()):
            jstick = pygame.joystick.Joystick(i)
            jstick.init()
            self.joysticks.append(jstick)

    def set_vars(self):
        self.colors = ("red", "blue")

    def setup(self):
        self.set_vars()
        self.start()

    def start(self):
        #temp#
        for i in range(2):
            man = Man(self, self.joysticks[i], self.colors[i],
                      (i+1)*200, (i+1)*200)
            games.screen.add(man)
            games.screen.add(man.arms)
            man.arms.lower(man)
            man.meter.elevate()
        ######

game = Game()

games.screen.mainloop()
