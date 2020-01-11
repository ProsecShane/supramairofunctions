from os import environ  # для положения окна
from math import *  # мат. функции для функций
import pygame  # pygame


SIZE = 650  # размер квадратного окна
FUNC_MOVE = 5  # скорость движения по функции за один кадр
FRAME_RATE = 30  # кадров в секунду

MODE, IM, IMAGE_MODE, MM, MUSIC_MODE = None, None, None, None, None
# режимы для изображений и музыки


def initmode(invert=True):  # определения режима игры
	global MODE, IM, IMAGE_MODE, MM, MUSIC_MODE

	if invert:  # инвертирование режима (используется в самом коде)
		MODE = 'N' if MODE == 'T' else 'T'
	else:  # прочтение текстового файла для определения режима
		MODE = 'N' if open('./Default Mode.txt', 'r').read().startswith('N') else 'T'
	IM = IMAGE_MODE = MODE + '.png'  # режим для изображений
	MM = MUSIC_MODE = MODE + '.mp3'  # для музыки


initmode(False)  # определение режима
environ['SDL_VIDEO_WINDOW_POS'] = '15,35'  #положение окна

SP = SPRITES = None  # переменная для хранения спрайтов

def initsprites():  # прогрузка спрайтов
	global SP, SPRITES

	def im(link):  # просто сокращение кода для сохранения места
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
	                	              for i in range(1, 11)]),}  # хранение спрайтов


initsprites()  # подгрузка спрайтов

MU = MUSIC = None  # переменная для хранения музыки


def initmusic():  #подгрузка музыки
	global MU, MUSIC  # хранение музыки

	MU = MUSIC = {'mainmenu': './sound/MainMenu' + MM, 'levelselect': 'sound/LevelSelect' + MM,
	              'bump': 'sound/Bump' + MODE + '.ogg', 'win': 'sound/Win' + MM,
	              'level': dict([(i, 'sound/Level' + str(i) + MM) for i in range(1, 11)])}


initmusic()  # подгрузка музыки


def nroot(n, num):  # корень n-ой степени
	return num ** (1 / float(n))


def interp(res):  # интерпретация строки к лямбда-функции
	try:
	    res = res.replace('^', '**').replace('ctg', '1 / tan')
	    # смена знаков для eval-вычислений в питоне
	    numbers = list(map(str, list(range(10)))) + ['.']
	    # список строк всех цифр и точки
	    while '√' in res:  # преобразование знака корня
	    	i = res.index('√')
	    	if res[i - 1:i] in numbers:  # корень определённой степени
	    		index = res.index('√')
	    		while res[i - 1] in numbers and i > 0:
	    			i -= 1
	    		res = res[:i] + 'nroot(' + res[i:index] + ', ' + res[index + 2:]
	    	else:  # квадратный корень
	    		res = res[:i] + 'sqrt' + res[i + 1:]
	    while '!' in res:  # преобразование знака факториала
	        if res[res.find('!') - 1] in numbers:  # перед числом
	            index = res.find('!')
	            res = res[:index] + ')' + res[index + 1:]
	            index -= 1
	            while res[index] in numbers:
	                index -= 1
	            res = res[:index + 1] + 'factorial(' + res[index + 1:]
	        elif res[res.find('!') - 1] == ')':  # перед скобкой
	            brackets, index = 1, res.find('!')
	            res = res[:index] + ')' + res[index + 1:]
	            index -= 1
	            while brackets > 0:
	                index -= 1
	                if res[index] in '()':
	                    brackets += -1 if res[index] == '(' else 1
	            if res[index - 1] in 'lt':
	                while res[index] not in 'sf':
	                    index -= 1
	            res = res[:index] + 'factorial(' + res[index:]
	        else:  # перед чем-либо другим, т. е. с синтаксической ошибкой
	            res = eval('1*+')
	    return eval('lambda x: ' + res)  # результат - лямбда-функция
	except BaseException:  # при какой-либо синтаксической или математической ошибке
	    # возвращается функция у=х
		return lambda x: x


class Position:  # небольшой класс для удобного обращения через ".x" или ".y"
	def __init__(self, x, y):
		self.x, self.y = x, y


class CoordsPlane:  # класс координатной плоскости
	def __init__(self, surface, pos_x, pos_y, size=SIZE):
		self.pos = Position(pos_x, pos_y)  # положение центра
		self.size = size  # половина ширины
		self.srf = surface  # поверхность, на которой будет рисоваться
		self.coords = {}  # словарь с преобразованием "х к "у" по функции

	def draw_plane(self):  # рисование самой плоскости
		pygame.draw.line(self.srf, (0, 0, 0), (self.pos.x - self.size, self.pos.y),
			             (self.pos.x + self.size, self.pos.y))
		pygame.draw.line(self.srf, (0, 0, 0), (self.pos.x, self.pos.y + self.size),
			             (self.pos.x, self.pos.y - self.size))
		# главные линии
		value = self.size // 100
		font = pygame.font.Font('freesansbold.ttf', 12) # шрифт
		for i in range(-1 * value, value + 1):  # рисование отметок на каждые сто точек
			t = i * 100
			pygame.draw.line(self.srf, (0, 0, 0), (self.pos.x - 10, self.pos.y + t), 
				             (self.pos.x + 10, self.pos.y + t))
			# небольшие штрихи как обозначения
			text = font.render(str(-1 * t), True, (0, 0, 0), (255, 255, 255))
			rect = text.get_rect()
			rect.center = (self.pos.x - 25, self.pos.y + t)
			self.srf.blit(text, rect)
			rect.center = (self.pos.x + 25, self.pos.y + t)
			self.srf.blit(text, rect)
			# рисование подписей с двух сторон по первой оси
			pygame.draw.line(self.srf, (0, 0, 0), (self.pos.x + t, self.pos.y - 10), 
				             (self.pos.x + t, self.pos.y + 10))
			text = font.render(str(t), True, (0, 0, 0), (255, 255, 255))
			rect = text.get_rect()
			rect.center = (self.pos.x + t, self.pos.y + 15)
			self.srf.blit(text, rect)
			rect.center = (self.pos.x + t, self.pos.y - 15)
			self.srf.blit(text, rect)
			# рисование подписей с двух сторон по второй оси

	def xy_to_pos(self, x, y):  # координаты на окне в координаты на плоскости
		return Position(self.pos.x + x, self.pos.y - y)

	def draw_function(self, function):  # рисование функции
		start = -1 * self.size + 1
		for i in range(-1 * self.size, self.size + 1):
			try:  # нахождение самой левой определённой точки
				prev = self.xy_to_pos(i, function(i))
				break
			except BaseException:
				start += 1
		for x in range(start, self.size + 1):
			try:  # рисование функции от точки к точке с проверкой на их определённость
				cur = self.xy_to_pos(x, function(x))
				if prev is None:
					prev = Position(cur.x, cur.y)
				pygame.draw.line(self.srf, (0, 0, 0), (prev.x, prev.y), (cur.x, cur.y))
				pygame.draw.line(self.srf, (255, 255, 255), (prev.x, prev.y + 1), 
					             (cur.x, cur.y + 1))
				pygame.draw.line(self.srf, (255, 255, 255), (prev.x, prev.y - 1), 
					             (cur.x, cur.y - 1))
				self.coords[prev.x] = prev.y
				prev = Position(cur.x, cur.y)
			except BaseException:
				prev = None  # проверка на определённость точки


class Obstacle:  # класс-четырёхугольник со своими координатами, размером и спрайтом
	def __init__(self, x, y, width, height, sprite, surface):
		self.x, self.y, self.w, self.h, self.sp, self.sr = x, y, width, height, sprite, surface

	def point_in(self, x, y):  # находится ли точка в этом объекте
		return self.x <= x <= self.x + self.w and self.y <= y <= self.y + self.h

	def rect_in(self, x, y, width, height, recur=False):
		if ((self.point_in(x, y) or self.point_in(x + width, y) or
			 self.point_in(x, y + height) or self.point_in(x + width, y + height))):
		    return True  # пересекаются ли два 4-угольника
		if not recur:
			return Obstacle(x, y, width, height, None, None
				            ).rect_in(self.x, self.y, self.w, self.h, True)
		return False

	def draw(self):  # рисование объекта
		self.sr.blit(self.sp, (int(self.x), int(self.y)))


class Button:  # класс-кнопка, основан на Obstacle
	def __init__(self, x, y, width, height, sprite, surface, function, *args, **kwargs):
		self.obst = Obstacle(x, y, width, height, sprite, surface)
		self.f, self.a, self.k = function, list(args), dict(kwargs)

	def is_pressed(self):  # нажата ли кнопка
		return pygame.mouse.get_pressed()[0] and self.obst.point_in(*pygame.mouse.get_pos())

	def press(self):  # функция после нажатия кнопки
		self.f(*self.a, **self.k)

	def react(self):  # выполнить функцию кнопки, если она нажата
		if self.is_pressed():
			self.press()

	def draw(self):  # нарисовать
		self.obst.draw()


class Sprite:  # класс-спрайт
	def __init__(self, surface, sprite, x, y):
		self.surface, self.sprite, self.x, self.y = surface, sprite, x, y

	def draw(self):  # нарисовать спрайт на данных координатах
		self.surface.blit(self.sprite, (self.x, self.y))


class Menu:  # класс-меню, сборщик кнопок, спрайтов и др. объектов
	def __init__(self, surface, background, *objects):
		self.bg, self.sf, self.objs, self.shown = background, surface, list(objects), False

	def show(self):  # показать, то есть при вызове рисования меню будет нарисовано
		self.shown = True

	def hide(self):  # скрыть, то есть при вызове рисования меню не будет нарисовано
		self.shown = False

	def draw(self):  # нарисовать
		if not self.shown:
			return  # отмена рисования при скрытии меню
		self.sf.blit(self.bg, (0, 0))
		for obj in self.objs:
			obj.draw()  # рисование объектов, относящихся к меню

	def react(self):  # реакция меню
		if not self.shown:
			return  # отмена реакции при скрытии меню
		for obj in self.objs:
			if isinstance(obj, Button):
				obj.react()  # реакция всех кнопок, относящихся к меню


class Level:  # класс-уровень, сборник препятствий, победы и спрайтов
	def __init__(self, *objects):
		self.objects, self.goal, self.shown = list(objects), None, False

	def show(self):  # показать уровень
		self.shown = True

	def hide(self):  # скрыть уровень
		self.shown = False

	def draw(self):
		if not self.shown:
			return  # отмена рисования при скрытии уровня
		for obj in self.objects:
			obj.draw()  # рисование объектов уровня

	def goal_reached(self):  # достиг ли игрок победы
		return game.player.obst.rect_in(*self.goal)


class Goal:  # класс-победа, основан на Obstacle
	def __init__(self, x, y, width, height, sprite, surface, level):
		self.obst = Obstacle(x, y, width, height, sprite, surface)
		self.level = level  # привязка к уровню
		self.level.goal = (x, y, width, height)
		self.level.objects.append(Sprite(surface, sprite, x, y))

	def draw(self):  # рисование победы
		self.obst.draw()


class Player:  # класс-игрок, основан на Obstacle
	def __init__(self, x, y, width, height, sprite, surface, level):
		self.obst = Obstacle(x, y, width, height, sprite, surface)
		self.state, self.level, self.grab = 'none', level, None

	def draw(self):  # рисование
		self.obst.draw()

	def move(self, direc, amount):  # передвинуться в нужную сторону
		if direc in ['u', 'd']:
			self.obst.y += amount if direc == 'd' else -1 * amount
		elif direc in ['l', 'r']:
			self.obst.x += amount if direc == 'r' else -1 * amount

	def clip(self):  # застрял ли игрок в одном из объектов данного уровня
		res = {'u': False, 'd': False, 'l': False, 'r': False}  # с каких сторон
		for obj in self.level.objects:
			if isinstance(obj, Obstacle):
				if obj.rect_in(self.obst.x, self.obst.y, self.obst.w, self.obst.h):
					if ((obj.x < self.obst.x + self.obst.w < obj.x + obj.w or 
						 obj.x < self.obst.x < obj.x + obj.w)):
					    if obj.y + obj.h > self.obst.y:
					    	res['u'] = True
					    if obj.y < self.obst.y + self.obst.h:
					    	res['d'] = True  # проверка по координатам
					if ((obj.y < self.obst.y + self.obst.h < obj.y + obj.h or 
						 obj.y < self.obst.y < obj.y + obj.h)):
						if obj.x + obj.w > self.obst.x:
							res['l'] = True
						if obj.x < self.obst.x + self.obst.w:
							res['r'] = True
				if all(list(res.values())):
					break  # если со всех сторон, то конец цикла
		return res

	def is_clipping(self):  # застревает хоть с какой-то стороны
		return any(list(self.clip().values()))

	def funcmove(self, func, afterfunc, *args, **kwargs):  # движение по функции
		if self.state == 'none':
			return  # если состояние не определенно, то и двигаться не надо

		if self.state == 'func_search':  # при поиске функции
			for i in range(int(self.obst.x), int(self.obst.x) + int(self.obst.w) + 1):
				# перебор всех "х"-координат игрока
				if self.obst.y < game.cpl.coords.get(i, -5555555555) < self.obst.y + self.obst.h:
					self.grab = Position(i - self.obst.x, game.cpl.coords[i] - self.obst.y)
					# какой частью зацеплено
					self.state = 'on_func'  # смена состояния - на функции
					self.obst.h = 85  # смена спрайта
					self.obst.sp = SP['plyGo']
					break
			if self.state == 'func_search':
				self.state = 'none'  # отмена состояния при ненахождении функции
		if self.state == 'on_func' and not self.is_clipping() and not self.level.goal_reached():
			self.obst.x += FUNC_MOVE  # движение на функции
			self.obst.y = game.cpl.coords[self.obst.x + self.grab.x] - self.grab.y + 15
		if self.level.goal_reached():  # достиг победы
			self.state = 'goal_reached'  # смена состояния
			self.obst.h = 100  # смена спрайта
			self.obst.sp = SP['plyStd']
			afterfunc(*args, **kwargs)  # выполнение функции после достижения победы
		if self.is_clipping():  # застрял
			self.state = 'none'  # отмена состояния
			self.obst.h = 100  # смена спрайта
			self.obst.sp = SP['plyStd']
			game.clipped()  # # выполнение функции после застревания


class Game:  # класс-игра
	def __init__(self, size_x, size_y, caption, icon):
		self.held = False  # зажата ли кнопка мыши
		self.SIZE = Position(size_x, size_y)  # размер
		self.cpl, self.icon, self.caption = None, icon, caption
		# коорд. плоск., иконка, название окна
		self.main = pygame.display.set_mode((self.SIZE.x, self.SIZE.y))
		# главный холст/поверхность

	def toLvlSelect(self, _):  # в "Выбор уровня"
		self.showmenu(self.levelselect, MU['levelselect'], True)
		# меню "Выбор уровня"
		for level in self.levels:
			level.hide()  # скрытие всех уровней
		self.flags['in_lvl'] = False  # флаг - вне уровня
		self.player.level = self.nonlevel  # уровень - никакой
		self.player.obst.x, self.player.obst.y = self.defCoords[0]
		# игрок перемещается за окно
		self.player.state = 'none'  # отмена состояния игрока
		self.player.obst.h = 100  # смена спрайта игрока
		self.player.obst.sp = SP['plyStd']

	def clipped(self):  # игрок застрял
		pygame.mixer.Channel(1).play(self.bump)  # звук удара
		self.player.obst.x, self.player.obst.y = self.defCoords[self.flags['in_lvl']]
		# возвращение в начальное положение
		self.player.state = 'none'  # смена состояния и спрайта
		self.player.obst.h = 100
		self.player.obst.sp = SP['plyStd']

	def changeMode(self, _):  # смена режима игры
		self.run = False
		self.flags['change'] = True

	def quit(self, _):  # выход
		self.run = False

	def toMainMenu(self, _):  # в "Главное меню"
		self.showmenu(self.mainmenu, MU['mainmenu'], True)

	def toLevel(self, number):  # в уровень
		self.levelbg.bg = SP['lvlBg'][number]
		# выбор заднего фона
		self.showmenu(self.formula, MU['level'][number], True)
		# показание меню формулы
		self.levelbg.shown = True  # и заднего фона
		self.showlevel(number)  # показать нужный уровень
		self.flags['in_lvl'] = number  # флаг - в каком уровне
		self.player.level = self.levels[number - 1]  # уровень для игрока
		self.player.obst.x, self.player.obst.y = self.defCoords[number]
		self.player.state = 'none'  # смена состояния, положения и спрайта
		self.player.obst.h = 100
		self.player.obst.sp = SP['plyStd']
		self.func = lambda x: x  # установка начальной функции "у=х"
		self.strfunc = 'x'

	def showlevel(self, number):  # показать уровень
		self.levels[number - 1].show()
		for otherlevel in self.levels:  # и скрыть все другие
			if otherlevel is not self.levels[number - 1]:
				otherlevel.hide()

	def showmenu(self, menu, music, type):  # показать меню,
		pygame.mixer.music.stop()
		self.flags['music'] = [music, type]  # установить нужную музыку
		menu.show()
		for othermenu in self.menus:
			if othermenu is not menu:  # и скрыть остальные меню
				othermenu.hide()

	def player_move(self, _):  # начать поиск функции у игрока
		self.player.state = 'func_search'

	def setup(self):  # перед главным циклом
		pygame.display.set_caption(self.caption)
		pygame.display.set_icon(pygame.image.load(self.icon))
		pygame.mixer.init()  # установка иконки и называния окна

		self.bump = pygame.mixer.Sound(MU['bump'])  # подгрузка звука удара

		self.clock = pygame.time.Clock()  # установка часов
		self.run = True  # определение, идёт ли игра
		self.main.fill((255, 255, 255))  # задний фон как белый изначально
		self.func = lambda x: x  # установка начальной функции
		self.strfunc = 'x'

		objects = [Button(225, 150, 200, 100, SP['start'], self.main, self.toLvlSelect, None),
		           Button(225, 300, 200, 100, SP['mode'], self.main, self.changeMode, None),
		           Button(225, 450, 200, 100, SP['quit'], self.main, self.quit, None)]
		self.mainmenu = Menu(self.main, SP['mainmenu'], *objects[:])
		self.mainmenu.show()  # Главное меню

		objects = ([Button(25, 105 * i + 5, 200, 100, SP['lvlBtn'][i + 1], self.main, 
			        self.toLevel, i + 1) for i in range(5)] + 
		           [Button(425, 105 * (i - 5) + 5, 200, 100, SP['lvlBtn'][i + 1], self.main, 
			        self.toLevel, i + 1) for i in range(5, 10)] +
		           [Button(225, 530, 200, 100, SP['backtomenu'], self.main, self.toMainMenu, None)])
		self.levelselect = Menu(self.main, SP['levelselect'], *objects[:])  # Выбор уровня

		self.levelbg = Menu(self.main, SP['none'], Sprite(self.main, SP['none'], 0, 0))
		# задний фон для уровней

		objects = [Sprite(self.main, SP['y'], 0, 550),
		           Sprite(self.main, SP['form'], 100, 550),
		           Button(550, 550, 100, 100, SP['yes'], self.main, self.player_move, None),
		           Button(SIZE - 50, 0, 50, 50, SP['back'], self.main, self.toLvlSelect, None)]
		self.formula = Menu(self.main, SP['none'], *objects[:])  # формула и т. п.

		# далее идут уровни

		objects = ([Obstacle(0, 26 * i, 26, 26, SP['lvlBlock'][1], self.main) for i in range(21)] +
				   [Obstacle(SIZE - 26, 26 * i, 26, 26, SP['lvlBlock'][1], self.main) 
				    for i in range(21)] +
				   [Obstacle(SIZE - 52, 26 * i, 26, 26, SP['lvlBlock'][1], self.main) 
				    for i in range(10, 21)] +
				   [Obstacle(SIZE - 78, 26 * i, 26, 26, SP['lvlBlock'][1], self.main) 
				    for i in range(10, 21)] +
				   [Obstacle(26 * i, 0, 26, 26, SP['lvlBlock'][1], self.main) for i in range(25)] +
				   [Obstacle(26 * i, SIZE - 126, 26, 26, SP['lvlBlock'][1], self.main) 
				    for i in range(25)])
		self.level1 = Level(*objects[:])
		self.level1goal = Goal(SIZE - 76, 210, 50, 50, SP['goal'], self.main, self.level1)

		objects = ([Obstacle(0, 26 * i, 26, 26, SP['lvlBlock'][2], self.main) for i in range(21)] +
				   [Obstacle(SIZE - 26, 26 * i, 26, 26, SP['lvlBlock'][2], self.main) 
				    for i in range(21)] +
				   [Obstacle(26 * i, 0, 26, 26, SP['lvlBlock'][2], self.main) for i in range(25)] +
				   [Obstacle(26 * i, SIZE - 126, 26, 26, SP['lvlBlock'][2], self.main) 
				    for i in range(25)])
		self.level2 = Level(*objects[:])
		self.level2goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level2)

		objects = ([Obstacle(0, 26 * i, 26, 26, SP['lvlBlock'][3], self.main) for i in range(21)] +
				   [Obstacle(SIZE - 26, 26 * i, 26, 26, SP['lvlBlock'][3], self.main) 
				    for i in range(21)] +
				   [Obstacle(26 * i, 0, 26, 26, SP['lvlBlock'][3], self.main) for i in range(25)] +
				   [Obstacle(26 * i, SIZE - 126, 26, 26, SP['lvlBlock'][3], self.main) 
				    for i in range(25)])
		self.level3 = Level(*objects[:])
		self.level3goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level3)

		objects = ([Obstacle(0, 26 * i, 26, 26, SP['lvlBlock'][4], self.main) for i in range(21)] +
				   [Obstacle(SIZE - 26, 26 * i, 26, 26, SP['lvlBlock'][4], self.main) 
				    for i in range(21)] +
				   [Obstacle(26 * i, 0, 26, 26, SP['lvlBlock'][4], self.main) for i in range(25)] +
				   [Obstacle(26 * i, SIZE - 126, 26, 26, SP['lvlBlock'][4], self.main) 
				    for i in range(25)])
		self.level4 = Level(*objects[:])
		self.level4goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level4)

		objects = ([Obstacle(0, 26 * i, 26, 26, SP['lvlBlock'][5], self.main) for i in range(21)] +
				   [Obstacle(SIZE - 26, 26 * i, 26, 26, SP['lvlBlock'][5], self.main) 
				    for i in range(21)] +
				   [Obstacle(26 * i, 0, 26, 26, SP['lvlBlock'][5], self.main) for i in range(25)] +
				   [Obstacle(26 * i, SIZE - 126, 26, 26, SP['lvlBlock'][5], self.main) 
				    for i in range(25)] +
				   [Obstacle(26 * i, (39 / 2 * i + 150) - (39 / 2 * i + 150) % 26, 26, 26, 
				   	         SP['lvlBlock'][1], self.main) for i in range(1, 24)] +
				   [Obstacle(26 * i, (39 / 2 * i - 50) - (39 / 2 * i - 50) % 26, 26, 26, 
				   	         SP['lvlBlock'][1], self.main) for i in range(1, 24)])
		self.level5 = Level(*objects[:])
		self.level5goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level5)

		objects = ([Obstacle(0, 26 * i, 26, 26, SP['lvlBlock'][6], self.main) for i in range(21)] +
				   [Obstacle(SIZE - 26, 26 * i, 26, 26, SP['lvlBlock'][6], self.main) 
				    for i in range(21)] +
				   [Obstacle(26 * i, 0, 26, 26, SP['lvlBlock'][6], self.main) for i in range(25)] +
				   [Obstacle(26 * i, SIZE - 126, 26, 26, SP['lvlBlock'][6], self.main) 
				    for i in range(25)])
		self.level6 = Level(*objects[:])
		self.level6goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level6)

		objects = ([Obstacle(0, 26 * i, 26, 26, SP['lvlBlock'][7], self.main) for i in range(21)] +
				   [Obstacle(SIZE - 26, 26 * i, 26, 26, SP['lvlBlock'][7], self.main) 
				    for i in range(21)] +
				   [Obstacle(26 * i, 0, 26, 26, SP['lvlBlock'][7], self.main) for i in range(25)] +
				   [Obstacle(26 * i, SIZE - 126, 26, 26, SP['lvlBlock'][7], self.main) 
				    for i in range(25)])
		self.level7 = Level(*objects[:])
		self.level7goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level7)

		objects = ([Obstacle(0, 26 * i, 26, 26, SP['lvlBlock'][8], self.main) for i in range(21)] +
				   [Obstacle(SIZE - 26, 26 * i, 26, 26, SP['lvlBlock'][8], self.main) 
				    for i in range(21)] +
				   [Obstacle(26 * i, 0, 26, 26, SP['lvlBlock'][8], self.main) for i in range(25)] +
				   [Obstacle(26 * i, SIZE - 126, 26, 26, SP['lvlBlock'][8], self.main) 
				    for i in range(25)])
		self.level8 = Level(*objects[:])
		self.level8goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level8)

		objects = ([Obstacle(0, 26 * i, 26, 26, SP['lvlBlock'][9], self.main) for i in range(21)] +
				   [Obstacle(SIZE - 26, 26 * i, 26, 26, SP['lvlBlock'][9], self.main) 
				    for i in range(21)] +
				   [Obstacle(26 * i, 0, 26, 26, SP['lvlBlock'][9], self.main) for i in range(25)] +
				   [Obstacle(26 * i, SIZE - 126, 26, 26, SP['lvlBlock'][9], self.main) 
				    for i in range(25)])
		self.level9 = Level(*objects[:])
		self.level9goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level9)

		objects = ([Obstacle(0, 26 * i, 26, 26, SP['lvlBlock'][10], self.main) for i in range(21)] +
				   [Obstacle(SIZE - 26, 26 * i, 26, 26, SP['lvlBlock'][10], self.main) 
				    for i in range(21)] +
				   [Obstacle(26 * i, 0, 26, 26, SP['lvlBlock'][10], self.main) for i in range(25)] +
				   [Obstacle(26 * i, SIZE - 126, 26, 26, SP['lvlBlock'][10], self.main) 
				    for i in range(25)])
		self.level10 = Level(*objects[:])
		self.level10goal = Goal(600, 300, 50, 50, SP['goal'], self.main, self.level10)

		self.nonlevel = Level(Obstacle(10000, 10000, 1, 1, SP['none'], self.main))
		self.nongoal = Goal(1000000, 1000000, 1, 1, SP['none'], self.main, self.nonlevel)
		# несуществующий уровень для временного хранения игрока

		self.defCoords = {1: (30, SIZE - 230), 2: (200, 200), 3: (200, 200), 4: (200, 200), 
		                  5: (200, 200), 6: (200, 200), 7: (200, 200), 8: (200, 200), 
		                  9: (200, 200), 10: (200, 200), 0: (-10000, -10000)}
		# начальные коорд. для уровней

		self.player = Player(-10000, -10000, 50, 100, SP['plyStd'], self.main, self.nonlevel)
		# игрок

		self.flags = {'music': [MU['mainmenu'], True], 'change': False, 'in_lvl': False}
		# флаги
		self.levels = [self.level1, self.level2, self.level3, self.level4, self.level5, 
		               self.level6, self.level7, self.level8, self.level9, self.level10]
		# список уровней
		self.menus = [self.mainmenu, self.levelselect, self.formula, self.levelbg]
		# список меню
		self.keysheld = {}  # какие клавиши зажаты

	def after(self):  # после главного цикла
		pygame.mixer.music.stop()
		if self.flags['change']:  # смена режима игры
			initmode()
			initsprites()
			initmusic()  # перезагрузка всего
			self.mainloop()
		else:
			print('Window Closed')  # закрытие окна

	def set_flag(self, key, value):
		self.flags[key] = value  # установить значение флага

	def win_anim(self, _):  # победный сиквенс
		pygame.mixer.music.stop()
		pygame.mixer.music.load(MU['win'])
		pygame.mixer.music.play()  # победная музыка
		i = 1
		while pygame.mixer.music.get_busy() and self.run:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.run = False
			self.clock.tick(FRAME_RATE)
			leng = FUNC_MOVE * i  # эффект действует пока играет музыка
			pygame.draw.rect(self.main, (255, 255, 255), (0, 0, leng, SIZE))
			pygame.draw.rect(self.main, (255, 255, 255), (SIZE - leng, 0, leng, SIZE))
			pygame.display.update()
			i += 1
		self.toLvlSelect(None)  # в "Выбор уровня"
		self.player.state = 'none'  # отмена состояния игрока

	def mainloop(self):  # главный цикл
		self.setup()  # предцикловые действия
		while self.run:
			self.clock.tick(FRAME_RATE)  # смена кадра
			for event in pygame.event.get():
				if event.type == pygame.QUIT:  # закрытие окна
					self.run = False

			self.func = interp(self.strfunc)  # интерпретация функции

			self.player.funcmove(self.func, self.win_anim, None)
			# попытка движения игрока по функции

			if self.flags['music'][1] in [True, 'loaded']:  # запуск музыки
				if self.flags['music'][1] is True:  # с повторением
					pygame.mixer.music.load(self.flags['music'][0])
					self.flags['music'][1] = 'loaded'
				if not pygame.mixer.music.get_busy():
					pygame.mixer.music.play()
			else:
				if self.flags['music'][1] is False:  # без повторения
					pygame.mixer.music.load(self.flags['music'][0])
					pygame.mixer.music.play()
					self.flags['music'][1] = 'played'

			if self.flags['in_lvl']:  # если в уровне
				self.levelbg.draw()  # рисование заднего фона
				for level in self.levels:
				    level.draw()  # рисование всех не скрытых уровней
				self.cpl.draw_plane()  # рисование плоскости
				self.cpl.draw_function(self.func)  # рисование функции
				self.formula.draw()  # рисование формулы

				keys = pygame.key.get_pressed()  # проверка нажатых клавиш и действия
				if keys[pygame.K_0] and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
					if not self.keysheld.get(')', False):
						self.strfunc += ')'
						self.keysheld[')'] = True
				else:
					self.keysheld[')'] = False
					if keys[pygame.K_0] or keys[pygame.K_KP0]:
						if not self.keysheld.get('0', False):
							self.strfunc += '0'
							self.keysheld['0'] = True
					else:
						self.keysheld['0'] = False
				if (((keys[pygame.K_1] and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])) 
					 or keys[pygame.K_f])):
					if not self.keysheld.get('!', False):
						self.strfunc += '!'
						self.keysheld['!'] = True
				else:
					self.keysheld['!'] = False
					if keys[pygame.K_1] or keys[pygame.K_KP1]:
						if not self.keysheld.get('1', False):
							self.strfunc += '1'
							self.keysheld['1'] = True
					else:
						self.keysheld['1'] = False
				if keys[pygame.K_2] or keys[pygame.K_KP2]:
					if not self.keysheld.get('2', False):
						self.strfunc += '2'
						self.keysheld['2'] = True
				else:
					self.keysheld['2'] = False
				if keys[pygame.K_3] or keys[pygame.K_KP3]:
					if not self.keysheld.get('3', False):
						self.strfunc += '3'
						self.keysheld['3'] = True
				else:
					self.keysheld['3'] = False
				if keys[pygame.K_4] or keys[pygame.K_KP4]:
					if not self.keysheld.get('4', False):
						self.strfunc += '4'
						self.keysheld['4'] = True
				else:
					self.keysheld['4'] = False
				if keys[pygame.K_5] or keys[pygame.K_KP5]:
					if not self.keysheld.get('5', False):
						self.strfunc += '5'
						self.keysheld['5'] = True
				else:
					self.keysheld['5'] = False
				if keys[pygame.K_6] and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
					if not self.keysheld.get('^', False):
						self.strfunc += '^'
						self.keysheld['^'] = True
				else:
					self.keysheld['^'] = False
					if keys[pygame.K_6] or keys[pygame.K_KP6]:
						if not self.keysheld.get('6', False):
							self.strfunc += '6'
							self.keysheld['6'] = True
					else:
						self.keysheld['6'] = False
				if keys[pygame.K_7] or keys[pygame.K_KP7]:
					if not self.keysheld.get('7', False):
						self.strfunc += '7'
						self.keysheld['7'] = True
				else:
					self.keysheld['7'] = False
				if (((keys[pygame.K_8] and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])) 
					 or keys[pygame.K_KP_MULTIPLY])):
					if not self.keysheld.get('*', False):
						self.strfunc += '*'
						self.keysheld['*'] = True
				else:
					self.keysheld['*'] = False
					if keys[pygame.K_8] or keys[pygame.K_KP8]:
						if not self.keysheld.get('8', False):
							self.strfunc += '8'
							self.keysheld['8'] = True
					else:
						self.keysheld['8'] = False
				if keys[pygame.K_9] and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
					if not self.keysheld.get('(', False):
						self.strfunc += '('
						self.keysheld['('] = True
				else:
					self.keysheld['('] = False
					if keys[pygame.K_9] or keys[pygame.K_KP9]:
						if not self.keysheld.get('9', False):
							self.strfunc += '9'
							self.keysheld['9'] = True
					else:
						self.keysheld['9'] = False
				if (((keys[pygame.K_EQUALS] and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])) 
					 or keys[pygame.K_KP_PLUS])):
					if not self.keysheld.get('+', False):
						self.strfunc += '+'
						self.keysheld['+'] = True
				else:
					self.keysheld['+'] = False
				if keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]:
					if not self.keysheld.get('-', False):
						self.strfunc += '-'
						self.keysheld['-'] = True
				else:
					self.keysheld['-'] = False
				if keys[pygame.K_SLASH] or keys[pygame.K_KP_DIVIDE]:
					if not self.keysheld.get('/', False):
						self.strfunc += '/'
						self.keysheld['/'] = True
				else:
					self.keysheld['/'] = False
				if keys[pygame.K_s]:
					if not self.keysheld.get('sin', False):
						self.strfunc += 'sin('
						self.keysheld['sin'] = True
				else:
					self.keysheld['sin'] = False
				if keys[pygame.K_c]:
					if not self.keysheld.get('cos', False):
						self.strfunc += 'cos('
						self.keysheld['cos'] = True
				else:
					self.keysheld['cos'] = False
				if keys[pygame.K_t]:
					if not self.keysheld.get('tan', False):
						self.strfunc += 'tan('
						self.keysheld['tan'] = True
				else:
					self.keysheld['tan'] = False
				if keys[pygame.K_g]:
					if not self.keysheld.get('ctg', False):
						self.strfunc += 'ctg('
						self.keysheld['ctg'] = True
				else:
					self.keysheld['ctg'] = False
				if keys[pygame.K_p]:
					if not self.keysheld.get('pi', False):
						self.strfunc += 'pi'
						self.keysheld['pi'] = True
				else:
					self.keysheld['pi'] = False
				if keys[pygame.K_r]:
					if not self.keysheld.get('√', False):
						self.strfunc += '√'
						self.keysheld['√'] = True
				else:
					self.keysheld['√'] = False
				if keys[pygame.K_a]:
					if not self.keysheld.get('a', False):
						self.strfunc += 'abs('
						self.keysheld['a'] = True
				else:
					self.keysheld['a'] = False
				if keys[pygame.K_x]:
					if not self.keysheld.get('x', False):
						self.strfunc += 'x'
						self.keysheld['x'] = True
				else:
					self.keysheld['x'] = False
				if keys[pygame.K_RETURN]:
					if not self.keysheld.get('Return', False):
						self.player_move(None)
						self.keysheld['Return'] = True
				else:
					self.keysheld['Return'] = False
				if keys[pygame.K_PERIOD]:
					if not self.keysheld.get('.', False):
						self.strfunc += '.'
						self.keysheld['.'] = True
				else:
					self.keysheld['.'] = False
				if keys[pygame.K_BACKSPACE]:
					if not self.keysheld.get('Backspace', False):
						if self.strfunc[-1:] in '0123456789.()x√!^+-*/':
							self.strfunc = self.strfunc[:-1]
						elif self.strfunc[-1:] == 'i':
							self.strfunc = self.strfunc[:-2]
						else:
							self.strfunc = self.strfunc[:-3]
						self.keysheld['Backspace'] = True
				else:
					self.keysheld['Backspace'] = False

				for i in range(50, 0, -1):  # печатание текста формулы
					font = pygame.font.Font('freesansbold.ttf', i)
					text = font.render(self.strfunc, True, (0, 0, 0), (255, 255, 255))
					rect = text.get_rect()
					rect.left = 100
					rect.centery = SIZE - 50
					if rect.width <= SIZE - 200 and rect.height <= 100:
						self.main.blit(text, rect)
						break
			else:
				for menu in self.menus:  # рисование нескрытых меню, если не в уровне
				     menu.draw()

			if pygame.mouse.get_pressed()[0]:
				if not self.held:
					self.held = True
					for menu in self.menus:  # реакция всех не скрытых меню
						menu.react()
			else:
				self.held = False

			if self.flags['in_lvl']:
				self.player.draw()  # рисование игрока, если в уровне

			pygame.display.update()
		self.after()  # послецикловые действия
		pygame.quit()  # выход


if __name__ == '__main__':
	pygame.init()  # начало
	game = Game(SIZE, SIZE, 'Supra Mairo Functions', 'sprites/Icon' + IM)
	# игра
	game.cpl = CoordsPlane(game.main, 0, SIZE - 100)  # плоскость
	game.mainloop()  # главный цикл
