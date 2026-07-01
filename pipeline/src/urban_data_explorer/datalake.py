"""Materialisation du Data Lake en fichiers Parquet (C1.3).

En plus de MySQL/MongoDB, le build ecrit les zones Silver et Gold sous forme de
fichiers **Parquet colonnaire**, avec un **partitionnement Hive** par annee pour
les tables temporelles (`year=YYYY/`). On obtient ainsi un vrai data lake fichier
a trois zones :

    data/bronze/   sources brutes telechargees (CSV, ZIP, XLSX, GeoJSON)
    data/silver/   tables nettoyees et normalisees (Parquet)
    data/gold/     tables analytiques pretes a l'usage (Parquet, partitionnees)

Parquet apporte compression, typage et lecture par colonnes/partitions ; le
partitionnement par annee permet le predicate/partition pruning a la lecture.
"""
from __future__ import annotations

from pathlib import Path
import shutil

import pandas as pd

from .paths import repo_path


SILVER_DIR = repo_path("data/silver")
GOLD_DIR = repo_path("data/gold")

# Tables temporelles : partitionnees physiquement par annee (Hive-style year=YYYY/).
PARTITIONED_BY_YEAR = {
    "sales_yearly",
    "sales_quartier_yearly",
    "sales_iris_yearly",
    "sales_street_yearly",
    "sales_building_yearly",
    "rents_yearly",
    "social_yearly",
}


def _write_dataset(zone_dir: Path, name: str, frame: pd.DataFrame) -> str:
    """Ecrit un dataset Parquet (partitionne par `year` si pertinent) de facon idempotente."""
    target = zone_dir / name
    if target.exists():
        shutil.rmtree(target)  # reconstruction complete a chaque build

    if name in PARTITIONED_BY_YEAR and "year" in frame.columns:
        # Dataset partitionne : un sous-dossier year=YYYY/ par annee.
        frame.to_parquet(target, partition_cols=["year"], index=False, engine="pyarrow")
    else:
        target.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(target / "data.parquet", index=False, engine="pyarrow")

    return str(target)


def write_zone(zone_dir: Path, datasets: dict[str, pd.DataFrame]) -> dict[str, str]:
    zone_dir.mkdir(parents=True, exist_ok=True)
    return {
        f"lake:{zone_dir.name}:{name}": _write_dataset(zone_dir, name, frame)
        for name, frame in datasets.items()
    }


def write_datalake(
    *,
    silver: dict[str, pd.DataFrame],
    gold: dict[str, pd.DataFrame],
) -> dict[str, str]:
    """Ecrit les zones Silver et Gold du data lake et renvoie les chemins produits."""
    outputs: dict[str, str] = {}
    outputs.update(write_zone(SILVER_DIR, silver))
    outputs.update(write_zone(GOLD_DIR, gold))
    return outputs
