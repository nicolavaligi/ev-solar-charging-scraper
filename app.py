"""
Dashboard Web Interattiva Streamlit per EV Solar Site Finder.
Visualizza la mappa, le statistiche energetiche e permette di filtrare i siti in tempo reale.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
CSV_FILE = OUTPUT_DIR / "aree_ricarica_ev_solare.csv"

st.set_page_config(
    page_title="EV Solar Site Finder - Italia",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚡ EV Solar Site Finder - Italia")
st.markdown("Piattaforma di qualificazione per **aree di ricarica veicoli elettrici con pensiline fotovoltaiche**.")

# Caricamento Dati
if not CSV_FILE.exists():
    st.warning("Nessun dato di scansione trovato. Esegui prima una scansione dalla CLI o clicca sul pulsante per generare i dati.")
    st.stop()

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_FILE)
    return df

df = load_data()

# Sidebar Filtri
st.sidebar.header("🔍 Filtri di Ricerca")

# Filtro Regione
regioni = ["Tutte"] + sorted(df["Regione"].dropna().unique().tolist())
selected_regione = st.sidebar.selectbox("Regione", regioni)

# Filtro Contratto
contratti = ["Tutti"] + sorted(df["Contratto"].dropna().unique().tolist())
selected_contratto = st.sidebar.selectbox("Tipo Contratto", contratti)

# Filtro Livello / Score
livelli = st.sidebar.multiselect(
    "Fascia di Idoneità",
    options=["TOP", "BUONO", "MEDIO", "BASSO"],
    default=["TOP", "BUONO"]
)

# Filtro Superficie Minima
min_mq_val = int(df["Superficie_mq"].min() if not df["Superficie_mq"].isna().all() else 100)
max_mq_val = int(df["Superficie_mq"].max() if not df["Superficie_mq"].isna().all() else 10000)
selected_mq = st.sidebar.slider("Superficie Minima (mq)", min_mq_val, min(max_mq_val, 15000), min_mq_val, step=50)

# Applicazione filtri
filtered_df = df.copy()

if selected_regione != "Tutte":
    filtered_df = filtered_df[filtered_df["Regione"] == selected_regione]

if selected_contratto != "Tutti":
    filtered_df = filtered_df[filtered_df["Contratto"] == selected_contratto]

if livelli:
    filtered_df = filtered_df[filtered_df["Livello"].isin(livelli)]

filtered_df = filtered_df[filtered_df["Superficie_mq"] >= selected_mq]

# KPI Metrics
col1, col2, col3, col4 = st.columns(4)

tot_siti = len(filtered_df)
tot_top = len(filtered_df[filtered_df["Livello"] == "TOP"])
tot_kwp = filtered_df["Potenza_Pensilina_kWp"].sum()
tot_gwh = (filtered_df["Produzione_Solare_Annua_kWh"].sum()) / 1_000_000

with col1:
    st.metric("Siti Qualificati", f"{tot_siti}")
with col2:
    st.metric("Opportunità TOP (Score ≥ 75)", f"{tot_top}")
with col3:
    st.metric("Potenziale Pensiline FV", f"{tot_kwp:,.0f} kWp")
with col4:
    st.metric("Produzione Solare Annua", f"{tot_gwh:.2f} GWh/anno")

st.markdown("---")

# Mappa Interattiva
st.subheader("🗺️ Mappa Geografica dei Siti Selezionati")

valid_geo = filtered_df.dropna(subset=["Latitudine", "Longitudine"])

if not valid_geo.empty:
    center_lat = valid_geo["Latitudine"].mean()
    center_lon = valid_geo["Longitudine"].mean()
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6 if len(valid_geo) > 10 else 9,
        tiles="OpenStreetMap"
    )
    
    cluster = MarkerCluster(name="Siti Ricarica").add_to(m)

    color_dict = {
        "TOP": "green",
        "BUONO": "orange",
        "MEDIO": "blue",
        "BASSO": "red"
    }

    for _, row in valid_geo.iterrows():
        color = color_dict.get(row["Livello"], "blue")
        
        popup_html = f"""
        <div style='font-family:sans-serif; width:260px;'>
            <b>{row['Titolo']}</b><br>
            📍 {row['Comune']} ({row['Provincia']})<br>
            📐 <b>{row['Superficie_mq']:,.0f} mq</b> | 💰 {row['Prezzo_Euro']:,.0f} €<br>
            ⚡ <b>Pensilina FV:</b> ~{row['Potenza_Pensilina_kWp']:.0f} kWp<br>
            ☀️ <b>Resa Annua:</b> {row['Produzione_Solare_Annua_kWh']:,.0f} kWh<br>
            <div style='margin-top:6px;'>
                <a href='{row['URL_Annuncio']}' target='_blank' style='color:#0066cc; font-weight:bold;'>Apri Annuncio ↗</a>
            </div>
        </div>
        """
        
        folium.Marker(
            location=[row["Latitudine"], row["Longitudine"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"[{row['Livello']}] {row['Score']}/100 - {row['Comune']} ({row['Superficie_mq']:,.0f} mq)",
            icon=folium.Icon(color=color, icon="bolt")
        ).add_to(cluster)

    st_folium(m, width="100%", height=550)
else:
    st.info("Nessun sito corrisponde ai filtri selezionati.")

st.markdown("---")

# Tabella Dati Dettagliata
st.subheader("📋 Elenco Dettagliato delle Opportunità")

cols_to_show = [
    "Score", "Livello", "Titolo", "Comune", "Provincia", "Regione",
    "Superficie_mq", "Prezzo_Euro", "Contratto", "Potenza_Pensilina_kWp",
    "Produzione_Solare_Annua_kWh", "URL_Annuncio"
]

available_cols = [c for c in cols_to_show if c in filtered_df.columns]
st.dataframe(
    filtered_df[available_cols],
    use_container_width=True,
    column_config={
        "URL_Annuncio": st.column_config.LinkColumn("Link Annuncio"),
        "Score": st.column_config.ProgressColumn("Punteggio", format="%.1f", min_value=0, max_value=100),
        "Superficie_mq": st.column_config.NumberColumn("Superficie (mq)", format="%d mq"),
        "Prezzo_Euro": st.column_config.NumberColumn("Prezzo (€)", format="%d €"),
        "Potenza_Pensilina_kWp": st.column_config.NumberColumn("Pensilina (kWp)", format="%.1f kWp"),
        "Produzione_Solare_Annua_kWh": st.column_config.NumberColumn("Produzione (kWh/a)", format="%d kWh"),
    },
    hide_index=True
)
