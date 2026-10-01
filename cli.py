#!/usr/bin/env python3
"""
CLI Interface per EV Solar Site Finder.
Permette di avviare ricerche mirate per regione, tipologia o parole chiave con output tabellare e mappa.
"""

import argparse
import sys
from pathlib import Path

# Assicura che la cartella corrente sia nel PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from pipeline import EVSolarPipeline


def main():
    parser = argparse.ArgumentParser(
        description="EV Solar Site Finder: Scraper e qualificatore aree per colonnine di ricarica + fotovoltaico"
    )
    parser.add_argument(
        "-q", "--query",
        type=str,
        default=None,
        help="Parola chiave di ricerca (default: 'piazzale', 'terreno commerciale', 'parcheggio')"
    )
    parser.add_argument(
        "-r", "--region",
        type=str,
        default=None,
        help="Regione specifica (es. lombardia, lazio, veneto, emilia-romagna). Default: tutta Italia"
    )
    parser.add_argument(
        "-c", "--contract",
        type=str,
        choices=["vendita", "affitto", "all"],
        default="all",
        help="Tipo contratto: vendita, affitto o all (default: all)"
    )
    parser.add_argument(
        "--cat", "--category",
        dest="category",
        type=str,
        choices=["commerciale", "terreni", "all"],
        default="all",
        help="Categoria annunci: commerciale, terreni o all (default: all)"
    )
    parser.add_argument(
        "--min-mq",
        type=int,
        default=120,
        help="Superficie minima in mq (default: 120 mq per micro-hub 2-4 stalli)"
    )
    parser.add_argument(
        "-p", "--pages",
        type=int,
        default=2,
        help="Numero massimo di pagine da scansionare per ogni combinazione (default: 2)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="aree_ricarica_ev_solare",
        help="Nome file base per l'export HTML/CSV/XLSX (default: 'aree_ricarica_ev_solare')"
    )

    args = parser.parse_args()

    queries = [args.query] if args.query else ["piazzale", "terreno commerciale", "parcheggio"]
    
    if args.contract == "all":
        contracts = ["vendita", "affitto"]
    else:
        contracts = [args.contract]

    if args.category == "all":
        categories = ["uffici-locali-commerciali", "terreni-e-rustici"]
    elif args.category == "commerciale":
        categories = ["uffici-locali-commerciali"]
    else:
        categories = ["terreni-e-rustici"]

    print("=" * 70)
    print("⚡ EV SOLAR SITE FINDER - SCANSIONE AREE DI RICARICA & FOTOVOLTAICO")
    print("=" * 70)

    pipeline = EVSolarPipeline()
    result = pipeline.run(
        queries=queries,
        categories=categories,
        contract_types=contracts,
        region=args.region,
        max_pages=args.pages,
        min_mq=args.min_mq,
        export_name=args.output
    )

    print("\n" + "=" * 70)
    print("📋 RIEPILOGO RISULTATI:")
    print(f"  • Annunci unici idonei estratti: {result['total_found']}")
    print(f"  • Opportunità TOP (Score ≥ 75):  {result['top_sites']}")
    print(f"  • Opportunità BUONE (60-74):    {result['good_sites']}")
    if result["total_found"] > 0:
        print(f"  • Potenziale Pensiline Solari:   {result['total_solar_kwp_potential']:,.1f} kWp")
        print(f"  • Energia Solare Stimata:       {result['total_annual_kwh_potential']:,.0f} kWh/anno")
    print("=" * 70)

    # Mostra i primi 5 risultati TOP nel terminale
    sites = result.get("sites", [])
    if sites:
        print("\n🏆 PRIME OPPORTUNITÀ IDENTIFICATE:")
        for idx, s in enumerate(sites[:5], 1):
            price_disp = s.price_str or (f"{s.price:,.0f} €" if s.price else "Trattativa ris.")
            print(f"\n{idx}. [{s.score_grade} - {s.score}/100] {s.title}")
            print(f"   📍 {s.town} ({s.province}) | Superficie: {s.size_mq:,.0f} mq | {s.contract_type.upper()}: {price_disp}")
            print(f"   ☀️ Pensilina FV: ~{s.estimated_canopy_potenza_kwp or 0:.0f} kWp | Produzione: {s.estimated_annual_pv_kwh or 0:,.0f} kWh/anno")
            if s.accessibility_tags:
                print(f"   🛣️ Accesso/Viabilità: {', '.join(s.accessibility_tags)}")
            print(f"   🔗 Link: {s.url}")

    print("\n✅ Completato con successo! I file sono pronti nella cartella 'output/'.\n")


if __name__ == "__main__":
    main()
