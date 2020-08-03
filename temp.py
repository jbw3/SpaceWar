# Space War Game
# John Wilkes
# 2-4 players
# Joysticks supported: Logitech Dual Action, Logitech Gamepad F310

from livewires import games
import color, copy, math, random
pygame = games.pygame

games.init(900, 650, 50, "Space War")

class Jstick(object):
    def __init__(self, id):
        self.jstick = pygame.joystick.Joystick(id)
        self.jstick.init()

    def get_leftxaxis(self):
        return self.jstick.get_axis(0)

    def get_leftyaxis(self):
        return self.jstick.get_axis(1)

    def get_rightxaxis(self):
        if self.jstick.get_numbuttons() == 10:
            return self.jstick.get_axis(4)
        else:
            return self.jstick.get_axis(2)

    def get_rightyaxis(self):
        return self.jstick.get_axis(3)

    def get_confirm(self):
        if self.jstick.get_numbuttons() == 10:
            return self.jstick.get_button(2)
        else:
            return self.jstick.get_button(0)

    def get_cancel(self):
        if self.jstick.get_numbuttons() == 10:
            return self.jstick.get_button(0)
        else:
            return self.jstick.get_button(1)

    def get_fire(self):
        return self.jstick.get_button(5)

    def get_grenade(self):
        if self.jstick.get_numbuttons() == 10:
            return self.jstick.get_axis(2) < -.2
        else:
            return self.jstick.get_button(7)

class Chooser(games.Text):
    AXIS_PAD = .2
    TIMER = 20
    def __init__(self, jstick, size, color, choices, choice=None, x=0, y=0,
                 left=None, right=None, top=None, bottom=None):
        self.jstick = jstick
        if choice == None:
            choice = choices[0]
        self.__choices = choices
        self.__choice = choice
        self.__idx = choices.index(choice)
        self.__timer = 0
        super(Chooser, self).__init__("< "+str(choice)+" >", size, color, x=x,
                                      y=y, left=left, right=right, top=top,
                                      bottom=bottom)

    def update(self):
        if -Chooser.AXIS_PAD <= self.jstick.get_leftxaxis() <= Chooser.AXIS_PAD:
            self.__timer = 0
        if self.__timer > 0:
            self.__timer -= 1
        else:
            if self.jstick.get_leftxaxis() > Chooser.AXIS_PAD:
                self.incr()
                self.__timer = Chooser.TIMER
            elif self.jstick.get_leftxaxis() < -Chooser.AXIS_PAD:
                self.decr()
                self.__timer = Chooser.TIMER

    def __new_choice(self):
        self.__choice = self.__choices[self.__idx]
        self.value = "< " + str(self.__choice) + " >"

    def incr(self):
        self.__idx += 1
        if self.__idx >= len(self.__choices):
            self.__idx = 0
        self.__new_choice()

    def decr(self):
        self.__idx -= 1
        if self.__idx < 0:
            self.__idx = len(self.__choices) - 1
        self.__new_choice()

    #------Properties------#
    ## choice
    def get_choice(self):
        return self.__choice
    choice = property(get_choice)

class Map_Chooser(games.Text):
    AXIS_PAD = .2
    TIMER = 20
    def __init__(self, jstick, choices, choice=None, x=0, y=0, left=None,
                 right=None, top=None, bottom=None):
        self.jstick = jstick
        if choice == None or choice not in choices:
            choice = choices[0]
        self.__choices = choices
        self.__choice = choice
        self.__idx = choices.index(choice)
        self.__timer = 0
        super(Map_Chooser, self).__init__("<"+" "*40+">", 70, color.WHITE, x=x,
                                          y=y, left=left, right=right, top=top,
                                          bottom=bottom)
        self.load_images(choices)
        self.sprite = games.Sprite(self.__images[self.__idx], x=self.x, y=self.y)
        games.screen.add(self.sprite)

    def update(self):
        if -Chooser.AXIS_PAD <= self.jstick.get_leftxaxis() <= Chooser.AXIS_PAD:
            self.__timer = 0
        if self.__timer > 0:
            self.__timer -= 1
        else:
            if self.jstick.get_leftxaxis() > Chooser.AXIS_PAD:
                self.incr()
                self.__timer = Chooser.TIMER
            elif self.jstick.get_leftxaxis() < -Chooser.AXIS_PAD:
                self.decr()
                self.__timer = Chooser.TIMER

    def __new_choice(self):
        self.__choice = self.__choices[self.__idx]
        self.sprite.image = self.__images[self.__idx]

    def incr(self):
        self.__idx += 1
        if self.__idx >= len(self.__choices):
            self.__idx = 0
        self.__new_choice()

    def decr(self):
        self.__idx -= 1
        if self.__idx < 0:
            self.__idx = len(self.__choices) - 1
        self.__new_choice()

    def load_images(self, choices):
        self.__images = []
        for num in choices:
            self.__images.append(games.load_image("images\\map"+str(num)+".bmp",
                                                  False))

    def destroy(self):
        self.sprite.destroy()
        super(Map_Chooser, self).destroy()

    #------Properties------#
    ## choice
    def get_choice(self):
        return self.__choice
    choice = property(get_choice)

class Woundable(games.Sprite):
    def wound(self, points, explosion=None):
        pass

class Smoke(games.Sprite):
    def __init__(self, x, y):
        super(Smoke, self).__init__(games.load_image("images\\smoke.bmp"),
                                    x=x, y=y, is_collideable=False)
        self.alpha = 255

    def update(self):
        self.alpha -= 10
        if self.alpha > 0:
            self.image.set_alpha(self.alpha)
        else:
            self.destroy()

class Laser(games.Sprite):
    SPEED = 13
    def __init__(self, man, num, points, angle, x, y):
        self.man = man
        self.points = points
        self.is_solid = False
        self.is_reflector = False
        super(Laser, self).__init__(games.load_image("images\\laser"+str(num)+".bmp"),
                                    angle, x, y,
                                    dx=self.SPEED * math.sin(math.radians(angle)),
                                    dy=self.SPEED * -math.cos(math.radians(angle)))

    def update(self):
        for sprite in self.overlapping_sprites:
            if sprite.is_reflector:
                self.bounce(sprite)
            elif sprite.is_solid and sprite != self.man:
                self.destroy()
            if issubclass(type(sprite), Woundable) and sprite != self.man:
                sprite.wound(self.points)

class Missile(Woundable):
    SPEED = 11
    POINTS = 90
    def __init__(self, man, angle, x, y):
        self.man = man
        self.is_solid = True
        self.is_reflector = False
        super(Missile, self).__init__(games.load_image("images\\missile.bmp"),
                                      angle, x, y,
                                      dx=self.SPEED * math.sin(math.radians(angle)),
                                      dy=self.SPEED * -math.cos(math.radians(angle)))

    def update(self):
        for sprite in self.overlapping_sprites:
            if sprite.is_solid and sprite != self.man:
                self.explode()

    def explode(self):
        explosion = Explosion(self.x, self.y, 109, Missile.POINTS)
        games.screen.add(explosion)
        explosion.lower()
        self.destroy()

    def wound(self, points, explosion=None):
        self.explode()

class Explosion(games.Animation):
    main_image = games.load_image("images\\explosion.bmp")
    sound = games.load_sound("sounds\\explosion.wav")
    def __init__(self, x, y, size, points):
        images = []
        for i in range(4, size+5, 5):
            images.append(pygame.transform.scale(Explosion.main_image, (i, i)))
        self.is_solid = False
        self.is_reflector = False
        self.wounded = []
        self.points = points
        super(Explosion, self).__init__(images, x=x, y=y, n_repeats=1)
        Explosion.sound.play()

    def update(self):
        for sprite in self.overlapping_sprites:
            if issubclass(type(sprite), Woundable) and sprite not in self.wounded:
                sprite.wound(self.points, self)
                self.wounded.append(sprite)

class Grenade(Woundable):
    SPEED = 7
    LIFETIME = 50
    POINTS = 45
    def __init__(self, man, angle, x, y):
        self.man = man
        self.life = Grenade.LIFETIME
        self.is_solid = True
        self.is_reflector = False
        super(Grenade, self).__init__(games.load_image("images\\grenade.bmp"),
                                      angle, x, y,
                                      dx=Grenade.SPEED * math.sin(math.radians(angle)),
                                      dy=Grenade.SPEED * -math.cos(math.radians(angle)))

    def update(self):
        for sprite in self.overlapping_sprites:
            if sprite.is_solid and sprite != self.man:
                self.explode()

        if self.life > 0:
            self.life -= 1
        else:
            self.explode()

    def explode(self):
        explosion = Explosion(self.x, self.y, 59, Grenade.POINTS)
        games.screen.add(explosion)
        explosion.lower()
        self.destroy()

    def wound(self, points, explosion=None):
        self.explode()

class Laser1(games.Sprite):
    WIDTH = 6
    POINTS = 100
    def __init__(self, length, angle=0, x=0, y=0, top=None, bottom=None,
                 left=None, right=None):
        img = pygame.surface.Surface((Laser1.WIDTH, length))
        img.fill(color.WHITE)
        img = pygame.transform.rotate(img, -angle)
        super(Laser1, self).__init__(img, x=x, y=y, top=top, bottom=bottom, left=left, right=right)
        self.is_solid = False
        self.is_reflector = False

        # create glow
        width = 22
        img1 = pygame.surface.Surface((width, 1), flags=pygame.SRCALPHA)
        alpha = 30
        for i in range(width):
            img1.set_at((i, 0), (237, 28, 36, alpha))
            if i <= 7:
                alpha += 22
            elif i >= 14:
                alpha -= 22
        img1 = pygame.transform.scale(img1, (width, length))
        img1 = pygame.transform.rotate(img1, -angle)
        self.glow = games.Sprite(img1, x=self.x, y=self.y, is_collideable=False)
        games.screen.add(self.glow)

    def update(self):
        for sprite in self.overlapping_sprites:
            if issubclass(type(sprite), Woundable):
                sprite.wound(Laser1.POINTS)

    def destroy(self):
        self.glow.destroy()
        super(Laser1, self).destroy()

class Generator(Woundable):
    image = games.load_image("images\\generator.bmp")
    def __init__(self, length, angle=0, x=0, y=0, top=None, bottom=None,
                 left=None, right=None):
        super(Generator, self).__init__(Generator.image, angle, x, y, top,
                                        bottom, left, right)
        self.health = 180
        self.is_solid = True
        self.is_reflector = False

        x = 0
        y = 0
        top = None
        bottom = None
        left = None
        right = None
        if angle == 0:
            x = self.x
            bottom = self.top
        elif angle == 90:
            y = self.y
            left = self.right
        elif angle == 180:
            x = self.x
            top = self.bottom
        elif angle == 270:
            y = self.y
            right = self.left
        self.laser = Laser1(length, angle, x, y, top, bottom, left, right)
        games.screen.add(self.laser)

    def wound(self, points, explosion=None):
        self.health -= points
        if self.health <= 0:
            self.die()

    def die(self):
        self.laser.destroy()
        self.destroy()

class Health(games.Sprite):
    COLORS = {"red" : color.RED, "blue" : color.BLUE, "green" : color.GREEN, "yellow" : color.YELLOW}
    meter_image = games.load_image("images\\health_meter.bmp", False)
    def __init__(self, color, top=None, bottom=None, left=None, right=None):
        super(Health, self).__init__(Health.meter_image.convert(), top=top,
                                     bottom=bottom, left=left, right=right,
                                     is_collideable=False)
        self.color = Health.COLORS[color]

    def update_image(self, health):
        health = max(0, health) # make sure health is not less than 0
        image = Health.meter_image.convert()
        for x in range(1, health+1):
            for y in range(1, self.height-1):
                image.set_at((x, y), self.color)
        self.image = image

class Bunker(Woundable):
    COLOR = (70, 70, 70)
    MIROR_COLOR = (200, 200, 200)
    def __init__(self, width, height, x=0, y=0, top=None, bottom=None,
                 left=None, right=None, destructable=True, is_reflector=False):
        image = pygame.surface.Surface((width, height))
        image.fill(Bunker.COLOR)
        if is_reflector:
            pygame.draw.rect(image, Bunker.MIROR_COLOR, image.get_rect(), 1)
        super(Bunker, self).__init__(image, x=x, y=y, top=top, bottom=bottom,
                                     left=left, right=right)
        self.destructable = destructable
        self.is_solid = True
        self.is_reflector = is_reflector

    def destruct(self, explosion):
        radius = 0
        for image in explosion.images:
            radius = max(radius, image.get_width())
        radius /= 2
        if self.width > 40:
            if explosion.x - radius < self.left + 40:
                if explosion.x + radius > self.right - 40:
                    self.destroy()
                else:
                    right = self.right
                    self.image = pygame.transform.scale(self.image,
                                                        (self.right-(explosion.x+radius),
                                                        self.height))
                    self.right = right
            elif explosion.x + radius > self.right - 40:
                left = self.left
                self.image = pygame.transform.scale(self.image,
                                                    (explosion.x-radius-self.left,
                                                    self.height))
                self.left = left
            else:
                bunker = Bunker(self.right-(explosion.x+radius), self.height,
                                y=self.y, right=self.right,
                                is_reflector=self.is_reflector)
                games.screen.add(bunker)
                bunker.lower()
                left = self.left
                self.image = pygame.transform.scale(self.image,
                                                    (explosion.x-radius-self.left,
                                                    self.height))
                self.left = left
        elif self.height > 40:
            if explosion.y - radius < self.top + 40:
                if explosion.y + radius > self.bottom - 40:
                    self.destroy()
                else:
                    bottom = self.bottom
                    self.image = pygame.transform.scale(self.image,
                                                        (self.width,
                                                        self.bottom-(explosion.y+radius)))
                    self.bottom = bottom
            elif explosion.y + radius > self.bottom - 40:
                top = self.top
                self.image = pygame.transform.scale(self.image,
                                                    (self.width,
                                                    explosion.y-radius-self.top))
                self.top = top
            else:
                bunker = Bunker(self.width, self.bottom-(explosion.y+radius),
                                x=self.x, bottom=self.bottom,
                                is_reflector=self.is_reflector)
                games.screen.add(bunker)
                bunker.lower()
                top = self.top
                self.image = pygame.transform.scale(self.image,
                                                    (self.width,
                                                    explosion.y-radius-self.top))
                self.top = top
        else:
            self.destroy()

    def wound(self, points, explosion=None):
        if self.destructable and points >= 90:
            self.destruct(explosion)

class Amo(Woundable):
    TIMER = 750
    def __init__(self, x, y):
        self.main_image = games.load_image("images\\amo.bmp", False)
        self.blank_image = games.load_image("images\\blank_image.bmp")
        super(Amo, self).__init__(self.main_image, x=x, y=y)
        self.is_solid = False
        self.is_reflector = False
        self.timer = 0

    def update(self):
        if self.timer > 0:
            self.timer -= 1
            if self.timer == 0:
                self.image = self.main_image
        else:
            for sprite in self.overlapping_sprites:
                if type(sprite) == Man:
                    if sprite.weapon == 1:
                        num = 20
                    elif sprite.weapon == 2:
                        num = 35
                    elif sprite.weapon == 3:
                        num = 25
                    elif sprite.weapon == 4:
                        num = 4
                    sprite.amo = min(sprite.amo+num, sprite.max_amo)
                    left = sprite.lmeter.left
                    sprite.lmeter.value = sprite.amo
                    sprite.lmeter.left = left
                    self.image = self.blank_image
                    self.timer = Amo.TIMER
                    break

class Man(Woundable):
    MAX_HEALTH = 100
    SPEED = 3
    all = []
    fire = games.load_sound("sounds\\laser.wav")
    click = games.load_sound("sounds\\click.wav")
    teams = [0, 0, 0, 0]
    def __init__(self, game, num, controller, x, y, weapon, team):
        Man.all.append(self)
        self.game = game
        self.controller = controller
        self.team = team
        self.weapon = weapon
        self.weapon1 = 1
        if weapon == 1:
            self.laser_delay = 20
            self.grenades = 5
            self.max_amo = 40
            self.amo = self.max_amo
            self.laser_pad = 25
            self.laser_angle = 13
        elif weapon == 2:
            self.laser_delay = 8
            self.grenades = 3
            self.max_amo = 70
            self.amo = self.max_amo
            self.laser_pad = 25
            self.laser_angle = 13
        elif weapon == 3:
            self.laser_delay = 20
            self.grenades = 10
            self.max_amo = 50
            self.amo = self.max_amo
            self.laser_pad = 14
            self.laser_angle = 0
        elif weapon == 4:
            self.laser_delay = 25
            self.grenades = 0
            self.max_amo = 7
            self.amo = 7
            self.laser_pad = 22
            self.laser_angle = 24
        self.laser_wait = 0
        self.throw_grenade = True
        self.grenade_pad = 20
        self.grenade_angle = -13
        self.mine_pad = 14
        self.health = self.MAX_HEALTH
        self.is_solid = True
        self.is_reflector = False
        super(Man, self).__init__(games.load_image("images\\"+self.game.colors[team]+"_man"+str(weapon)+"-"+str(Man.teams[self.team])+".bmp"),
                                  x=x, y=y)
        Man.teams[self.team] += 1
        if num == 0:
            self.hmeter = Health(self.game.colors[self.team], top=10, left=10)
            self.hmeter.update_image(self.health)
            games.screen.add(self.hmeter)
            self.lmeter = games.Text(self.amo, 25, color.RED,
                                     left=self.hmeter.right+10, top=10,
                                     is_collideable=False)
            games.screen.add(self.lmeter)
            self.gmeter = games.Text(self.grenades, 25, color.BLACK,
                                     left=self.lmeter.right+10, top=10,
                                     is_collideable=False)
            games.screen.add(self.gmeter)
        elif num == 1:
            self.gmeter = games.Text(self.grenades, 25, color.BLACK,
                                     right=games.screen.width-10, top=10,
                                     is_collideable=False)
            games.screen.add(self.gmeter)
            self.lmeter = games.Text(self.amo, 25, color.RED,
                                     right=self.gmeter.left-10, top=10,
                                     is_collideable=False)
            games.screen.add(self.lmeter)
            self.hmeter = Health(self.game.colors[self.team], top=10, right=self.lmeter.left-10)
            self.hmeter.update_image(self.health)
            games.screen.add(self.hmeter)
        elif num == 2:
            self.hmeter = Health(self.game.colors[self.team], bottom=games.screen.height-10, left=10)
            self.hmeter.update_image(self.health)
            games.screen.add(self.hmeter)
            self.lmeter = games.Text(self.amo, 25, color.RED,
                                     left=self.hmeter.right+10,
                                     bottom=games.screen.height-10,
                                     is_collideable=False)
            games.screen.add(self.lmeter)
            self.gmeter = games.Text(self.grenades, 25, color.BLACK,
                                     left=self.lmeter.right+10,
                                     bottom=games.screen.height-10,
                                     is_collideable=False)
            games.screen.add(self.gmeter)
        elif num == 3:
            self.gmeter = games.Text(self.grenades, 25, color.BLACK,
                                     right=games.screen.width-10, bottom=games.screen.height-10,
                                     is_collideable=False)
            games.screen.add(self.gmeter)
            self.lmeter = games.Text(self.amo, 25, color.RED,
                                     right=self.gmeter.left-10, bottom=games.screen.height-10,
                                     is_collideable=False)
            games.screen.add(self.lmeter)
            self.hmeter = Health(self.game.colors[self.team], bottom=games.screen.height-10,
                                 right=self.lmeter.left-10)
            self.hmeter.update_image(self.health)
            games.screen.add(self.hmeter)

    def update(self):
        # move
        if abs(self.controller.get_rightxaxis()) > .2 or abs(self.controller.get_rightyaxis()) > .2:
            self.rotate(90 + math.degrees(math.atan2(self.controller.get_rightyaxis(), self.controller.get_rightxaxis())))
        if abs(self.controller.get_leftxaxis()) > .1 or abs(self.controller.get_leftyaxis()) > .1:
            speed = min(self.SPEED, self.SPEED * (self.controller.get_leftxaxis()**2 + self.controller.get_leftyaxis()**2)**.5)
            angle = math.pi/2 + math.atan2(self.controller.get_leftyaxis(), self.controller.get_leftxaxis())
            self.move(speed, angle)

        # shoot
        if self.laser_wait > 0:
            self.laser_wait -= 1
        else:
            if self.controller.get_fire():
                self.shoot()

        # throw grenade
        if self.controller.get_grenade() and self.throw_grenade and self.grenades > 0:
            if self.weapon1 == 1:
                self.grenade()
            elif self.weapon1 == 2:
                self.mine()
            self.throw_grenade = False
        if not self.controller.get_grenade():
            self.throw_grenade = True

    def shoot(self):
        if self.amo > 0:
            if self.weapon == 4:
                missile = Missile(self, self.angle,
                                  self.x + self.laser_pad * math.sin(math.radians(self.angle+self.laser_angle)),
                                  self.y + self.laser_pad * -math.cos(math.radians(self.angle+self.laser_angle)))
                games.screen.add(missile)
                missile.lower()
                smoke = Smoke(self.x + self.laser_pad * math.sin(math.radians(self.angle+self.laser_angle)),
                              self.y + self.laser_pad * -math.cos(math.radians(self.angle+self.laser_angle)))
                games.screen.add(smoke)
            else:
                if self.weapon == 1:
                    points = 40
                    num = 1
                elif self.weapon == 2 or self.weapon == 3:
                    points = 20
                    num = 2
                laser = Laser(self, num, points, self.angle,
                              self.x + self.laser_pad * math.sin(math.radians(self.angle+self.laser_angle)),
                              self.y + self.laser_pad * -math.cos(math.radians(self.angle+self.laser_angle)))
                games.screen.add(laser)
                laser.lower()
                Man.fire.play()
            self.amo -= 1
            left = self.lmeter.left
            self.lmeter.value = self.amo
            self.lmeter.left = left
            self.laser_wait = self.laser_delay
        else:
            Man.click.play()
            self.laser_wait = self.laser_delay

    def grenade(self):
        grenade = Grenade(self, self.angle,
                          self.x + self.grenade_pad * math.sin(math.radians(self.angle+self.grenade_angle)),
                          self.y + self.grenade_pad * -math.cos(math.radians(self.angle+self.grenade_angle)))
        games.screen.add(grenade)
        grenade.lower()
        self.grenades -= 1
        left = self.gmeter.left
        self.gmeter.value = self.grenades
        self.gmeter.left = left

    def rotate(self, angle):
        pad = 4
        self.angle = angle
        for sprite in self.overlapping_sprites:
            if sprite.is_solid:
                if sprite.bottom - Man.SPEED - pad <= self.top < sprite.bottom:
                    self.top = sprite.bottom
                if sprite.top + Man.SPEED + pad >= self.bottom > sprite.top:
                    self.bottom = sprite.top
                if sprite.right - Man.SPEED - pad <= self.left < sprite.right:
                    self.left = sprite.right
                if sprite.left + Man.SPEED + pad >= self.right > sprite.left:
                    self.right = sprite.left

    def move(self, speed, angle):
        self.x += speed * math.sin(angle)
        self.y += speed * -math.cos(angle)
        angle = math.degrees(angle) % 360
        for sprite in self.overlapping_sprites:
            if sprite.is_solid:
                if sprite.bottom - Man.SPEED <= self.top < sprite.bottom:
                    self.top = sprite.bottom
                if sprite.top + Man.SPEED >= self.bottom > sprite.top:
                    self.bottom = sprite.top
                if sprite.right - Man.SPEED <= self.left < sprite.right:
                    self.left = sprite.right
                if sprite.left + Man.SPEED >= self.right > sprite.left:
                    self.right = sprite.left

    def wound(self, points, explosion=None):
        self.health -= points
        self.hmeter.update_image(self.health)
        if self.health <= 0:
            self.die()

    def die(self):
        self.destroy()
        self.game.teams[self.team] -= 1
        remaining = 0
        for i in self.game.teams:
            if i != 0:
                remaining += 1
        if remaining == 1:
            self.game.end()

    def destroy(self):
        Man.all.remove(self)
        Man.teams[self.team] -= 1
        super(Man, self).destroy()

class Setup(games.Text):
    def __init__(self, game, jstick, x=0, y=0, left=None, right=None, top=None,
                 bottom=None):
        super(Setup, self).__init__("Press 1 to continue", 50, color.WHITE, x=x,
                                    y=y, left=left, right=right, top=top,
                                    bottom=bottom)
        self.game = game
        self.jstick = jstick
        self.idx = 0
        self.can_press = True

        self.game.setup_funcs[0]()

    def update(self):
        if self.jstick.get_confirm():
            if self.can_press:
                self.new_func()
                self.can_press = False
        else:
            self.can_press = True

    def new_func(self):
        for sprite in games.screen.all_objects:
            if sprite != self:
                sprite.destroy()
        self.idx += 1
        self.game.setup_funcs[self.idx]()

class Weapon_confirm(games.Text):
    all = []
    def __init__(self, game, chooser, size, color, x, y):
        super(Weapon_confirm, self).__init__("Press 1 to confirm", size, color,
                                             x=x, y=y)
        Weapon_confirm.all.append(self)
        self.game = game
        self.chooser = chooser
        self.jstick = chooser.jstick
        self.locked = False
        if self.jstick.get_confirm():
            self.can_press = False
        else:
            self.can_press = True

        games.screen.remove(self.game.setup_text)

    def update(self):
        if self.can_press:
            if self.jstick.get_confirm() and not self.locked:
                self.locked = True
                self.chooser.stop()
                self.value = "Press 2 to choose"
                for text in Weapon_confirm.all:
                    if not text.locked:
                        break
                else:
                    games.screen.add(self.game.setup_text)
            elif self.jstick.get_cancel() and self.locked:
                self.locked = False
                self.chooser.start()
                self.value = "Press 1 to confirm"
                games.screen.remove(self.game.setup_text)
        elif not self.jstick.get_confirm():
            self.can_press = True

    def destroy(self):
        Weapon_confirm.all.remove(self)
        super(Weapon_confirm, self).destroy()

class Weapon_man(games.Sprite):
    teams = [0, 0, 0, 0]
    def __init__(self, game, w_num, team_num, x, y, chooser):
        self.num = Weapon_man.teams[team_num]
        Weapon_man.teams[team_num] += 1
        super(Weapon_man, self).__init__(games.load_image("images\\"+game.colors[team_num]+"_man"+str(w_num+1)+"-"+str(self.num)+".bmp"),
                                         x=x, y=y)
        self.game = game
        self.w_num = w_num
        self.team_num = team_num
        self.chooser = chooser

    def update(self):
        if self.game.weapon_choices.index(self.chooser.choice) != self.w_num:
            self.w_num = self.game.weapon_choices.index(self.chooser.choice)
            self.image = games.load_image("images\\"+self.game.colors[self.team_num]+"_man"+str(self.w_num+1)+"-"+str(self.num)+".bmp")

    def destroy(self):
        Weapon_man.teams = [0, 0, 0, 0]
        super(Weapon_man, self).destroy()

class Game(object):
    MIN_JSTICKS = 2
    MAX_PLAYERS = 4
    MAP_NUMS = {"2" : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                "3" : [1, 2, 4, 5, 6, 7, 8, 9, 10, 11],
                "4" : [2, 4, 5, 6, 7, 8, 9, 10, 11]}
    def __init__(self):
        self.colors = ("red", "blue", "green", "yellow")
        self.tcolors = (color.RED, color.BLUE, color.GREEN, color.YELLOW) # tuple colors
        self.map_num = 1
        self.num_players = 2
        self.teams_choice = "P1 vs. P2 vs. P3"
        self.teams = []
        self.weapon_choices = ("Rifle", "Machine Gun", "Pistol", "Missile Launcher")
        self.weapon_choosers = []
        self.weapons = [0, 0, 0, 0]
        self.setup_funcs = (self.get_num_players, self.get_teams, self.pick_map,
                            self.pick_weapons, self.start)

        if pygame.joystick.get_count() < Game.MIN_JSTICKS:
            message = games.Message("Not enough controllers", 70, color.RED,
                                    x=games.screen.width/2,
                                    y=games.screen.height/2, lifetime=200,
                                    after_death=games.screen.quit)
            games.screen.add(message)
            return
        
        self.init_joysticks()
        self.setup()

    def init_joysticks(self):
        self.joysticks = []
        for i in range(pygame.joystick.get_count()):
            jstick = Jstick(i)
            self.joysticks.append(jstick)

    def setup(self):
        games.screen.clear()
        games.screen.background = games.load_image("images\\black_background.bmp", False)
        self.setup_text = Setup(self, self.joysticks[0], right=games.screen.width-10,
                           bottom=games.screen.height-10)
        games.screen.add(self.setup_text)

    def pick_map(self):
        text = games.Text("Pick a map:", 70, color.WHITE,
                          x=games.screen.width/2, y=100)
        games.screen.add(text)
        self.map_text = Map_Chooser(self.joysticks[0], Game.MAP_NUMS[str(self.num_players)],
                                    self.map_num, x=games.screen.width/2,
                                    y=games.screen.height/2)
        games.screen.add(self.map_text)

    def get_num_players(self):
        text = games.Text("Set number of players:", 70, color.WHITE,
                          x=games.screen.width/2, y=games.screen.height/4)
        games.screen.add(text)
        self.player_text = Chooser(self.joysticks[0], 70, color.WHITE,
                                   range(2, min(Game.MAX_PLAYERS, pygame.joystick.get_count())+1),
                                   self.num_players,
                                   x=games.screen.width/2, y=games.screen.height/2)
        games.screen.add(self.player_text)

    def get_teams(self):
        self.num_players = self.player_text.choice
        if self.num_players == 2:
            self.setup_text.new_func()
            return
        elif self.num_players == 3:
            text = games.Text("Set teams:", 70, color.WHITE,
                              x=games.screen.width/2, y=games.screen.height/4)
            games.screen.add(text)
            self.teams_text = Chooser(self.joysticks[0], 70, color.WHITE,
                                      ["P1 vs. P2 vs. P3", "P1 & P2 vs. P3",
                                       "P1 vs. P2 & P3", "P1 & P3 vs. P2"],
                                      self.teams_choice,
                                      x=games.screen.width/2, y=games.screen.height/2)
            games.screen.add(self.teams_text)
        elif self.num_players == 4:
            self.setup_text.new_func()#temp

    def pick_weapons(self):
        if self.num_players == 2:
            self.teams = [1, 1]
            team_nums = [0, 1]
        elif self.num_players == 3:
            self.teams_choice = self.teams_text.choice
            if self.teams_choice == "P1 vs. P2 vs. P3":
                self.teams = [1, 1, 1]
                team_nums = [0, 1, 2]
            elif self.teams_choice == "P1 & P2 vs. P3":
                self.teams = [2, 1]
                team_nums = [0, 0, 1]
            elif self.teams_choice == "P1 vs. P2 & P3":
                self.teams = [2, 1]
                team_nums = [1, 0, 0]
            elif self.teams_choice == "P1 & P3 vs. P2":
                self.teams = [2, 1]
                team_nums = [0, 1, 0]
        elif self.num_players == 4:
            self.teams = [1, 1, 1, 1]#temp
            team_nums = [0, 1, 2, 3]#temp
        self.weapon_choosers = []
        for i in range(self.num_players):
            y = games.screen.height * (i + 1) / (self.num_players + 1)
            text = Chooser(self.joysticks[i], 40, self.tcolors[team_nums[i]],
                           self.weapon_choices,
                           self.weapon_choices[self.weapons[i]],
                           x=games.screen.width/3, y=y)
            games.screen.add(text)
            self.weapon_choosers.append(text)
            sprite = Weapon_man(self, self.weapons[i], team_nums[i], 100, y,
                                text)
            games.screen.add(sprite)
            text = Weapon_confirm(self, text, 40, self.tcolors[team_nums[i]],
                                  x=games.screen.width*2/3, y=y)
            games.screen.add(text)

    def start(self):
        self.map_num = self.map_text.choice
        for i in range(len(self.weapon_choosers)):
            self.weapons[i] = self.weapon_choices.index(self.weapon_choosers[i].choice)
        games.screen.clear()
        games.screen.background = games.load_image("images\\gray_background.bmp", False)
        positions = (((50, 500), (850, 325), (450, 50)),
                     ((350, 600), (800, 150), (625, 50), (400, 180)),
                     ((50, 100), (850, 100)),
                     ((130, 600), (780, 50), (50, 130), (850, 520)),
                     ((150, 150), (550, 500), (50, 600), (650, 115)),
                     ((400, 275), (500, 275), (400, 375), (500, 375)),
                     ((50, 80), (850, 80), (50, 570), (850, 570)),
                     ((50, 50), (850, 50), (50, 600), (850, 600)),
                     ((50, 275), (850, 275), (50, 375), (850, 375)),
                     ((40, 150), (750, 40), (150, 610), (860, 500)),
                     ((37, 50), (863, 600), (50, 613), (850, 37)))
        self.terrain(self.map_num)
        self.add_men(positions[self.map_num-1])

    def end(self):
        for sprite in games.screen.all_objects:
            sprite.stop()
        for i in range(len(self.teams)):
            if self.teams[i] != 0:
                team = i
                break
        message = games.Message(self.colors[team].title() + " won!", 80,
                                self.tcolors[team], x=games.screen.width/2,
                                y=games.screen.height/2, lifetime=200,
                                after_death=self.setup, is_collideable=False)
        games.screen.add(message)

    def add_men(self, positions):
        if self.num_players == 2:
            team_nums = [0, 1]
        elif self.num_players == 3:
            self.teams_choice = self.teams_text.choice
            if self.teams_choice == "P1 vs. P2 vs. P3":
                team_nums = [0, 1, 2]
            elif self.teams_choice == "P1 & P2 vs. P3":
                team_nums = [0, 0, 1]
            elif self.teams_choice == "P1 vs. P2 & P3":
                team_nums = [1, 0, 0]
            elif self.teams_choice == "P1 & P3 vs. P2":
                team_nums = [0, 1, 0]
        elif self.num_players == 4:
            team_nums = [0, 1, 2, 3]#temp
        for i in range(self.num_players):
            man = Man(self, i, self.joysticks[i], positions[i][0],
                      positions[i][1], self.weapons[i]+1, team_nums[i])
            games.screen.add(man)
            man.lower()

    def terrain(self, num):
        bunker = Bunker(games.screen.width, 40, x=games.screen.width/2,
                        bottom=5, destructable=False)
        games.screen.add(bunker)
        bunker = Bunker(games.screen.width, 40, x=games.screen.width/2,
                        top=games.screen.height-5, destructable=False)
        games.screen.add(bunker)
        bunker = Bunker(40, games.screen.height, right=5,
                        y=games.screen.height/2, destructable=False)
        games.screen.add(bunker)
        bunker = Bunker(40, games.screen.height, left=games.screen.width-5,
                        y=games.screen.height/2, destructable=False)
        games.screen.add(bunker)
        if num == 1:
            amo = Amo(games.screen.width/2, 500)
            games.screen.add(amo)
            bunker = Bunker(200, 40, 450, 150)
            games.screen.add(bunker)
            bunker = Bunker(40, 40, 370, 110)
            games.screen.add(bunker)
            bunker = Bunker(40, 200, 800, 325)
            games.screen.add(bunker)
            bunker = Bunker(40, 100, 100, 500)
            games.screen.add(bunker)
        elif num == 2:
            amo = Amo(games.screen.width/2, games.screen.height/2)
            games.screen.add(amo)
            bunker = Bunker(40, 300, x=games.screen.width/2, top=0)
            games.screen.add(bunker)
            bunker = Bunker(70, 40, right=bunker.left, y=225)
            games.screen.add(bunker)
            bunker = Bunker(40, 300, x=games.screen.width/2,
                            bottom=games.screen.height)
            games.screen.add(bunker)
            bunker = Bunker(200, 40, right=games.screen.width/2-20,
                            y=games.screen.height*.75)
            games.screen.add(bunker)
            bunker = Bunker(40, 400, right=bunker.left, bottom=bunker.bottom)
            games.screen.add(bunker)
            bunker = Bunker(50, 40, right=bunker.left, y=bunker.y)
            games.screen.add(bunker)
            bunker = Bunker(40, 500, x=games.screen.width*.75, top=0)
            games.screen.add(bunker)
            bunker = Bunker(60, 40, right=bunker.left, bottom=bunker.bottom)
            games.screen.add(bunker)
            bunker = Bunker(75, 40, right=bunker.right, y=175)
            games.screen.add(bunker)
            bunker = Bunker(80, 40, left=bunker.right+40, y=300)
            games.screen.add(bunker)
        elif num == 3:
            amo = Amo(700, 50)
            games.screen.add(amo)
            bunker = Bunker(40, 550, x=150, top=0)
            games.screen.add(bunker)
            bunker = Bunker(250, 40, left=bunker.right, bottom=bunker.bottom)
            games.screen.add(bunker)
            bunker = Bunker(40, 260, right=bunker.right, bottom=bunker.top)
            games.screen.add(bunker)
            bunker = Bunker(260, 40, left=bunker.left, bottom=bunker.top)
            games.screen.add(bunker)
            bunker = Bunker(40, 200, right=bunker.right, top=bunker.bottom)
            games.screen.add(bunker)
            bunker = Bunker(40, 550, x=750, top=0)
            games.screen.add(bunker)
            bunker = Bunker(250, 40, right=bunker.left, bottom=bunker.bottom)
            games.screen.add(bunker)
            bunker = Bunker(40, 200, left=bunker.left, bottom=bunker.top)
            games.screen.add(bunker)
            bunker = Bunker(475, 40, right=730, y=110)
            games.screen.add(bunker)
            bunker = Bunker(40, 325, left=bunker.left, top=bunker.bottom)
            games.screen.add(bunker)
        elif num == 4:
            amo = Amo(games.screen.width/2, games.screen.height/2)
            games.screen.add(amo)
            for x in range(130, games.screen.width, 130):
                for y in range(130, games.screen.height, 130):
                    bunker = Bunker(40, 40, x, y)
                    games.screen.add(bunker)
        elif num == 5:
            amo = Amo(525, 150)
            games.screen.add(amo)
            bunker = Bunker(40, 550, x=200, y=games.screen.height/2)
            games.screen.add(bunker)
            bunker = Bunker(125, 40, right=bunker.left, y=200)
            games.screen.add(bunker)
            bunker = Bunker(125, 40, left=5, y=400)
            games.screen.add(bunker)
            bunker = Bunker(560, 40, left=290, y=games.screen.height-200)
            games.screen.add(bunker)
            bunker = Bunker(40, 180, x=500, bottom=games.screen.height)
            games.screen.add(bunker)
            bunker = Bunker(630, 40, left=220, top=50)
            games.screen.add(bunker)
            bunker = Bunker(40, 145, x=600, top=bunker.bottom)
            games.screen.add(bunker)
            bunker = Bunker(40, 145, x=600, top=bunker.bottom+50)
            games.screen.add(bunker)
        elif num == 6:
            amo = Amo(games.screen.width/2, 20)
            games.screen.add(amo)
            amo = Amo(games.screen.width/2, games.screen.height-20)
            games.screen.add(amo)
            amo = Amo(20, games.screen.height/2)
            games.screen.add(amo)
            amo = Amo(games.screen.width-20, games.screen.height/2)
            games.screen.add(amo)
            bunker = Bunker(750, 40, x=games.screen.width/2,
                            y=games.screen.height/2)
            games.screen.add(bunker)
            bunker = Bunker(40, 240, x=games.screen.width/2,
                            bottom=games.screen.height/2-20)
            games.screen.add(bunker)
            bunker = Bunker(40, 240, x=games.screen.width/2,
                            top=games.screen.height/2+20)
            games.screen.add(bunker)
        elif num == 7:
            amo = Amo(games.screen.width/3, games.screen.height/2)
            games.screen.add(amo)
            amo = Amo(games.screen.width*2/3, games.screen.height/2)
            games.screen.add(amo)
            bunker = Bunker(300, 40, games.screen.width/4, 80)
            games.screen.add(bunker)
            bunker = Bunker(40, 40, left=bunker.left, top=bunker.bottom)
            games.screen.add(bunker)
            bunker = Bunker(300, 40, games.screen.width*3/4, 80)
            games.screen.add(bunker)
            bunker = Bunker(40, 40, right=bunker.right, top=bunker.bottom)
            games.screen.add(bunker)
            bunker = Bunker(300, 40, games.screen.width/4, 570)
            games.screen.add(bunker)
            bunker = Bunker(40, 40, left=bunker.left, bottom=bunker.top)
            games.screen.add(bunker)
            bunker = Bunker(300, 40, games.screen.width*3/4, 570)
            games.screen.add(bunker)
            bunker = Bunker(40, 40, right=bunker.right, bottom=bunker.top)
            games.screen.add(bunker)
            bunker = Bunker(200, 40, y=games.screen.height/2, left=0)
            games.screen.add(bunker)
            bunker = Bunker(200, 40, y=games.screen.height/2,
                            right=games.screen.width)
            games.screen.add(bunker)
            bunker = Bunker(200, 40, games.screen.width/2, games.screen.height/2)
            games.screen.add(bunker)
        elif num == 8:
            amo = Amo(games.screen.width/2, games.screen.height/2)
            games.screen.add(amo)
            bunker = Bunker(100, 40, 50, 100)
            games.screen.add(bunker)
            bunker = Bunker(40, 40, 170, 100)
            games.screen.add(bunker)
            bunker = Bunker(40, 100, 800, 50)
            games.screen.add(bunker)
            bunker = Bunker(40, 40, 800, 170)
            games.screen.add(bunker)
            bunker = Bunker(40, 100, 100, 600)
            games.screen.add(bunker)
            bunker = Bunker(40, 40, 100, 480)
            games.screen.add(bunker)
            bunker = Bunker(100, 40, 850, 550)
            games.screen.add(bunker)
            bunker = Bunker(40, 40, 730, 550)
            games.screen.add(bunker)
            bunker = Bunker(100, 40, games.screen.width/2, games.screen.height/2-140)
            games.screen.add(bunker)
            bunker = Bunker(100, 40, games.screen.width/2, games.screen.height/2+140)
            games.screen.add(bunker)
            bunker = Bunker(40, 100, games.screen.width/2-140, games.screen.height/2)
            games.screen.add(bunker)
            bunker = Bunker(40, 100, games.screen.width/2+140, games.screen.height/2)
            games.screen.add(bunker)
        elif num == 9:
            amo = Amo(games.screen.width/2-25, games.screen.height/2)
            games.screen.add(amo)
            amo = Amo(games.screen.width/2+25, games.screen.height/2)
            games.screen.add(amo)
            generator = Generator(628, 0, x=games.screen.width/2, y=games.screen.height-11)
            games.screen.add(generator)
            bunker = Bunker(250, 40, left=0, y=games.screen.height/2)
            games.screen.add(bunker)
            bunker = Bunker(40, 200, left=bunker.right, y=games.screen.height/2)
            games.screen.add(bunker)
            bunker = Bunker(250, 40, right=games.screen.width,
                            y=games.screen.height/2)
            games.screen.add(bunker)
            bunker = Bunker(40, 200, right=bunker.left, y=games.screen.height/2)
            games.screen.add(bunker)
            bunker = Bunker(40, 50, right=games.screen.width/2-20,
                            bottom=games.screen.height)
            games.screen.add(bunker)
            bunker = Bunker(40, 50, left=games.screen.width/2+20,
                            bottom=games.screen.height)
            games.screen.add(bunker)
        elif num == 10:
            amo = Amo(375, 250)
            games.screen.add(amo)
            amo = Amo(525, 250)
            games.screen.add(amo)
            amo = Amo(375, 400)
            games.screen.add(amo)
            amo = Amo(525, 400)
            games.screen.add(amo)
            generator = Generator(628, 0, x=games.screen.width/2+50, y=games.screen.height-11)
            games.screen.add(generator)
            generator = Generator(628, 180, x=games.screen.width/2-50, y=11)
            games.screen.add(generator)
            generator = Generator(878, 90, left=3, y=games.screen.height/2+50)
            games.screen.add(generator)
            generator = Generator(878, 270, right=games.screen.width-2, y=games.screen.height/2-50)
            games.screen.add(generator)
            bunker = Bunker(40, 200, right=games.screen.width/2-70, top=0)
            games.screen.add(bunker)
            bunker = Bunker(40, 200, left=games.screen.width/2+70, bottom=games.screen.height)
            games.screen.add(bunker)
            bunker = Bunker(200, 40, left=0, top=games.screen.height/2+70)
            games.screen.add(bunker)
            bunker = Bunker(200, 40, right=games.screen.width, bottom=games.screen.height/2-70)
            games.screen.add(bunker)
            bunker = Bunker(120, 40, left=0, y=200)
            games.screen.add(bunker)
            bunker = Bunker(120, 40, right=games.screen.width, y=games.screen.height-200)
            games.screen.add(bunker)
            bunker = Bunker(40, 120, x=games.screen.width-200, top=0)
            games.screen.add(bunker)
            bunker = Bunker(40, 120, x=200, bottom=games.screen.height)
            games.screen.add(bunker)
        elif num == 11:
            amo = Amo(games.screen.width/2, games.screen.height/2)
            games.screen.add(amo)
            bunker = Bunker(40, 460, left=75, top=0)
            games.screen.add(bunker)
            bunker = Bunker(480, 40, left=bunker.right, bottom=bunker.bottom)
            games.screen.add(bunker)
            bunker = Bunker(710, 40, left=0, bottom=games.screen.height-75)
            games.screen.add(bunker)
            bunker = Bunker(40, 230, right=bunker.right, bottom=bunker.top)
            games.screen.add(bunker)
            bunker = Bunker(40, 460, right=games.screen.width-75, bottom=games.screen.height)
            games.screen.add(bunker)
            bunker = Bunker(480, 40, right=bunker.left, top=bunker.top)
            games.screen.add(bunker)
            bunker = Bunker(710, 40, right=games.screen.width, top=75)
            games.screen.add(bunker)
            bunker = Bunker(40, 230, left=bunker.left, top=bunker.bottom)
            games.screen.add(bunker)

game = Game()

games.screen.mainloop()
