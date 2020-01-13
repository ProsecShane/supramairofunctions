from os import environ
import math
import pygame


SIZE = 650
FUNC_MOVE = 5
FRAME_RATE = 30
M = MODE = ('N' if open('./Default Mode.txt', 'r').read().startswith('N') else 'T') + '.png'
MM = MUSIC_MODE = MODE.split('.')[0] + '.mp3'
environ['SDL_VIDEO_WINDOW_POS'] = '15,35'


def sign(num):
	return -1 if num < 0 else 1


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
		self.objects, self.goal = list(objects), None

	def draw(self):
		for obj in self.objects:
			obj.draw()

	def goal_reached(self):
		return game.player.obst.rect_in(*self.goal)


class Goal:
	def __init__(self, x, y, width, height, sprite, surface, level):
		self.obst = Obstacle(x, y, width, height, sprite, surface)
		self.level = level
		self.level.goal = (x, y, width, height)

	def draw(self):
		self.obst.draw()


class Player:
	def __init__(self, x, y, width, height, sprite, surface, level):
		self.obst = Obstacle(x, y, width, height, sprite, surface)
		self.on_func, self.level, self.grab = None, level, None

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
		if self.obst.x < 0:
			res['l'] = True
		if self.obst.x + self.obst.w >= SIZE:
			res['r'] = True
		if self.obst.y < 0:
			res['u'] = True
		if self.obst.y + self.obst.h >= SIZE:
			res['d'] = True
		return res

	def is_clipping(self):
		return any(list(self.clip().values()))

	def funcmove(self, func):
		def windowed(num1, num2):
			return game.cpl.on_pygame(num1, num2)

		def planed(num1, num2):
			return game.cpl.on_plane(num1, num2)

		if self.on_func is None:
			for i in range(int(self.obst.x), int(self.obst.x) + int(self.obst.w) + 1):
			    self.grab = Position(i - self.obst.x, windowed(None, func(planed(i, None)[0]))[1])
			    if self.obst.y <= self.grab.y <= self.obst.y + self.obst.h:
			    	self.grab.y -= self.obst.y
			    	self.on_func = True
			    	break
		if self.on_func is True and not self.is_clipping() and not self.level.goal_reached():
			self.move('r', FUNC_MOVE)
			value = windowed(None, func(planed(self.obst.x + self.grab.x + FUNC_MOVE, None)[0]))[1]
			self.move('u', self.obst.y - (value - self.grab.y))
		if self.on_func is True and self.level.goal_reached():
			pygame.mixer.music.load('sound/WinT.mp3')
			pygame.mixer.music.play()
			self.on_func = False
		if self.on_func is True and self.is_clipping():
			print('You suck!')
			self.on_func = False


class Game:
	def __init__(self, size_x, size_y, caption, icon):
		self.SIZE = Position(size_x, size_y)
		self.main = pygame.display.set_mode((self.SIZE.x, self.SIZE.y))
		pygame.display.set_caption(caption)
		pygame.display.set_icon(pygame.image.load('sprites/' + icon))
		self.clock = pygame.time.Clock()
		self.run = True
		self.cpl = None
		self.held = False
		pygame.mixer.init()

	def setup(self):
		self.main.fill((255, 255, 255))
		self.obsts = [Sprite(game.main, pygame.image.load('sprites/MainMenuT.png'), 0, 0),
		              Obstacle(-50, -200, 200, 100, pygame.image.load('sprites/Level1' + M), game.main),
		              Obstacle(-500, -250, 200, 100, pygame.image.load('sprites/Level3' + M), game.main)]
		self.level = Level(*self.obsts)
		self.goal = Goal(SIZE - 200, SIZE - 200, 200, 100, pygame.image.load('sprites/Level5' + M), game.main, self.level)
		self.player = Player(0, 0, 200, 100, pygame.image.load('sprites/Level5' + M), game.main, self.level)
		self.effects = None


	def after(self):
		pass

	def mainloop(self):
		self.setup()
		while self.run:
			self.clock.tick(FRAME_RATE)
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.run = False

			self.level.draw()
			self.cpl.draw_plane()
			self.cpl.draw_function(lambda x: x * x * -0.005 + SIZE)
			self.player.draw()
			self.goal.draw()

			if self.player.on_func is False:
				if self.effects is None:
					self.effects = 0
				else:
					self.effects += 5
				pygame.draw.rect(self.player.obst.sr, (255, 255, 255), (0, 0, self.effects, SIZE))
				pygame.draw.rect(self.player.obst.sr, (255, 255, 255), (SIZE - self.effects, 0, self.effects, SIZE))

			self.player.funcmove(lambda x: x * x * -0.005 + SIZE)
			
			if pygame.mouse.get_pressed()[0]:
				if not self.held:
					self.held = True

					pass
			else:
				self.held = False

			pygame.display.update()

		self.after()
		pygame.quit()


if __name__ == '__main__':
	pygame.init()
	game = Game(SIZE, SIZE, 'Supra Mairo Functions', 'Icon' + M)
	game.cpl = CoordsPlane(game.main, 0, SIZE)
	game.mainloop()
