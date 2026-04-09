const state = {
  meta: null,
  sources: [],
  salesYear: null,
  metric: "median_price_m2",
  mapLevel: "arrondissement",
  left: 11,
  right: 18,
  map: null,
  popup: null,
  referenceGeojson: {
    quartier: null,
    street: null,
  },
  referenceRequests: {},
};

const MAP_METRIC_PREFERENCES = {
  arrondissement: [
    "median_price_m2",
    "transactions",
    "median_surface_m2",
    "months_income_for_1sqm",
    "median_income_eur",
    "reference_rent_majorated_eur_m2",
    "social_units_financed",
    "social_units_financed_5y",
    "quality_of_life_score",
  ],
  quartier: ["median_price_m2", "transactions", "median_surface_m2"],
  street: ["median_price_m2", "transactions", "median_surface_m2"],
  building: ["median_price_m2", "transactions", "median_surface_m2"],
};
const POINT_MAP_LEVELS = new Set(["building"]);

const currency = new Intl.NumberFormat("fr-FR", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

const number = new Intl.NumberFormat("fr-FR", {
  maximumFractionDigits: 0,
});

const decimal = new Intl.NumberFormat("fr-FR", {
  maximumFractionDigits: 2,
});

function formatMetricValue(metric, value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "n.d.";
  }

  const numeric = Number(value);
  if (metric.includes("eur") || metric.includes("price") || metric.includes("rent")) {
    if (metric.endsWith("_m2")) {
      return `${currency.format(numeric)}/m²`;
    }
    return currency.format(numeric);
  }
  if (metric.includes("_pct") || metric.includes("share")) {
    return `${decimal.format(numeric)} %`;
  }
  if (metric.includes("score") || metric.includes("index") || metric.includes("months")) {
    return decimal.format(numeric);
  }
  return number.format(numeric);
}

function safeMetricLabel(key) {
  return state.meta?.metrics?.[key]?.label ?? key;
}

function formatCount(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? number.format(numeric) : "n.d.";
}

function buildingSourceLabel(source) {
  const labels = {
    ban_address: "Adresse BAN",
    parcel: "Parcelle",
    address_key: "Cle d'adresse",
  };
  return labels[source] ?? source ?? "n.d.";
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`${response.status} ${message}`);
  }
  return response.json();
}

async function loadReferenceLayer(level) {
  if (state.referenceGeojson[level]) {
    return state.referenceGeojson[level];
  }
  if (!state.referenceRequests[level]) {
    state.referenceRequests[level] = fetchJson(`/api/reference/${encodeURIComponent(level)}`).then((payload) => {
      state.referenceGeojson[level] = payload;
      return payload;
    });
  }
  return state.referenceRequests[level];
}

function supportedMetricsForLevel(level = state.mapLevel) {
  const supported = state.meta?.map_levels?.find((item) => item.key === level)?.supported_metrics ?? [];
  return new Set(supported);
}

function populateMapLevelSelect() {
  const select = document.getElementById("map-level-select");
  const levels = state.meta?.map_levels ?? [];
  select.innerHTML = "";
  levels.forEach((level) => {
    const option = document.createElement("option");
    option.value = level.key;
    option.textContent = level.label;
    select.append(option);
  });
  select.value = state.mapLevel;
  select.onchange = async (event) => {
    state.mapLevel = event.target.value;
    populateMetricSelect();
    await refreshMap();
  };
}

function populateMetricSelect() {
  const select = document.getElementById("metric-select");
  select.innerHTML = "";
  const supported = supportedMetricsForLevel();
  const preferred = (MAP_METRIC_PREFERENCES[state.mapLevel] ?? []).filter(
    (key) => supported.has(key) && state.meta.metrics[key],
  );
  const metricKeys = preferred.length
    ? preferred
    : Object.keys(state.meta.metrics).filter((key) => supported.has(key));

  metricKeys.forEach((key) => {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = state.meta.metrics[key].label;
    select.append(option);
  });
  if (!metricKeys.includes(state.metric)) {
    state.metric = metricKeys[0] ?? "median_price_m2";
  }
  select.value = state.metric;
  select.onchange = async (event) => {
    state.metric = event.target.value;
    await refreshMap();
  };
}

function populateYearSelect() {
  const select = document.getElementById("sales-year-select");
  select.innerHTML = "";
  state.meta.available_sales_years.forEach((year) => {
    const option = document.createElement("option");
    option.value = String(year);
    option.textContent = String(year);
    select.append(option);
  });
  select.value = String(state.salesYear);
  select.onchange = async (event) => {
    state.salesYear = Number(event.target.value);
    await refreshAll();
  };
}

function populateArrondissementSelects(arrondissements) {
  const selects = [
    document.getElementById("left-select"),
    document.getElementById("right-select"),
  ];

  selects.forEach((select) => {
    const previous = Number(select.value || 0);
    select.innerHTML = "";
    arrondissements.forEach((item) => {
      const option = document.createElement("option");
      option.value = String(item.arrondissement);
      option.textContent = `${item.arrondissement} - ${item.name}`;
      select.append(option);
    });
    if (arrondissements.some((item) => item.arrondissement === previous)) {
      select.value = String(previous);
    }
  });

  document.getElementById("left-select").value = String(state.left);
  document.getElementById("right-select").value = String(state.right);

  document.getElementById("left-select").onchange = async (event) => {
    state.left = Number(event.target.value);
    await Promise.all([refreshComparison(), refreshTimeline()]);
    updateMapSelection();
  };
  document.getElementById("right-select").onchange = async (event) => {
    state.right = Number(event.target.value);
    await refreshComparison();
    updateMapSelection();
  };
}

function renderCitySummary(city) {
  const container = document.getElementById("city-summary");
  const cards = [
    {
      label: "Prix median au m²",
      value: formatMetricValue("median_price_m2", city.median_price_m2),
      context: `Serie ventes ${city.selected_sales_year}`,
    },
    {
      label: "Revenu median",
      value: formatMetricValue("median_income_eur", city.median_income_eur),
      context: "Filosofi 2021",
    },
    {
      label: "Mois de revenu pour 1 m²",
      value: formatMetricValue("months_income_for_1sqm", city.months_income_for_1sqm),
      context: "Prix / revenu",
    },
    {
      label: "Logements sociaux finances",
      value: formatMetricValue("social_units_financed", city.social_units_financed),
      context: `Derniere annee sociale ${state.meta.latest_social_year}`,
    },
    {
      label: "Effort locatif estime pour 50 m²",
      value: formatMetricValue("estimated_50m2_rent_effort_pct", city.estimated_50m2_rent_effort_pct),
      context: "Loyer majore / revenu median",
    },
  ];

  container.innerHTML = cards
    .map(
      (card) => `
        <article class="summary-card">
          <span>${card.label}</span>
          <strong>${card.value}</strong>
          <span>${card.context}</span>
        </article>
      `,
    )
    .join("");
}

function renderRanking(arrondissements) {
  const container = document.getElementById("ranking-grid");
  container.innerHTML = arrondissements
    .map(
      (item) => `
        <article class="ranking-card">
          <span class="rank">#${item.rank_by_price}</span>
          <strong>${item.arrondissement}. ${item.name}</strong>
          <div class="ranking-meta">
            <span>Prix median: ${formatMetricValue("median_price_m2", item.median_price_m2)}</span>
            <span>Revenu median: ${formatMetricValue("median_income_eur", item.median_income_eur)}</span>
            <span>Logements sociaux: ${formatMetricValue("social_units_financed", item.social_units_financed)}</span>
            <span>Qualite de vie: ${formatMetricValue("quality_of_life_score", item.quality_of_life_score)}</span>
          </div>
        </article>
      `,
    )
    .join("");
}

function renderSources() {
  const container = document.getElementById("source-list");
  container.innerHTML = state.sources
    .map(
      (source) => `
        <a
          class="source-link-card"
          href="${source.url}"
          target="_blank"
          rel="noreferrer"
          title="${source.summary}"
        >
          <span class="source-link-group">${source.group}</span>
          <strong>${source.label}</strong>
          <span class="source-link-summary">${source.summary}</span>
        </a>
      `,
    )
    .join("");
}

function isPointLevel(level = state.mapLevel) {
  return POINT_MAP_LEVELS.has(level);
}

function showQuartierBackdrop(level = state.mapLevel) {
  return level === "street" || level === "building";
}

function mapBaseLineWidth() {
  if (state.mapLevel === "street") {
    return 2.2;
  }
  return state.mapLevel === "quartier" ? 0.8 : 1.2;
}

function mapHighlightWidth() {
  if (state.mapLevel === "street") {
    return 3.8;
  }
  return state.mapLevel === "quartier" ? 2.2 : 3.5;
}

function mapPointBaseStrokeWidth() {
  return state.mapLevel === "building" ? 0.6 : 1;
}

function mapPointHighlightStrokeWidth() {
  return state.mapLevel === "building" ? 1.6 : 2.4;
}

function mapPointRadiusExpression() {
  const low = state.mapLevel === "building" ? 3 : 5;
  const mid = state.mapLevel === "building" ? 5 : 8;
  const high = state.mapLevel === "building" ? 7 : 11;
  return [
    "interpolate",
    ["linear"],
    ["to-number", ["coalesce", ["get", "transactions"], 0]],
    1,
    low,
    10,
    mid,
    40,
    high,
  ];
}

function mapAreaLabel(properties) {
  if (properties.map_level === "building") {
    return properties.building_label || properties.name || properties.building_id;
  }
  if (properties.map_level === "street") {
    return properties.street_name || properties.name || properties.street_key;
  }
  if (properties.map_level === "quartier") {
    return properties.name;
  }
  return `${properties.arrondissement}. ${properties.name}`;
}

function mapPopupHtml(properties) {
  const label = safeMetricLabel(state.metric);
  const value = formatMetricValue(state.metric, properties.metric_value);
  const lines = [`${label}: ${value}`, `Prix median: ${formatMetricValue("median_price_m2", properties.median_price_m2)}`];

  if (properties.map_level === "street") {
    lines.unshift(`Arrondissement: ${formatCount(properties.arrondissement)}`);
    lines.push(`Transactions: ${formatMetricValue("transactions", properties.transactions)}`);
    lines.push(`Batiments: ${formatCount(properties.buildings)}`);
  } else if (properties.map_level === "building") {
    lines.unshift(`Arrondissement: ${formatCount(properties.arrondissement)}`);
    if (properties.street_name) {
      lines.push(`Rue: ${properties.street_name}`);
    }
    lines.push(`Transactions: ${formatMetricValue("transactions", properties.transactions)}`);
    lines.push(`Parcelles: ${formatCount(properties.parcel_count)}`);
    lines.push(`Source batiment: ${buildingSourceLabel(properties.building_id_source)}`);
  } else if (properties.map_level === "quartier") {
    lines.unshift(`Arrondissement: ${number.format(Number(properties.arrondissement))}`);
    lines.push(`Transactions: ${formatMetricValue("transactions", properties.transactions)}`);
  } else {
    lines.push(`Revenu median: ${formatMetricValue("median_income_eur", properties.median_income_eur)}`);
  }

  return `<strong>${mapAreaLabel(properties)}</strong><br />${lines.join("<br />")}`;
}

function createMap() {
  if (state.map) {
    return;
  }
  state.map = new maplibregl.Map({
    container: "map",
    style: {
      version: 8,
      sources: {},
      layers: [
        {
          id: "background",
          type: "background",
          paint: {
            "background-color": "#f7f3ea",
          },
        },
      ],
    },
    center: [2.3488, 48.861],
    zoom: 10.5,
    attributionControl: true,
  });

  state.map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

  state.popup = new maplibregl.Popup({
    closeButton: false,
    closeOnClick: false,
  });

  const registerMapInteractions = (layerId) => {
    state.map.on("mouseenter", layerId, () => {
      state.map.getCanvas().style.cursor = "pointer";
    });

    state.map.on("mousemove", layerId, (event) => {
      const feature = event.features?.[0];
      if (!feature) {
        return;
      }
      state.popup.setLngLat(event.lngLat).setHTML(mapPopupHtml(feature.properties)).addTo(state.map);
    });

    state.map.on("mouseleave", layerId, () => {
      state.map.getCanvas().style.cursor = "";
      state.popup.remove();
    });

    state.map.on("click", layerId, async (event) => {
      const feature = event.features?.[0];
      if (!feature) {
        return;
      }
      const nextArrondissement = Number(feature.properties.arrondissement);
      if (!Number.isFinite(nextArrondissement)) {
        return;
      }
      state.left = nextArrondissement;
      document.getElementById("left-select").value = String(state.left);
      await Promise.all([refreshComparison(), refreshTimeline()]);
      updateMapSelection();
    });
  };

  state.map.on("load", () => {
    state.map.addSource("osm-base", {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      maxzoom: 19,
      attribution: "&copy; OpenStreetMap contributors",
    });

    state.map.addLayer({
      id: "osm-base",
      type: "raster",
      source: "osm-base",
      paint: {
        "raster-opacity": 1,
      },
    });

    state.map.addSource("background-quartiers", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });

    state.map.addLayer({
      id: "background-quartier-fill",
      type: "fill",
      source: "background-quartiers",
      paint: {
        "fill-color": "#f3ecdd",
        "fill-opacity": 0.14,
      },
      layout: {
        visibility: "none",
      },
    });

    state.map.addLayer({
      id: "background-quartier-line",
      type: "line",
      source: "background-quartiers",
      paint: {
        "line-color": "#8f8778",
        "line-width": 1,
        "line-opacity": 0.75,
      },
      layout: {
        visibility: "none",
      },
    });

    state.map.addSource("map-features", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });

    state.map.addLayer({
      id: "map-fill",
      type: "fill",
      source: "map-features",
      filter: ["==", ["geometry-type"], "Polygon"],
      paint: {
        "fill-color": "#d9d4c8",
        "fill-opacity": 0.66,
      },
    });

    state.map.addLayer({
      id: "map-line",
      type: "line",
      source: "map-features",
      filter: ["!=", ["geometry-type"], "Point"],
      paint: {
        "line-color": "#31483c",
        "line-width": mapBaseLineWidth(),
      },
    });

    state.map.addLayer({
      id: "map-highlight",
      type: "line",
      source: "map-features",
      filter: ["!=", ["geometry-type"], "Point"],
      paint: {
        "line-color": [
          "match",
          ["get", "arrondissement"],
          ["literal", [state.left, state.right]],
          "#d16d37",
          "rgba(0, 0, 0, 0)",
        ],
        "line-width": [
          "match",
          ["get", "arrondissement"],
          ["literal", [state.left, state.right]],
          mapHighlightWidth(),
          0,
        ],
      },
    });

    state.map.addLayer({
      id: "map-points",
      type: "circle",
      source: "map-features",
      filter: ["==", ["geometry-type"], "Point"],
      paint: {
        "circle-color": "#d9d4c8",
        "circle-radius": mapPointRadiusExpression(),
        "circle-opacity": 0.88,
        "circle-stroke-color": "#31483c",
        "circle-stroke-width": mapPointBaseStrokeWidth(),
      },
    });

    registerMapInteractions("map-fill");
    registerMapInteractions("map-line");
    registerMapInteractions("map-points");
  });
}

function buildColorStops(values) {
  const sorted = [...values].sort((left, right) => left - right);
  if (!sorted.length) {
    return [0, 0, 0];
  }
  const first = sorted[0];
  const mid = sorted[Math.floor(sorted.length / 2)];
  const last = sorted[sorted.length - 1];
  if (first === last) {
    return [first, first + 1, first + 2];
  }
  return [first, mid, last];
}

function renderLegend(stops) {
  const container = document.getElementById("map-legend");
  const colors = ["#f9e5b8", "#eba461", "#9f2716"];
  const labels = stops.map((stop) => formatMetricValue(state.metric, stop));
  container.innerHTML = colors
    .map(
      (color, index) => `
        <span class="legend-chip">
          <span class="legend-swatch" style="background:${color}"></span>
          ${labels[index]}
        </span>
      `,
    )
    .join("");
}

async function syncMapBackdrops(level) {
  const quartierVisibility = showQuartierBackdrop(level) ? "visible" : "none";
  if (showQuartierBackdrop(level)) {
    const quartierData = await loadReferenceLayer("quartier");
    state.map.getSource("background-quartiers").setData(quartierData);
  }
  state.map.setLayoutProperty("background-quartier-fill", "visibility", quartierVisibility);
  state.map.setLayoutProperty("background-quartier-line", "visibility", quartierVisibility);
}

async function refreshMap() {
  const metricMeta = state.meta.metrics[state.metric];
  const year = metricMeta.supports_year ? state.salesYear : "";
  const data = await fetchJson(
    `/api/map?metric=${encodeURIComponent(state.metric)}&level=${encodeURIComponent(state.mapLevel)}${year ? `&year=${year}` : ""}`,
  );

  createMap();
  if (!state.map.isStyleLoaded()) {
    await new Promise((resolve) => state.map.once("load", resolve));
  }
  state.popup.remove();
  await syncMapBackdrops(data.metric.level);

  document.getElementById("map-title").textContent = data.metric.label;
  document.getElementById("metric-context").textContent = data.metric.year
    ? `${data.metric.year} · ${data.metric.unit}`
    : data.metric.unit;

  const source = state.map.getSource("map-features");
  source.setData({
    type: "FeatureCollection",
    features: data.features,
  });
  document.getElementById("metric-context").textContent = data.metric.year
    ? `${data.metric.level_label} · ${data.metric.year} · ${data.metric.unit}`
    : `${data.metric.level_label} · ${data.metric.unit}`;
  state.map.setPaintProperty("map-line", "line-width", mapBaseLineWidth());
  state.map.setPaintProperty("map-points", "circle-radius", mapPointRadiusExpression());

  const values = data.features
    .map((feature) => Number(feature.properties.metric_value))
    .filter((value) => Number.isFinite(value));
  const stops = buildColorStops(values);
  renderLegend(stops);

  const colorExpression = [
    "case",
    ["==", ["coalesce", ["get", "metric_value"], -99999], -99999],
    "#d9d4c8",
    [
      "interpolate",
      ["linear"],
      ["to-number", ["get", "metric_value"]],
      stops[0],
      "#f9e5b8",
      stops[1],
      "#eba461",
      stops[2],
      "#9f2716",
    ],
  ];
  state.map.setPaintProperty("map-fill", "fill-color", colorExpression);
  state.map.setPaintProperty("map-points", "circle-color", colorExpression);
  state.map.setPaintProperty(
    "map-line",
    "line-color",
    data.metric.level === "street" ? colorExpression : "#31483c",
  );

  const polygonVisibility = isPointLevel(data.metric.level) ? "none" : "visible";
  const pointVisibility = isPointLevel(data.metric.level) ? "visible" : "none";
  state.map.setLayoutProperty("map-fill", "visibility", polygonVisibility);
  state.map.setLayoutProperty("map-line", "visibility", polygonVisibility);
  state.map.setLayoutProperty("map-highlight", "visibility", polygonVisibility);
  state.map.setLayoutProperty("map-points", "visibility", pointVisibility);

  updateMapSelection();
}

function updateMapSelection() {
  if (!state.map) {
    return;
  }

  if (state.map.getLayer("map-highlight")) {
    state.map.setPaintProperty("map-highlight", "line-width", [
      "match",
      ["get", "arrondissement"],
      ["literal", [state.left, state.right]],
      mapHighlightWidth(),
      0,
    ]);
    state.map.setPaintProperty("map-highlight", "line-color", [
      "match",
      ["get", "arrondissement"],
      ["literal", [state.left, state.right]],
      "#d16d37",
      "rgba(0, 0, 0, 0)",
    ]);
  }

  if (state.map.getLayer("map-points")) {
    state.map.setPaintProperty("map-points", "circle-stroke-width", [
      "match",
      ["get", "arrondissement"],
      ["literal", [state.left, state.right]],
      mapPointHighlightStrokeWidth(),
      mapPointBaseStrokeWidth(),
    ]);
    state.map.setPaintProperty("map-points", "circle-stroke-color", [
      "match",
      ["get", "arrondissement"],
      ["literal", [state.left, state.right]],
      "#d16d37",
      "#31483c",
    ]);
  }
}

function deltaClass(value) {
  if (value > 0) {
    return "delta-positive";
  }
  if (value < 0) {
    return "delta-negative";
  }
  return "";
}

async function refreshComparison() {
  const data = await fetchJson(`/api/compare?left=${state.left}&right=${state.right}&sales_year=${state.salesYear}`);
  const metrics = [
    "median_price_m2",
    "median_income_eur",
    "reference_rent_majorated_eur_m2",
    "social_units_financed",
    "quality_of_life_score",
    "months_income_for_1sqm",
    "estimated_50m2_rent_effort_pct",
  ];

  const renderCard = (side, title) => `
    <article class="compare-card">
      <strong>${title}: ${side.arrondissement}. ${side.name}</strong>
      ${metrics
        .map(
          (metric) => `
            <div class="compare-row">
              <small>${safeMetricLabel(metric)}</small>
              <span>${formatMetricValue(metric, side[metric])}</span>
            </div>
          `,
        )
        .join("")}
    </article>
  `;

  const deltaRows = metrics
    .map(
      (metric) => `
        <div class="compare-row">
          <small>${safeMetricLabel(metric)}</small>
          <span class="${deltaClass(data.delta[metric])}">
            ${data.delta[metric] > 0 ? "+" : ""}${formatMetricValue(metric, data.delta[metric])}
          </span>
        </div>
      `,
    )
    .join("");

  document.getElementById("compare-panel").innerHTML = `
    <div class="compare-grid">
      ${renderCard(data.left, "A")}
      ${renderCard(data.right, "B")}
    </div>
    <div class="compare-card" style="margin-top:14px;">
      <strong>Delta A - B</strong>
      ${deltaRows}
    </div>
  `;
}

function renderLineChart(containerId, series, key, color, formatter) {
  const container = document.getElementById(containerId);
  if (!series.length) {
    container.innerHTML = `<p class="empty-state">Aucune donnee disponible.</p>`;
    return;
  }

  const width = 360;
  const height = 160;
  const padding = 18;
  const values = series.map((item) => Number(item[key])).filter((value) => Number.isFinite(value));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points = series.map((item, index) => {
    const x = padding + (index / Math.max(series.length - 1, 1)) * (width - padding * 2);
    const y = height - padding - ((Number(item[key]) - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  });

  const circles = series
    .map((item, index) => {
      const [x, y] = points[index].split(",");
      return `<circle cx="${x}" cy="${y}" r="4" fill="${color}"></circle>`;
    })
    .join("");

  const labels = series
    .map((item) => `<span>${item.year}: ${formatter(item[key])}</span>`)
    .join(" · ");

  container.innerHTML = `
    <svg class="chart-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
      <polyline
        fill="none"
        stroke="${color}"
        stroke-width="4"
        stroke-linecap="round"
        stroke-linejoin="round"
        points="${points.join(" ")}"
      ></polyline>
      ${circles}
    </svg>
    <div class="chart-caption">${labels}</div>
  `;
}

async function refreshTimeline() {
  const data = await fetchJson(`/api/timeline?arrondissement=${state.left}`);
  document.getElementById("timeline-title").textContent = `Evolution du ${data.arrondissement}. ${data.name}`;

  renderLineChart("sales-chart", data.sales, "median_price_m2", "#8f3215", (value) =>
    formatMetricValue("median_price_m2", value),
  );
  renderLineChart("social-chart", data.social, "social_units_financed", "#2f6751", (value) =>
    formatMetricValue("social_units_financed", value),
  );
  renderLineChart("rent-chart", data.rents, "reference_rent_majorated_eur_m2", "#335b82", (value) =>
    formatMetricValue("reference_rent_majorated_eur_m2", value),
  );
}

async function refreshOverview() {
  const data = await fetchJson(`/api/overview?sales_year=${state.salesYear}`);
  renderCitySummary(data.city);
  renderRanking(data.arrondissements);
  populateArrondissementSelects(data.arrondissements);
}

async function refreshAll() {
  await refreshOverview();
  await Promise.all([refreshMap(), refreshComparison(), refreshTimeline()]);
}

async function init() {
  try {
    const [meta, sources] = await Promise.all([fetchJson("/api/meta"), fetchJson("/sources")]);
    state.meta = meta;
    state.sources = sources.sources;
    state.salesYear = meta.latest_sales_year;
    populateMapLevelSelect();
    populateMetricSelect();
    populateYearSelect();
    renderSources();
    await refreshAll();
  } catch (error) {
    document.body.innerHTML = `<pre style="padding:24px;">${error.message}</pre>`;
  }
}

window.addEventListener("DOMContentLoaded", init);
