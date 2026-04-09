from __future__ import annotations

import argparse

from .config import load_sources
from .build import build_gold
from .ingestion.downloader import download_source


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="urban-data-explorer",
        description="Telecharge les sources ouvertes du projet Urban Data Explorer.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="Affiche les sources configurees.")

    download_parser = subparsers.add_parser("download", help="Telecharge une ou plusieurs sources.")
    download_parser.add_argument(
        "names",
        nargs="*",
        help="Noms des sources a telecharger. Si vide, toutes les sources sont prises.",
    )
    download_parser.add_argument(
        "--force",
        action="store_true",
        help="Retelecharge le fichier meme s'il existe deja.",
    )

    build_parser = subparsers.add_parser("build", help="Construit les zones Silver et Gold.")
    build_parser.add_argument(
        "--skip-noise",
        action="store_true",
        help="Ignore le calcul Bruitparif si vous voulez un build plus rapide.",
    )

    return parser


def cmd_list() -> int:
    sources = load_sources()
    for name, source in sources.items():
        print(f"{name}: {source.label}")
        print(f"  groupe: {source.group}")
        print(f"  cible:  {source.target_path}")
        print(f"  resume: {source.summary}")
    return 0


def cmd_download(names: list[str], force: bool) -> int:
    sources = load_sources()
    selected_names = names or list(sources.keys())

    unknown = [name for name in selected_names if name not in sources]
    if unknown:
        raise SystemExit(f"Sources inconnues: {', '.join(unknown)}")

    for name in selected_names:
        source = sources[name]
        output_path = download_source(source, force=force)
        print(f"{name}: {output_path}")

    return 0


def cmd_build(skip_noise: bool) -> int:
    outputs = build_gold(include_noise=not skip_noise)
    for name, output_path in outputs.items():
        print(f"{name}: {output_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        return cmd_list()
    if args.command == "download":
        return cmd_download(args.names, args.force)
    if args.command == "build":
        return cmd_build(args.skip_noise)

    parser.error("Commande non prise en charge.")
    return 1
