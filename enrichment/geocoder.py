"""
Modulo Geocoder per normalizzare indirizzi e coordinate geografiche in Italia.
Utilizza un database offline ad altissima velocità dei comuni italiani (ISTAT)
con supporto a normalizzazione caratteri e fallback opzionale.
"""

import json
import logging
import unicodedata
from typing import Optional, Tuple, Dict
from pathlib import Path

from config import COMUNI_COORDS_FILE

logger = logging.getLogger(__name__)


def normalize_city_name(name: str) -> str:
    """Rimuove accenti, apostrofi e spazi superflui per match fuzzy affidabile."""
    if not name:
        return ""
    # Decomposizione NFD per separare caratteri base da diacritici
    nfd = unicodedata.normalize("NFD", name)
    cleaned = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    cleaned = cleaned.lower().replace("'", "").replace("’", "").replace("-", " ")
    return " ".join(cleaned.split())


class ItalianGeocoder:
    """Geocoder offline per i comuni italiani."""

    _instance: Optional["ItalianGeocoder"] = None
    _coords_lookup: Dict[str, Tuple[float, float]] = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ItalianGeocoder, cls).__new__(cls)
            cls._instance._load_database()
        return cls._instance

    def _load_database(self):
        """Carica il database di coordinate dei comuni italiani."""
        if self._coords_lookup:
            return

        if not COMUNI_COORDS_FILE.exists():
            logger.warning(f"File comuni non trovato: {COMUNI_COORDS_FILE}")
            return

        try:
            with open(COMUNI_COORDS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data:
                name = item.get("name", "")
                lat = item.get("lat")
                lon = item.get("lon")
                if name and lat is not None and lon is not None:
                    norm_key = normalize_city_name(name)
                    self._coords_lookup[norm_key] = (float(lat), float(lon))

            logger.info(f"[Geocoder] Caricati {len(self._coords_lookup)} comuni italiani per geocoding offline.")
        except Exception as e:
            logger.error(f"Errore caricamento database comuni: {e}")

    def geocode_town(self, town: str, province: Optional[str] = None) -> Optional[Tuple[float, float]]:
        """
        Risolve latitudine e longitudine di un comune italiano in pochi microsecondi.
        """
        if not town:
            return None

        # 1. Ricerca diretta per nome comune normalizzato
        norm_town = normalize_city_name(town)
        if norm_town in self._coords_lookup:
            return self._coords_lookup[norm_town]

        # 2. Ricerca parziale (se il nome contiene frazioni o specifiche es. 'Milano Rogoredo')
        for known_name, coords in self._coords_lookup.items():
            if norm_town.startswith(known_name) or known_name in norm_town:
                return coords

        # 3. Fallback sulla provincia se fornita
        if province:
            norm_prov = normalize_city_name(province)
            if norm_prov in self._coords_lookup:
                return self._coords_lookup[norm_prov]

        return None
