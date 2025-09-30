import asyncio
import curses


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await asyncio.sleep(0)

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

    # Определяем позицию для звездочки в углу (левый верхний угол)
    star_y = 1
    star_x = 1

    # Проверяем, что позиция звездочки валидна
    if not (star_y > 0 and star_x > 0 and star_y < max_y - 1 and star_x < max_x - 1):
        return

    # Создаем асинхронную задачу для мигания звездочки в углу
    task = asyncio.create_task(blink(canvas, star_y, star_x))

    # Обновляем экран
    canvas.refresh()

    try:
        while True:
            # Проверяем нажатие клавиш и события окна
            key = canvas.getch()
            if key == curses.KEY_RESIZE:
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

                # Обновляем позицию звездочки для нового размера (левый верхний угол)
                star_y = 1
                star_x = 1

                canvas.refresh()

            elif key in [ord('q'), ord('Q'), ord('й'), ord('Й')]:
                break

            # Небольшая пауза для снижения нагрузки на процессор
            await asyncio.sleep(0.1)

    finally:
        # Отменяем задачу мигания при выходе
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

def main(stdscr):
    """Синхронная обертка для запуска асинхронной функции в curses"""
    asyncio.run(draw(stdscr))

if __name__ == '__main__':
    curses.wrapper(main)