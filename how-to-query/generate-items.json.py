#!/usr/bin/env python3

import u


def main():
    u.parse_args()

    db = u.open_db()

    data = {}

    # Names
    for row in db.execute('''
        SELECT item_id, items.identifier, iso3166, name
        FROM items

        JOIN item_names
        ON items.id = item_names.item_id

        JOIN languages
        ON item_names.local_language_id = languages.id
    '''):
        datum = data.setdefault(row.item_id, {
            'id': row.identifier,
            'category': None,
            'name': {},
            'flavor_text': {},
            'effect': {},
        })
        datum['name'][row.iso3166] = row.name

    # Categories
    for row in db.execute('''
        SELECT items.id, item_categories.identifier
        FROM items

        JOIN item_categories
        ON items.category_id = item_categories.id
    '''):
        if row.id in data:
            data[row.id]['category'] = row.identifier

    # Flavor text
    for row in db.execute('''
        SELECT t1.item_id, iso3166, t1.flavor_text
        FROM item_flavor_text AS t1

        JOIN languages
        ON t1.language_id = languages.id

        -- Only get the flavor text from the latest version group
        LEFT JOIN item_flavor_text AS t2
        ON t1.item_id = t2.item_id
        AND t1.language_id = t2.language_id
        AND t1.version_group_id < t2.version_group_id
        WHERE t2.version_group_id IS NULL
    '''):
        if row.item_id in data:
            data[row.item_id]['flavor_text'][row.iso3166] = row.flavor_text

    # Effects
    for row in db.execute('''
        SELECT item_id, iso3166, short_effect
        FROM item_prose

        JOIN languages
        ON item_prose.local_language_id = languages.id
    '''):
        if row.item_id in data:
            data[row.item_id]['effect'][row.iso3166] = row.short_effect

    # Convert to a dict keyed by id
    data = { datum['id']: datum for datum in data.values() }
    for datum in data.values():
        del datum['id']

    print(u.json_dumps(data))


main()
