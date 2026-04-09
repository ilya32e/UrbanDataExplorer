from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from fastapi import HTTPException
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
GOLD_DIR = REPO_ROOT / "data" / "gold"
QUARTIER_MAP_METRICS = ("median_price_m2", "transactions", "median_surface_m2")
STREET_MAP_METRICS = ("median_price_m2", "transactions", "median_surface_m2")
BUILDING_MAP_METRICS = ("median_price_m2", "transactions", "median_surface_m2")
MAP_LEVEL_LABELS = {
    "arrondissement": "Arrondissements",
    "quartier": "Quartiers",
    "street": "Rues",
    "building": "Batiments",
}


def _gold_path(filename: str) -> Path:
    return GOLD_DIR / filename


def _ensure_exists(path: Path) -> None:
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Le fichier {path.name} est introuvable. Lancez `python pipeline/run_imports.py build`.",
        )


@lru_cache(maxsize=1)
def load_dashboard_payload() -> dict[str, object]:
    path = _gold_path("dashboard.json")
    _ensure_exists(path)
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_summary() -> pd.DataFrame:
    path = _gold_path("arrondissement_summary.csv")
    _ensure_exists(path)
    return pd.read_csv(path)


@lru_cache(maxsize=1)
def load_sales() -> pd.DataFrame:
    path = _gold_path("sales_yearly.csv")
    _ensure_exists(path)
    return pd.read_csv(path)


@lru_cache(maxsize=1)
def load_social() -> pd.DataFrame:
    path = _gold_path("social_yearly.csv")
    _ensure_exists(path)
    return pd.read_csv(path)


@lru_cache(maxsize=1)
def load_rents() -> pd.DataFrame:
    path = _gold_path("rents_yearly.csv")
    _ensure_exists(path)
    return pd.read_csv(path)


@lru_cache(maxsize=1)
def load_geojson() -> dict[str, object]:
    path = _gold_path("arrondissements.geojson")
    _ensure_exists(path)
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_sales_quartier() -> pd.DataFrame:
    path = _gold_path("sales_quartier_yearly.csv")
    _ensure_exists(path)
    data = pd.read_csv(path, dtype={"quartier_id": str})
    if "arrondissement" in data.columns:
        data["arrondissement"] = pd.to_numeric(data["arrondissement"], errors="coerce")
    return data


@lru_cache(maxsize=1)
def load_sales_street() -> pd.DataFrame:
    path = _gold_path("sales_street_yearly.csv")
    _ensure_exists(path)
    data = pd.read_csv(path, dtype={"street_key": str, "street_name": str, "commune_insee": str})
    for column in ["arrondissement", "year", "longitude", "latitude"]:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    return data


@lru_cache(maxsize=1)
def load_street_geojson() -> dict[str, object]:
    path = _gold_path("streets.geojson")
    _ensure_exists(path)
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_sales_building() -> pd.DataFrame:
    path = _gold_path("sales_building_yearly.csv")
    _ensure_exists(path)
    data = pd.read_csv(
        path,
        dtype={
            "building_id": str,
            "building_id_source": str,
            "building_label": str,
            "commune_insee": str,
            "street_name": str,
            "house_number": str,
            "house_suffix": str,
        },
    )
    for column in ["arrondissement", "year", "longitude", "latitude"]:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    return data


@lru_cache(maxsize=1)
def load_quartier_geojson() -> dict[str, object]:
    path = _gold_path("quartiers.geojson")
    _ensure_exists(path)
    return json.loads(path.read_text(encoding="utf-8"))


def metric_catalog() -> dict[str, dict[str, object]]:
    payload = load_dashboard_payload()
    return payload["metrics"]


def reference_geojson(level: str) -> dict[str, object]:
    if level == "quartier":
        return load_quartier_geojson()
    if level == "street":
        return load_street_geojson()
    raise HTTPException(status_code=404, detail=f"Reference cartographique inconnue: {level}")


def metadata() -> dict[str, object]:
    payload = load_dashboard_payload()
    return {
        "generated_at": payload["generated_at"],
        "latest_sales_year": payload["latest_sales_year"],
        "latest_social_year": payload["latest_social_year"],
        "latest_rent_year": payload["latest_rent_year"],
        "available_sales_years": payload["available_sales_years"],
        "available_social_years": payload["available_social_years"],
        "available_rent_years": payload["available_rent_years"],
        "metrics": payload["metrics"],
        "map_levels": [
            {
                "key": "arrondissement",
                "label": "Arrondissements",
                "supported_metrics": list(payload["metrics"].keys()),
            },
            {
                "key": "quartier",
                "label": "Quartiers",
                "supported_metrics": list(QUARTIER_MAP_METRICS),
            },
            {
                "key": "street",
                "label": "Rues",
                "supported_metrics": list(STREET_MAP_METRICS),
            },
            {
                "key": "building",
                "label": "Batiments",
                "supported_metrics": list(BUILDING_MAP_METRICS),
            },
        ],
    }


def overview_for_year(sales_year: int | None = None) -> dict[str, object]:
    base = load_summary().copy()
    sales = load_sales()
    selected_year = sales_year or int(sales["year"].max())

    if selected_year not in set(sales["year"].tolist()):
        raise HTTPException(status_code=404, detail=f"Aucune donnee de ventes pour {selected_year}.")

    yearly_sales = sales.loc[sales["year"] == selected_year].copy()
    yearly_sales_columns = [
        "transactions",
        "median_price_m2",
        "median_sale_value_eur",
        "median_surface_m2",
        "median_rooms",
        "apartment_share_pct",
        "house_share_pct",
    ]

    merged = base.drop(columns=yearly_sales_columns + ["months_income_for_1sqm"], errors="ignore")
    merged = merged.merge(
        yearly_sales[["arrondissement", *yearly_sales_columns]],
        on="arrondissement",
        how="left",
    )

    merged["months_income_for_1sqm"] = (
        merged["median_price_m2"] / (merged["median_income_eur"] / 12.0)
    ).round(2)

    merged["rank_by_price"] = merged["median_price_m2"].rank(method="min", ascending=False).astype(int)
    merged = merged.sort_values("arrondissement").reset_index(drop=True)

    city = {
        "arrondissement_count": int(merged["arrondissement"].nunique()),
        "selected_sales_year": selected_year,
        "median_price_m2": round(float(merged["median_price_m2"].median()), 2),
        "median_income_eur": round(float(merged["median_income_eur"].median()), 2),
        "reference_rent_majorated_eur_m2": round(float(merged["reference_rent_majorated_eur_m2"].median()), 2),
        "social_units_financed": int(merged["social_units_financed"].sum()),
        "social_units_financed_5y": int(merged["social_units_financed_5y"].sum()),
        "quality_of_life_score": round(float(merged["quality_of_life_score"].median()), 2),
        "months_income_for_1sqm": round(float(merged["months_income_for_1sqm"].median()), 2),
        "estimated_50m2_rent_effort_pct": round(float(merged["estimated_50m2_rent_effort_pct"].median()), 1),
    }

    return {
        "city": city,
        "arrondissements": json.loads(merged.to_json(orient="records")),
    }


def timeline_for_arrondissement(arrondissement: int) -> dict[str, object]:
    summary = load_summary()
    record = summary.loc[summary["arrondissement"] == arrondissement]
    if record.empty:
        raise HTTPException(status_code=404, detail="Arrondissement introuvable.")

    sales = load_sales().loc[load_sales()["arrondissement"] == arrondissement].sort_values("year")
    social = load_social().loc[load_social()["arrondissement"] == arrondissement].sort_values("year")
    rents = load_rents().loc[load_rents()["arrondissement"] == arrondissement].sort_values("year")

    return {
        "arrondissement": int(arrondissement),
        "name": record.iloc[0]["name"],
        "sales": json.loads(sales.to_json(orient="records")),
        "social": json.loads(social.to_json(orient="records")),
        "rents": json.loads(rents.to_json(orient="records")),
    }


def compare_arrondissements(left: int, right: int, sales_year: int | None = None) -> dict[str, object]:
    overview = overview_for_year(sales_year=sales_year)
    rows = {item["arrondissement"]: item for item in overview["arrondissements"]}

    if left not in rows or right not in rows:
        raise HTTPException(status_code=404, detail="Impossible de comparer ces arrondissements.")

    metrics = [
        "median_price_m2",
        "median_income_eur",
        "reference_rent_majorated_eur_m2",
        "social_units_financed",
        "quality_of_life_score",
        "months_income_for_1sqm",
        "estimated_50m2_rent_effort_pct",
    ]
    delta = {}
    for metric in metrics:
        left_value = rows[left].get(metric)
        right_value = rows[right].get(metric)
        if left_value is None or right_value is None:
            continue
        delta[metric] = round(float(left_value) - float(right_value), 2)

    return {
        "sales_year": overview["city"]["selected_sales_year"],
        "left": rows[left],
        "right": rows[right],
        "delta": delta,
    }


def _resolve_sales_year(sales: pd.DataFrame, year: int | None) -> int:
    selected_year = year or int(sales["year"].max())
    if selected_year not in set(sales["year"].tolist()):
        raise HTTPException(status_code=404, detail=f"Aucune donnee de ventes pour {selected_year}.")
    return selected_year


def _build_map_metric_payload(metric: str, metrics: dict[str, dict[str, object]], selected_year: int | None, level: str) -> dict[str, object]:
    return {
        "key": metric,
        **metrics[metric],
        "year": selected_year if metrics[metric]["supports_year"] else None,
        "level": level,
        "level_label": MAP_LEVEL_LABELS[level],
    }


def _map_geojson_arrondissement(metric: str, year: int | None, metrics: dict[str, dict[str, object]]) -> dict[str, object]:
    overview = overview_for_year(sales_year=year)
    rows = {item["arrondissement"]: item for item in overview["arrondissements"]}
    payload = load_geojson()

    features = []
    for feature in payload["features"]:
        arrondissement = int(feature["properties"]["arrondissement"])
        row = rows[arrondissement]
        properties = dict(feature["properties"])
        properties.update(row)
        properties["arrondissement"] = arrondissement
        properties["map_level"] = "arrondissement"
        properties["selected_metric"] = metric
        properties["metric_value"] = row.get(metric)
        features.append(
            {
                "type": "Feature",
                "geometry": feature["geometry"],
                "properties": properties,
            }
        )

    return {
        "type": "FeatureCollection",
        "metric": _build_map_metric_payload(
            metric,
            metrics,
            overview["city"]["selected_sales_year"],
            level="arrondissement",
        ),
        "features": features,
    }


def _map_geojson_quartier(metric: str, year: int | None, metrics: dict[str, dict[str, object]]) -> dict[str, object]:
    if metric not in QUARTIER_MAP_METRICS:
        supported = ", ".join(QUARTIER_MAP_METRICS)
        raise HTTPException(
            status_code=400,
            detail=f"La vue quartier prend en charge uniquement: {supported}.",
        )

    sales = load_sales_quartier()
    selected_year = _resolve_sales_year(sales, year)
    yearly_sales = sales.loc[sales["year"] == selected_year].copy()
    rows = {item["quartier_id"]: item for item in json.loads(yearly_sales.to_json(orient="records"))}
    payload = load_quartier_geojson()

    features = []
    for feature in payload["features"]:
        quartier_id = str(feature["properties"]["quartier_id"])
        properties = dict(feature["properties"])
        row = rows.get(quartier_id, {})
        properties.update(row)
        properties["quartier_id"] = quartier_id
        properties["arrondissement"] = int(properties["arrondissement"])
        properties["map_level"] = "quartier"
        properties["selected_metric"] = metric
        properties["metric_value"] = row.get(metric)
        features.append(
            {
                "type": "Feature",
                "geometry": feature["geometry"],
                "properties": properties,
            }
        )

    return {
        "type": "FeatureCollection",
        "metric": _build_map_metric_payload(metric, metrics, selected_year, level="quartier"),
        "features": features,
    }


def _map_geojson_points(
    metric: str,
    year: int | None,
    metrics: dict[str, dict[str, object]],
    *,
    sales: pd.DataFrame,
    key_column: str,
    label_column: str,
    level: str,
    supported_metrics: tuple[str, ...],
) -> dict[str, object]:
    if metric not in supported_metrics:
        supported = ", ".join(supported_metrics)
        raise HTTPException(
            status_code=400,
            detail=f"La vue {MAP_LEVEL_LABELS[level].lower()} prend en charge uniquement: {supported}.",
        )

    selected_year = _resolve_sales_year(sales, year)
    yearly_sales = sales.loc[sales["year"] == selected_year].copy()
    yearly_sales = yearly_sales.loc[yearly_sales["longitude"].notna() & yearly_sales["latitude"].notna()].copy()

    features = []
    for row in json.loads(yearly_sales.to_json(orient="records")):
        properties = dict(row)
        properties["map_level"] = level
        properties["name"] = row.get(label_column) or row.get(key_column)
        properties["selected_metric"] = metric
        properties["metric_value"] = row.get(metric)
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row["longitude"], row["latitude"]],
                },
                "properties": properties,
            }
        )

    return {
        "type": "FeatureCollection",
        "metric": _build_map_metric_payload(metric, metrics, selected_year, level=level),
        "features": features,
    }


def _map_geojson_street(metric: str, year: int | None, metrics: dict[str, dict[str, object]]) -> dict[str, object]:
    if metric not in STREET_MAP_METRICS:
        supported = ", ".join(STREET_MAP_METRICS)
        raise HTTPException(
            status_code=400,
            detail=f"La vue rues prend en charge uniquement: {supported}.",
        )

    sales = load_sales_street()
    selected_year = _resolve_sales_year(sales, year)
    yearly_sales = sales.loc[sales["year"] == selected_year].copy()
    rows = {item["street_key"]: item for item in json.loads(yearly_sales.to_json(orient="records"))}
    payload = load_street_geojson()

    features = []
    for feature in payload["features"]:
        street_key = str(feature["properties"]["street_key"])
        row = rows.get(street_key)
        if row is None:
            continue

        properties = dict(feature["properties"])
        properties.update(row)
        properties["map_level"] = "street"
        properties["name"] = properties.get("display_name") or row.get("street_name") or street_key
        properties["selected_metric"] = metric
        properties["metric_value"] = row.get(metric)
        features.append(
            {
                "type": "Feature",
                "geometry": feature["geometry"],
                "properties": properties,
            }
        )

    return {
        "type": "FeatureCollection",
        "metric": _build_map_metric_payload(metric, metrics, selected_year, level="street"),
        "features": features,
    }


def _map_geojson_building(metric: str, year: int | None, metrics: dict[str, dict[str, object]]) -> dict[str, object]:
    return _map_geojson_points(
        metric,
        year,
        metrics,
        sales=load_sales_building(),
        key_column="building_id",
        label_column="building_label",
        level="building",
        supported_metrics=BUILDING_MAP_METRICS,
    )


def map_geojson(metric: str, year: int | None = None, level: str = "arrondissement") -> dict[str, object]:
    metrics = metric_catalog()
    if metric not in metrics:
        raise HTTPException(status_code=404, detail=f"Metrique inconnue: {metric}")
    if level == "quartier":
        return _map_geojson_quartier(metric=metric, year=year, metrics=metrics)
    if level == "street":
        return _map_geojson_street(metric=metric, year=year, metrics=metrics)
    if level == "building":
        return _map_geojson_building(metric=metric, year=year, metrics=metrics)
    if level == "arrondissement":
        return _map_geojson_arrondissement(metric=metric, year=year, metrics=metrics)
    raise HTTPException(status_code=404, detail=f"Niveau cartographique inconnu: {level}")
