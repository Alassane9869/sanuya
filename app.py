"""
Dashboard de priorisation des interventions de nettoyage
=========================================================
Prototype fonctionnel avec données factices (à remplacer par les sorties
réelles du modèle YOLOv8 + module d'estimation de volume + géolocalisation).

Lancement :
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------
# Configuration générale
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Priorisation Nettoyage Urbain",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded",
)

CENTRE_VILLE = {"lat": 12.6392, "lon": -8.0029, "nom": "Bamako"}  # à adapter à la ville cible

QUARTIERS = [
    "Centre-ville", "Hamdallaye", "Badalabougou", "Sotuba",
    "Lafiabougou", "Magnambougou", "Sabalibougou", "Niamakoro",
]

TYPES_DECHETS = ["Sac poubelle", "Encombrants", "Gravats", "Déchets verts", "Déchets diffus"]
VOLUMES = ["Faible", "Moyen", "Important", "Critique"]
VOLUME_POIDS = {"Faible": 1, "Moyen": 3, "Important": 6, "Critique": 10}
VOLUME_COULEUR = {"Faible": "#2ecc71", "Moyen": "#f1c40f", "Important": "#e67e22", "Critique": "#e74c3c"}

STATUTS = ["En attente", "Planifiée", "Traitée"]


# ----------------------------------------------------------------------------
# Génération de données factices (simule les sorties du pipeline CV)
# ----------------------------------------------------------------------------
@st.cache_data
def generer_donnees_factices(n=180, seed=42):
    rng = np.random.default_rng(seed)

    rows = []
    for i in range(n):
        quartier = rng.choice(QUARTIERS)
        # dispersion géographique autour du centre, par quartier (offset fixe + bruit)
        offset_lat = (QUARTIERS.index(quartier) - len(QUARTIERS) / 2) * 0.01
        offset_lon = (QUARTIERS.index(quartier) % 4 - 1.5) * 0.015
        lat = CENTRE_VILLE["lat"] + offset_lat + rng.normal(0, 0.004)
        lon = CENTRE_VILLE["lon"] + offset_lon + rng.normal(0, 0.004)

        type_dechet = rng.choice(TYPES_DECHETS, p=[0.35, 0.2, 0.15, 0.15, 0.15])
        volume = rng.choice(VOLUMES, p=[0.35, 0.3, 0.22, 0.13])
        confiance = round(float(rng.uniform(0.62, 0.98)), 2)
        jours_ago = int(rng.integers(0, 21))
        date_detection = datetime.now() - timedelta(days=jours_ago, hours=int(rng.integers(0, 23)))
        recurrence = int(rng.poisson(2)) + 1  # nb de détections au même point sur 21 jours
        statut = rng.choice(STATUTS, p=[0.55, 0.25, 0.2])
        camera_id = f"CAM-{rng.integers(1, 40):03d}"

        rows.append({
            "id": f"DET-{i+1:04d}",
            "camera_id": camera_id,
            "quartier": quartier,
            "lat": lat,
            "lon": lon,
            "type_dechet": type_dechet,
            "volume": volume,
            "confiance": confiance,
            "date_detection": date_detection,
            "recurrence_21j": recurrence,
            "statut": statut,
        })

    df = pd.DataFrame(rows)
    return df


def calculer_score_priorite(df):
    """Score de priorité = f(volume, récurrence, ancienneté, confiance du modèle)."""
    df = df.copy()
    poids_volume = df["volume"].map(VOLUME_POIDS)
    anciennete_jours = (datetime.now() - df["date_detection"]).dt.total_seconds() / 86400
    score = (
        poids_volume * 3
        + df["recurrence_21j"] * 2
        + anciennete_jours.clip(upper=21) * 0.8
    ) * df["confiance"]
    df["score_priorite"] = score.round(1)
    return df


# ----------------------------------------------------------------------------
# Chargement des données
# ----------------------------------------------------------------------------
df_full = calculer_score_priorite(generer_donnees_factices())

# ----------------------------------------------------------------------------
# Barre latérale — filtres
# ----------------------------------------------------------------------------
st.sidebar.title("🧹 Filtres")
st.sidebar.caption("Données simulées — à connecter au pipeline de détection réel.")

quartiers_sel = st.sidebar.multiselect("Quartiers", QUARTIERS, default=QUARTIERS)
types_sel = st.sidebar.multiselect("Types de déchets", TYPES_DECHETS, default=TYPES_DECHETS)
volumes_sel = st.sidebar.multiselect("Volume estimé", VOLUMES, default=VOLUMES)
statuts_sel = st.sidebar.multiselect("Statut d'intervention", STATUTS, default=STATUTS)

periode = st.sidebar.slider("Ancienneté max des détections (jours)", 1, 21, 21)
confiance_min = st.sidebar.slider("Confiance minimale du modèle", 0.5, 1.0, 0.6, 0.01)

df = df_full[
    df_full["quartier"].isin(quartiers_sel)
    & df_full["type_dechet"].isin(types_sel)
    & df_full["volume"].isin(volumes_sel)
    & df_full["statut"].isin(statuts_sel)
    & ((datetime.now() - df_full["date_detection"]).dt.days <= periode)
    & (df_full["confiance"] >= confiance_min)
].copy()

st.sidebar.divider()
st.sidebar.metric("Détections affichées", len(df))

# ----------------------------------------------------------------------------
# En-tête et KPIs
# ----------------------------------------------------------------------------
st.title("🧹 Priorisation des interventions de nettoyage")
st.caption(f"Ville : {CENTRE_VILLE['nom']} · Données simulées en attendant l'intégration du modèle YOLOv8")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Dépôts détectés", len(df))
col2.metric("Zones critiques (volume Important/Critique)",
            int(df["volume"].isin(["Important", "Critique"]).sum()))
col3.metric("En attente d'intervention", int((df["statut"] == "En attente").sum()))
col4.metric("Confiance moyenne du modèle", f"{df['confiance'].mean()*100:.0f} %" if len(df) else "—")

st.divider()

# ----------------------------------------------------------------------------
# Carte interactive
# ----------------------------------------------------------------------------
st.subheader("🗺️ Carte des zones critiques")

mode_carte = st.radio("Affichage", ["Points par priorité", "Carte de chaleur"], horizontal=True)

if len(df):
    carte = folium.Map(location=[CENTRE_VILLE["lat"], CENTRE_VILLE["lon"]], zoom_start=13, tiles="CartoDB positron")

    if mode_carte == "Carte de chaleur":
        heat_data = df[["lat", "lon", "score_priorite"]].values.tolist()
        HeatMap(heat_data, radius=18, blur=15, max_zoom=13).add_to(carte)
    else:
        cluster = MarkerCluster().add_to(carte)
        for _, row in df.iterrows():
            couleur = VOLUME_COULEUR[row["volume"]]
            popup_html = (
                f"<b>{row['id']}</b> — {row['quartier']}<br>"
                f"Type : {row['type_dechet']}<br>"
                f"Volume : {row['volume']}<br>"
                f"Score priorité : {row['score_priorite']}<br>"
                f"Statut : {row['statut']}<br>"
                f"Caméra : {row['camera_id']}"
            )
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=5 + row["score_priorite"] / 10,
                color=couleur,
                fill=True,
                fill_color=couleur,
                fill_opacity=0.75,
                popup=folium.Popup(popup_html, max_width=250),
            ).add_to(cluster)

    st_folium(carte, width=None, height=520, returned_objects=[])
else:
    st.info("Aucune détection ne correspond aux filtres sélectionnés.")

st.divider()

# ----------------------------------------------------------------------------
# Analyses complémentaires
# ----------------------------------------------------------------------------
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("📊 Répartition par quartier")
    if len(df):
        rep_quartier = df.groupby("quartier").size().reset_index(name="détections").sort_values("détections", ascending=True)
        fig = px.bar(rep_quartier, x="détections", y="quartier", orientation="h",
                     color="détections", color_continuous_scale="Oranges")
        fig.update_layout(showlegend=False, coloraxis_showscale=False, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader("📦 Répartition par type et volume")
    if len(df):
        rep_type = df.groupby(["type_dechet", "volume"]).size().reset_index(name="détections")
        fig2 = px.bar(rep_type, x="type_dechet", y="détections", color="volume",
                      color_discrete_map=VOLUME_COULEUR,
                      category_orders={"volume": VOLUMES})
        fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0), legend_title="Volume")
        st.plotly_chart(fig2, use_container_width=True)

st.subheader("📈 Évolution des détections (21 derniers jours)")
if len(df):
    df_tendance = df.copy()
    df_tendance["jour"] = df_tendance["date_detection"].dt.date
    tendance = df_tendance.groupby("jour").size().reset_index(name="détections")
    fig3 = px.line(tendance, x="jour", y="détections", markers=True)
    fig3.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ----------------------------------------------------------------------------
# Tableau priorisé des interventions
# ----------------------------------------------------------------------------
st.subheader("🚧 Liste priorisée des interventions")

df_table = df.sort_values("score_priorite", ascending=False)[
    ["id", "quartier", "type_dechet", "volume", "score_priorite",
     "recurrence_21j", "confiance", "statut", "date_detection", "camera_id"]
].rename(columns={
    "id": "ID",
    "quartier": "Quartier",
    "type_dechet": "Type",
    "volume": "Volume",
    "score_priorite": "Score priorité",
    "recurrence_21j": "Récurrence (21j)",
    "confiance": "Confiance",
    "statut": "Statut",
    "date_detection": "Dernière détection",
    "camera_id": "Caméra",
})

st.dataframe(
    df_table,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Confiance": st.column_config.ProgressColumn("Confiance", min_value=0, max_value=1, format="%.0f %%"),
        "Score priorité": st.column_config.ProgressColumn(
            "Score priorité", min_value=0,
            max_value=float(df_full["score_priorite"].max()) if len(df_full) else 100,
        ),
        "Dernière détection": st.column_config.DatetimeColumn("Dernière détection", format="DD/MM/YYYY HH:mm"),
    },
)

st.caption(
    "Score de priorité = f(volume estimé, récurrence sur 21 jours, ancienneté, confiance du modèle). "
    "À calibrer avec les équipes terrain une fois les vraies données de détection disponibles."
)
