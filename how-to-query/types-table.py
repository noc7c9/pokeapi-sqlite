#!/usr/bin/env python3

import re
import u

LOCAL_LANGUAGE_ID=9 # english

DEFAULT_GENERATION=9

def main():
    args = u.parse_args(
        args={
            "generation": {
                "type": int,
                "nargs": '?',
                "default": DEFAULT_GENERATION,
                "choices": range(1, 10),
                "metavar": "GENERATION",
                "help": "The generation to use for the type table"
            },
            "--no-color": {
                "action": "store_true",
                "help": "Disable color output"
            },
            '--ascii': {
                "action": "store_true",
                "help": "Use ASCII characters instead of Unicode to draw the table"
            },
        }
    )

    if args.no_color:
        u.Color.disable()

    db = u.open_db()
    type_ids = db.execute('''
        SELECT types.id, type_names.name
        FROM types
            INNER JOIN type_names
                ON type_names.type_id = types.id
        WHERE types.id < 10000 -- ignore non-standard types
            AND types.generation_id <= ?
            AND type_names.local_language_id = ?
    ''', (args.generation, LOCAL_LANGUAGE_ID)).fetchall()

    type_efficacies = db.execute('''
        SELECT
            te.damage_type_id, te.target_type_id,
            coalesce(tep.damage_factor, te.damage_factor) AS damage_factor
        FROM type_efficacy AS te
        LEFT JOIN (
            SELECT *
            FROM type_efficacy_past
            WHERE generation_id >= ? OR generation_id IS NULL
        ) AS tep
        ON te.damage_type_id = tep.damage_type_id AND te.target_type_id = tep.target_type_id
    ''', (args.generation,)).fetchall()
    type_efficacies = {
        (att_type_id, def_type_id): damage_factor
        for att_type_id, def_type_id, damage_factor in type_efficacies
    }

    type_names = [name for _, name in type_ids]
    max_len = max(len(name) for name in type_names)
    type_names = [name.rjust(max_len) for name in type_names]

    width = 3 + 2 + max_len * 2 + 2 + (len(type_names) * 4)
    height = 1 + 1 + max_len + 1 + (len(type_names) * 2)
    grid = u.Grid(width, height)

    x_offset = 3 + 2 + max_len * 2

    def print_separator(y, prefix, s, j, c, e):
        grid.set_hor(0, y, prefix)
        grid.set_hor(x_offset, y, f'{j}{c}{c}{c}' * len(type_names))
        grid.set_hor(x_offset, y, s)
        grid.set_hor(x_offset + 4 * len(type_names), y, e)

    print_separator(1, ' ' * x_offset, '┏', '┳', '━', '┓')

    x = x_offset
    for name in type_names:
        grid.set_ver(x + 0, 2, '┃' * max_len)
        grid.set_ver(x + 1, 2, ' ' * max_len)
        grid.set_ver(x + 2, 2, name)
        grid.set_ver(x + 3, 2, ' ' * max_len)
        grid.set_ver(x + 4, 2, '┃' * max_len)
        x += 4

    y_offset = 1 + 1 + max_len + 1
    print_separator(y_offset - 1, '   ┏' + '━' * (x_offset - 4), '╋', '╇', '━', '┩')

    efficacy_chars = {
        0: u.Color.bold(' 0 '),
        50: u.Color.red(u.Color.bold('1/2' if args.ascii else ' ½ ')),
        100: '   ',
        200: u.Color.green(u.Color.bold(' 2 ')),
    }

    y = y_offset
    for att_type_id, att_type_name in type_ids:
        name = ' '.join(' '.join(name) for name in att_type_name.rjust(max_len))
        grid.set_hor(0, y, f'   ┃ {name} ┃')

        x = x_offset + 1
        for def_type_id, _ in type_ids:
            efficacy = type_efficacies[(att_type_id, def_type_id)]
            grid.set_hor(x, y, f'{efficacy_chars[efficacy]}│')
            x += 4

        print_separator(y + 1, '   ┣' + '━' * (x_offset - 4), '╉', '┼', '─', '┤')
        y += 2

    print_separator(y - 1, '   ┗' + '━' * (x_offset - 4), '┹', '┴', '─', '┘')

    grid.set_hor(x_offset + 2, 0, u.Color.bold(u.Color.yellow('D e f e n d e r')))
    grid.set_ver(1, y_offset, u.Color.bold(u.Color.blue('Attacker')))

    grid.print_to_terminal(replace_box_chars if args.ascii else None)


ASCII_REPLACEMENTS = {
    '─': '-',
    '━': '-',

    '│': '|',
    '┃': '|',

    '┏': '+',
    '┓': '+',
    '┗': '+',
    '┘': '+',
    '┣': '+',
    '┤': '+',
    '┩': '+',
    '┳': '+',
    '┴': '+',
    '┹': '+',
    '┼': '+',
    '╇': '+',
    '╉': '+',
    '╋': '+',
}
PATTERN = re.compile("|".join(ASCII_REPLACEMENTS.keys()))
def replace_box_chars(s):
    return PATTERN.sub(lambda m: ASCII_REPLACEMENTS[m.group(0)], s)


main()
