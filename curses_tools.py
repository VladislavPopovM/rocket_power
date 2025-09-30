import curses

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

# WASD клавиши
W_KEY_CODE = ord('w')
A_KEY_CODE = ord('a')
S_KEY_CODE = ord('s')
D_KEY_CODE = ord('d')


def read_controls(canvas):
    """Read keys pressed and returns tuple witl controls state."""

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        # Стрелки
        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1

        # WASD клавиши
        if pressed_key_code == W_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == S_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == D_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == A_KEY_CODE:
            columns_direction = -1

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


def draw_frame(canvas, start_row, start_column, text, negative=False):
    """Draw multiline text fragment on canvas, erase text instead of drawing if negative=True is specified."""

    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0 or row >= rows_number - 1:
            continue

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0 or column >= columns_number - 1:
                continue

            if symbol == ' ':
                continue

            # Check that current position it is not in a lower right corner of the window
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            try:
                symbol = symbol if not negative else ' '
                # Используем addch для одного символа - это безопаснее
                canvas.addch(row, column, ord(symbol))
            except (curses.error, ValueError):
                # Skip problematic characters
                continue


def get_frame_size(text):
    """Calculate size of multiline text fragment, return pair — number of rows and colums."""

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns
