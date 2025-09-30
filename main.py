import asyncio
import curses
import random
import itertools
from curses_tools import draw_frame
import locale

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

TIC_TIMEOUT = 0.1

# Читаем кадры анимации корабля заранее
with open('frames/rocket_frame_1.txt', 'r', encoding='utf-8') as f:
    frame1 = f.read()
with open('frames/rocket_frame_2.txt', 'r', encoding='utf-8') as f:
    frame2 = f.read()

async def blink(canvas, row, column, symbol='*', offset_tics=0):
    for _ in range(offset_tics):
        await asyncio.sleep(0)
    
    while True:
        max_y, max_x = canvas.getmaxyx()
        if row >= 0 and column >= 0 and row < max_y and column < max_x:
            canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)

        max_y, max_x = canvas.getmaxyx()
        if row >= 0 and column >= 0 and row < max_y and column < max_x:
            canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        max_y, max_x = canvas.getmaxyx()
        if row >= 0 and column >= 0 and row < max_y and column < max_x:
            canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        max_y, max_x = canvas.getmaxyx()
        if row >= 0 and column >= 0 and row < max_y and column < max_x:
            canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.02, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    def inside(current_row: float, current_column: float) -> bool:
        return 1 <= current_row < max_row and 1 <= current_column < max_column

    def draw_symbol(char: str) -> None:
        if inside(row, column):
            canvas.addstr(round(row), round(column), char)
            canvas.refresh()

    draw_symbol('*')
    for _ in range(5):
        await asyncio.sleep(0)

    draw_symbol('O')
    for _ in range(5):
        await asyncio.sleep(0)
    if inside(row, column):
        canvas.addstr(round(row), round(column), ' ')

    symbol = '-' if columns_speed else '|'
    curses.beep()

    prev_coords = None
    while inside(row, column):
        current_coords = (round(row), round(column))
        if inside(*current_coords):
            canvas.addstr(*current_coords, symbol)
            canvas.refresh()
        for _ in range(3):
            await asyncio.sleep(0)
        if prev_coords and inside(*prev_coords):
            canvas.addstr(*prev_coords, ' ')
        prev_coords = current_coords
        row += rows_speed
        column += columns_speed

    if prev_coords and inside(*prev_coords):
        canvas.addstr(*prev_coords, ' ')




async def draw(canvas):
    curses.curs_set(False)
    canvas.nodelay(True)

    max_y, max_x = canvas.getmaxyx()
    canvas.border()

    center_y = max_y // 2
    center_x = max_x // 2

    
    
    rocket_frames = [frame1, frame2]

    # Добавляем подсказку
    hint_text = "Press SPACE to fire!"
    hint_x = max_x - len(hint_text) - 2
    if hint_x > 0:
        canvas.addstr(1, hint_x, hint_text)

    stars_count = 100
    star_symbols = '+*.:'
    tasks = []
    
    for _ in range(stars_count):
        star_y = random.randint(1, max_y - 2)
        star_x = random.randint(1, max_x - 2)
        symbol = random.choice(star_symbols)
        offset = random.randint(0, 100)
        
        task = asyncio.create_task(blink(canvas, star_y, star_x, symbol, offset))
        tasks.append(task)

    # Позиция корабля (начинаем в центре)
    spaceship_row = center_y
    spaceship_column = center_x
    
    # Итератор для кадров анимации корабля
    frame_iterator = itertools.cycle(rocket_frames)
    current_frame = next(frame_iterator)
    frame_counter = 0

    canvas.refresh()

    while True:
        # Читаем клавиши напрямую
        key = canvas.getch()
        
        # Обработка управления
        rows_direction = columns_direction = 0
        space_pressed = False
        
        if key == curses.KEY_RESIZE:
            max_y, max_x = canvas.getmaxyx()
            center_y = max_y // 2
            center_x = max_x // 2
            canvas.clear()
            canvas.border()
            
            hint_text = "WASD/Arrows: move, SPACE: fire, Q: quit"
            hint_x = max_x - len(hint_text) - 2
            if hint_x > 0:
                canvas.addstr(1, hint_x, hint_text)
            
            canvas.refresh()
            
        elif key in [ord('q'), ord('Q'), ord('й'), ord('Й')]:
            break
            
        elif key == ord('w') or key == curses.KEY_UP:
            rows_direction = -1
        elif key == ord('s') or key == curses.KEY_DOWN:
            rows_direction = 1
        elif key == ord('a') or key == curses.KEY_LEFT:
            columns_direction = -1
        elif key == ord('d') or key == curses.KEY_RIGHT:
            columns_direction = 1
        elif key == ord(' '):
            space_pressed = True
        
        # Стираем старый кадр корабля
        draw_frame(canvas, spaceship_row, spaceship_column, current_frame, negative=True)
        
        # Обновляем позицию корабля
        if rows_direction != 0 or columns_direction != 0:
            # Вычисляем новую позицию
            new_row = spaceship_row + rows_direction
            new_column = spaceship_column + columns_direction
            
            # Проверяем границы
            if 1 <= new_row <= max_y - 10 and 1 <= new_column <= max_x - 10:
                spaceship_row = new_row
                spaceship_column = new_column
        
        # Обновляем кадр анимации каждые 2 тика
        frame_counter += 1
        if frame_counter >= 2:
            current_frame = next(frame_iterator)
            frame_counter = 0
        
        # Рисуем текущий кадр корабля
        draw_frame(canvas, spaceship_row, spaceship_column, current_frame)
        
        # Выстрел
        if space_pressed:
            fire_task = asyncio.create_task(fire(canvas, spaceship_row, spaceship_column + 2))
            tasks.append(fire_task)

        # Удаляем завершенные задачи
        tasks = [task for task in tasks if not task.done()]

        canvas.refresh()
        await asyncio.sleep(TIC_TIMEOUT)
    
    # Отменяем все задачи при выходе
    for task in tasks:
        task.cancel()
    for task in tasks:
        try:
            await task
        except asyncio.CancelledError:
            pass

def main(stdscr):
    curses.use_default_colors()
    asyncio.run(draw(stdscr))

if __name__ == '__main__':
    curses.wrapper(main)