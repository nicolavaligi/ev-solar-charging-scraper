"""
Scraper per Subito.it (Immobili commerciali, piazzali e terreni).
Estrae annunci strutturati dal payload Next.js per massima velocità e affidabilità.
"""

import json
import logging
import re
import time
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus
import httpx
from bs4 import BeautifulSoup

from config import DEFAULT_HEADERS, MIN_SURFACE_MQ, KEYWORDS_NEGATIVE
from scrapers.base_scraper import BaseScraper, ListingSite

logger = logging.getLogger(__name__)


class SubitoScraper(BaseScraper):
    """
    Scraper ad alte prestazioni per Subito.it.
    Interroga le pagine di ricerca e deserializza direttamente lo stato React/Next.js (__NEXT_DATA__).
    """

    BASE_URL = "https://www.subito.it"

    CATEGORIES = {
        "commerciale": "uffici-locali-commerciali",
        "uffici-locali-commerciali": "uffici-locali-commerciali",
        "terreni": "terreni-e-rustici",
        "terreni-e-rustici": "terreni-e-rustici",
        "parcheggi": "garage-e-box",
        "garage-e-box": "garage-e-box",
    }

    # Mappatura regioni italiane ai rispettivi slug Subito
    REGIONS = {
        "abruzzo": "abruzzo",
        "basilicata": "basilicata",
        "calabria": "calabria",
        "campania": "campania",
        "emilia-romagna": "emilia-romagna",
        "friuli-venezia-giulia": "friuli-venezia-giulia",
        "lazio": "lazio",
        "liguria": "liguria",
        "lombardia": "lombardia",
        "marche": "marche",
        "molise": "molise",
        "piemonte": "piemonte",
        "puglia": "puglia",
        "sardegna": "sardegna",
        "sicilia": "sicilia",
        "toscana": "toscana",
        "trentino-alto-adige": "trentino-alto-adige",
        "umbria": "umbria",
        "valle-d-aosta": "valle-d-aosta",
        "veneto": "veneto",
    }

    def __init__(self, request_delay: float = 1.0, timeout: float = 12.0):
        self.request_delay = request_delay
        self.timeout = timeout
        self.client = httpx.Client(
            headers=DEFAULT_HEADERS,
            follow_redirects=True,
            timeout=self.timeout
        )

    def _build_search_url(
        self,
        query: str,
        category: str,
        contract_type: str,
        region: Optional[str] = None,
        page: int = 1
    ) -> str:
        cat_slug = self.CATEGORIES.get(category, "uffici-locali-commerciali")
        reg_slug = self.REGIONS.get(region.lower(), region.lower()) if region else "italia"
        
        url = f"{self.BASE_URL}/annunci-{reg_slug}/{contract_type}/{cat_slug}/?q={quote_plus(query)}"
        if page > 1:
            url += f"&o={page}"
        return url

    def _extract_size_from_text(self, text: str) -> Optional[float]:
        """Estrae la superficie in mq dal testo tramite espressioni regolari avanzate."""
        if not text:
            return None
            
        # Pattern 1: 'piazzale/area/terreno di 1500 mq' o '1500 mq'
        patterns = [
            r'(?:piazzale|area\s+esterna|terreno|lotto|superficie)?\s*(?:di|circa|da)?\s*(\d+(?:[\.,]\d+)?)\s*(?:mq|m2|metri\s*quadr[io])',
            r'(?:mq|m2|metri\s*quadr[io])\.?\s*(\d+(?:[\.,]\d+)?)'
        ]
        
        found_sizes = []
        for pat in patterns:
            matches = re.findall(pat, text, re.IGNORECASE)
            for m in matches:
                clean_num = m.replace(".", "").replace(",", ".")
                try:
                    val = float(clean_num)
                    if 50 <= val <= 200000:
                        found_sizes.append(val)
                except ValueError:
                    continue
                    
        if found_sizes:
            # Se ci sono più metrature menzionate, cerchiamo di preferire quella maggiore (spesso il piazzale/lotto intero)
            return max(found_sizes)
        return None

    def _parse_item(self, item_dict: Dict[str, Any], default_contract: str) -> Optional[ListingSite]:
        """Converte un dizionario grezzo di annuncio Subito in un oggetto ListingSite."""
        try:
            urn = item_dict.get("urn", "")
            if not urn:
                return None
            
            subject = item_dict.get("subject", "").strip()
            body = item_dict.get("body", "").strip()
            full_text = f"{subject} {body}".lower()

            # Controllo parole negative severe (es. vendita appartamento o solo cessione ramo d'azienda)
            if any(neg in full_text for neg in ["mansarda", "seminativo collina", "solo licenza bar", "senza piazzale"]):
                return None

            urls = item_dict.get("urls", {})
            ad_url = urls.get("default") or urls.get("mobile") or ""

            # Estrazione Prezzo
            features = item_dict.get("features", {})
            price_val = None
            price_str = ""
            price_feat = features.get("/price", {})
            if price_feat and price_feat.get("values"):
                pv = price_feat["values"][0]
                price_str = pv.get("value", "")
                try:
                    price_val = float(pv.get("key", 0))
                except (ValueError, TypeError):
                    price_val = None

            # Estrazione Superficie (mq)
            size_val = None
            size_feat = features.get("/size", {})
            if size_feat and size_feat.get("values"):
                sv = size_feat["values"][0]
                try:
                    size_val = float(sv.get("key", 0))
                except (ValueError, TypeError):
                    size_val = None

            # Se la superficie non è nei metadati strutturati, o è molto piccola (<200 mq per un capannone che cita un piazzale)
            # cerchiamo la metratura reale dell'area esterna nel testo
            text_size = self._extract_size_from_text(f"{subject} {body}")
            if text_size and (size_val is None or text_size > size_val):
                size_val = text_size

            # Dati geografici
            geo = item_dict.get("geo", {})
            region_name = geo.get("region", {}).get("value", "")
            province_name = geo.get("city", {}).get("value", "")
            town_name = geo.get("town", {}).get("value", "")

            # Coordinate e Mappa
            lat, lon = None, None
            address_str = ""
            geo_source = ""
            
            map_data = geo.get("map", {})
            if map_data:
                address_str = map_data.get("address", "")
                try:
                    if map_data.get("latitude") and map_data.get("longitude"):
                        lat = float(map_data["latitude"])
                        lon = float(map_data["longitude"])
                        geo_source = "portal_map"
                except (ValueError, TypeError):
                    pass

            # Inserzionista
            adv = item_dict.get("advertiser", {})
            advertiser_name = adv.get("name", "")
            is_company = adv.get("company", False)

            # Immagine principale
            images = item_dict.get("images", [])
            image_url = ""
            if images and isinstance(images, list):
                first_img = images[0]
                if isinstance(first_img, dict):
                    image_url = first_img.get("scale", [{}])[-1].get("uri", "")

            # Tipologia contratto
            ad_type = item_dict.get("type", {}).get("value", "").lower()
            if "affitto" in ad_type:
                contract = "affitto"
            elif "vendita" in ad_type:
                contract = "vendita"
            else:
                contract = default_contract

            category_label = item_dict.get("category", {}).get("label", "Commerciale")

            return ListingSite(
                id=urn,
                title=subject,
                url=ad_url,
                description=body,
                price=price_val,
                price_str=price_str,
                size_mq=size_val,
                contract_type=contract,
                category=category_label,
                region=region_name,
                province=province_name,
                town=town_name,
                address=address_str,
                latitude=lat,
                longitude=lon,
                geo_source=geo_source,
                advertiser=advertiser_name,
                is_company=is_company,
                date_posted=item_dict.get("date", ""),
                image_url=image_url
            )
        except Exception as e:
            logger.debug(f"Errore parsing annuncio: {e}")
            return None

    def search(
        self,
        query: str = "piazzale",
        category: str = "uffici-locali-commerciali",
        contract_type: str = "vendita",
        region: Optional[str] = None,
        max_pages: int = 3,
        min_mq: Optional[int] = MIN_SURFACE_MQ
    ) -> List[ListingSite]:
        """
        Esegue la ricerca su Subito.it con gestione della paginazione.
        """
        results: List[ListingSite] = []
        seen_ids = set()

        for page in range(1, max_pages + 1):
            url = self._build_search_url(query, category, contract_type, region, page)
            logger.info(f"[SubitoScraper] Pagina {page}/{max_pages} -> {url}")
            
            try:
                resp = self.client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"Status HTTP {resp.status_code} su {url}")
                    break

                soup = BeautifulSoup(resp.text, "html.parser")
                next_data_script = soup.find("script", id="__NEXT_DATA__")
                if not next_data_script or not next_data_script.string:
                    logger.warning(f"Script __NEXT_DATA__ non trovato su {url}")
                    break

                data = json.loads(next_data_script.string)
                items_obj = (
                    data.get("props", {})
                    .get("pageProps", {})
                    .get("initialState", {})
                    .get("items", {})
                )

                raw_items = items_obj.get("originalList", [])
                if not raw_items:
                    logger.info("Nessun altro annuncio trovato nella pagina.")
                    break

                for raw in raw_items:
                    # In Subito, a volte l'oggetto è annidato in raw["item"] o direttamente in raw
                    item_dict = raw.get("item", raw)
                    site = self._parse_item(item_dict, contract_type)
                    if not site:
                        continue

                    # Filtro superficie minima (se specificata)
                    if min_mq and site.size_mq and site.size_mq < min_mq:
                        continue

                    if site.id not in seen_ids:
                        seen_ids.add(site.id)
                        results.append(site)

                # Se ci sono meno elementi della pagina o abbiamo raggiunto l'ultima
                total_pages = items_obj.get("totalPages", 1)
                if page >= total_pages:
                    logger.info(f"Raggiunta l'ultima pagina disponibile ({total_pages}).")
                    break

                time.sleep(self.request_delay)

            except Exception as e:
                logger.error(f"Errore durante lo scraping di {url}: {e}")
                break

        logger.info(f"[SubitoScraper] Totale annunci estratti per '{query}': {len(results)}")
        return results

    def close(self):
        self.client.close()
