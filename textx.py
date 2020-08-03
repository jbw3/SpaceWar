# RISK text

from livewires import games

class Color_clicker(games.Text):
    def __init__(self, value, size, color1, color2=None, nonact_color=None,
                 angle=0, activated=True, func=None, x=0, y=0, top=None,
                 bottom=None, left=None, right=None, is_collideable=False):

        self._color1 = color1
        if color2 == None:
            self._color2 = color1
        else:
            self._color2 = color2
        if nonact_color == None:
            self._nonact_color = color1
        else:
            self._nonact_color = nonact_color
        self._activated = activated
        self.func = func
        if games.mouse.is_pressed(0):
            self._can_press = False
        else:
            self._can_press = True

        super(Color_clicker, self).__init__(value, size, color1, angle, x, y,
                                            top, bottom, left, right,
                                            is_collideable=is_collideable)

    def tick(self):
        if self._activated:
            if self.left <= games.mouse.x <= self.right and self.top <= games.mouse.y <= self.bottom:
                self.color = self._color2
                if games.mouse.is_pressed(0):
                    if self._can_press and self.func != None:
                        self.func()
            else:
                self.color = self._color1
        else:
            self.color = self._nonact_color

        if games.mouse.is_pressed(0):
            self._can_press = False
        else:
            self._can_press = True

    #------Properties------#

    ## color1
    def get_color1(self):
        return self._color1

    def set_color1(self, new_color):
        self._color1 = new_color

    color1 = property(get_color1, set_color1)

    ## color2
    def get_color2(self):
        return self._color2

    def set_color2(self, new_color):
        self._color2 = new_color

    color2 = property(get_color2, set_color2)

    ## nonact_color
    def get_nonact_color(self):
        return self._nonact_color

    def set_nonact_color(self, new_color):
        self._nonact_color = new_color

    nonact_color = property(get_nonact_color, set_nonact_color)

    ## activated
    def get_activated(self):
        return self._activated

    def set_activated(self, new_status):
        if new_status:
            self._activated = True
        else:
            self._activated = False

    activated = property(get_activated, set_activated)

class Growing_clicker(games.Text):
    def __init__(self, value, color, minsize, maxsize, dsize, func=None, x=0,
                 y=0, left=None, right=None, top=None, bottom=None,
                 is_collideable=False):

        if minsize > maxsize:
            raise games.GamesError, "maxsize must be greater than minsize"
        if dsize < 0:
            raise games.GamesError, "dsize must be a positive number"

        self._minsize = minsize
        self._maxsize = maxsize
        self._dsize = dsize
        self.func = func
        if games.mouse.is_pressed(0):
            self._can_press = False
        else:
            self._can_press = True

        super(Growing_clicker, self).__init__(value, minsize, color,
                                              x=x, y=y, left=left, right=right,
                                              top=top, bottom=bottom,
                                              is_collideable=is_collideable)

    def tick(self):
        if self.left <= games.mouse.x <= self.right and self.top <= games.mouse.y <= self.bottom:
            if self.size < self._maxsize:
                self.size += self._dsize
                if self.size > self._maxsize:
                    self.size = self._maxsize
            if games.mouse.is_pressed(0):
                if self._can_press and self.func != None:
                    self.func()
        else:
            if self.size > self._minsize:
                self.size -= self._dsize
                if self.size < self._minsize:
                    self.size = self._minsize

        if games.mouse.is_pressed(0):
            self._can_press = False
        else:
            self._can_press = True

    #------Properties------#

    ## minsize
    def get_minsize(self):
        return self._minsize

    def set_minsize(self, new_size):
        if new_size > self._maxsize:
            raise games.GamesError, "maxsize must be greater than minsize"
        else:
            self._minsize = new_size

    minsize = property(get_minsize, set_minsize)

    ## maxsize
    def get_maxsize(self):
        return self._maxsize

    def set_maxsize(self, new_size):
        if new_size < self._minsize:
            raise games.GamesError, "maxsize must be greater than minsize"
        else:
            self._maxsize = new_size

    maxsize = property(get_maxsize, set_maxsize)

    ## dsize
    def get_dsize(self):
        return self._dsize

    def set_dsize(self, new_dsize):
        if new_dsize < 0:
            raise games.GamesError, "dsize must be a positive number"
        else:
            self._dsize = new_dsize

    dsize = property(get_dsize, set_dsize)

class Chooser(games.Text):
    def __init__(self, size, color1, color2, choices, choice=None, func=None,
                 x=0, y=0, left=None, right=None, top=None, bottom=None,
                 is_collideable=False):
        if choice == None:
            choice = choices[0]
        if choice not in choices:
            raise games.GamesError, "choice must be in choices"
        self.__choices = choices
        self.__choice = choice
        self.__idx = choices.index(choice)
        self.func = func
        super(Chooser, self).__init__(choice, size, color1, x=x, y=y, left=left,
                                      right=right, top=top, bottom=bottom,
                                      is_collideable=is_collideable)
        self.rarrow = Color_clicker(">", size, color1, color2, func=self.incr,
                                    left=self.right, y=y)
        self.larrow = Color_clicker("<", size, color1, color2, func=self.decr,
                                    right=self.left, y=y)

    def __new_choice(self):
        self.value = self.__choices[self.__idx]
        self.rarrow.left=self.right
        self.larrow.right=self.left
        if self.func != None:
            self.func()

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
