#!/usr/bin/env python3

import csv
import glob
import os
import re
import sqlite3
import subprocess
import sys
from collections import defaultdict


def info(*args): print('INFO:', *args, file=sys.stderr)
def warn(*args): print('WARN:', *args, file=sys.stderr)


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
    return string
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


def counts(iterable):
    counts = defaultdict(int)
    for item in iterable:
        counts[item] += 1
    return counts


if __name__ == '__main__':
    # Clone
    if not os.path.exists('pokeapi'):
        subprocess.call(['git', 'clone', '--depth=1', 'https://github.com/PokeAPI/pokeapi.git'])

    # Build
    try:
        os.remove('pokeapi.sqlite')
    except OSError:
        pass

    db = sqlite3.connect('pokeapi.sqlite')

    for file in glob.glob('pokeapi/data/v2/csv/*.csv'):
        table_name = os.path.splitext(os.path.basename(file))[0]
        info(f'Importing {table_name}...')

        with open(file, 'rt', encoding='utf8') as f:
            reader = csv.reader(f)

            # ASSUMATION: First row will always be the header
            headers = next(reader)
            column_count = len(headers)

            # Create the table for this CSV file
            rows = list(reader)
            sql = []
            for col_idx, column_name in enumerate(headers):
                # Figure out the type of the column
                type_counts = counts(get_value_type(row[col_idx]) for row in rows)
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

            # Ensure all rows have the same number of columns
            for i, row in enumerate(rows):
                if len(row) != column_count:
                    warn(f'Row has wrong number of columns (expected {column_count}): {row}')
                    rows[i] = (row + [None] * column_count)[:column_count]

            # Insert the data, all values will be coerced by SQLite
            db.executemany(f'INSERT INTO "{table_name}" VALUES ({",".join("?" * column_count)})', rows)
            db.commit()
