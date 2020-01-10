from os import environ
from sys import exit as closewindow
import math
import pygame


SIZE = 650
FUNC_MOVE = 5
FRAME_RATE = 30

MODE, IM, IMAGE_MODE, MM, MUSIC_MODE = None, None, None, None, None


def initmode(invert=True):
	global MODE, IM, IMAGE_MODE, MM, MUSIC_MODE

	if invert:
		MODE = 'N' if MODE == 'T' else 'T'
	else:
		MODE = 'N' if open('./Default Mode.txt', 'r').read().startswith('N') else 'T'
	IM = IMAGE_MODE = MODE + '.png'
	MM = MUSIC_MODE = MODE + '.mp3'


initmode(False)
environ['SDL_VIDEO_WINDOW_POS'] = '15,35'

SP = SPRITES = None

def initsprites():
	global SP, SPRITES

	def im(link):
		return pygame.image.load(link)

	SP = SPRITES = {'mainmenu': im('sprites/MainMenu' + IM), 'start': im('sprites/Start' + IM),
	                'quit': im('sprites/Quit' + IM), 'backtomenu': im('sprites/MenuBack' + IM),
	                'levelselect': im('sprites/Levels' + IM), 'mode': im('sprites/Mode' + IM),
	                'lvlBtn': dict([(i, im('sprites/Level' + str(i) + IM)) for i in range(1, 11)]),
	                'y': im('sprites/Y' + IM), 'yes': im('sprites/Confirm' + IM),
	                'form': im('sprites/Formula' + IM), 'none': im('sprites/None.png'),
	                'goal': im('sprites/Goal' + IM), 'plyStd': im('sprites/PlayerStand' + IM),
	                'plyGo': im('sprites/PlayerGo' + IM), 'back': im('sprites/Back' + IM),
	                'lvlBg': dict([(i, im('sprites/Level' + str(i) + 'Bg' + IM)) 
	                	           for i in range(1, 11)]),
	                'lvlBlock': dict([(i, im('sprites/Level' + str(i) + 'Block' + IM)) 
	                	              for i in range(1, 11)]),}


initsprites()

MU = MUSIC = None


def initmusic():
	global MU, MUSIC

	MU = MUSIC = {'mainmenu': './sound/MainMenu' + MM, 'levelselect': 'sound/LevelSelect' + MM,
	              'bump': 'sound/Bump' + MODE + '.ogg', 'win': 'sound/Win' + MM,
	              'level': dict([(i, 'sound/Level' + str(i) + MM) for i in range(1, 11)])}


initmusic()


def sign(num):
	return -1 if num < 0 else 1


def interp(func, eval_=True):
	func = func.replace('^', '**')
	pass
	return eval(func) if eval_ else func


class Position:
	def __init__(self, x, y):
		self.x, self.y = x, y


class CoordsPlane:
	def __init__(self, surface, pos_x, pos_y, size=SIZE):
		self.pos = Position(pos_x, pos_y)
		self.size = size
		self.srf = surface

	def on_plane(self, pos_x, pos_y):
		res = [None]
		if pos_x is not None:
			res = [pos_x - self.pos.x]
		if pos_y is not None:
			res += [self.size - pos_y - self.pos.y]
		else:
			res += [None]
		return res

	def on_pygame(self, pos_x, pos_y):
		res = [None]
		if pos_x is not None:
			res = [self.pos.x + pos_x]
		if pos_y is not None:
			res += [self.size * 2 - pos_y - self.pos.y]
		else:
			res += [None]
		return res

	def draw_plane(self):
		pygame.draw.line(self.srf, (0, 0, 0), (self.pos.x - self.size, self.pos.y),
			             (self.pos.x + self.size, self.pos.y))
		pygame.draw.line(self.srf, (0, 0, 0), (self.pos.x, self.pos.y + self.size),
			             (self.pos.x, self.pos.y - self.size))
		value = self.size // 100
		font = pygame.font.Font('freesansbold.ttf', 12) 
		for i in range(-1 * value, value + 1):
			t = i * 100
			pygame.draw.line(self.srf, (0, 0, 0), (self.pos.x - 10, self.pos.y + t), 
				             (self.pos.x + 10, self.pos.y + t))
			text = font.render(str(-1 * t), True, (0, 0, 0), (255, 255, 255))
			rect = text.get_rect()
			rect.center = (self.pos.x - 25, self.pos.y + t)
			self.srf.blit(text, rect)
			rect.center = (self.pos.x + 25, self.pos.y + t)
			self.srf.blit(text, rect)
			pygame.draw.line(self.srf, (0, 0, 0), (self.pos.x + t, self.pos.y - 10), 
				             (self.pos.x + t, self.pos.y + 10))
			text = font.render(str(t), True, (0, 0, 0), (255, 255, 255))
			rect = text.get_rect()
			rect.center = (self.pos.x + t, self.pos.y + 15)
			self.srf.blit(text, rect)
			rect.center = (self.pos.x + t, self.pos.y - 15)
			self.srf.blit(text, rect)

	def xy_to_pos(self, x, y):
		return Position(self.pos.x + x, self.pos.y - y)

	def draw_function(self, function):
		start = -1 * self.size + 1
		for i in range(-1 * self.size, self.size + 1):
			try:
				prev = self.xy_to_pos(i, function(i))
				break
			except BaseException:
				start += 1
		for x in range(start, self.size + 1):
			try:
				cur = self.xy_to_pos(x, function(x))
				if prev is None:
					prev = Position(cur.x, cur.y)
				pygame.draw.line(self.srf, (0, 0, 0), (prev.x, prev.y), (cur.x, cur.y))
				prev = Position(cur.x, cur.y)
			except BaseException:
				prev = None


class Obstacle:
	def __init__(self, x, y, width, height, sprite, surface):
		self.x, self.y, self.w, self.h, self.sp, self.sr = x, y, width, height, sprite, surface

	def point_in(self, x, y):
		return self.x <= x <= self.x + self.w and self.y <= y <= self.y + self.h

	def rect_in(self, x, y, width, height, recur=False):
		if ((self.point_in(x, y) or self.point_in(x + width, y) or
			 self.point_in(x, y + height) or self.point_in(x + width, y + height))):
		    return True
		if not recur:
			return Obstacle(x, y, width, height, None, None).rect_in(self.x, self.y, self.w, self.h, True)
		return False

	def draw(self):
		self.sr.blit(self.sp, (int(self.x), int(self.y)))


class Button:
	def __init__(self, x, y, width, height, sprite, surface, function, *args, **kwargs):
		self.obst = Obstacle(x, y, width, height, sprite, surface)
		self.f, self.a, self.k, self.held = function, list(args), dict(kwargs), False

	def is_pressed(self):
		return pygame.mouse.get_pressed()[0] and self.obst.point_in(*pygame.mouse.get_pos())

	def press(self):
		self.f(*self.a, **self.k)

	def react(self):
		if self.is_pressed():
			self.press()

	def draw(self):
		self.obst.draw()


class Sprite:
	def __init__(self, surface, sprite, x, y):
		self.surface, self.sprite, self.x, self.y = surface, sprite, x, y

	def draw(self):
		self.surface.blit(self.sprite, (self.x, self.y))


class Menu:
	def __init__(self, surface, background, *objects):
		self.bg, self.sf, self.objs, self.shown = background, surface, list(objects), False

	def show(self):
		self.shown = True

	def hide(self):
		self.shown = False

	def draw(self):
		if not self.shown:
			return
		self.sf.blit(self.bg, (0, 0))
		for obj in self.objs:
			obj.draw()

	def react(self):
		if not self.shown:
			return
		for obj in self.objs:
			if isinstance(obj, Button):
				obj.react()


class Level:
	def __init__(self, *objects):
		self.objects, self.goal, self.shown = list(objects), None, False

	def show(self):
		self.shown = True

	def hide(self):
		self.shown = False

	def draw(self):
		if not self.shown:
			return
		for obj in self.objects:
			obj.draw()

	def goal_reached(self):
		return game.player.obst.rect_in(*self.goal)


class Goal:
	def __init__(self, x, y, width, height, sprite, surface, level):
		self.obst = Obstacle(x, y, width, height, sprite, surface)
		self.level = level
		self.level.goal = (x, y, width, height)
		self.level.objects.append(Sprite(surface, sprite, x, y))

	def draw(self):
		self.obst.draw()


class Player:
	def __init__(self, x, y, width, height, sprite, surface, level):
		self.obst = Obstacle(x, y, width, height, sprite, surface)
		self.state, self.level, self.grab = 'none', level, None

	def draw(self):
		self.obst.draw()

	def move(self, direc, amount):
		if direc in ['u', 'd']:
			self.obst.y += amount if direc == 'd' else -1 * amount
		elif direc in ['l', 'r']:
			self.obst.x += amount if direc == 'r' else -1 * amount

	def clip(self):
		res = {'u': False, 'd': False, 'l': False, 'r': False}
		for obj in self.level.objects:
			if isinstance(obj, Obstacle):
				if obj.rect_in(self.obst.x, self.obst.y, self.obst.w, self.obst.h):
					if ((obj.x < self.obst.x + self.obst.w < obj.x + obj.w or 
						 obj.x < self.obst.x < obj.x + obj.w)):
					    if obj.y + obj.h > self.obst.y:
					    	res['u'] = True
					    if obj.y < self.obst.y + self.obst.h:
					    	res['d'] = True
					if ((obj.y < self.obst.y + self.obst.h < obj.y + obj.h or 
						 obj.y < self.obst.y < obj.y + obj.h)):
						if obj.x + obj.w > self.obst.x:
							res['l'] = True
						if obj.x < self.obst.x + self.obst.w:
							res['r'] = True
				if all(list(res.values())):
					break
		return res

	def is_clipping(self):
		return any(list(self.clip().values()))

	def funcmove(self, func, afterfunc, *args, **kwargs):
		if self.state == 'none':
			return

		if self.state == 'func_search':
			for i in range(int(self.obst.x), int(self.obst.x) + int(self.obst.w) + 1):
				self.grab = game.cpl.xy_to_pos(i, func(i))
				if self.obst.y <= self.grab.y <= self.obst.y + self.obst.h:
					self.grab.y -= self.obst.y
					self.state = 'on_func'
					self.obst.h = 85
					self.obst.sp = SP['plyGo']
					break
		if self.state == 'on_func' and not self.is_clipping() and not self.level.goal_reached():
			# value = windowed(None, func(planed(self.obst.x + self.grab.x + FUNC_MOVE, None)[0]))[1]
			value = game.cpl.xy_to_pos(0, func(self.obst.x + self.grab.x + FUNC_MOVE))
			self.move('r', FUNC_MOVE)
			self.move('u', self.obst.y - (value.y - self.grab.y) + 15)
		if self.level.goal_reached():
			self.state = 'goal_reached'
			self.obst.h = 100
			self.obst.sp = SP['plyStd']
			afterfunc(*args, **kwargs)
		if self.is_clipping():
			self.state = 'none'
			self.obst.h = 100
			self.obst.sp = SP['plyStd']
			game.clipped()


class Game:
	def __init__(self, size_x, size_y, caption, icon):
		self.held = False
		self.SIZE = Position(size_x, size_y)
		self.cpl, self.icon, self.caption = None, icon, caption
		self.main = pygame.display.set_mode((self.SIZE.x, self.SIZE.y))

	def toLvlSelect(self, _):
		self.showmenu(self.levelselect, MU['levelselect'], True)
		for level in self.levels:
			level.hide()
		self.flags['in_lvl'] = False
		self.player.level = self.nonlevel
		self.player.obst.x, self.player.obst.y = self.defCoords[0]
		self.player.state = 'none'
		self.player.obst.h = 100
		self.player.obst.sp = SP['plyStd']

	def clipped(self):
		pygame.mixer.Channel(1).play(self.bump)
		self.player.obst.x, self.player.obst.y = self.defCoords[self.flags['in_lvl']]
		self.player.state = 'none'
		self.player.obst.h = 100
		self.player.obst.sp = SP['plyStd']

	def changeMode(self, _):
		self.run = False
		self.flags['change'] = True

	def quit(self, _):
		self.run = False

	def toMainMenu(self, _):
		self.showmenu(self.mainmenu, MU['mainmenu'], True)

	def toLevel(self, number):
		self.levelbg.bg = SP['lvlBg'][number]
		self.showmenu(self.formula, MU['level'][number], True)
		self.levelbg.shown = True
		self.showlevel(number)
		self.flags['in_lvl'] = number
		self.player.level = self.levels[number - 1]
		self.player.obst.x, self.player.obst.y = self.defCoords[number]
		self.player.state = 'none'
		self.player.obst.h = 100
		self.player.obst.sp = SP['plyStd']

	def showlevel(self, number):
		self.levels[number - 1].show()
		for otherlevel in self.levels:
			if otherlevel is not self.levels[number - 1]:
				otherlevel.hide()

	def showmenu(self, menu, music, type):
		pygame.mixer.music.stop()
		self.flags['music'] = [music, type]
		menu.show()
		for othermenu in self.menus:
			if othermenu is not menu:
				othermenu.hide()

	def player_move(self, _):
		self.player.state = 'func_search'

	def setup(self):
		pygame.display.set_caption(self.caption)
		pygame.display.set_icon(pygame.image.load(self.icon))
		pygame.mixer.init()

		self.bump = pygame.mixer.Sound(MU['bump'])

		self.clock = pygame.time.Clock()
		self.run = True
		self.main.fill((255, 255, 255))

		objects = [Button(225, 150, 200, 100, SP['start'], self.main, self.toLvlSelect, None),
		           Button(225, 300, 200, 100, SP['mode'], self.main, self.changeMode, None),
		           Button(225, 450, 200, 100, SP['quit'], self.main, self.quit, None)]
		self.mainmenu = Menu(self.main, SP['mainmenu'], *objects[:])
		self.mainmenu.show()

		objects = ([Button(25, 105 * i + 5, 200, 100, SP['lvlBtn'][i + 1], self.main, 
			        self.toLevel, i + 1) for i in range(5)] + 
		           [Button(425, 105 * (i - 5) + 5, 200, 100, SP['lvlBtn'][i + 1], self.main, 
			        self.toLevel, i + 1) for i in range(5, 10)] +
		           [Button(225, 530, 200, 100, SP['backtomenu'], self.main, self.toMainMenu, None)])
		self.levelselect = Menu(self.main, SP['levelselect'], *objects[:])

		self.levelbg = Menu(self.main, SP['none'], Sprite(self.main, SP['none'], 0, 0))

		objects = [Sprite(self.main, SP['y'], 0, 550),
		           Sprite(self.main, SP['form'], 100, 550),
		           Button(550, 550, 100, 100, SP['yes'], self.main, self.player_move, None),
		           Button(SIZE - 50, 0, 50, 50, SP['back'], self.main, self.toLvlSelect, None)]
		self.formula = Menu(self.main, SP['none'], *objects[:])

		objects = [Obstacle(0, 0, 26, 26, SP['lvlBlock'][1], self.main),
		           Obstacle(0, 26, 26, 26, SP['lvlBlock'][1], self.main),
		           Obstacle(400, 300, 26, 26, SP['lvlBlock'][1], self.main)]
		self.level1 = Level(*objects[:])
		self.level1goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level1)

		objects = [Obstacle(0, 0, 26, 26, SP['lvlBlock'][2], self.main),
		           Obstacle(0, 26, 26, 26, SP['lvlBlock'][2], self.main)]
		self.level2 = Level(*objects[:])
		self.level2goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level2)

		objects = [Obstacle(0, 0, 26, 26, SP['lvlBlock'][3], self.main),
		           Obstacle(0, 26, 26, 26, SP['lvlBlock'][3], self.main)]
		self.level3 = Level(*objects[:])
		self.level3goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level3)

		objects = [Obstacle(0, 0, 26, 26, SP['lvlBlock'][4], self.main),
		           Obstacle(0, 26, 26, 26, SP['lvlBlock'][4], self.main)]
		self.level4 = Level(*objects[:])
		self.level4goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level4)

		objects = [Obstacle(0, 0, 26, 26, SP['lvlBlock'][5], self.main),
		           Obstacle(0, 26, 26, 26, SP['lvlBlock'][5], self.main)]
		self.level5 = Level(*objects[:])
		self.level5goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level5)

		objects = [Obstacle(0, 0, 26, 26, SP['lvlBlock'][6], self.main),
		           Obstacle(0, 26, 26, 26, SP['lvlBlock'][6], self.main)]
		self.level6 = Level(*objects[:])
		self.level6goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level6)

		objects = [Obstacle(0, 0, 26, 26, SP['lvlBlock'][7], self.main),
		           Obstacle(0, 26, 26, 26, SP['lvlBlock'][7], self.main)]
		self.level7 = Level(*objects[:])
		self.level7goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level7)

		objects = [Obstacle(0, 0, 26, 26, SP['lvlBlock'][8], self.main),
		           Obstacle(0, 26, 26, 26, SP['lvlBlock'][8], self.main)]
		self.level8 = Level(*objects[:])
		self.level8goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level8)

		objects = [Obstacle(0, 0, 26, 26, SP['lvlBlock'][9], self.main),
		           Obstacle(0, 26, 26, 26, SP['lvlBlock'][9], self.main)]
		self.level9 = Level(*objects[:])
		self.level9goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level9)

		objects = [Obstacle(0, 0, 26, 26, SP['lvlBlock'][10], self.main),
		           Obstacle(0, 26, 26, 26, SP['lvlBlock'][10], self.main)]
		self.level10 = Level(*objects[:])
		self.level10goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level10)

		self.nonlevel = Level(Obstacle(10000, 10000, 1, 1, SP['none'], self.main))
		self.nongoal = Goal(1000000, 1000000, 1, 1, SP['none'], self.main, self.nonlevel)

		self.defCoords = {1: (200, 200), 2: (200, 200), 3: (200, 200), 4: (200, 200), 
		                  5: (200, 200), 6: (200, 200), 7: (200, 200), 8: (200, 200), 
		                  9: (200, 200), 10: (200, 200), 0: (-10000, -10000)}

		self.player = Player(-10000, -10000, 50, 100, SP['plyStd'], self.main, self.nonlevel)

		self.flags = {'music': [MU['mainmenu'], True], 'change': False, 'in_lvl': False}
		self.levels = [self.level1, self.level2, self.level3, self.level4, self.level5, 
		               self.level6, self.level7, self.level8, self.level9, self.level10]
		self.menus = [self.mainmenu, self.levelselect, self.formula, self.levelbg]

	def after(self):
		pygame.mixer.music.stop()
		if self.flags['change']:
			initmode()
			initsprites()
			initmusic()
			self.mainloop()
		else:
			print('Window Closed')

	def set_flag(self, key, value):
		self.flags[key] = value

	def win_anim(self, _):
		pygame.mixer.music.stop()
		pygame.mixer.music.load(MU['win'])
		pygame.mixer.music.play()
		i = 1
		while pygame.mixer.music.get_busy() and self.run:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.run = False
			self.clock.tick(FRAME_RATE)
			leng = FUNC_MOVE * i
			pygame.draw.rect(self.main, (255, 255, 255), (0, 0, leng, SIZE))
			pygame.draw.rect(self.main, (255, 255, 255), (SIZE - leng, 0, leng, SIZE))
			pygame.display.update()
			i += 1
		self.toLvlSelect(None)
		self.player.state = 'none'

	def mainloop(self):
		self.setup()
		while self.run:
			self.clock.tick(FRAME_RATE)
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.run = False

			self.player.funcmove(lambda x: 300 - x / 7, self.win_anim, None)

			if self.flags['music'][1] in [True, 'loaded']:
				if self.flags['music'][1] is True:
					pygame.mixer.music.load(self.flags['music'][0])
					self.flags['music'][1] = 'loaded'
				if not pygame.mixer.music.get_busy():
					pygame.mixer.music.play()
			else:
				if self.flags['music'][1] is False:
					pygame.mixer.music.load(self.flags['music'][0])
					pygame.mixer.music.play()
					self.flags['music'][1] = 'played'

			if self.flags['in_lvl']:
				self.levelbg.draw()
				for level in self.levels:
				    level.draw()
				self.cpl.draw_plane()
				self.cpl.draw_function(lambda x: 300 - x / 7)
				self.formula.draw()
			else:
				for menu in self.menus:
				     menu.draw()

			if pygame.mouse.get_pressed()[0]:
				if not self.held:
					self.held = True
					for menu in self.menus:
						menu.react()
			else:
				self.held = False

			if self.flags['in_lvl']:
				self.player.draw()

			pygame.display.update()
		self.after()
		pygame.quit()


if __name__ == '__main__':
	pygame.init()
	game = Game(SIZE, SIZE, 'Supra Mairo Functions', 'sprites/Icon' + IM)
	game.cpl = CoordsPlane(game.main, 0, SIZE - 100)
	game.mainloop()
