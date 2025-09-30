import asyncio
import curses


async def blink(canvas, row, column, symbol='*'):
    while True:
        # Проверяем границы перед выводом
        max_y, max_x = canvas.getmaxyx()
        if row >= 0 and column >= 0 and row < max_y and column < max_x:
            canvas.addstr(row, column, symbol, curses.A_DIM)
        await asyncio.sleep(0)

        if row >= 0 and column >= 0 and row < max_y and column < max_x:
            canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        if row >= 0 and column >= 0 and row < max_y and column < max_x:
            canvas.addstr(row, column, symbol, curses.A_BOLD)
        await asyncio.sleep(0)

        if row >= 0 and column >= 0 and row < max_y and column < max_x:
            canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)


async def draw_text(canvas, row, column, text):
    """Выводит текст в указанной позиции"""
    canvas.addstr(row, column, text)
    canvas.refresh()


# Основная функция рисования, которая вызывается curses.wrapper()
# canvas - это объект экрана curses, предоставляемый библиотекой
async def draw(canvas):
    curses.curs_set(False)
    canvas.nodelay(True)

    # Получаем размеры окна
    max_y, max_x = canvas.getmaxyx()

    # Выводим рамку
    canvas.border()

    # Выводим "Hello" в центре экрана
    center_y = max_y // 2
    center_x = (max_x - 5) // 2  # 5 - длина слова "Hello"
    if center_y > 0 and center_x > 0 and center_y < max_y - 1 and center_x + 5 < max_x - 1:
        canvas.addstr(center_y, center_x, "Hello")

    # Определяем позиции для 5 звездочек в разных местах экрана
    stars_positions = [
        (1, 1),                                    # Левый верхний угол
        (1, max_x - 2),                           # Правый верхний угол
        (max_y - 2, 1),                           # Левый нижний угол
        (max_y - 2, max_x - 2),                   # Правый нижний угол
        (max_y // 2 - 2, max_x // 2)             # Центр сверху (выше "Hello")
    ]

    # Создаем асинхронные задачи для мигания всех звездочек
    tasks = []
    for star_y, star_x in stars_positions:
        # Проверяем, что позиция звездочки валидна
        if star_y > 0 and star_x > 0 and star_y < max_y - 1 and star_x < max_x - 1:
            task = asyncio.create_task(blink(canvas, star_y, star_x))
            tasks.append(task)

    # Обновляем экран
    canvas.refresh()

    try:
        while True:
            # Проверяем нажатие клавиш и события окна
            key = canvas.getch()
            if key == curses.KEY_RESIZE:
                # Отменяем старые задачи мигания
                for task in tasks:
                    task.cancel()
                tasks = []
                
                # При изменении размера окна пересчитываем позиции и перерисовываем
                max_y, max_x = canvas.getmaxyx()

                # Очищаем экран и рисуем рамку заново
                canvas.clear()
                canvas.border()

                # Пересчитываем позицию для "Hello" в центре
                center_y = max_y // 2
                center_x = (max_x - 5) // 2
                if center_y > 0 and center_x > 0 and center_y < max_y - 1 and center_x + 5 < max_x - 1:
                    canvas.addstr(center_y, center_x, "Hello")

                # Обновляем позиции звездочек для нового размера
                stars_positions = [
                    (1, 1),                                    # Левый верхний угол
                    (1, max_x - 2),                           # Правый верхний угол
                    (max_y - 2, 1),                           # Левый нижний угол
                    (max_y - 2, max_x - 2),                   # Правый нижний угол
                    (max_y // 2 - 2, max_x // 2)             # Центр сверху
                ]
                
                # Создаем новые задачи для звездочек с новыми позициями
                for star_y, star_x in stars_positions:
                    if star_y > 0 and star_x > 0 and star_y < max_y - 1 and star_x < max_x - 1:
                        task = asyncio.create_task(blink(canvas, star_y, star_x))
                        tasks.append(task)

                canvas.refresh()

            elif key in [ord('q'), ord('Q'), ord('й'), ord('Й')]:
                break

            # Небольшая пауза для снижения нагрузки на процессор
            await asyncio.sleep(0.1)

    finally:
        # Отменяем все задачи мигания при выходе
        for task in tasks:
            task.cancel()
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass

def main(stdscr):
    """Синхронная обертка для запуска асинхронной функции в curses"""
    asyncio.run(draw(stdscr))

if __name__ == '__main__':
    curses.wrapper(main)