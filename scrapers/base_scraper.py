"""
Classe base per gli scraper e definizione del modello dati ListingSite.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


@dataclass
class ListingSite:
    id: str
    title: str
    url: str
    description: str = ""
    price: Optional[float] = None
    price_str: str = ""
    size_mq: Optional[float] = None
    contract_type: str = "vendita"  # "vendita" o "affitto"
    category: str = "commerciale"   # "commerciale", "terreno", "parcheggio"
    
    # Dati Geografici
    region: str = ""
    province: str = ""
    town: str = ""
    address: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geo_source: str = ""  # "portal_map", "offline_istat", "geocoded"
    
    # Inserzionista e Immagini
    advertiser: str = ""
    is_company: bool = False
    date_posted: str = ""
    image_url: str = ""
    
    # Arricchimento Solare (PVGIS)
    solar_irradiance_kwh_m2: Optional[float] = None    # Irraggiamento annuale sul piano (kWh/m²/anno)
    solar_yield_kwh_per_kwp: Optional[float] = None    # Produzione specifica (kWh/kWp/anno)
    estimated_canopy_potenza_kwp: Optional[float] = None # Potenza stimata installabile su pensilina (kWp)
    estimated_annual_pv_kwh: Optional[float] = None     # Energia solare annua stimata prodotta (kWh/anno)
    
    # Analisi del testo e tag
    features_detected: List[str] = field(default_factory=list)
    accessibility_tags: List[str] = field(default_factory=list)
    
    # Scoring
    score: float = 0.0
    score_grade: str = "NON_VALUTATO"  # "TOP", "BUONO", "MEDIO", "BASSO"
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    score_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseScraper(ABC):
    """Interfaccia astratta per gli scraper immobiliari."""

    @abstractmethod
    def search(
        self,
        query: str = "piazzale",
        category: str = "uffici-locali-commerciali",
        contract_type: str = "vendita",
        region: Optional[str] = None,
        max_pages: int = 3,
        min_mq: Optional[int] = 400
    ) -> List[ListingSite]:
        """Esegue la ricerca e restituisce una lista di ListingSite grezzi."""
        pass
