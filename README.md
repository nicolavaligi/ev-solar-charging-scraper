# ⚡ EV Solar Site Finder (Italia)

> Scraper intelligente e motore di qualificazione per individuare piazzali e terreni ad elevata idoneità per l'installazione di **colonnine di ricarica per veicoli elettrici (EV Charging Hubs)** con **pensiline fotovoltaiche (Solar Carports)** su tutto il territorio nazionale.

---

## 🎯 Obiettivo del Progetto

Trovare aree per la ricarica rapida/ultrarapida e pensiline fotovoltaiche non richiede solo di raccogliere annunci generici, ma di **qualificarli scientificamente** e **filtrarli da falsi positivi**.

EV Solar Site Finder:
1. **Scansiona** le categorie commerciali e terreni su scala nazionale o regionale.
2. **Estrae la reale metratura del piazzale** tramite parsing dei metadati e regex avanzato sul testo dell'annuncio.
3. **Geocodifica istantaneamente** ogni comune tramite il database offline ISTAT integrato (7.904 comuni).
4. **Arricchisce i siti con dati solari scientifici** tramite le API ufficiali **PVGIS (Commissione Europea JRC)** e i modelli regionali ENEA/GSE (irraggiamento annuo in $kWh/m^2$, resa specifica $kWh/kWp/anno$, dimensionamento potenza e produzione stimata della pensilina).
5. **Calcola un Indice di Idoneità (Score 0-100)** basato su 5 pilastri: Superficie, Accessibilità/Viabilità, Resa Solare, Caratteristiche Tecniche e Fattibilità Economica.
6. **Esporta i risultati** su una mappa interattiva HTML (Leaflet/Folium) navigabile con marker cluster e in tabelle Excel (.xlsx) e CSV pronte per il business development.

---

## 🏗️ Architettura dei Moduli

```text
ev-solar-charging-scraper/
├── config.py                 # Pesi di scoring, filtri superficie, parametri pensiline FV
├── pipeline.py               # Orchestratore end-to-end (scrape -> geocode -> pvgis -> score -> export)
├── cli.py                    # Interfaccia a riga di comando per avviare scansioni
├── app.py                    # Dashboard Web Interattiva Streamlit (Mappa + KPI + Filtri)
├── MANUALE.md                # Manuale Utente e Guida Operativa completa
├── GUIDELINES.md             # Linee Guida Architetturali e Standard di Sviluppo
├── scrapers/
│   ├── base_scraper.py       # Interfaccia astratta e dataclass 'ListingSite'
│   └── subito_scraper.py     # Parser JSON Next.js ad alte prestazioni con paginazione
├── enrichment/
│   ├── geocoder.py           # Geocoding offline ISTAT (7.904 comuni italiani)
│   └── pvgis_client.py       # Client PVGIS (JRC) con caching e modelli climatici regionali
├── scoring/
│   └── site_evaluator.py     # Algoritmo di scoring multicriterio (0-100)
├── export/
│   ├── map_generator.py      # Generatore mappa interattiva HTML (Folium) con popup completi
│   └── table_exporter.py     # Esportatore DataFrame, CSV ed Excel con openpyxl
└── data/
    ├── reference/            # Database coordinate comuni italiani ISTAT
    └── cache_pvgis.json      # Cache irraggiamento solare
```

📚 **Documentazione di approfondimento:**
* 👉 [**Manuale Operativo e d'Uso (MANUALE.md)**](MANUALE.md)
* 👉 [**Linee Guida di Progetto (GUIDELINES.md)**](GUIDELINES.md)

---

## 🚀 Guida all'Uso (CLI)

Il tool può essere eseguito con Python 3 standard (utilizzando il virtual environment esistente in `projects/scraping-opere/.venv` o qualsiasi Python 3.10+):

### 1. Scansione Nazionale Veloce (Default)
Cerca piazzali con superficie minima ≥ 500 mq su tutta Italia in vendita e in affitto:
```bash
python cli.py -q "piazzale" --min-mq 500 -p 1
```

### 2. Scansione Mirata per Regione
Cerca terreni commerciali o piazzali in una regione specifica (es. Lombardia, Lazio, Veneto, Emilia-Romagna):
```bash
python cli.py -r lombardia -q "piazzale" --min-mq 800 -p 2
```

### 3. Filtro su Terreni Commerciali in Vendita
```bash
python cli.py -q "terreno commerciale" -c vendita --cat terreni --min-mq 1000 -p 3
```

### 4. Filtro su Piazzali in Affitto per Hub Temporanei o Concessioni
```bash
python cli.py -q "piazzale" -c affitto --cat commerciale -p 2
```

### Parametri CLI Disponibili:
| Argomento | Descrizione | Default |
| :--- | :--- | :--- |
| `-q`, `--query` | Parola chiave (`piazzale`, `terreno commerciale`, `parcheggio`, ecc.) | Lista predefinita |
| `-r`, `--region` | Filtro regionale (es. `lombardia`, `lazio`, `toscana`, `veneto`) | `None` (Tutta Italia) |
| `-c`, `--contract` | Tipo contratto: `vendita`, `affitto`, `all` | `all` |
| `--cat`, `--category` | Categoria: `commerciale`, `terreni`, `all` | `all` |
| `--min-mq` | Superficie minima accettabile in metri quadri | `120` mq |
| `-p`, `--pages` | Numero di pagine da scansionare per combinazione | `2` |
| `-o`, `--output` | Nome base dei file esportati in `output/` | `aree_ricarica_ev_solare` |

---

## 📊 Matrice di Scoring (0 - 100 Punti)

Ogni annuncio viene valutato e classificato nelle seguenti fasce:
* 🌟 **TOP (Score ≥ 75)**: Siti ad alta idoneità immediata (ottimo spazio, visibilità viaria, resa solare elevata, costo congruo).
* 👍 **BUONO (Score 60 - 74)**: Opportunità interessanti con caratteristiche solide da approfondire.
* ℹ️ **MEDIO (Score 45 - 59)**: Idoneità sufficiente, possibili limiti di prezzo o viabilità.
* ❌ **BASSO (Score < 45)**: Poco idoneo per vincoli dimensionali o morfologici.

### Ripartizione dei Punteggi:
1. **Superficie Utile (25 pt)**:
   - `< 120 mq`: 0 pt (spazio insufficiente per stalli e pensilina)
   - `120 - 250 mq`: 16 pt (micro-hub 2-4 stalli fast con pensilina compatta 15-30 kWp)
   - `250 - 600 mq`: 22 pt (hub cittadino/commerciale 4-6 stalli con pensilina 30-70 kWp)
   - `600 - 2.500 mq`: 25 pt (taglia ottimale standard per hub 6-12 stalli e pensiline 70-150 kWp)
   - `2.500 - 8.000 mq`: 22 pt (grande hub di ricarica ad alta intensità)
   - `> 8.000 mq`: 18 pt (superficie estesa, richiede frazionamento)
2. **Accessibilità e Logistica (25 pt)**:
   - Riconoscimento NLP di assi viari primari: `fronte strada`, `tangenziale`, `casello autostradale`, `strada statale`, `alto passaggio`, `accesso bilici`, `rotatoria`.
3. **Resa Solare PVGIS (20 pt)**:
   - Basato sul rendimento specifico annuale calcolato scientificamente per coordinate:
     - `≥ 1450 kWh/kWp`: 20 pt (Sud e Isole, massima producibilità)
     - `1350 - 1449 kWh/kWp`: 17 pt (Centro Italia)
     - `1250 - 1349 kWh/kWp`: 14 pt (Emilia/Liguria)
     - `1150 - 1249 kWh/kWp`: 11 pt (Pianura Padana / Nord)
4. **Caratteristiche del Sito & Infrastruttura (15 pt)**:
   - Presenza di pavimentazione (`asfaltato`), recinzione, illuminazione, destinazione (`zona commerciale/industriale/artigianale`) e vicinanza/presenza citata di `cabina`, `media tensione`, `trasformatore`.
5. **Fattibilità Economica Prezzo/Valore (15 pt)**:
   - Analisi del prezzo al mq (per acquisto) o canone mensile al mq (per locazione).

---

## 📁 Output Generati

I file vengono salvati automaticamente nella directory `output/`:
* 🗺️ **`aree_ricarica_ev_solare.html`**: Mappa geografica interattiva Folium con cluster, pin colorati per fascia di score, badge di qualifica, dettagli tecnici FV e link diretto all'annuncio originale.
* 📑 **`aree_ricarica_ev_solare.xlsx`**: File Excel con formattazione e ordinamento per punteggio decrescente, completo di tutte le metriche tecniche e note di qualifica.
* 📈 **`aree_ricarica_ev_solare.csv`**: File CSV per integrazione con database o CRM.
