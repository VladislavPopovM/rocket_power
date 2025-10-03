import asyncio
import curses
from curses_tools import draw_frame, get_frame_size

EXPLOSION_FRAMES = [
    """           (_)
       (  (   (  (
      () (  (  )
        ( )  ()
    """,
    """           (_)
       (  (   (
         (  (  )
          )  (
    """,
    """            (
          (   (
         (     (
          )  (
    """,
    """            (
              (
            (

    """,
]

FRAME_DELAY = 0.1

async def explode(canvas, center_row, center_column):
    rows, columns = get_frame_size(EXPLOSION_FRAMES[0])
    corner_row = round(center_row - rows / 2)
    corner_column = round(center_column - columns / 2)

    curses.beep()
    for frame in EXPLOSION_FRAMES:
        draw_frame(canvas, corner_row, corner_column, frame)
        await asyncio.sleep(FRAME_DELAY)
        draw_frame(canvas, corner_row, corner_column, frame, negative=True)
        await asyncio.sleep(FRAME_DELAY)
