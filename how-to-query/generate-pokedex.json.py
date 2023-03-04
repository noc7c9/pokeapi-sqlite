#!/usr/bin/env python3

import u

NATIONAL_DEX_ID = 1

def main():
    u.parse_args()

    db = u.open_db()

    data = {}

    # Basic info
    for row in db.execute('''
        SELECT
            p.species_id AS pokemon_id, p.identifier, ps."order" AS "order",
            p.height, p.weight, p.base_experience, ps.base_happiness,
            ps.hatch_counter, ps.capture_rate, ps.gender_rate,
            ps.is_baby, ps.is_legendary, ps.is_mythical,
            pokemon_habitats.identifier AS habitat,
            growth_rates.identifier AS growth_rate
        FROM pokemon AS p

        JOIN pokemon_species AS ps
        ON p.species_id = ps.id

        LEFT JOIN pokemon_habitats
        ON ps.habitat_id = pokemon_habitats.id

        LEFT JOIN growth_rates
        ON ps.growth_rate_id = growth_rates.id

        WHERE pokemon_id < 10000 -- ignore non-standard pokemon
    '''):
        datum = data.setdefault(row.pokemon_id, {
            'id': row.identifier,
            'national_dex_number': None,
            'sort_order': row.order,
            'name': {},
            'genus': {},
            'flavor_text': {},
            'type': None,
            'abilities': None,
            'base_stats': {},
            'effort_values': {},
            'moves': {
                'level-up': {},
            },
            'evolves_from': None,
            'evolves_to': [],
            'base_experience': row.base_experience,
            'height': row.height,
            'weight': row.weight,
            'gender_rate': row.gender_rate,
            'capture_rate': row.capture_rate,
            'base_happiness': row.base_happiness,
            'hatch_counter': row.hatch_counter,
            'egg_groups': [],
            'is_baby': row.is_baby,
            'is_legendary': row.is_legendary,
            'is_mythical': row.is_mythical,
            'habitat': row.habitat,
            'growth_rate': row.growth_rate,
        })

    # Names
    for row in db.execute('''
        SELECT pokemon_species_id AS pokemon_id, iso3166, name, genus
        FROM pokemon_species_names

        JOIN languages
        ON pokemon_species_names.local_language_id = languages.id
    '''):
        data[row.pokemon_id]['name'][row.iso3166] = row.name
        if row.genus != "":
            data[row.pokemon_id]['genus'][row.iso3166] = row.genus

    # Pokedex numbers
    for row in db.execute('''
        SELECT species_id AS pokemon_id, pokedex_number
        FROM pokemon_dex_numbers
        WHERE pokedex_id = ?
    ''', (NATIONAL_DEX_ID,)):
        data[row.pokemon_id]['national_dex_number'] = row.pokedex_number

    # Flavor text
    for row in db.execute('''
        SELECT species_id AS pokemon_id, iso3166, flavor_text
        FROM pokemon_species_flavor_text

        JOIN languages
        ON pokemon_species_flavor_text.language_id = languages.id
    '''):
        data[row.pokemon_id]['flavor_text'].setdefault(row.iso3166, set())
        flavor_text = data[row.pokemon_id]['flavor_text'][row.iso3166]
        flavor_text.add(clean_flavor_text(row.flavor_text))
    for datum in data.values():
        for lang, text in datum['flavor_text'].items():
            datum['flavor_text'][lang] = list(text)

    # Types
    for row in db.execute('''
        SELECT p.pokemon_id, t1.identifier AS type1, t2.identifier AS type2
        FROM (SELECT DISTINCT pokemon_id FROM pokemon_types) p

        LEFT JOIN pokemon_types pt1 ON p.pokemon_id = pt1.pokemon_id AND pt1.slot = 1
        LEFT JOIN pokemon_types pt2 ON p.pokemon_id = pt2.pokemon_id AND pt2.slot = 2

        LEFT JOIN types t1 ON pt1.type_id = t1.id
        LEFT JOIN types t2 ON pt2.type_id = t2.id

        WHERE pt1.pokemon_id < 10000 -- ignore non-standard pokemon
    '''):
        data[row.pokemon_id]['type'] = [row.type1]
        if row.type2:
            data[row.pokemon_id]['type'].append(row.type2)

    # Base stats
    for row in db.execute('''
        SELECT pokemon_id, stats.identifier AS stat, base_stat, effort
        FROM pokemon_stats

        JOIN stats
        ON pokemon_stats.stat_id = stats.id

        WHERE pokemon_id < 10000 -- ignore non-standard pokemon
    '''):
        data[row.pokemon_id]['base_stats'][row.stat] = row.base_stat
        if row.effort != 0:
            data[row.pokemon_id]['effort_values'][row.stat] = row.effort
    for datum in data.values():
        datum['base_stats']['total'] = sum(datum['base_stats'].values())

    # Abilities
    for row in db.execute('''
        SELECT
            p.pokemon_id,
            a1.identifier AS slot1, pa1.is_hidden AS is_hidden1,
            a2.identifier AS slot2, pa2.is_hidden AS is_hidden2,
            a3.identifier AS slot3, pa3.is_hidden AS is_hidden3
        FROM (SELECT DISTINCT pokemon_id FROM pokemon_abilities) p

        LEFT JOIN pokemon_abilities pa1 ON p.pokemon_id = pa1.pokemon_id AND pa1.slot = 1
        LEFT JOIN pokemon_abilities pa2 ON p.pokemon_id = pa2.pokemon_id AND pa2.slot = 2
        LEFT JOIN pokemon_abilities pa3 ON p.pokemon_id = pa3.pokemon_id AND pa3.slot = 3

        LEFT JOIN abilities a1 ON pa1.ability_id = a1.id
        LEFT JOIN abilities a2 ON pa2.ability_id = a2.id
        LEFT JOIN abilities a3 ON pa3.ability_id = a3.id

        WHERE p.pokemon_id < 10000 -- ignore non-standard pokemon
    '''):
        datum = data[row.pokemon_id]

        def to_dict(ability, is_hidden):
            if is_hidden == 0:
                return { 'ability': ability }
            return { 'ability': ability, 'is_hidden': is_hidden }

        datum['abilities'] = []
        if row.slot1: datum['abilities'].append(to_dict(row.slot1, row.is_hidden1))
        if row.slot2: datum['abilities'].append(to_dict(row.slot2, row.is_hidden2))
        if row.slot3: datum['abilities'].append(to_dict(row.slot3, row.is_hidden3))

    # Egg groups
    for row in db.execute('''
        SELECT
            species_id AS pokemon_id,
            egg_groups.identifier AS egg_group
        FROM pokemon_egg_groups

        JOIN egg_groups
        ON pokemon_egg_groups.egg_group_id = egg_groups.id

        WHERE pokemon_id < 10000 -- ignore non-standard pokemon
    '''):
        data[row.pokemon_id]['egg_groups'].append(row.egg_group)

    # Moves
    for row in db.execute('''
        SELECT
            pm.pokemon_id, pm.version_group_id,
            m.identifier AS move,
            pmm.identifier AS move_method,
            IIF(pmm.identifier = 'level-up', pm.level, NULL) AS level
        FROM pokemon_moves AS pm

        -- Get the latest moveset for each pokemon
        JOIN (
            SELECT pokemon_id, MAX(version_group_id) AS latest
            FROM pokemon_moves
            GROUP BY pokemon_id
        ) AS ver
        ON pm.pokemon_id = ver.pokemon_id AND pm.version_group_id = ver.latest

        JOIN moves AS m
        ON pm.move_id = m.id

        JOIN pokemon_move_methods AS pmm
        ON pm.pokemon_move_method_id = pmm.id

        WHERE pm.pokemon_id < 10000 -- ignore non-standard pokemon

        ORDER BY pm.pokemon_id, pm.level
    '''):
        datum = data[row.pokemon_id]
        if row.move_method == 'level-up':
            datum['moves']['level-up'][row.level] = row.move
        else:
            datum['moves'].setdefault(row.move_method, []).append(row.move)

    # Evolution From
    for row in db.execute('''
        SELECT ps1.id AS pokemon_id, ps2.identifier AS evolves_from
        FROM pokemon_species AS ps1

        JOIN pokemon_species AS ps2
        ON ps1.evolves_from_species_id = ps2.id

        WHERE ps1.id < 10000 -- ignore non-standard pokemon
    '''):
        datum = data[row.pokemon_id]
        datum['evolves_from'] = row.evolves_from

    # Evolutions To
    for row in db.execute('''
        SELECT
            ps.evolves_from_species_id AS pokemon_id,
            ps.identifier AS evolves_to,
            et.identifier AS evolution_trigger,
            pe.minimum_level,
            pe.minimum_happiness, pe.minimum_affection, pe.minimum_beauty,
            pe.time_of_day, pe.relative_physical_stats,
            pe.needs_overworld_rain, pe.turn_upside_down,
            ti.identifier AS trigger_item,
            hi.identifier AS held_item,
            km.identifier AS known_move,
            kt.identifier AS known_move_type,
            g.identifier AS gender,
            l.identifier AS location,
            r.identifier AS location_region,
            party_species.identifier AS party_species,
            party_type.identifier AS party_type,
            trade_species.identifier AS trade_species
        FROM pokemon_evolution AS pe

        JOIN pokemon_species AS ps
        ON pe.evolved_species_id = ps.id

        JOIN evolution_triggers AS et
        ON pe.evolution_trigger_id = et.id

        LEFT JOIN items AS ti
        ON pe.trigger_item_id = ti.id

        LEFT JOIN items AS hi
        ON pe.held_item_id = hi.id

        LEFT JOIN moves AS km
        ON pe.known_move_id = km.id

        LEFT JOIN types AS kt
        ON pe.known_move_type_id = kt.id

        LEFT JOIN genders AS g
        ON pe.gender_id = g.id

        LEFT JOIN locations AS l
        ON pe.location_id = l.id
        LEFT JOIN regions AS r
        ON l.region_id = r.id

        LEFT JOIN pokemon_species AS party_species
        ON pe.party_species_id = party_species.id

        LEFT JOIN types AS party_type
        ON pe.party_type_id = party_type.id

        LEFT JOIN pokemon_species AS trade_species
        ON pe.trade_species_id = trade_species.id

        WHERE ps.id < 10000 -- ignore non-standard pokemon
    '''):
        datum = data[row.pokemon_id]
        entry = {
            'pokemon': row.evolves_to,
            'trigger': row.evolution_trigger,
        }
        is_valid = lambda x: x != None and x != ''

        if is_valid(row.minimum_level):
            entry['minimum_level'] = row.minimum_level

        if is_valid(row.minimum_happiness):
            entry['minimum_happiness'] = row.minimum_happiness
        if is_valid(row.minimum_affection):
            entry['minimum_affection'] = row.minimum_affection
        if is_valid(row.minimum_beauty):
            entry['minimum_beauty'] = row.minimum_beauty

        if is_valid(row.time_of_day):
            entry['time_of_day'] = row.time_of_day
        if is_valid(row.relative_physical_stats):
            entry['relative_physical_stats'] = row.relative_physical_stats
        if row.needs_overworld_rain == 1:
            entry['during_overworld_rain'] = True
        if row.turn_upside_down == 1:
            entry['hold_device_upside_down'] = True

        if is_valid(row.trigger_item):
            entry['trigger_item'] = row.trigger_item
        if is_valid(row.held_item):
            entry['held_item'] = row.held_item

        if is_valid(row.known_move):
            entry['known_move'] = row.known_move
        if is_valid(row.known_move_type):
            entry['known_move_type'] = row.known_move_type

        if is_valid(row.gender):
            entry['gender'] = row.gender

        if is_valid(row.location):
            entry['location'] = { "location": row.location, "region": None }
            if is_valid(row.location_region):
                entry['location']['region'] = row.location_region

        if is_valid(row.party_species):
            entry['pokemon_in_party'] = row.party_species
        if is_valid(row.party_type):
            entry['type_in_party'] = row.party_type
        if is_valid(row.trade_species):
            entry['trade_for'] = row.trade_species

        datum['evolves_to'].append(entry)

    # Convert to a dict keyed by id
    data = { datum['id']: datum for datum in data.values() }
    for datum in data.values():
        del datum['id']

    print(u.json_dumps(data))


def clean_flavor_text(flavor_text):
    return flavor_text.replace('\n', ' ').replace('\x0c', ' ')


main()
