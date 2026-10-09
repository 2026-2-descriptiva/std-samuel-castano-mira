"""Analisis bibliometrico de Scopus (proptech / real estate technology)."""
import base64
import io
import itertools
import textwrap
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import folium  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.cluster import AgglomerativeClustering  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
DATA, OUT = BASE / "data", BASE / "submission"

TOP_KW, TOP_COUNTRY, N_CLUSTERS = 40, 25, 5

# Lat/lon aproximada (centroide) por pais; sin geojson ni internet.
COORDS = {
    "United States": (39.8, -98.6), "China": (35.9, 104.2), "United Kingdom": (54.0, -2.0),
    "India": (21.1, 78.0), "Australia": (-25.3, 133.8), "Germany": (51.2, 10.4),
    "South Korea": (36.5, 127.9), "Malaysia": (4.2, 102.0), "Spain": (40.5, -3.7),
    "Italy": (42.8, 12.6), "Russian Federation": (61.5, 105.3), "Indonesia": (-0.8, 113.9),
    "Sweden": (60.1, 18.6), "Brazil": (-14.2, -51.9), "Canada": (56.1, -106.3),
    "United Arab Emirates": (23.4, 53.8), "France": (46.2, 2.2), "Viet Nam": (14.1, 108.3),
    "Thailand": (15.9, 100.99), "Singapore": (1.35, 103.8), "Finland": (61.9, 25.7),
    "Iran": (32.4, 53.7), "Egypt": (26.8, 30.8), "Portugal": (39.4, -8.2),
    "Poland": (51.9, 19.1), "Netherlands": (52.1, 5.3), "Belarus": (53.7, 27.95),
    "Japan": (36.2, 138.3), "Colombia": (4.6, -74.3), "Jordan": (30.6, 36.2),
    "Costa Rica": (9.7, -83.8), "Norway": (60.5, 8.5), "Lithuania": (55.2, 23.9),
    "Morocco": (31.8, -7.1), "South Africa": (-30.6, 22.9), "New Zealand": (-40.9, 174.9),
    "Iraq": (33.2, 43.7), "Turkey": (38.96, 35.2), "Mexico": (23.6, -102.6),
    "Hong Kong": (22.3, 114.2), "Saudi Arabia": (23.9, 45.1), "Taiwan": (23.7, 121.0),
    "Slovakia": (48.7, 19.7), "Nigeria": (9.1, 8.7), "Hungary": (47.2, 19.5),
    "Algeria": (28.0, 1.7), "Romania": (45.9, 24.97), "Oman": (21.5, 55.9),
    "Tunisia": (33.9, 9.5), "Serbia": (44.0, 21.0), "Denmark": (56.3, 9.5),
    "Croatia": (45.1, 15.2), "Pakistan": (30.4, 69.3), "Ireland": (53.4, -8.2),
    "Cyprus": (35.1, 33.4), "Greece": (39.1, 21.8), "Belgium": (50.5, 4.5),
    "Bahrain": (26.0, 50.55), "Slovenia": (46.15, 14.99), "North Macedonia": (41.6, 21.7),
    "Austria": (47.5, 14.55), "Lebanon": (33.9, 35.9), "Israel": (31.0, 34.9),
    "Ukraine": (48.4, 31.2), "Kazakhstan": (48.0, 66.9), "Palestine": (31.95, 35.2),
    "Philippines": (12.9, 121.8), "Bulgaria": (42.7, 25.5), "Switzerland": (46.8, 8.2),
    "Czech Republic": (49.8, 15.5), "Chile": (-35.7, -71.5), "Argentina": (-38.4, -63.6),
    "Peru": (-9.2, -75.0), "Ecuador": (-1.8, -78.2), "Qatar": (25.35, 51.2),
    "Kuwait": (29.3, 47.5), "Bangladesh": (23.7, 90.4), "Sri Lanka": (7.9, 80.8),
    "Estonia": (58.6, 25.0), "Latvia": (56.9, 24.6), "Luxembourg": (49.8, 6.1),
    "Ghana": (7.95, -1.0), "Kenya": (-0.02, 37.9), "Iceland": (64.96, -19.0),
}
ALIAS = {"USA": "United States", "United States of America": "United States"}


def split_list(s, sep=";"):
    return [x.strip() for x in str(s).split(sep) if x.strip()] if pd.notna(s) else []


def countries_of(aff):
    """Pais = ultimo segmento tras la ultima coma de cada afiliacion; unico por documento."""
    found = []
    for a in split_list(aff):
        c = ALIAS.get(a.rsplit(",", 1)[-1].strip(), a.rsplit(",", 1)[-1].strip())
        if c in COORDS and c not in found:  # descarta segmentos que no son paises
            found.append(c)
    return found


def freq_df(lists, label, total):
    c = Counter(itertools.chain.from_iterable(lists))
    df = pd.DataFrame(c.most_common(), columns=[label, "Documents"])
    df["Percentage"] = (df["Documents"] / total * 100).round(2)
    return df


def cooc_matrix(lists, items):
    idx = {k: i for i, k in enumerate(items)}
    m = np.zeros((len(items), len(items)), dtype=int)
    for row in lists:
        ids = sorted({idx[k] for k in row if k in idx})
        for i in ids:
            m[i, i] += 1
        for i, j in itertools.combinations(ids, 2):
            m[i, j] += 1
            m[j, i] += 1
    return pd.DataFrame(m, index=items, columns=items)


def fig_html(fig, title):
    """Figura matplotlib -> HTML autocontenido (PNG base64)."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    img = base64.b64encode(buf.getvalue()).decode()
    return (f'<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>{title}</title></head>'
            f'<body style="font-family:sans-serif;text-align:center"><h2>{title}</h2>'
            f'<img style="max-width:100%" src="data:image/png;base64,{img}"></body></html>')


def network_fig(mat, labels_clusters, title):
    g = nx.Graph()
    for i, a in enumerate(mat.index):
        g.add_node(a, size=mat.iloc[i, i])
    for i, j in itertools.combinations(range(len(mat)), 2):
        if mat.iloc[i, j] > 0:
            g.add_edge(mat.index[i], mat.index[j], weight=int(mat.iloc[i, j]))
    fig, ax = plt.subplots(figsize=(12, 9))
    pos = nx.spring_layout(g, seed=42, k=1.2 / np.sqrt(len(g)), weight="weight")
    sizes = [60 + 25 * g.nodes[n]["size"] for n in g]
    colors = [labels_clusters[n] for n in g]
    w = [0.3 + 0.4 * g[u][v]["weight"] for u, v in g.edges]
    nx.draw_networkx_edges(g, pos, width=w, alpha=0.3, ax=ax)
    nx.draw_networkx_nodes(g, pos, node_size=sizes, node_color=colors, cmap="tab10", ax=ax)
    nx.draw_networkx_labels(g, pos, font_size=8, ax=ax)
    ax.set_title(title)
    ax.axis("off")
    return fig


def cluster_report(mat, path, what):
    """Agrupa con AgglomerativeClustering (perfiles de co-ocurrencia) y escribe reporte."""
    k = min(N_CLUSTERS, len(mat))
    x = mat.values.astype(float)
    np.fill_diagonal(x, 0)  # perfiles de co-ocurrencia normalizados (coseno)
    x = x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-9)
    labels = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(x)
    freq = pd.Series(np.diag(mat.values), index=mat.index)
    total, rows = len(mat), []
    for c in sorted(set(labels), key=lambda c: -(labels == c).sum()):
        items = freq[labels == c].sort_values(ascending=False)
        rows.append((len(items), ", ".join(items.index[:12])))
    w = 117
    lines = [f"{'Cluster':<9}{'Cantidad de ' + what:<30}{'Porcentaje':<14}Principales " + what, "-" * w]
    for n, (cnt, top) in enumerate(rows, 1):
        wrapped = textwrap.wrap(top + ".", 70)
        lines.append(f"{n:^9}{cnt:<30}{cnt / total * 100:>5.1f} %       {wrapped[0]}")
        lines += [" " * 53 + t for t in wrapped[1:]]
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return dict(zip(mat.index, labels))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA / "scopus.csv.gz")

    # --- limpieza / normalizacion
    df = df.drop_duplicates(subset="EID").copy()
    for col in ["Authors", "Author Keywords", "Source title", "Affiliations"]:
        df[col] = df[col].astype("string").str.strip()
    df["Author Keywords"] = df["Author Keywords"].str.lower()
    df["Countries"] = df["Affiliations"].map(lambda a: "; ".join(countries_of(a)))
    df.to_csv(OUT / "scopus.csv.gz", index=False, compression="gzip")
    n = len(df)

    authors = [split_list(a) for a in df["Authors"]]
    keywords = [list(dict.fromkeys(split_list(k))) for k in df["Author Keywords"]]
    countries = [split_list(c) for c in df["Countries"]]
    sources = [[s] for s in df["Source title"].dropna()]

    # --- frecuencias
    freq_df(authors, "Author", n).to_csv(OUT / "authors_frequency.csv", index=False)
    freq_df(keywords, "Keyword", n).to_csv(OUT / "keywords_frequency.csv", index=False)
    freq_df(sources, "Source", n).to_csv(OUT / "source_frequency.csv", index=False)
    cf = freq_df(countries, "Country", n)
    cf.to_csv(OUT / "country_frequency.csv", index=False)

    # --- documentos por anio
    by_year = df["Year"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(by_year.index.astype(str), by_year.values, color="#2a6f97")
    ax.set(xlabel="Anio", ylabel="Documentos", title="Documentos por anio")
    ax.tick_params(axis="x", rotation=90, labelsize=7)
    (OUT / "documents_by_year.html").write_text(fig_html(fig, "Documentos por anio"), encoding="utf-8")

    # --- paises: barras, matriz, heatmap, red, clusters
    top = cf.head(TOP_COUNTRY)
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(top["Country"][::-1], top["Documents"][::-1], color="#2a6f97")
    ax.set(xlabel="Documentos", title=f"Documentos por pais (top {TOP_COUNTRY})")
    (OUT / "country_frequency_plot.html").write_text(fig_html(fig, "Frecuencia por pais"), encoding="utf-8")

    cmat = cooc_matrix(countries, list(cf["Country"]))
    cmat.to_csv(OUT / "country_cooc_matrix.csv")
    ctop = cmat.loc[top["Country"], top["Country"]]
    fig, ax = plt.subplots(figsize=(10, 8))
    off = ctop.where(~np.eye(len(ctop), dtype=bool), 0)  # diagonal fuera de la escala
    im = ax.imshow(off.values, cmap="YlOrRd")
    ax.set_xticks(range(len(ctop)), ctop.columns, rotation=90, fontsize=7)
    ax.set_yticks(range(len(ctop)), ctop.index, fontsize=7)
    fig.colorbar(im, label="Documentos en colaboracion")
    ax.set_title("Co-ocurrencia de paises (colaboracion)")
    (OUT / "country_cooc_heatmap.html").write_text(fig_html(fig, "Heatmap de colaboracion"), encoding="utf-8")

    c_labels = cluster_report(ctop, OUT / "country_clusters.txt", "paises")
    fig = network_fig(ctop, c_labels, "Red de colaboracion entre paises")
    (OUT / "country_collab_network.html").write_text(fig_html(fig, "Red de colaboracion"), encoding="utf-8")

    # --- palabras clave
    kf = freq_df(keywords, "Keyword", n)
    kmat = cooc_matrix(keywords, list(kf["Keyword"].head(TOP_KW)))
    kmat.to_csv(OUT / "keywords_cooc_matrix.csv")
    k_labels = cluster_report(kmat, OUT / "keywords_clusters.txt", "palabras clave")
    fig = network_fig(kmat, k_labels, f"Red de co-ocurrencia de palabras clave (top {TOP_KW})")
    (OUT / "keywords_cooc_network.html").write_text(fig_html(fig, "Red de palabras clave"), encoding="utf-8")

    # --- mapa mundial (folium, centroides hardcodeados)
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="OpenStreetMap")
    for _, r in cf.iterrows():
        lat, lon = COORDS[r["Country"]]
        folium.CircleMarker(
            [lat, lon], radius=4 + 2.2 * np.sqrt(r["Documents"]), color="#c1121f",
            fill=True, fill_opacity=0.5, tooltip=f'{r["Country"]}: {r["Documents"]} documentos',
        ).add_to(m)
    m.save(str(OUT / "world_map.html"))
    print(f"OK: {len(list(OUT.glob('*')))} archivos en {OUT}")


if __name__ == "__main__":
    main()
