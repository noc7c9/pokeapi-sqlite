# pokeapi.sqlite

The CSV data from [PokeAPI](https://github.com/PokeAPI/pokeapi) as a SQLite file
as an alternative to the REST/GraphQL APIs.

The `build.py` script will build the SQLite file from a clone of the PokeAPI
repo (it will clone if it doesn't exist). This means you can build the database
for any version of PokeAPI by just checking out the correct commit.

The script is written in python 3 and has no dependencies (other than stdlib).

---

Downloads if you just want the latest version (updated weekly)
- [pokeapi.sqlite.gz](https://github.com/noc7c9/pokeapi-sqlite/raw/dist/pokeapi.sqlite.gz) (~12 MB)
- [pokeapi.sqlite.xz](https://github.com/noc7c9/pokeapi-sqlite/raw/dist/pokeapi.sqlite.xz) (~6 MB)
