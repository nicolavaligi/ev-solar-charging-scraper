"""
Modulo di esportazione dati tabellari (CSV ed Excel .xlsx).
Crea fogli di lavoro ordinati per score e completi di metriche tecniche e finanziarie.
"""

import logging
from pathlib import Path
from typing import List
import pandas as pd

from scrapers.base_scraper import ListingSite

logger = logging.getLogger(__name__)


class TableExporter:
    """Esporta i siti valutati in formati CSV ed Excel."""

    def to_dataframe(self, sites: List[ListingSite]) -> pd.DataFrame:
        """Converte la lista di ListingSite in un DataFrame Pandas arricchito e ordinato."""
        rows = []
        for s in sites:
            price_per_mq = round(s.price / s.size_mq, 1) if s.price and s.size_mq and s.size_mq > 0 else None
            
            rows.append({
                "Score": s.score,
                "Livello": s.score_grade,
                "Titolo": s.title,
                "Comune": s.town,
                "Provincia": s.province,
                "Regione": s.region,
                "Superficie_mq": s.size_mq,
                "Prezzo_Euro": s.price,
                "Prezzo_al_mq": price_per_mq,
                "Contratto": s.contract_type.capitalize(),
                "Categoria": s.category,
                "Potenza_Pensilina_kWp": s.estimated_canopy_potenza_kwp,
                "Produzione_Solare_Annua_kWh": s.estimated_annual_pv_kwh,
                "Resa_PVGIS_kWh_kWp": s.solar_yield_kwh_per_kwp,
                "Irraggiamento_kWh_m2": s.solar_irradiance_kwh_m2,
                "Accessibilita": ", ".join(s.accessibility_tags),
                "Caratteristiche": ", ".join(s.features_detected),
                "Note_Valutazione": " | ".join(s.score_notes),
                "Indirizzo": s.address,
                "Latitudine": s.latitude,
                "Longitudine": s.longitude,
                "Fonte_Geo": s.geo_source,
                "Inserzionista": s.advertiser,
                "Data_Annuncio": s.date_posted,
                "URL_Annuncio": s.url
            })

        df = pd.DataFrame(rows)
        if not df.empty and "Score" in df.columns:
            # Ordina dal punteggio più alto al più basso
            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

        return df

    def export_csv(self, sites: List[ListingSite], output_path: Path) -> str:
        df = self.to_dataframe(sites)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        logger.info(f"[TableExporter] CSV salvato in: {output_path}")
        return str(output_path)

    def export_excel(self, sites: List[ListingSite], output_path: Path) -> str:
        df = self.to_dataframe(sites)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(output_path, index=False, engine="openpyxl")
        logger.info(f"[TableExporter] Excel salvato in: {output_path}")
        return str(output_path)
