RESET = '\x1b[0m'

class Grid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cells = [' ' for i in range(width * height)]

    def to_index(self, x, y):
        if x < 0 or x >= self.width:
            raise ValueError(f'x={x} is out of range (width={self.width})')
        if y < 0 or y >= self.height:
            raise ValueError(f'y={y} is out of range (height={self.height})')
        return y * self.width + x

    def set_hor(self, x, y, text):
        for i, ch in enumerate(text_to_cells(text)):
            self.cells[self.to_index(x + i, y)] = ch

    def set_ver(self, x, y, text):
        for i, ch in enumerate(text_to_cells(text)):
            self.cells[self.to_index(x, y + i)] = ch

    def print_to_terminal(self, preprocess_cell=None):
        for y in range(self.height):
            for x in range(self.width):
                cell = self.cells[y * self.width + x]
                cell = preprocess_cell(cell) if preprocess_cell else cell
                print(cell, end='')
            print()


# Iterates over each character in the string but changes ASCII codes to apply
# to each character.
#
# This ensures ASCII escapes to not take up cells and also allows ASCII escapes
# to apply when printing vertically as well.
#
# Example:
#    >>> text_to_cells('ABC')
#    ['A', 'B', 'C']
#    >>> text_to_cells('\x1b[31mABC\x1b[0m')
#    ['\x1b[31mA\x1b[0m', '\x1b[31mB\x1b[0m', '\x1b[31mC\x1b[0m']
#    >>> text_to_cells('A\x1b[1m\x1b[31mBC\x1b[0m\x1b[0mD')
#    ['A', '\x1b[1m\x1b[31mB\x1b[0m', '\x1b[1m\x1b[31mC\x1b[0m', 'D']
def text_to_cells(text):
    escape_seq_stack = []
    for token in tokenize(text):
        if token == RESET:
            escape_seq_stack = []
        elif token.startswith('\x1b'):
            escape_seq_stack.append(token)
        elif escape_seq_stack:
            yield ''.join(escape_seq_stack) + token + RESET
        else:
            yield token


# Tokenizes a string into individual characters and ASCII escape sequences.
#
# Example:
#    >>> text_to_cells('ABC')
#    ['A', 'B', 'C']
#    >>> text_to_cells('\x1b[31mABC\x1b[0m')
#    ['\x1b[31m', 'A', 'B', 'C', '\x1b[0m']
#    >>> text_to_cells('A\x1b[1m\x1b[31mBC\x1b[0m\x1b[0mD')
#    ['A', '\x1b[1m', '\x1b[31m', 'B', 'C', '\x1b[0m', '\x1b[0m', 'D']
def tokenize(text):
    escape_seq = ''
    for char in text:
        if char == '\x1b':
            escape_seq = char
        elif escape_seq and char == 'm':
            escape_seq += char
            yield escape_seq
            escape_seq = ''
        elif escape_seq:
            escape_seq += char
        else:
            yield char
