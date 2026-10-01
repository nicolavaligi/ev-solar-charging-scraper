"""
Motore di valutazione e scoring di idoneità per installazione colonnine di ricarica + fotovoltaico.
Assegna un punteggio scientifico e ponderato da 0 a 100 e genera la motivazione di qualifica.
"""

from typing import List, Dict, Any, Tuple
from scrapers.base_scraper import ListingSite
from config import (
    SCORE_WEIGHTS,
    KEYWORDS_ACCESS,
    KEYWORDS_SITE,
    MIN_SURFACE_MQ,
    RECOMMENDED_SURFACE_MQ,
)


class SiteEvaluator:
    """Valuta le caratteristiche fisiche, solari, logistiche ed economiche di ogni sito."""

    def evaluate(self, site: ListingSite) -> ListingSite:
        """Calcola lo score complessivo e aggiorna l'oggetto ListingSite."""
        text_corpus = f"{site.title} {site.description}".lower()

        # 1. Punteggio Superficie (max 25)
        surf_score, surf_note = self._calc_surface_score(site.size_mq)

        # 2. Punteggio Accessibilità e Viabilità (max 25)
        access_score, access_tags, access_note = self._calc_accessibility_score(text_corpus)

        # 3. Punteggio Resa Solare (max 20)
        solar_score, solar_note = self._calc_solar_score(site.solar_yield_kwh_per_kwp)

        # 4. Punteggio Caratteristiche Sito e Rete Elettrica (max 15)
        feat_score, detected_feats, feat_note = self._calc_features_score(text_corpus)

        # 5. Punteggio Economico (max 15)
        price_score, price_note = self._calc_price_score(site)

        # Totale (0 - 100)
        total_score = round(surf_score + access_score + solar_score + feat_score + price_score, 1)

        # Assegnazione Livello (Grade)
        if total_score >= 75:
            grade = "TOP"
        elif total_score >= 60:
            grade = "BUONO"
        elif total_score >= 45:
            grade = "MEDIO"
        else:
            grade = "BASSO"

        breakdown = {
            "surface": surf_score,
            "accessibility": access_score,
            "solar_yield": solar_score,
            "site_features": feat_score,
            "price_value": price_score,
        }

        notes = [n for n in [surf_note, access_note, solar_note, feat_note, price_note] if n]

        # Aggiornamento dell'oggetto
        site.score = total_score
        site.score_grade = grade
        site.score_breakdown = breakdown
        site.score_notes = notes
        site.accessibility_tags = access_tags
        site.features_detected = detected_feats

        return site

    def _calc_surface_score(self, mq: float) -> Tuple[float, str]:
        max_pts = SCORE_WEIGHTS["surface"]
        if not mq:
            return 12.0, "Superficie non dichiarata in scheda (da verificare da planimetria)"

        if mq < MIN_SURFACE_MQ:
            return 0.0, f"Superficie insufficiente ({mq:.0f} mq < {MIN_SURFACE_MQ} mq)"
        elif mq < 250:
            return 16.0, f"Micro-hub compatto ({mq:.0f} mq, ideale per 2-4 stalli fast e pensilina 15-30 kWp)"
        elif 250 <= mq < 600:
            return 22.0, f"Hub cittadino/commerciale ({mq:.0f} mq, ottimo per 4-6 stalli e pensilina 30-70 kWp)"
        elif 600 <= mq <= 2500:
            return float(max_pts), f"Superficie ottimale ({mq:.0f} mq, ideale per hub 6-12 stalli e pensiline FV 70-150 kWp)"
        elif 2500 < mq <= 8000:
            return 22.0, f"Grande area ({mq:.0f} mq, adatta per hub di ricarica ad alta intensità)"
        else:
            return 18.0, f"Superficie molto estesa ({mq:.0f} mq, richiede frazionamento/sviluppo ampio)"

    def _calc_accessibility_score(self, text: str) -> Tuple[float, List[str], str]:
        max_pts = SCORE_WEIGHTS["accessibility"]
        score = 5.0  # Base minima
        tags = []

        for kw, pts in KEYWORDS_ACCESS.items():
            if kw in text:
                score += pts
                tags.append(kw)

        score = min(float(max_pts), score)
        if tags:
            note = f"Ottima accessibilità riscontrata: {', '.join(tags[:4])}"
        else:
            note = "Accessibilità viaria standard da verificare da mappa"

        return round(score, 1), tags, note

    def _calc_solar_score(self, yield_kwh: float) -> Tuple[float, str]:
        max_pts = SCORE_WEIGHTS["solar_yield"]
        if not yield_kwh:
            return 10.0, "Dato solare stimato"

        if yield_kwh >= 1450:
            return float(max_pts), f"Irraggiamento solare eccellente ({yield_kwh:.0f} kWh/kWp/anno)"
        elif yield_kwh >= 1350:
            return 17.0, f"Ottimo rendimento solare ({yield_kwh:.0f} kWh/kWp/anno)"
        elif yield_kwh >= 1250:
            return 14.0, f"Buon rendimento solare ({yield_kwh:.0f} kWh/kWp/anno)"
        elif yield_kwh >= 1150:
            return 11.0, f"Rendimento solare moderato Nord Italia ({yield_kwh:.0f} kWh/kWp/anno)"
        else:
            return 8.0, f"Rendimento solare basso ({yield_kwh:.0f} kWh/kWp/anno)"

    def _calc_features_score(self, text: str) -> Tuple[float, List[str], str]:
        max_pts = SCORE_WEIGHTS["site_features"]
        score = 3.0
        features = []

        for kw, pts in KEYWORDS_SITE.items():
            if kw in text:
                score += pts
                features.append(kw)

        score = min(float(max_pts), score)
        if "cabina" in features or "media tensione" in features or "trasformatore" in features:
            note = "Presenza di infrastruttura elettrica/cabina citata nell'annuncio"
        elif features:
            note = f"Caratteristiche rilevate: {', '.join(features[:3])}"
        else:
            note = "Stato del lotto da verificare (pavimentazione/recinzione)"

        return round(score, 1), features, note

    def _calc_price_score(self, site: ListingSite) -> Tuple[float, str]:
        max_pts = SCORE_WEIGHTS["price_value"]

        if not site.price or not site.size_mq or site.size_mq <= 0:
            return 8.0, "Prezzo/canone riservato o non specificato"

        if site.contract_type == "vendita":
            price_per_mq = site.price / site.size_mq
            if price_per_mq <= 50:
                return float(max_pts), f"Prezzo molto competitivo ({price_per_mq:.1f} €/mq)"
            elif price_per_mq <= 120:
                return 12.0, f"Prezzo congruo di mercato ({price_per_mq:.1f} €/mq)"
            elif price_per_mq <= 250:
                return 8.0, f"Prezzo sopra la media ({price_per_mq:.1f} €/mq)"
            else:
                return 4.0, f"Prezzo elevato ({price_per_mq:.1f} €/mq, possibile fabbricato incluso)"
        else:  # Affitto / Locazione
            # Spesso il canone indicato è mensile
            rent_per_mq_month = site.price / site.size_mq
            if rent_per_mq_month <= 1.0:
                return float(max_pts), f"Canone di locazione vantaggioso ({rent_per_mq_month:.2f} €/mq/mese)"
            elif rent_per_mq_month <= 2.5:
                return 12.0, f"Canone di mercato ({rent_per_mq_month:.2f} €/mq/mese)"
            else:
                return 6.0, f"Canone elevato ({rent_per_mq_month:.2f} €/mq/mese)"
