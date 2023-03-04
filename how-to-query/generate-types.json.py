#!/usr/bin/env python3

import u


def main():
    u.parse_args()

    db = u.open_db()

    data = {}

    # Names
    for row in db.execute('''
        SELECT type_id, types.identifier, iso3166, name
        FROM types

        JOIN type_names
        ON types.id = type_names.type_id

        JOIN languages
        ON type_names.local_language_id = languages.id

        WHERE type_id < 10000 -- ignore non-standard types
    '''):
        datum = data.setdefault(row.type_id, {
            'id': row.identifier,
            'name': {},
            'super_effective': [],
            'not_very_effective': [],
            'no_effect': [],
        })
        datum['name'][row.iso3166] = row.name

    # Type efficacies
    for row in db.execute('''
        SELECT damage_type_id, target_type_id, damage_factor
        FROM type_efficacy
    '''):
        target_type_id = data[row.target_type_id]['id']
        if row.damage_factor == 0:
            data[row.damage_type_id]['no_effect'].append(target_type_id)
        elif row.damage_factor == 50:
            data[row.damage_type_id]['not_very_effective'].append(target_type_id)
        elif row.damage_factor == 200:
            data[row.damage_type_id]['super_effective'].append(target_type_id)

    # Convert to a dict keyed by id
    data = { datum['id']: datum for datum in data.values() }
    for datum in data.values():
        del datum['id']

    print(u.json_dumps(data))


main()
