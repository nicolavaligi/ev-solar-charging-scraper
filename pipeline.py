"""
Orchestratore della pipeline end-to-end:
Scraping -> Geocoding -> Arricchimento Solare PVGIS -> Scoring -> Esportazione Mappa ed Excel.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from config import OUTPUT_DIR, MIN_SURFACE_MQ
from scrapers.base_scraper import ListingSite
from scrapers.subito_scraper import SubitoScraper
from enrichment.geocoder import ItalianGeocoder
from enrichment.pvgis_client import PVGISClient
from scoring.site_evaluator import SiteEvaluator
from export.map_generator import MapGenerator
from export.table_exporter import TableExporter

logger = logging.getLogger(__name__)


class EVSolarPipeline:
    """Pipeline integrata per l'individuazione e qualifica di aree per ricarica EV e solare."""

    def __init__(self):
        self.geocoder = ItalianGeocoder()
        self.pvgis = PVGISClient()
        self.evaluator = SiteEvaluator()
        self.map_gen = MapGenerator()
        self.table_exp = TableExporter()

    def run(
        self,
        queries: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        contract_types: Optional[List[str]] = None,
        region: Optional[str] = None,
        max_pages: int = 2,
        min_mq: int = MIN_SURFACE_MQ,
        export_name: str = "aree_ricarica_solare"
    ) -> Dict[str, Any]:
        """
        Esegue la scansione completa e restituisce le statistiche e i percorsi dei file generati.
        """
        if not queries:
            queries = ["piazzale", "terreno commerciale", "parcheggio"]
        if not categories:
            categories = ["uffici-locali-commerciali", "terreni-e-rustici"]
        if not contract_types:
            contract_types = ["vendita", "affitto"]

        scraper = SubitoScraper(request_delay=0.8)
        all_sites: List[ListingSite] = []
        seen_ids = set()

        print(f"\n🚀 [1/4] Avvio scraping su scala {'Nazionale' if not region else region.upper()}...")
        print(f"    • Parole chiave: {', '.join(queries)}")
        print(f"    • Contratti: {', '.join(contract_types)}")
        print(f"    • Categorie: {', '.join(categories)}")
        print(f"    • Superficie minima: {min_mq} mq")

        # 1. Scraping multi-query
        for cat in categories:
            for ctype in contract_types:
                for q in queries:
                    print(f"  🔍 Ricerca: '{q}' [{ctype.upper()} / {cat}]...")
                    batch = scraper.search(
                        query=q,
                        category=cat,
                        contract_type=ctype,
                        region=region,
                        max_pages=max_pages,
                        min_mq=min_mq
                    )
                    for site in batch:
                        if site.id not in seen_ids:
                            seen_ids.add(site.id)
                            all_sites.append(site)

        scraper.close()
        print(f"  ✅ Trovati {len(all_sites)} annunci unici idonei per dimensione.")

        if not all_sites:
            return {
                "total_found": 0,
                "top_sites": 0,
                "good_sites": 0,
                "output_files": {}
            }

        # 2. Geocoding & Risoluzione Coordinate
        print("\n📍 [2/4] Normalizzazione geografica e geocoding...")
        geocoded_count = 0
        for site in all_sites:
            if not site.latitude or not site.longitude:
                coords = self.geocoder.geocode_town(site.town, site.province)
                if coords:
                    site.latitude, site.longitude = coords
                    site.geo_source = "offline_istat"
                    geocoded_count += 1
            else:
                site.geo_source = "portal_map"

        print(f"  ✅ Coordinate assegnate a {sum(1 for s in all_sites if s.latitude)}/{len(all_sites)} siti ({geocoded_count} tramite database ISTAT).")

        # 3. Arricchimento Solare PVGIS & Dimensionamento Pensiline
        print("\n☀️ [3/4] Calcolo potenziale fotovoltaico scientifico (PVGIS)...")
        for idx, site in enumerate(all_sites, 1):
            if idx % 10 == 0 or idx == len(all_sites):
                print(f"  ⚡ Elaborazione solare: {idx}/{len(all_sites)} siti...", end="\r", flush=True)

            if site.latitude and site.longitude:
                solar_data = self.pvgis.get_solar_data(site.latitude, site.longitude)
                site.solar_yield_kwh_per_kwp = solar_data.get("yield_kwh_per_kwp")
                site.solar_irradiance_kwh_m2 = solar_data.get("irradiance_kwh_m2")

                if site.size_mq and site.solar_yield_kwh_per_kwp:
                    kwp, annual_kwh = self.pvgis.estimate_canopy_system(
                        site.size_mq,
                        site.solar_yield_kwh_per_kwp
                    )
                    site.estimated_canopy_potenza_kwp = kwp
                    site.estimated_annual_pv_kwh = annual_kwh

            # 4. Scoring di idoneità
            self.evaluator.evaluate(site)

        print(f"\n  ☀️ Calcolo solare e scoring completati per tutti i {len(all_sites)} siti.")

        # Ordina per punteggio decrescente
        all_sites.sort(key=lambda x: x.score, reverse=True)

        top_sites = [s for s in all_sites if s.score_grade == "TOP"]
        good_sites = [s for s in all_sites if s.score_grade == "BUONO"]

        print(f"  ✅ Valutazione completata:")
        print(f"     🌟 TOP (Score ≥ 75): {len(top_sites)}")
        print(f"     👍 BUONO (Score 60-74): {len(good_sites)}")
        print(f"     ℹ️ MEDIO/BASSO: {len(all_sites) - len(top_sites) - len(good_sites)}")

        # 5. Esportazione
        print("\n📊 [4/4] Generazione Mappa Interattiva ed Export Dati...")
        map_path = OUTPUT_DIR / f"{export_name}.html"
        csv_path = OUTPUT_DIR / f"{export_name}.csv"
        xlsx_path = OUTPUT_DIR / f"{export_name}.xlsx"

        self.map_gen.generate_html_map(all_sites, map_path)
        self.table_exp.export_csv(all_sites, csv_path)
        self.table_exp.export_excel(all_sites, xlsx_path)

        print(f"  🗺️ Mappa HTML:  {map_path}")
        print(f"  📈 Tabella CSV:  {csv_path}")
        print(f"  📑 Tabella XLSX: {xlsx_path}")

        total_kwp = sum(s.estimated_canopy_potenza_kwp or 0 for s in all_sites)
        total_kwh = sum(s.estimated_annual_pv_kwh or 0 for s in all_sites)

        return {
            "total_found": len(all_sites),
            "top_sites": len(top_sites),
            "good_sites": len(good_sites),
            "total_solar_kwp_potential": round(total_kwp, 1),
            "total_annual_kwh_potential": round(total_kwh, 0),
            "output_files": {
                "map": str(map_path),
                "csv": str(csv_path),
                "xlsx": str(xlsx_path)
            },
            "sites": all_sites
        }
