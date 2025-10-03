import asyncio
import curses
import random
import itertools
import locale
from curses_tools import draw_frame, read_controls, get_frame_size
from physics import update_speed
from obstacles import Obstacle
from explosion import explode
from game_scenario import PHRASES, get_garbage_delay_tics

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
FIRE_FLASH_DURATION = 2
FIRE_MOVE_DURATION = 1
FIRE_SPEED = -0.999

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
GARBAGE_SPEED_RANGE = (0.3, 1.0)

YEAR_START = 1957
YEAR_SECONDS = 1.5
YEAR_TICS = max(1, int(YEAR_SECONDS / TIC_TIMEOUT))

FIRE_UNLOCK_YEAR = 2020

obstacles = []
obstacles_in_last_collisions = []

year = YEAR_START

with open('frames/gameover.txt', 'r', encoding='utf-8') as fh:
    GAME_OVER_FRAME = fh.read()

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


async def show_gameover(canvas):
    """Отображает экран Game Over в центре."""
    rows, columns = get_frame_size(GAME_OVER_FRAME)
    max_row, max_column = canvas.getmaxyx()
    start_row = max((max_row - rows) // 2, BORDER_WIDTH)
    start_column = max((max_column - columns) // 2, BORDER_WIDTH)

    while True:
        draw_frame(canvas, start_row, start_column, GAME_OVER_FRAME)
        await sleep(1)


async def update_year():
    """Увеличивает текущий год согласно игровому темпу."""
    global year
    while True:
        await sleep(YEAR_TICS)
        year += 1


async def show_year_info(canvas):
    """Показывает текущий год и событие в верхней части экрана."""
    last_phrase = ''
    last_phrase_year = None
    while True:
        if year in PHRASES:
            last_phrase = PHRASES[year]
            last_phrase_year = year
        elif last_phrase and last_phrase_year is not None and year - last_phrase_year > 2:
            last_phrase = ''
            last_phrase_year = None

        max_rows, max_columns = canvas.getmaxyx()
        info_row = min(max_rows - BORDER_WIDTH - 1, BORDER_WIDTH + 1)
        message_row = min(info_row + 1, max_rows - BORDER_WIDTH - 1)
        clear_width = max_columns - BORDER_WIDTH * 2
        if clear_width > 0:
            blank = ' ' * clear_width
            try:
                canvas.addstr(info_row, BORDER_WIDTH, blank)
                canvas.addstr(info_row, BORDER_WIDTH, f'Year: {year}'[:clear_width])
                canvas.addstr(message_row, BORDER_WIDTH, blank)
                if last_phrase:
                    canvas.addstr(message_row, BORDER_WIDTH, last_phrase[:clear_width])
                canvas.refresh()
            except curses.error:
                pass

        await sleep(1)


async def show_fire_hint(canvas, max_x):
    """Показывает подсказку об огне, когда пушка появится."""
    hint_text = "Press SPACE to fire!"
    hint_column = max(max_x - len(hint_text) - HINT_OFFSET, BORDER_WIDTH)
    while year < FIRE_UNLOCK_YEAR:
        await sleep(1)
    try:
        canvas.addstr(BORDER_WIDTH, hint_column, hint_text)
        canvas.refresh()
    except curses.error:
        pass


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
    """Animate garbage falling within the playfield and register obstacle state."""
    rows_number, columns_number = canvas.getmaxyx()
    frame_height, frame_width = get_frame_size(garbage_frame)

    max_column = max(BORDER_WIDTH, columns_number - frame_width - BORDER_WIDTH)
    column = max(column, BORDER_WIDTH)
    column = min(column, max_column)

    max_row_position = max(rows_number - frame_height - BORDER_WIDTH, BORDER_WIDTH)

    row = 0
    obstacle = Obstacle(row, column, frame_height, frame_width)
    obstacles.append(obstacle)

    try:
        while row < max_row_position:
            obstacle.row = row
            obstacle.column = column

            draw_frame(canvas, row, column, garbage_frame)
            await sleep(1)
            draw_frame(canvas, row, column, garbage_frame, negative=True)

            if obstacle not in obstacles or obstacle in obstacles_in_last_collisions:
                if obstacle in obstacles_in_last_collisions:
                    obstacles_in_last_collisions.remove(obstacle)
                break

            row += speed
    finally:
        if obstacle in obstacles:
            obstacles.remove(obstacle)
        if obstacle in obstacles_in_last_collisions:
            obstacles_in_last_collisions.remove(obstacle)


async def fill_orbit_with_garbage(canvas, garbage_frames, garbage_tasks):
    """Создает бесконечный поток мусора согласно сценарию."""
    while True:
        delay = get_garbage_delay_tics(year)
        if delay is None:
            await sleep(1)
            continue

        frame = random.choice(garbage_frames)
        _, columns = canvas.getmaxyx()
        _, frame_width = get_frame_size(frame)
        max_column = max(columns - frame_width - BORDER_WIDTH, BORDER_WIDTH)
        column = random.randint(BORDER_WIDTH, max_column)
        speed = random.uniform(*GARBAGE_SPEED_RANGE)
        task = asyncio.create_task(
            fly_garbage(canvas, column, frame, speed)
        )
        garbage_tasks.add(task)
        task.add_done_callback(lambda task: garbage_tasks.discard(task))
        await sleep(delay)


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
        row_int = round(row)
        col_int = round(column)

        hit_obstacle = None
        for obstacle in tuple(obstacles):
            if obstacle.has_collision(row_int, col_int):
                hit_obstacle = obstacle
                break

        if hit_obstacle is not None:
            if hit_obstacle not in obstacles_in_last_collisions:
                obstacles_in_last_collisions.append(hit_obstacle)

            await explode(canvas, row_int, col_int)

            if hit_obstacle in obstacles:
                obstacles.remove(hit_obstacle)
            if hit_obstacle in obstacles_in_last_collisions:
                obstacles_in_last_collisions.remove(hit_obstacle)
            return

        canvas.addstr(row_int, col_int, symbol)
        canvas.refresh()
        await sleep(FIRE_MOVE_DURATION)

        canvas.addstr(row_int, col_int, ' ')
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

        ship_row_int = round(spaceship_row)
        ship_col_int = round(spaceship_column)
        hit_obstacle = None
        for obstacle in tuple(obstacles):
            if obstacle.has_collision(ship_row_int, ship_col_int, frame_height, frame_width):
                hit_obstacle = obstacle
                break

        if hit_obstacle is not None:
            draw_frame(canvas, ship_row_int, ship_col_int, current_frame, negative=True)
            canvas.refresh()
            for task in tuple(fire_tasks):
                task.cancel()
            asyncio.create_task(show_gameover(canvas))
            return

        if space_pressed and year >= FIRE_UNLOCK_YEAR:
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

    fire_tasks = set()
    garbage_tasks = set()
    tasks = [
        asyncio.create_task(run_spaceship(canvas, rocket_frames, max_y, max_x, fire_tasks)),
        asyncio.create_task(fill_orbit_with_garbage(canvas, garbage_frames, garbage_tasks)),
        asyncio.create_task(update_year()),
        asyncio.create_task(show_year_info(canvas)),
    ]
    tasks.append(asyncio.create_task(show_fire_hint(canvas, max_x)))

    info_row = min(max_y - BORDER_WIDTH - 1, BORDER_WIDTH + 1)
    message_row = min(info_row + 1, max_y - BORDER_WIDTH - 1)
    star_row_top = min(message_row + 1, max_y - BORDER_WIDTH - 1)
    star_row_bottom = max_y - BORDER_WIDTH - 1
    star_row_top = min(star_row_top, star_row_bottom)

    for _ in range(STARS_COUNT):
        star_row = random.randint(star_row_top, star_row_bottom)
        star_column = random.randint(BORDER_WIDTH, max_x - BORDER_WIDTH - 1)
        tasks.append(asyncio.create_task(
            blink(
                canvas,
                star_row,
                star_column,
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
