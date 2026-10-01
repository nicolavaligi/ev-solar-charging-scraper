"""
Configurazione per EV Solar Site Finder.
Parametri di filtro, pesi di scoring e impostazioni delle API.
"""

from pathlib import Path

# Percorsi base
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REFERENCE_DIR = DATA_DIR / "reference"
OUTPUT_DIR = BASE_DIR / "output"

# Crea directory output se non esistono
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# File di riferimento
COMUNI_COORDS_FILE = REFERENCE_DIR / "comuni_coords.json"

# Criteri di filtraggio minimi per hub di ricarica + pensiline FV
# Un hub di ricarica compatto da 2-4 stalli con pensilina FV richiede da 100 a 250 mq.
# Un hub medio (4-8 stalli) richiede da 300 a 800 mq.
MIN_SURFACE_MQ = 120          # 120 mq: soglia reale per micro-hub 2-4 stalli con pensilina e locale tecnico
RECOMMENDED_SURFACE_MQ = 500  # Superficie ottimale per 4-8 stalli e 40-80 kWp di pensilina
MAX_SURFACE_MQ = 100000       # Per evitare mega lotti agricoli fuori contesto

# Parametri Fotovoltaico Pensiline
# In media una pensilina fotovoltaica per parcheggio richiede circa 10-12 mq per stallo (2-3 kWp a stallo)
# Riconoscimento della superficie copribile (circa il 40-60% dell'area totale per preservare corsie di manovra)
CANOPY_COVERAGE_RATIO = 0.40  # 40% del piazzale coperto da pensiline fotovoltaiche
MQ_PER_KWP = 6.5              # ~6.5 mq per kWp con moduli fotovoltaici moderni ad alta efficienza (430-500W)
SYSTEM_LOSS_PERCENT = 14      # Perdite di sistema standard PVGIS (inverter, cavi, ombreggiamenti)

# Pesi Scoring di Idoneità (Totale: 100)
SCORE_WEIGHTS = {
    "surface": 25,       # Adeguatezza delle dimensioni del lotto
    "accessibility": 25, # Accessibilità viaria, fronte strada, caselli/tangenziali
    "solar_yield": 20,   # Resa fotovoltaica scientifica da PVGIS (kWh/kWp/anno)
    "site_features": 15, # Caratteristiche del sito (asfaltato, recintato, illuminato, industriale)
    "price_value": 15,   # Convenienza economica (prezzo/mq vendita o canone/mq affitto)
}

# Parole chiave con bonus per l'accessibilità e la logistica di ricarica
KEYWORDS_ACCESS = {
    "fronte strada": 10,
    "visibilità": 6,
    "tangenziale": 8,
    "casello": 8,
    "autostrada": 8,
    "strada statale": 7,
    "ss": 4,
    "alto passaggio": 7,
    "scorrimento veloce": 6,
    "rotatoria": 5,
    "rotonda": 5,
    "accesso carrabile": 5,
    "accesso bilici": 5,
    "manovra": 4,
    "snodo": 5,
}

# Parole chiave con bonus per caratteristiche dell'area
KEYWORDS_SITE = {
    "piazzale": 8,
    "asfaltato": 6,
    "recintato": 5,
    "illuminato": 4,
    "urbanizzato": 6,
    "zona commerciale": 7,
    "zona industriale": 6,
    "zona artigianale": 5,
    "cabina": 8,
    "trasformatore": 7,
    "allacciamento": 6,
    "energia elettrica": 5,
    "media tensione": 8,
    "pozzo": 3,
    "cancello": 3,
}

# Parole chiave negative (penalità o scarto se presenti senza spazio esterno)
KEYWORDS_NEGATIVE = [
    "appartamento", "mansarda", "seminativo", "bosco", "boscoso",
    "scosceso", "rudere", "fienile", "solo licenza", "senza piazzale",
    "cessione attività", "avviamento", "cedesi attività", "tabaccheria",
    "edicola", "panificio", "bar pizzeria", "slot"
]

# User agent standard per web request
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
}
