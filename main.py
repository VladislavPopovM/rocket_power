import time
import curses


# Основная функция рисования, которая вызывается curses.wrapper()
# canvas - это объект экрана curses, предоставляемый библиотекой
def draw(canvas):
    # Отключаем отображение курсора для более чистого интерфейса
    curses.curs_set(False)

    # Включаем неблокирующий режим получения клавиш
    # Теперь getch() не будет ждать нажатия клавиши, а сразу вернет -1 если клавиша не нажата
    canvas.nodelay(True)

    text = 'Hello, World!'

    def redraw():
        # Очищаем экран перед перерисовкой
        canvas.clear()
        # Рисуем рамку вокруг всего окна
        canvas.border()

        max_y, max_x = canvas.getmaxyx()
        row = max_y // 2
        column = (max_x - len(text)) // 2

        if row > 0 and column > 0 and row < max_y - 1 and column + len(text) < max_x - 1:
            canvas.addstr(row, column, text)

        # Обновляем экран, показывая все изменения
        canvas.refresh()

    # Первоначальная отрисовка при запуске программы
    redraw()

    # Основной цикл обработки событий
    while True:
        key = canvas.getch()

        if key == curses.KEY_RESIZE:
            redraw()
        elif key in [ord('q'), ord('Q'), ord('й'), ord('Й')]:
            break

        # Небольшая пауза для снижения нагрузки на процессор
        time.sleep(0.1)

if __name__ == '__main__':
    curses.wrapper(draw)