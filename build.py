#!/usr/bin/env python3

import collections
import csv
import datetime
import glob
import os
import re
import sqlite3
import subprocess
import sys
import utils as u


# src: pokeapi/data/v2/build.py
GROUP_RGX = r"\[(.*?)\]\{(.*?)\}"
SUB_RGX = r"\[.*?\]\{.*?\}"
def scrub_string(string):
    """
    The purpose of this function is to scrub the weird template mark-up out of strings
    that Veekun is using for their pokedex.
    Example:
        []{move:dragon-tail} will effect the opponents [HP]{mechanic:hp}.
    Becomes:
        dragon tail will effect the opponents HP.

    If you find this results in weird strings please take a stab at improving or re-writing.
    """
    groups = re.findall(GROUP_RGX, string)
    for group in groups:
        if group[0]:
            sub = group[0]
        else:
            sub = group[1].split(":")
            if len(sub) >= 2:
                sub = sub[1]
            else:
                sub = sub[0]
            sub = sub.replace("-", " ")
        string = re.sub(SUB_RGX, sub, string, 1)
    return string


INT_PATTTERN = re.compile(r'^-?\d+$') # Matches: 123, -123, 0
REAL_PATTERN = re.compile(r'^(?:-?\d+\.\d*|\.\d+)$') # Matches: 123.456, -123.456, 0.456, .456, 123.
def get_value_type(value):
    if not value:
        return 'NULL'
    if INT_PATTTERN.match(value):
        return 'INTEGER'
    if REAL_PATTERN.match(value):
        return 'REAL'
    if value != '':
        return 'TEXT'
    return 'NULL'


def get_column_type(type_counts):
    # if there is even a single TEXT value, the column is TEXT
    if type_counts['TEXT'] > 0:
        return 'TEXT'
    if type_counts['REAL'] > 0:
        return 'REAL'
    if type_counts['INTEGER'] > 0:
        return 'INTEGER'
    # if there's no values at all, default to BLOB (ie. no coercion)
    return 'BLOB'


def get_column_is_nullable(type_counts):
    # if there is even a single NULL value, the column is NULLABLE
    return type_counts['NULL'] > 0


def safe_index(array, index, default = None):
    try:
        return array[index]
    except IndexError:
        return default


def counts(iterable):
    counts = collections.defaultdict(int)
    for item in iterable:
        counts[item] += 1
    return counts


if __name__ == '__main__':
    args = u.parse_args(
        description='Builds the pokeapi.sqlite file. It will clone the PokeAPI repo if it does not exist.',
        args={
            '--overwrite': {
                'action': 'store_true',
                'help': 'Overwrite the pokeapi.sqlite file if it exists',
            },
            '--no-clone': {
                'action': 'store_true',
                'help': 'Do not clone the PokeAPI repo if it does not exist',
            },
        }
    )


    # Clone
    if not os.path.exists('pokeapi'):
        if args.no_clone:
            u.error('PokeAPI repo does not exist.')
            sys.exit(1)

        u.info('Cloning PokeAPI repo...')
        subprocess.call(['git', 'clone', '--depth=1', 'https://github.com/PokeAPI/pokeapi.git'])
        u.info()


    # Build
    if os.path.exists('pokeapi.sqlite'):
        if not args.overwrite:
            u.error('The pokeapi.sqlite file already exists.')
            sys.exit(1)

        u.warn('Removing existing pokeapi.sqlite file...')
        os.remove('pokeapi.sqlite')
        u.info()

    db = sqlite3.connect('pokeapi.sqlite')


    # Add metadata
    db.execute('CREATE TABLE __metadata (key TEXT PRIMARY KEY, value TEXT)')

    sql = 'INSERT INTO __metadata VALUES (?, ?)'

    now = datetime.datetime.utcnow().isoformat()
    u.info(f'Created at: {now}')
    db.execute(sql, ('created_at', now))

    pokeapi_git_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd='pokeapi').decode('utf8').strip()
    u.info(f'PokeAPI Git SHA: {pokeapi_git_sha}')
    db.execute(sql, ('pokeapi_git_sha', pokeapi_git_sha))

    pokeapi_sqlite_git_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf8').strip()
    u.info(f'PokeAPI SQLite Git SHA: {pokeapi_sqlite_git_sha}')
    db.execute(sql, ('pokeapi_sqlite_git_sha', pokeapi_sqlite_git_sha))

    u.info()


    # Close and re-open the database to ensure the total_changes count doesn't include the metadata
    db.commit()
    db.close()
    db = sqlite3.connect('pokeapi.sqlite')


    # Add pokeapi data
    total_tables = 0
    for file in glob.glob('pokeapi/data/v2/csv/*.csv'):
        table_name = os.path.splitext(os.path.basename(file))[0]
        u.info(f'Importing {table_name}...')

        with open(file, 'rt', encoding='utf8') as f:
            reader = csv.reader(f)

            # ASSUMPTION: First row will always be the header
            headers = next(reader)
            column_count = len(headers)

            # Create the table for this CSV file
            rows = list(reader)
            sql = []
            for col_idx, column_name in enumerate(headers):
                # Figure out the type of the column
                type_counts = counts(get_value_type(safe_index(row, col_idx)) for row in rows)
                column_type = get_column_type(type_counts)
                column_is_nullable = get_column_is_nullable(type_counts)
                column_is_primary_key = (
                    column_name == 'id' and
                    column_type == 'INTEGER' and
                    not column_is_nullable and
                    len(rows) == len(set(row[col_idx] for row in rows)))

                sql_decl = f'"{column_name}" {column_type}'
                if not column_is_nullable:
                    sql_decl += ' NOT NULL'
                if column_is_primary_key:
                    sql_decl += ' PRIMARY KEY'

                sql.append(sql_decl)

                # Scrub string data
                if column_type == 'TEXT':
                    for row in rows:
                        row[col_idx] = scrub_string(row[col_idx])

            db.execute(f'CREATE TABLE "{table_name}" ({",".join(sql)})')
            total_tables += 1

            # Ensure all rows have the same number of columns
            for i, row in enumerate(rows):
                if len(row) != column_count:
                    u.warn(f'Row has wrong number of columns (expected {column_count}): {row}')
                    rows[i] = (row + [None] * column_count)[:column_count]

            # Insert the data, all values will be coerced by SQLite
            db.executemany(f'INSERT INTO "{table_name}" VALUES ({",".join("?" * column_count)})', rows)
            db.commit()

    total_rows = db.total_changes
    db.close()

    u.info()
    u.info('Database Metadata:')
    u.info(f'   Tables: {total_tables}')
    u.info(f'   Rows: {total_rows}')
    filesize = os.path.getsize("pokeapi.sqlite")
    u.info(f'   File Size: {filesize / 1024 / 1024:.2f} MB ({filesize} bytes)')

    u.info()
    u.info('Done!')
