import argparse

def parse_args(*, description=None, args={}):
    parser = argparse.ArgumentParser(description=description)
    for name, options in args.items():
        if isinstance(name, str):
            parser.add_argument(name, **options)
        else:
            parser.add_argument(*name, **options)
    return parser.parse_args()
