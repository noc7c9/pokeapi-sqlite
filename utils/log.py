import sys
import os


# Disable colors if not on a TTY
disable_colors = not sys.stderr.isatty()

# Attempt to fix Windows console colors
if not disable_colors:
    try:
        from colorama import just_fix_windows_console
        just_fix_windows_console()
    except:
        # Disable colors if on Windows and colorama fails for any reason
        disable_colors = os.name == 'nt'


# Codes
BLACK = '\x1b[30m'
RED = '\x1b[31m'
GREEN = '\x1b[32m'
YELLOW = '\x1b[33m'
BLUE = '\x1b[34m'
MAGENTA = '\x1b[35m'
CYAN = '\x1b[36m'
WHITE = '\x1b[37m'

BOLD = '\x1b[1m'

RESET = '\x1b[0m'

class Color:
    def disable():
        global disable_colors
        disable_colors = True

    def wrap(text, color): return text if disable_colors else color + text + RESET

    def black(text): return Color.wrap(text, BLACK)
    def red(text): return Color.wrap(text, RED)
    def green(text): return Color.wrap(text, GREEN)
    def yellow(text): return Color.wrap(text, YELLOW)
    def blue(text): return Color.wrap(text, BLUE)
    def magenta(text): return Color.wrap(text, MAGENTA)
    def cyan(text): return Color.wrap(text, CYAN)
    def white(text): return Color.wrap(text, WHITE)

    def bold(text): return Color.wrap(text, BOLD)


def info(*args):
    if len(args) == 0:
        print()
        return
    print(Color.blue('[INFO]'), *args, file=sys.stderr)


def warn(*args):
    if len(args) == 0:
        print()
        return
    print(Color.yellow('[WARN]'), *args, file=sys.stderr)


def error(*args):
    if len(args) == 0:
        print()
        return
    print(Color.red('[ERROR]'), *args, file=sys.stderr)
