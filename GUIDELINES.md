# 📐 Linee Guida di Progetto (Project Guidelines)

> **EV Solar Site Finder** — Linee guida architetturali, standard ingegneristici, convenzioni di codice e buone pratiche per lo sviluppo e l'estensione del sistema.

---

## 1. Principi Architetturali Fondamentali

1. **Separazione Netta delle Responsabilità (SoC)**:
   * **`scrapers/`**: Solo estrazione e normalizzazione di dati grezzi dal web nel modello `ListingSite`. Nessun calcolo solare o logica di scoring in questo layer.
   * **`enrichment/`**: Arricchimento con sorgenti scientifiche e geografiche (coordinate ISTAT, irraggiamento PVGIS, concorrenza EV). Funzioni pure e idempotenti.
   * **`scoring/`**: Valutazione qualitativa e assegnazione del punteggio ponderato (0–100). Regole deterministiche e trasparenti (spiegabilità dei risultati).
   * **`export/`**: Rendering e persistenza verso l'utente finale (HTML Folium, Excel, CSV, GeoJSON).
   * **`pipeline.py` & `cli.py`**: Orchestrazione delle fasi senza implementare logiche di basso livello.

2. **Attendibilità dei Dati Prima della Quantità**:
   * Non salvare annunci non verificabili o sprovvisti di coerenza territoriale.
   * Se un annuncio ha coordinate ambigue, risolvere il comune tramite il database ISTAT ufficiale a zero latenza.
   * Non dedurre mai vincoli territoriali o allacci MT non verificabili: distinguere sempre i fatti rilevati dalle stime di modello (iniziare i campi con prefisso `estimated_`).

3. **Resilienza e Circuit Breaker verso i Servizi Esterni**:
   * Qualsiasi chiamata a servizi esterni o API terze (es. PVGIS Commissione UE) deve essere protetta da timeout rigidi (≤ 1.5 secondi) e da un **circuit-breaker pattern**.
   * In caso di indisponibilità o rate-limit dei server remoti, il sistema deve effettuare il fallback istantaneo su modelli ingegneristici deterministici locali (tabelle regionali ENEA/GSE).

---

## 2. Modello Dati e Standard di Rappresentazione

Tutti i dati scambiati tra i moduli devono aderire alla dataclass `ListingSite` definita in [`scrapers/base_scraper.py`](file:///Users/houdinick/projects/ev-solar-charging-scraper/scrapers/base_scraper.py):

* **Campi Obbligatori**: `id`, `title`, `url`, `contract_type`, `category`.
* **Standard Metrici**:
  * Superfici: sempre espresse in **metri quadri ($mq$)** come `float`.
  * Potenza elettrica: sempre espressa in **$kWp$** come `float`.
  * Energia solare: sempre espressa in **$kWh$** come `float`.
  * Irraggiamento: sempre espresso in **$kWh/m^2/anno$** come `float`.
  * Prezzi: sempre espressi in **Euro (€)** come `float` (prezzo complessivo di vendita o canone mensile).
* **Tracciabilità della Fonte Geografica (`geo_source`)**:
  * `"portal_map"`: Coordinate esatte estratte dal pin cartografico dell'annuncio.
  * `"offline_istat"`: Coordinate del baricentro comunale risolte dal database ISTAT.
  * `"geocoded"`: Risolte tramite servizio di geocoding esterno.

---

## 3. Standard di Web Scraping e Politiche di Rispetto (Etica & Robustezza)

1. **Evitare Browser Pesanti Dove Possibile**:
   * Preferire l'ispezione di payload Next.js (`__NEXT_DATA__`) e chiamate HTTP sincrone/asincrone (`httpx`) ad alte prestazioni rispetto ad istanze Playwright/Selenium non necessarie.
2. **Rate Limiting e Politeness**:
   * Mantenere un intervallo minimo di **0.8 - 1.2 secondi** tra le richieste successive per non sovraccaricare i server sorgente.
   * Includere un `User-Agent` standard e realistico.
3. **Gestione Errori e Timeout**:
   * Intercettare eccezioni di rete (`httpx.ConnectError`, `httpx.TimeoutException`, `httpx.HTTPStatusError`).
   * Non bloccare mai l'intera pipeline per il fallimento di un singolo annuncio o pagina.

---

## 4. Modello Fisico per le Pensiline Fotovoltaiche (Solar Carports)

I calcoli di producibilità solare integrati in [`enrichment/pvgis_client.py`](file:///Users/houdinick/projects/ev-solar-charging-scraper/enrichment/pvgis_client.py) seguono gli standard dell'industria EPC:

* **Tasso di Copertura Utile del Piazzale (`CANOPY_COVERAGE_RATIO`)**:
  * Valore predefinito: **`0.40` (40%)**.
  * Razionale: In un piazzale commerciale, circa il 40% della superficie è occupato da stalli effettivi copribili con pensilina fotovoltaica, mentre il restante 60% è riservato a corsie di manovra, aree di svolta per veicoli di soccorso, cabina elettrica e distacchi dai confini.
* **Superficie Specifica Moduli (`MQ_PER_KWP`)**:
  * Valore predefinito: **`6.5 mq/kWp`**.
  * Calcolato considerando moduli fotovoltaici bifacciali commerciali ad alta efficienza (potenza nominale 430–500W con efficienza di modulo > 21.5%).
* **Perdite di Sistema (`SYSTEM_LOSS_PERCENT`)**:
  * Valore predefinito: **`14%`**.
  * Tiene conto di perdite per mismatch, caduta di tensione su cavi DC/AC, rendimento medio inverter trifase (98%), sporcamento (soiling) e perdite termiche dei moduli esposti.

---

## 5. Calibrazione e Trasparenza dell'Algoritmo di Scoring (0–100)

L'indice di idoneità calcolato da [`scoring/site_evaluator.py`](file:///Users/houdinick/projects/ev-solar-charging-scraper/scoring/site_evaluator.py) è articolato su 5 macro-aree con somma pesi pari a 100:

| Macro-Area | Peso Massimale | Metrica Valutata |
| :--- | :---: | :--- |
| **Superficie Utile** | **25 pt** | Dimensionamento stalli: da micro-hub (120–250 mq) a hub standard (600–2.500 mq). |
| **Accessibilità & Viabilità** | **25 pt** | Riconoscimento NLP di assi viari ad alto scorrimento (autostrade, tangenziali, statali, rotatorie, fronte strada). |
| **Resa Solare PVGIS** | **20 pt** | Rendimento specifico annuo reale da $1.150$ a $>1.450\text{ kWh/kWp/anno}$. |
| **Infrastruttura del Sito** | **15 pt** | Pavimentazione asfaltata, recinzione, illuminazione, presenza di cabina elettrica / media tensione. |
| **Fattibilità Economica** | **15 pt** | Congruità del costo al mq (vendita) o canone al mq/mese (affitto). |

Ogni valutazione **deve includere la spiegazione qualitativa** (`score_notes`) salvata nel report Excel e nel popup della mappa, per consentire al team di sviluppo di comprendere immediatamente i punti di forza e debolezza dell'area.

---

## 6. Convenzioni di Codice (Code Conventions)

* **Linguaggio**: Python 3.10+ (compatibile con 3.11 e 3.14).
* **Tipizzazione**: Utilizzare type hints (`Optional`, `List`, `Dict`, `Tuple`, `Any`) in tutte le funzioni pubbliche.
* **Docstring**: Docstring in lingua italiana con sintassi Google Style o standard PEP 257.
* **Percorsi File**: Utilizzare esclusivamente `pathlib.Path` per garantire la portabilità tra macOS, Linux e Windows. Evitare concatenazioni manuali di stringhe per i path.

---

## 7. Procedura per Aggiungere Nuovi Portali Immobiliari

Per aggiungere un nuovo portale (es. *Immobiliare.it*, *Idealista*, o piattaforme di appalti pubblici comunali):

1. Creare una nuova classe in `scrapers/` che eredita da `BaseScraper`:
   ```python
   from scrapers.base_scraper import BaseScraper, ListingSite

   class NuovoScraper(BaseScraper):
       def search(self, query, category, contract_type, region, max_pages, min_mq):
           # Implementazione specifica
           ...
   ```
2. Mappare gli annunci estratti nel formato standard `ListingSite`.
3. Registrare il nuovo scraper in `pipeline.py` nel ciclo di aggregazione.
