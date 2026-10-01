"""
Generatore di mappa interattiva HTML con Folium/Leaflet.
Visualizza i siti qualificati con marker colorati in base al punteggio,
cluster di navigazione e popup informativi dettagliati con dati FV e link all'annuncio.
"""

import logging
from pathlib import Path
from typing import List
import folium
from folium.plugins import MarkerCluster

from scrapers.base_scraper import ListingSite

logger = logging.getLogger(__name__)


class MapGenerator:
    """Genera mappe interattive georeferenziate per i siti di ricarica solare."""

    COLOR_MAP = {
        "TOP": "green",
        "BUONO": "orange",
        "MEDIO": "blue",
        "BASSO": "red",
        "NON_VALUTATO": "gray"
    }

    ICON_MAP = {
        "TOP": "bolt",
        "BUONO": "charging-station",
        "MEDIO": "info-sign",
        "BASSO": "map-pin",
        "NON_VALUTATO": "question-sign"
    }

    def generate_html_map(
        self,
        sites: List[ListingSite],
        output_file: Path,
        title: str = "Aree Idonee Colonnine di Ricarica + Fotovoltaico"
    ) -> str:
        """Crea una mappa HTML completa e la salva su disco."""
        # Filtra i siti con coordinate valide
        valid_sites = [s for s in sites if s.latitude and s.longitude]
        
        if not valid_sites:
            logger.warning("Nessun sito con coordinate geografiche valide per la mappa.")
            # Centra sull'Italia centrale come fallback
            center_lat, center_lon = 42.50, 12.50
            zoom = 6
        else:
            center_lat = sum(s.latitude for s in valid_sites) / len(valid_sites)
            center_lon = sum(s.longitude for s in valid_sites) / len(valid_sites)
            zoom = 6 if len(valid_sites) > 10 else 10

        # Inizializza la mappa Folium con OpenStreetMap standard (100% libera e senza API key)
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles="OpenStreetMap",
            control_scale=True
        )

        # Aggiungi cluster di marker
        cluster = MarkerCluster(name="Siti Ricarica EV + Solare").add_to(m)

        for site in valid_sites:
            color = self.COLOR_MAP.get(site.score_grade, "blue")
            icon_name = self.ICON_MAP.get(site.score_grade, "bolt")

            popup_html = self._build_popup_html(site)
            popup = folium.Popup(popup_html, max_width=360)

            folium.Marker(
                location=[site.latitude, site.longitude],
                popup=popup,
                tooltip=f"[{site.score_grade}] {site.score}/100 - {site.town} ({site.size_mq or 0:.0f} mq)",
                icon=folium.Icon(color=color, icon=icon_name, prefix="fa" if icon_name == "charging-station" else "glyphicon")
            ).add_to(cluster)

        # Aggiungi layer di controllo
        folium.LayerControl().add_to(m)

        # Salva file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        m.save(str(output_file))
        logger.info(f"[MapGenerator] Mappa salvata con successo in: {output_file}")
        return str(output_file)

    def _build_popup_html(self, site: ListingSite) -> str:
        """Crea il contenuto HTML stilizzato per il popup di ciascun sito."""
        grade_colors = {
            "TOP": "#1b5e20",
            "BUONO": "#e65100",
            "MEDIO": "#0d47a1",
            "BASSO": "#b71c1c"
        }
        badge_bg = grade_colors.get(site.score_grade, "#333333")

        tags_html = ""
        all_tags = site.accessibility_tags + site.features_detected
        if all_tags:
            tags_html = " ".join([f"<span style='background:#f0f2f5; color:#333; padding:2px 6px; border-radius:4px; font-size:11px; margin-right:3px;'>#{t}</span>" for t in all_tags[:5]])

        pv_info_html = ""
        if site.estimated_canopy_potenza_kwp:
            pv_info_html = f"""
            <div style='margin-top:8px; padding:6px; background:#f4fbf5; border-left:3px solid #2e7d32; border-radius:3px; font-size:12px;'>
                <b>⚡ Potenziale Pensilina FV:</b> ~{site.estimated_canopy_potenza_kwp:.0f} kWp<br>
                <b>☀️ Resa Annua Stimata:</b> {site.estimated_annual_pv_kwh:,.0f} kWh/anno<br>
                <b>📊 Irraggiamento PVGIS:</b> {site.solar_yield_kwh_per_kwp or 0:.0f} kWh/kWp
            </div>
            """

        price_str = site.price_str or (f"{site.price:,.0f} €" if site.price else "Trattativa riservata")
        surface_str = f"{site.size_mq:,.0f} mq" if site.size_mq else "N.D."

        html = f"""
        <div style='font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif; min-width:280px;'>
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;'>
                <span style='background:{badge_bg}; color:#fff; font-weight:bold; font-size:11px; padding:3px 8px; border-radius:12px;'>
                    {site.score_grade} • Score {site.score}/100
                </span>
                <span style='font-size:11px; color:#666; text-transform:uppercase;'>{site.contract_type}</span>
            </div>
            <h4 style='margin:0 0 6px 0; font-size:14px; line-height:1.3; color:#111;'>{site.title}</h4>
            <div style='font-size:12px; color:#444; margin-bottom:6px;'>
                📍 <b>{site.town}</b> ({site.province}) - {site.region}<br>
                📐 <b>Superficie:</b> {surface_str} | 💰 <b>Prezzo:</b> {price_str}
            </div>
            {pv_info_html}
            <div style='margin-top:8px; line-height:1.6;'>
                {tags_html}
            </div>
            <div style='margin-top:10px; border-top:1px solid #eee; padding-top:8px; text-align:right;'>
                <a href='{site.url}' target='_blank' style='background:#0066cc; color:#fff; text-decoration:none; padding:5px 10px; border-radius:4px; font-size:12px; font-weight:bold; display:inline-block;'>
                    Vedi Annuncio ↗
                </a>
            </div>
        </div>
        """
        return html
