import asyncio
import curses
import random

TIC_TIMEOUT = 0.1


async def blink(canvas, row, column, symbol='*', offset_tics=0):
    # Случайная задержка перед началом, чтобы звезды мигали не синхронно
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


async def draw(canvas):
    curses.curs_set(False)
    canvas.nodelay(True)

    max_y, max_x = canvas.getmaxyx()
    canvas.border()

    center_y = max_y // 2
    center_x = (max_x - 5) // 2
    if center_y > 0 and center_x > 0 and center_y < max_y - 1 and center_x + 5 < max_x - 1:
        canvas.addstr(center_y, center_x, "Hello")

    # Создаем 100 звезд в случайных позициях
    stars_count = 100
    star_symbols = '+*.:'
    tasks = []
    
    for _ in range(stars_count):
        star_y = random.randint(1, max_y - 2)
        star_x = random.randint(1, max_x - 2)
        symbol = random.choice(star_symbols)
        offset = random.randint(0, 30)
        
        task = asyncio.create_task(blink(canvas, star_y, star_x, symbol, offset))
        tasks.append(task)

    canvas.refresh()

    try:
        while True:
            key = canvas.getch()
            if key == curses.KEY_RESIZE:
                for task in tasks:
                    task.cancel()
                tasks = []
                
                max_y, max_x = canvas.getmaxyx()
                canvas.clear()
                canvas.border()

                center_y = max_y // 2
                center_x = (max_x - 5) // 2
                if center_y > 0 and center_x > 0 and center_y < max_y - 1 and center_x + 5 < max_x - 1:
                    canvas.addstr(center_y, center_x, "Hello")

                for _ in range(stars_count):
                    star_y = random.randint(1, max_y - 2)
                    star_x = random.randint(1, max_x - 2)
                    symbol = random.choice(star_symbols)
                    offset = random.randint(0, 30)
                    task = asyncio.create_task(blink(canvas, star_y, star_x, symbol, offset))
                    tasks.append(task)

                canvas.refresh()

            elif key in [ord('q'), ord('Q'), ord('й'), ord('Й')]:
                break

            await asyncio.sleep(TIC_TIMEOUT)

    finally:
        for task in tasks:
            task.cancel()
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass

def main(stdscr):
    asyncio.run(draw(stdscr))

if __name__ == '__main__':
    curses.wrapper(main)