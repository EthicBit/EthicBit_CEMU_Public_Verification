#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def resolve_path(data, path):
    current = data
    if not path:
        return current

    for part in path.split("."):
        if isinstance(current, list):
            try:
                index = int(part)
            except ValueError:
                raise KeyError(f"List index required at '{part}'")
            try:
                current = current[index]
            except IndexError:
                raise KeyError(f"List index out of range at '{part}'")
        elif isinstance(current, dict):
            if part not in current:
                raise KeyError(f"Missing key '{part}'")
            current = current[part]
        else:
            raise KeyError(f"Cannot descend into non-container at '{part}'")
    return current


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file")
    parser.add_argument("path")
    parser.add_argument("--joined", action="store_true")
    args = parser.parse_args()

    data = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    value = resolve_path(data, args.path)

    if args.joined:
        if isinstance(value, list):
            for item in value:
                if isinstance(item, (dict, list)):
                    print(json.dumps(item, ensure_ascii=False))
                elif item is None:
                    print("null")
                else:
                    print(str(item))
        else:
            if isinstance(value, (dict, list)):
                print(json.dumps(value, ensure_ascii=False))
            elif value is None:
                print("null")
            else:
                print(str(value))
        return

    if isinstance(value, (dict, list)):
        print(json.dumps(value, ensure_ascii=False))
    elif value is None:
        print("null")
    else:
        print(str(value))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)