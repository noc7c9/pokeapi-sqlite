import os
import sqlite3
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Import the utils module from the parent directory
sys.path.append(parent_dir)
from utils import *

def open_db():
    pokeapi_sqlite = os.path.join(parent_dir, 'pokeapi.sqlite')

    try:
        # Open the database in read-only mode and don't create it if it doesn't exist
        db = sqlite3.connect(f'file:{pokeapi_sqlite}?mode=ro', uri=True)
        db.row_factory = Row.row_factory
        return db
    except sqlite3.OperationalError as e:
        error(f'Failed to open pokeapi.sqlite database: {e}')
        info('Did you forget to run "build.py"?')
        sys.exit(1)
