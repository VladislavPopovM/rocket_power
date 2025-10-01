import curses
import random
import itertools
import locale
import time
from curses_tools import draw_frame, read_controls

# Глобальные константы
TIC_TIMEOUT = 0.1
STARS_COUNT = 100
STAR_SYMBOLS = '+*.:'
FRAME_SWITCH_INTERVAL = 2

# Границы и размеры
BORDER_WIDTH = 1
SPACESHIP_SIZE = 10  # Размер корабля для проверки границ
HINT_OFFSET = 2  # Отступ для подсказки
HINT_LONG_OFFSET = 40  # Отступ для длинной подсказки

# Анимация звезд
STAR_DIM_DURATION = 20
STAR_NORMAL_DURATION = 3
STAR_BOLD_DURATION = 5
STAR_OFFSET_MAX = 100

# Анимация выстрела
FIRE_FLASH_DURATION = 5
FIRE_MOVE_DURATION = 3
FIRE_SPEED = -0.9

# Позиционирование
CENTER_DIVISOR = 2
SPACESHIP_FIRE_OFFSET = 2


def load_rocket_frames():
    """Загружает кадры анимации ракеты из файлов."""
    with open('frames/rocket_frame_1.txt', 'r', encoding='utf-8') as f:
        frame1 = f.read()
    with open('frames/rocket_frame_2.txt', 'r', encoding='utf-8') as f:
        frame2 = f.read()
    return [frame1, frame2]


def sleep(seconds):
    """Простая функция задержки для корутин."""
    end_time = time.time() + seconds
    while time.time() < end_time:
        yield


def blink(canvas, row, column, symbol='*', offset_tics=0):
    """Генератор для анимации мерцания звезд."""
    for _ in range(offset_tics):
        yield
    
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(STAR_DIM_DURATION):
            yield

        canvas.addstr(row, column, symbol)
        for _ in range(STAR_NORMAL_DURATION):
            yield

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(STAR_BOLD_DURATION):
            yield

        canvas.addstr(row, column, symbol)
        for _ in range(STAR_NORMAL_DURATION):
            yield


def fire(canvas, start_row, start_column, rows_speed=FIRE_SPEED, columns_speed=0):
    """Генератор для анимации выстрела."""
    row, column = start_row, start_column
    max_row, max_column = canvas.getmaxyx()
    max_row -= BORDER_WIDTH
    max_column -= BORDER_WIDTH

    # Начальная вспышка
    canvas.addstr(round(row), round(column), '*')
    canvas.refresh()
    for _ in range(FIRE_FLASH_DURATION):
        yield

    canvas.addstr(round(row), round(column), 'O')
    canvas.refresh()
    for _ in range(FIRE_FLASH_DURATION):
        yield
    
    canvas.addstr(round(row), round(column), ' ')
    canvas.refresh()

    # Движение снаряда
    symbol = '-' if columns_speed else '|'
    curses.beep()

    while BORDER_WIDTH <= row < max_row and BORDER_WIDTH <= column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        canvas.refresh()
        for _ in range(FIRE_MOVE_DURATION):
            yield
        
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def animate_spaceship(canvas, rocket_frames, max_y, max_x):
    """Генератор для анимации корабля."""
    # Позиция корабля (начинаем в центре)
    spaceship_row = max_y // CENTER_DIVISOR
    spaceship_column = max_x // CENTER_DIVISOR
    
    # Итератор для кадров анимации корабля
    frame_iterator = itertools.cycle(rocket_frames)
    current_frame = next(frame_iterator)
    frame_counter = 0

    while True:
        # Читаем управление
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        
        # Стираем старый кадр корабля
        draw_frame(canvas, spaceship_row, spaceship_column, current_frame, negative=True)
        
        # Обновляем позицию корабля
        if rows_direction or columns_direction:
            new_row = spaceship_row + rows_direction
            new_column = spaceship_column + columns_direction
            if (BORDER_WIDTH <= new_row <= max_y - SPACESHIP_SIZE and 
                BORDER_WIDTH <= new_column <= max_x - SPACESHIP_SIZE):
                spaceship_row, spaceship_column = new_row, new_column
        
        # Обновляем кадр анимации
        frame_counter += 1
        if frame_counter >= FRAME_SWITCH_INTERVAL:
            current_frame = next(frame_iterator)
            frame_counter = 0
        
        # Рисуем текущий кадр корабля
        draw_frame(canvas, spaceship_row, spaceship_column, current_frame)
        
        # Возвращаем информацию о выстреле
        yield space_pressed, spaceship_row, spaceship_column


def draw(canvas):
    curses.curs_set(False)
    canvas.nodelay(True)

    max_y, max_x = canvas.getmaxyx()
    canvas.border()

    rocket_frames = load_rocket_frames()

    # Добавляем подсказку
    hint_text = "Press SPACE to fire!"
    canvas.addstr(BORDER_WIDTH, max_x - len(hint_text) - HINT_OFFSET, hint_text)

    # Создаем корутины для звезд
    coroutines = [blink(canvas, random.randint(BORDER_WIDTH, max_y - BORDER_WIDTH - 1), 
                      random.randint(BORDER_WIDTH, max_x - BORDER_WIDTH - 1), 
                      random.choice(STAR_SYMBOLS), 
                      random.randint(0, STAR_OFFSET_MAX)) 
                  for _ in range(STARS_COUNT)]

    # Создаем корутину для корабля
    spaceship_coro = animate_spaceship(canvas, rocket_frames, max_y, max_x)

    canvas.refresh()

    while True:
        # Получаем состояние корабля
        space_pressed, spaceship_row, spaceship_column = next(spaceship_coro)
        
        # Выстрел
        if space_pressed:
            fire_coro = fire(canvas, spaceship_row, spaceship_column + SPACESHIP_FIRE_OFFSET)
            coroutines.append(fire_coro)

        # Выполняем все корутины
        for coro in coroutines[:]:  # Создаем копию списка для безопасной итерации
            try:
                next(coro)
            except StopIteration:
                # Корутина завершилась, удаляем её
                coroutines.remove(coro)

        canvas.refresh()
        time.sleep(TIC_TIMEOUT)

def main(stdscr):
    """Основная функция программы."""
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    curses.use_default_colors()
    draw(stdscr)

if __name__ == '__main__':
    curses.wrapper(main)    