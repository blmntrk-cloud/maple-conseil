"""
Arme Fatale — Gestionnaire de catalogues BSH & Franke
Recherche de produits par référence dans les catalogues électroménager et sanitaire.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

CATALOG_DIR = os.path.join(os.path.dirname(__file__), 'data')


class CatalogManager:
    """Gestionnaire des catalogues BSH et Franke."""

    def __init__(self):
        self.bsh_catalog = self._load_catalog('bsh_catalog.json')
        self.franke_catalog = self._load_catalog('franke_catalog.json')

    def _load_catalog(self, filename: str) -> Dict[str, Any]:
        """Load a catalog JSON file."""
        path = os.path.join(CATALOG_DIR, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        logger.warning(f"Catalog file not found: {path}")
        return {'products': []}

    def get_bsh_catalog(self) -> Dict[str, Any]:
        """Return the full BSH catalog."""
        return self.bsh_catalog

    def get_franke_catalog(self) -> Dict[str, Any]:
        """Return the full Franke catalog."""
        return self.franke_catalog

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search across all catalogs by reference code or name."""
        results = []
        query_lower = query.lower()

        # Search BSH
        for product in self.bsh_catalog.get('products', []):
            if (query_lower in product.get('reference', '').lower() or
                query_lower in product.get('name', '').lower() or
                query_lower in product.get('brand', '').lower()):
                product['catalog'] = 'BSH'
                results.append(product)

        # Search Franke
        for product in self.franke_catalog.get('products', []):
            if (query_lower in product.get('reference', '').lower() or
                query_lower in product.get('name', '').lower() or
                query_lower in product.get('brand', '').lower()):
                product['catalog'] = 'Franke'
                results.append(product)

        return results

    def lookup_bsh(self, reference: str) -> Optional[Dict[str, Any]]:
        """Look up a BSH product by reference."""
        for product in self.bsh_catalog.get('products', []):
            if product.get('reference', '').upper() == reference.upper():
                return product
        return None

    def lookup_franke(self, reference: str) -> Optional[Dict[str, Any]]:
        """Look up a Franke product by reference."""
        for product in self.franke_catalog.get('products', []):
            if product.get('reference', '').upper() == reference.upper():
                return product
        return None
