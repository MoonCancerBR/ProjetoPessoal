import argparse
import json
import shutil
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
BALANCE_PATH = PROJECT_DIR / "config" / "balance.json"


def _prepare_import_path():
    sys.path.insert(0, str(PROJECT_DIR.parent))


def _load_balance():
    if not BALANCE_PATH.exists():
        return {}
    with BALANCE_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("balance.json precisa conter um objeto JSON.")
    return data


def _save_balance(data, backup=False):
    if backup and BALANCE_PATH.exists():
        backup_path = BALANCE_PATH.with_suffix(".json.bak")
        shutil.copy2(BALANCE_PATH, backup_path)
        print(f"Backup salvo em: {backup_path}")

    BALANCE_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _parse_value(raw_value, current_value=None):
    if isinstance(current_value, bool):
        lowered = raw_value.lower()
        if lowered in ("true", "1", "yes", "sim"):
            return True
        if lowered in ("false", "0", "no", "nao", "não"):
            return False
        raise ValueError("Valor booleano invalido.")

    if isinstance(current_value, int) and not isinstance(current_value, bool):
        return int(raw_value)

    if isinstance(current_value, float):
        return float(raw_value)

    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return raw_value


def _known_constant_keys():
    _prepare_import_path()
    from Sobrevivencia.data import constants

    return {
        key
        for key, value in vars(constants).items()
        if key.isupper() and isinstance(value, (int, float, bool, str, list, dict))
    }


def command_list(_args):
    data = _load_balance()
    for key in sorted(data):
        print(f"{key}={data[key]!r}")


def command_get(args):
    data = _load_balance()
    if args.key not in data:
        print(f"{args.key} nao encontrado em balance.json")
        return 1
    print(f"{args.key}={data[args.key]!r}")
    return 0


def command_set(args):
    data = _load_balance()
    known_keys = _known_constant_keys()
    if args.key not in known_keys and not args.force:
        print(f"{args.key} nao existe em data.constants. Use --force para gravar mesmo assim.")
        return 1

    current_value = data.get(args.key)
    value = _parse_value(args.value, current_value)
    data[args.key] = value
    _save_balance(data, backup=args.backup)
    print(f"{args.key}={value!r}")
    return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Editor CLI de config/balance.json.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="Lista overrides atuais.")
    list_parser.set_defaults(handler=command_list)

    get_parser = subparsers.add_parser("get", help="Mostra uma chave.")
    get_parser.add_argument("key")
    get_parser.set_defaults(handler=command_get)

    set_parser = subparsers.add_parser("set", help="Atualiza uma chave.")
    set_parser.add_argument("key")
    set_parser.add_argument("value")
    set_parser.add_argument("--backup", action="store_true")
    set_parser.add_argument("--force", action="store_true")
    set_parser.set_defaults(handler=command_set)

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    result = args.handler(args)
    return 0 if result is None else result


if __name__ == "__main__":
    raise SystemExit(main())
