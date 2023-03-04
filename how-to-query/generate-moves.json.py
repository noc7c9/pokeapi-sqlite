#!/usr/bin/env python3

import u


def main():
    u.parse_args()

    db = u.open_db()

    data = {}

    # Names
    for row in db.execute('''
        SELECT move_id, moves.identifier, iso3166, name
        FROM moves

        JOIN move_names
        ON moves.id = move_names.move_id

        JOIN languages
        ON move_names.local_language_id = languages.id

        WHERE type_id < 10000 -- ignore non-standard moves
    '''):
        datum = data.setdefault(row.move_id, {
            'id': row.identifier,
            'name': {},
            'flavor_text': {},
            'effect': {},
            'meta': {},
        })
        datum['name'][row.iso3166] = row.name

    # Basic data
    for row in db.execute('''
        SELECT
            moves.id AS move_id,
            power, pp, accuracy, priority,
            move_targets.identifier AS target,
            move_damage_classes.identifier AS damage_class,
            types.identifier AS type
        FROM moves

        LEFT JOIN move_targets
        ON moves.target_id = move_targets.id

        LEFT JOIN move_damage_classes
        ON moves.damage_class_id = move_damage_classes.id

        LEFT JOIN types
        ON moves.type_id = types.id

        WHERE move_id < 10000 -- ignore non-standard moves
    '''):
        datum = data[row.move_id]

        datum['power'] = row.power
        datum['pp'] = row.pp
        datum['accuracy'] = row.accuracy
        datum['priority'] = row.priority

        datum['type'] = row.type
        datum['damage_class'] = row.damage_class
        datum['target'] = row.target

    # Flavor text
    for row in db.execute('''
        SELECT t1.move_id, iso3166, t1.flavor_text
        FROM move_flavor_text AS t1

        JOIN languages
        ON t1.language_id = languages.id

        -- Only get the flavor text from the latest version group
        LEFT JOIN move_flavor_text AS t2
        ON t1.move_id = t2.move_id
        AND t1.language_id = t2.language_id
        AND t1.version_group_id < t2.version_group_id
        WHERE t2.version_group_id IS NULL
    '''):
        data[row.move_id]['flavor_text'][row.iso3166] = row.flavor_text

    # Effects
    for row in db.execute('''
        SELECT moves.id AS move_id, iso3166, short_effect
        FROM moves

        JOIN move_effect_prose
        ON moves.effect_id = move_effect_prose.move_effect_id

        JOIN languages
        ON move_effect_prose.local_language_id = languages.id

        WHERE move_id < 10000 -- ignore non-standard moves
    '''):
        data[row.move_id]['effect'][row.iso3166] = row.short_effect

    # Basic meta data
    for row in db.execute('''
        SELECT
            move_id,
            move_meta_categories.identifier AS meta_category,
            min_hits, max_hits, min_turns, max_turns,
            drain, healing, crit_rate, flinch_chance
        FROM move_meta

        LEFT JOIN move_meta_categories
        ON move_meta.meta_category_id = move_meta_categories.id

        WHERE move_id < 10000 -- ignore non-standard moves;
    '''):
        meta = data[row.move_id]['meta']

        meta['category'] = row.meta_category

        if row.min_hits != '' and row.max_hits != '':
            meta['min_hits'] = row.min_hits
            meta['max_hits'] = row.max_hits

        if row.min_turns != '' and row.max_turns != '':
            meta['min_turns'] = row.min_turns
            meta['max_turns'] = row.max_turns

        if row.drain > 0:
            meta['drain'] = row.drain
        if row.healing > 0:
            meta['healing'] = row.healing
        if row.crit_rate > 0:
            meta['crit_rate'] = row.crit_rate
        if row.flinch_chance > 0:
            meta['flinch_chance'] = row.flinch_chance

    # Ailment data
    for row in db.execute('''
        SELECT
            move_id, ailment_chance,
            move_meta_ailments.identifier AS meta_ailment
        FROM move_meta

        JOIN move_meta_ailments
        ON move_meta.meta_ailment_id = move_meta_ailments.id

        WHERE move_id < 10000 -- ignore non-standard moves;
    '''):
        meta = data[row.move_id]['meta']

        if row.ailment_chance > 0:
            meta['ailment'] = {
                'ailment': row.meta_ailment,
                'chance': row.ailment_chance,
            }

    # Stat change data
    for row in db.execute('''
        SELECT
            move_meta.move_id, stat_chance,
            move_meta_stat_changes.change AS change,
            stats.identifier AS stat
        FROM move_meta

        JOIN move_meta_stat_changes
        ON move_meta.move_id = move_meta_stat_changes.move_id

        JOIN stats
        ON move_meta_stat_changes.stat_id = stats.id

        WHERE move_meta.move_id < 10000 -- ignore non-standard moves;
    '''):
        meta = data[row.move_id]['meta']

        if row.stat_chance > 0:
            meta.setdefault('stat_changes', {
                'chance': row.stat_chance,
                'changes': [],
            })
            meta['stat_changes']['changes'].append({
                'stat': row.stat,
                'change': row.change,
            })

    # Convert to a dict keyed by id
    data = { datum['id']: datum for datum in data.values() }
    for datum in data.values():
        del datum['id']

    print(u.json_dumps(data))


main()
