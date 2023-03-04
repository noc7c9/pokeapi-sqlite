# Custom sqlite row factory that allows accessing columns by name or index
class Row:
    @staticmethod
    def row_factory(cursor, row):
        return Row(cursor, row)

    def __init__(self, cursor, row):
        self._fields = { column[0]: i for i, column in enumerate(cursor.description) }
        self._values = row

    def __getitem__(self, key):
        return self._values[key]

    def __getattr__(self, key):
        if key in self._fields:
            return self._values[self._fields[key]]
        raise AttributeError(f'Row has no attribute {key}')

    def __len__(self):
        return len(self._values)

    def __iter__(self):
        for field, index in self._fields.items():
            yield field, self._values[index]

    def __repr__(self):
        inner = (", ".join(f"{field}={value!r}" for field, value in self))
        return f'Row({inner})'
