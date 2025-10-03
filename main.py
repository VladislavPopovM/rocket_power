import asyncio
import curses
import random
import itertools
import locale
from curses_tools import draw_frame, read_controls, get_frame_size
from physics import update_speed

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
GARBAGE_FILES = [
    'frames/duck.txt',
    'frames/hubble.txt',
    'frames/lamp.txt',
    'frames/trash_small.txt',
    'frames/trash_large.txt',
    'frames/trash_xl.txt',
]
GARBAGE_SPAWN_DELAY_RANGE = (10, 30)
GARBAGE_SPEED_RANGE = (0.3, 1.0)


def load_rocket_frames():
    """Загружает кадры анимации ракеты из файлов."""
    with open('frames/rocket_frame_1.txt', 'r', encoding='utf-8') as f:
        frame1 = f.read()
    with open('frames/rocket_frame_2.txt', 'r', encoding='utf-8') as f:
        frame2 = f.read()
    return [frame1, frame2]


def load_garbage_frames():
    """Загружает кадры мусора."""
    frames = []
    for path in GARBAGE_FILES:
        with open(path, 'r', encoding='utf-8') as fh:
            frames.append(fh.read())
    return frames


async def sleep(tics=1):
    """Задержка на указанное количество тиков."""
    if tics <= 0:
        return
    await asyncio.sleep(tics * TIC_TIMEOUT)


async def blink(canvas, row, column, symbol='*', offset_tics=0):
    """Корутина для анимации мерцания звезд."""
    await sleep(offset_tics)

    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        canvas.refresh()
        await sleep(STAR_DIM_DURATION)

        canvas.addstr(row, column, symbol)
        canvas.refresh()
        await sleep(STAR_NORMAL_DURATION)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        canvas.refresh()
        await sleep(STAR_BOLD_DURATION)

        canvas.addstr(row, column, symbol)
        canvas.refresh()
        await sleep(STAR_NORMAL_DURATION)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Column position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await sleep(1)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed


async def fill_orbit_with_garbage(canvas, garbage_frames, garbage_tasks):
    """Создает бесконечный поток мусора."""
    while True:
        frame = random.choice(garbage_frames)
        _, columns = canvas.getmaxyx()
        _, frame_width = get_frame_size(frame)
        max_column = max(columns - frame_width - BORDER_WIDTH, BORDER_WIDTH)
        column = random.randint(BORDER_WIDTH, max_column)
        speed = random.uniform(*GARBAGE_SPEED_RANGE)
        task = asyncio.create_task(fly_garbage(canvas, column, frame, speed))
        garbage_tasks.add(task)
        task.add_done_callback(lambda task: garbage_tasks.discard(task))
        await sleep(random.randint(*GARBAGE_SPAWN_DELAY_RANGE))


async def fire(canvas, start_row, start_column, rows_speed=FIRE_SPEED, columns_speed=0):
    """Корутина для анимации выстрела."""
    row, column = start_row, start_column
    max_row, max_column = canvas.getmaxyx()
    max_row -= BORDER_WIDTH
    max_column -= BORDER_WIDTH

    canvas.addstr(round(row), round(column), '*')
    canvas.refresh()
    await sleep(FIRE_FLASH_DURATION)

    canvas.addstr(round(row), round(column), 'O')
    canvas.refresh()
    await sleep(FIRE_FLASH_DURATION)

    canvas.addstr(round(row), round(column), ' ')
    canvas.refresh()

    symbol = '-' if columns_speed else '|'
    curses.beep()

    while BORDER_WIDTH <= row < max_row and BORDER_WIDTH <= column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        canvas.refresh()
        await sleep(FIRE_MOVE_DURATION)

        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed



async def run_spaceship(canvas, rocket_frames, max_y, max_x, fire_tasks):
    """Корутина для анимации корабля."""
    spaceship_row = max_y / CENTER_DIVISOR
    spaceship_column = max_x / CENTER_DIVISOR
    row_speed = 0.0
    column_speed = 0.0

    frame_iterator = itertools.cycle(rocket_frames)
    current_frame = next(frame_iterator)
    frame_height, frame_width = get_frame_size(current_frame)
    frame_counter = 0

    min_row = BORDER_WIDTH
    min_column = BORDER_WIDTH
    max_row_position = max(min_row, max_y - frame_height - BORDER_WIDTH)
    max_column_position = max(min_column, max_x - frame_width - BORDER_WIDTH)
    spaceship_row = min(max(spaceship_row, min_row), max_row_position)
    spaceship_column = min(max(spaceship_column, min_column), max_column_position)

    draw_frame(canvas, round(spaceship_row), round(spaceship_column), current_frame)
    canvas.refresh()

    while True:
        rows_direction, columns_direction, space_pressed = read_controls(canvas)

        draw_frame(canvas, round(spaceship_row), round(spaceship_column), current_frame, negative=True)

        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)

        next_row = spaceship_row + row_speed
        next_column = spaceship_column + column_speed

        min_row = BORDER_WIDTH
        min_column = BORDER_WIDTH
        max_row_position = max_y - frame_height - BORDER_WIDTH
        max_column_position = max_x - frame_width - BORDER_WIDTH
        max_row_position = max(min_row, max_row_position)
        max_column_position = max(min_column, max_column_position)

        if next_row < min_row:
            next_row = min_row
            row_speed = 0
        elif next_row > max_row_position:
            next_row = max_row_position
            row_speed = 0

        if next_column < min_column:
            next_column = min_column
            column_speed = 0
        elif next_column > max_column_position:
            next_column = max_column_position
            column_speed = 0

        spaceship_row, spaceship_column = next_row, next_column

        frame_counter += 1
        if frame_counter >= FRAME_SWITCH_INTERVAL:
            current_frame = next(frame_iterator)
            frame_height, frame_width = get_frame_size(current_frame)
            frame_counter = 0

            max_row_position = max_y - frame_height - BORDER_WIDTH
            max_column_position = max_x - frame_width - BORDER_WIDTH
            max_row_position = max(min_row, max_row_position)
            max_column_position = max(min_column, max_column_position)
            spaceship_row = min(max(spaceship_row, min_row), max_row_position)
            spaceship_column = min(max(spaceship_column, min_column), max_column_position)

        draw_frame(canvas, round(spaceship_row), round(spaceship_column), current_frame)
        canvas.refresh()

        if space_pressed:
            fire_row = max(round(spaceship_row) - 1, BORDER_WIDTH)
            fire_column = round(spaceship_column) + frame_width // 2
            fire_column = max(fire_column, BORDER_WIDTH)
            fire_column = min(fire_column, max_x - BORDER_WIDTH)
            fire_task = asyncio.create_task(
                fire(canvas, fire_row, fire_column)
            )
            fire_tasks.add(fire_task)
            fire_task.add_done_callback(lambda task: fire_tasks.discard(task))

        await sleep(1)


async def draw(canvas):
    curses.curs_set(False)
    canvas.nodelay(True)

    max_y, max_x = canvas.getmaxyx()
    canvas.border()

    rocket_frames = load_rocket_frames()
    garbage_frames = load_garbage_frames()

    hint_text = "Press SPACE to fire!"
    canvas.addstr(BORDER_WIDTH, max_x - len(hint_text) - HINT_OFFSET, hint_text)
    canvas.refresh()

    fire_tasks = set()
    garbage_tasks = set()
    tasks = [
        asyncio.create_task(run_spaceship(canvas, rocket_frames, max_y, max_x, fire_tasks)),
        asyncio.create_task(fill_orbit_with_garbage(canvas, garbage_frames, garbage_tasks)),
    ]

    for _ in range(STARS_COUNT):
        tasks.append(asyncio.create_task(
            blink(
                canvas,
                random.randint(BORDER_WIDTH, max_y - BORDER_WIDTH - 1),
                random.randint(BORDER_WIDTH, max_x - BORDER_WIDTH - 1),
                random.choice(STAR_SYMBOLS),
                random.randint(0, STAR_OFFSET_MAX)
            )
        ))

    await asyncio.gather(*tasks)


def main(stdscr):
    """Основная функция программы."""
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    curses.use_default_colors()
    asyncio.run(draw(stdscr))


if __name__ == '__main__':
    curses.wrapper(main)
