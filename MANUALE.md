# 📖 Manuale Utente e Guida Operativa

> **EV Solar Site Finder (Italia)** — Manuale operativo completo per l'utilizzo da riga di comando, l'esplorazione tramite Dashboard Web Streamlit e l'interpretazione dei dati tecnici e finanziari.

---

## 1. Introduzione e Requisiti

**EV Solar Site Finder** è progettato per sviluppatori di infrastrutture di ricarica per veicoli elettrici (CPO), fondi di investimento nelle rinnovabili, EPC contractor e studi di ingegneria energetica interessati a identificare e contrattualizzare piazzali, terreni commerciali e parcheggi per la realizzazione di:
* **Charging Hubs Fast & Ultra-Fast (HPC da 50 kW a 350+ kW)**.
* **Pensiline Fotovoltaiche (Solar Carports)** per l'autoconsumo in loco e la vendita in rete.

### Requisiti di Sistema:
* **Sistema Operativo**: macOS, Linux o Windows (con WSL2).
* **Python**: versione 3.10 o superiore.
* **Dipendenze principali**: `httpx`, `beautifulsoup4`, `folium`, `pandas`, `openpyxl`, `streamlit`, `streamlit_folium`.

---

## 2. Installazione Rapida

Dalla directory del progetto:

```bash
# 1. Posizionati nella directory di progetto
cd /Users/houdinick/projects/ev-solar-charging-scraper

# 2. Utilizza il virtual environment già configurato
# oppure creane uno nuovo dedicato con uv o venv:
uv venv .venv
source .venv/bin/activate
uv pip install -r <(echo "httpx beautifulsoup4 folium pandas openpyxl streamlit streamlit_folium")
```

---

## 3. Guida all'Uso da Riga di Comando (CLI)

Il file [`cli.py`](file:///Users/houdinick/projects/ev-solar-charging-scraper/cli.py) offre un'interfaccia a riga di comando rapida e parametrizzabile.

### Sintassi Base:
```bash
python cli.py [OPZIONI]
```

### Esempi Pratici di Scansione:

#### A. Scansione Nazionale Veloce (Default)
Esegue 1 pagina per ciascuna categoria e contratto, analizzando aree con superficie $\ge 120\text{ mq}$:
```bash
python cli.py -p 1 --min-mq 120
```

#### B. Scansione Mirata per Regione
Cerca esclusivamente in Lombardia per identificare hub commerciali di medie dimensioni:
```bash
python cli.py -r lombardia -q "piazzale" --min-mq 500 -p 2
```

#### C. Ricerca Solo di Terreni Commerciali in Vendita
Ideale per chi cerca l'acquisizione della proprietà:
```bash
python cli.py -q "terreno commerciale" -c vendita --cat terreni --min-mq 800 -p 3
```

#### D. Ricerca Piazzali in Locazione
Ideale per accordi di affitto a lungo termine (canone annuo o diritto di superficie):
```bash
python cli.py -q "piazzale" -c affitto --cat commerciale -p 2
```

### Tabella dei Parametri Disponibili:

| Parametro | Abbreviazione | Descrizione | Default |
| :--- | :---: | :--- | :--- |
| `--query` | `-q` | Parola chiave personalizzata (es. `"fronte strada"`, `"piazzale"`) | `"piazzale, terreno commerciale, parcheggio"` |
| `--region` | `-r` | Regione italiana (es. `lazio`, `veneto`, `toscana`, `sicilia`) | `None` (Tutta Italia) |
| `--contract` | `-c` | Contratto: `vendita`, `affitto`, oppure `all` | `all` |
| `--category` | `--cat` | Categoria: `commerciale`, `terreni`, oppure `all` | `all` |
| `--min-mq` | - | Superficie minima accettabile in mq | `120` mq |
| `--pages` | `-p` | Pagine di risultati da scorrere per ogni combinazione | `2` |
| `--output` | `-o` | Nome base dei file salvati nella cartella `output/` | `aree_ricarica_ev_solare` |

---

## 4. Guida all'Uso della Dashboard Web Interattiva

La dashboard Streamlit consente al team di analizzare visivamente i siti, applicare filtri granulari e visualizzare immediatamente le statistiche aggregate.

### Avvio della Dashboard:
```bash
streamlit run app.py --server.port 8502
```
La dashboard si aprirà all'indirizzo: **[http://localhost:8502](http://localhost:8502)**.

### Funzionalità della Dashboard:
1. **Indicatori Sintetici (KPI)** in cima alla pagina:
   * **Siti Qualificati**: numero di lotti che rispettano i filtri selezionati.
   * **Opportunità TOP**: numero di siti con score $\ge 75/100$.
   * **Potenziale Pensiline FV (kWp)**: potenza complessiva stimata installabile sulle aree filtrate.
   * **Produzione Solare Annua (GWh/anno)**: energia verde producibile in un anno solare medio.
2. **Pannello Filtri (Sidebar Sinistra)**:
   * **Filtro Regione**: seleziona una singola regione per analisi localizzate o "Tutte".
   * **Tipo Contratto**: filtra per Vendita o Affitto.
   * **Fascia di Idoneità**: seleziona solo opportunità TOP, BUONO o includi MEDIO/BASSO.
   * **Slider Superficie Minima**: regola la metratura da $120\text{ mq}$ in su con aggiornamento in tempo reale della mappa.
3. **Mappa Leaflet Integrata**:
   * Cluster intelligenti con raggruppamento geografico per provincia e comune.
   * Marker colorati per livello di idoneità (Verde per TOP, Arancione per BUONO).
   * Popup informativo completo di metratura, resa solare e pulsante diretto all'annuncio.
4. **Tabella Dati Interattiva**:
   * Ordinamento dinamico per qualsiasi colonna (Score, Superficie, Prezzo, kWp).
   * Link diretti cliccabili per aprire la scheda dell'annuncio sul portale.

---

## 5. Mappa HTML Standalone ad Alta Risoluzione

Se desideri consultare la mappa senza avviare l'ambiente Streamlit, puoi utilizzare il server locale integrato:

* **URL Diretto**: **[http://localhost:8888/aree_ricarica_ev_solare.html](http://localhost:8888/aree_ricarica_ev_solare.html)**
* **Percorso del File**: [`output/aree_ricarica_ev_solare.html`](file:///Users/houdinick/projects/ev-solar-charging-scraper/output/aree_ricarica_ev_solare.html)

Il file è completamente autosufficiente e può essere condiviso con colleghi o allegato a presentazioni.

---

## 6. Struttura del File Excel (`aree_ricarica_ev_solare.xlsx`)

Il file salvato in [`output/aree_ricarica_ev_solare.xlsx`](file:///Users/houdinick/projects/ev-solar-charging-scraper/output/aree_ricarica_ev_solare.xlsx) contiene le seguenti colonne di business:

| Colonna | Descrizione |
| :--- | :--- |
| **Score** | Indice complessivo di idoneità calcolato su base 0–100. |
| **Livello** | Fascia sintetica: `TOP` (≥75), `BUONO` (60–74), `MEDIO` (45–59), `BASSO` (<45). |
| **Titolo** | Titolo dell'annuncio sul portale immobiliare. |
| **Comune / Provincia / Regione** | Localizzazione amministrativa verificata. |
| **Superficie_mq** | Superficie utile dell'area esterna/piazzale. |
| **Prezzo_Euro** | Prezzo di vendita o canone mensile di locazione. |
| **Prezzo_al_mq** | Costo parametrato al metro quadro (€/mq o €/mq/mese). |
| **Contratto** | Vendita o Affitto. |
| **Potenza_Pensilina_kWp** | Taglia stimata dell'impianto fotovoltaico su pensilina (kWp). |
| **Produzione_Solare_Annua_kWh** | Energia elettrica solare producibile all'anno (kWh/anno da PVGIS). |
| **Resa_PVGIS_kWh_kWp** | Resa specifica del luogo geografico ($kWh/kWp/anno$). |
| **Accessibilita** | Tag viari identificati nel testo (es. *fronte strada, autostrada, ss, rotatoria*). |
| **Caratteristiche** | Caratteristiche del sito rilevate (es. *piazzale, asfaltato, recintato, cabina MT*). |
| **Note_Valutazione** | Motivazione analitica con riepilogo dei punti di forza e debolezza. |
| **URL_Annuncio** | Link web diretto all'annuncio originale per il contatto con l'inserzionista. |

---

## 7. Personalizzazione dei Parametri (`config.py`)

Tutti i parametri di calcolo possono essere personalizzati modificando il file [`config.py`](file:///Users/houdinick/projects/ev-solar-charging-scraper/config.py):

* **`MIN_SURFACE_MQ`**: Modifica la superficie minima per includere/escludere aree più piccole (default: `120 mq`).
* **`CANOPY_COVERAGE_RATIO`**: Quota percentuale del piazzale copribile con pensiline (default: `0.40` = 40%).
* **`MQ_PER_KWP`**: Superficie per ogni kWp installato (default: `6.5 mq/kWp`).
* **`SCORE_WEIGHTS`**: Pesi relativi delle 5 macro-aree di scoring (Superficie, Accessibilità, Resa Solare, Infrastruttura, Economicità).

---

## 8. Risoluzione dei Problemi (Troubleshooting)

### A. La mappa mostra "API key required"
* **Causa**: Cache del browser con vecchi layer cartografici di CartoDB.
* **Soluzione**: Esegui un hard-refresh nel browser con `Cmd + Shift + R` (su Mac) o `Ctrl + F5` (su Windows), oppure apri l'URL con cache-buster: `http://localhost:8888/aree_ricarica_ev_solare.html?v=3`.

### B. Porta 8502 o 8888 già occupata
* Per avviare Streamlit su un'altra porta:
  ```bash
  streamlit run app.py --server.port 8505
  ```

### C. Le chiamate all'API PVGIS sembrano lente
* Il sistema include un **circuit-breaker automatico**: se il server della Commissione Europea è sovraccarico o in timeout, passa istantaneamente e in modo trasparente al modello solare regionale ufficiale GSE/ENEA garantendo scansioni in pochi secondi.
