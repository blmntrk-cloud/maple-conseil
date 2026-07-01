"""
Arme Fatale — Parseur XML In Situ
Analyse les fichiers XML exportés du logiciel In Situ et extrait les données du projet cuisine.
"""

import os
import re
import logging
from lxml import etree
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class InSituXMLParser:
    """
    Parseur flexible pour les fichiers XML d'export In Situ.
    
    Le format XML In Situ n'étant pas encore formellement documenté,
    ce parseur est conçu pour être résilient et gérer plusieurs structures
    possibles. Il log des warnings pour les éléments non reconnus.
    """

    # Codes de référence SCHMIDT connus
    CABINET_PREFIXES = {
        'L': {'type': 'Meuble bas', 'category': 'base'},
        'H': {'type': 'Meuble mural', 'category': 'wall'},
        'M': {'type': 'Meuble colonne', 'category': 'tall'},
    }

    FINISH_CODES = {
        '7H': {'name': 'Laquée', 'category': 'laque'},
        '5C': {'name': 'Chêne', 'category': 'wood'},
        '2E': {'name': 'Érable', 'category': 'wood'},
        '7S': {'name': 'Satin', 'category': 'mat'},
        '3P': {'name': 'Plastique', 'category': 'laminate'},
        '5E': {'name': 'Frêne', 'category': 'wood'},
        '5P': {'name': 'Pin', 'category': 'wood'},
        '5S': {'name': 'Sapin', 'category': 'wood'},
        '5O': {'name': 'Olivier', 'category': 'wood'},
        '2K': {'name': 'Chêne clair', 'category': 'wood'},
        '2L': {'name': 'Noyer', 'category': 'wood'},
        '2M': {'name': 'Merisier', 'category': 'wood'},
        '2A': {'name': 'Acajou', 'category': 'wood'},
        '2H': {'name': 'Hêtre', 'category': 'wood'},
        '1C': {'name': 'Chêne massif', 'category': 'wood'},
        '1L': {'name': 'Larche', 'category': 'wood'},
        '1S': {'name': 'Spruce', 'category': 'wood'},
        '1T': {'name': 'Teck', 'category': 'wood'},
        '0N': {'name': 'Noir mat', 'category': 'mat'},
        '0M': {'name': 'Marron', 'category': 'mat'},
    }

    HANDLE_CODES = {
        '8O': 'Poignée bouton',
        '8I': 'Poignée intégrée',
        '8J': 'Poignée profil',
        '8L': 'Poignée coquille',
        '8M': 'Poignée manette',
        '8P': 'Poignée tube',
        '8Q': 'Poignée carrée',
        '8T': 'Poignée T',
        '9A': 'Poignée barre alu',
        '9G': 'Poignée barre inox',
        '9I': 'Poignée intégrée G',
        '9U': 'Poignée U',
        '9X': 'Poignée X design',
        '9Z': 'Poignée Z',
        '91': 'Poignée 1',
        '92': 'Poignée 2',
        '93': 'Poignée 3',
        '96': 'Poignée 6',
    }

    WORKTOP_MATERIALS = {
        'statuario': {'name': 'Statuario', 'type': 'céramique'},
        'portoro': {'name': 'Portoro', 'type': 'céramique'},
        'caliza': {'name': 'Caliza Avorio', 'type': 'céramique'},
        'noir zimbabwe': {'name': 'Noir Zimbabwe', 'type': 'granit'},
        'vermont': {'name': 'Vermont', 'type': 'quartz'},
        'moonstone': {'name': 'Moonstone', 'type': 'quartz'},
        'jurassic grey': {'name': 'Jurassic Grey', 'type': 'quartz'},
        'via lactea': {'name': 'Via Lactea', 'type': 'quartz'},
        'claystone': {'name': 'Claystone', 'type': 'céramique'},
        'avocado': {'name': 'Avocado', 'type': 'quartz'},
        'botanic coral': {'name': 'Botanic Coral', 'type': 'céramique'},
        'iris des marais': {'name': 'Iris des Marais', 'type': 'céramique'},
    }

    def parse(self, xml_path: str) -> Dict[str, Any]:
        """
        Parse an In Situ XML file and return structured project data.
        
        Args:
            xml_path: Path to the XML file
            
        Returns:
            Dict with project data: client, room, cabinets, finishes, appliances, worktops
        """
        if not os.path.exists(xml_path):
            raise FileNotFoundError(f"XML file not found: {xml_path}")

        # Parse XML
        tree = etree.parse(xml_path)
        root = tree.getroot()

        # Log root element for debugging
        logger.info(f"XML root element: {root.tag}")

        # Extract project data with flexible parsing
        project = {
            'source_file': os.path.basename(xml_path),
            'raw_root_tag': root.tag,
            'client': self._extract_client(root),
            'project_info': self._extract_project_info(root),
            'rooms': self._extract_rooms(root),
            'cabinets': self._extract_cabinets(root),
            'finishes': self._extract_finishes(root),
            'handles': self._extract_handles(root),
            'worktops': self._extract_worktops(root),
            'appliances': self._extract_appliances(root),
            'sinks': self._extract_sinks(root),
            'faucets': self._extract_faucets(root),
            'warnings': [],
        }

        # Collect any parsing warnings
        project['warnings'] = logger.warning.call_args_list if hasattr(logger, 'warning') else []

        return project

    def _find_elements(self, root, possible_tags: List[str]) -> List[Any]:
        """Find elements by trying multiple possible tag names."""
        for tag in possible_tags:
            # Try direct children
            elements = root.findall(f'.//{tag}')
            if elements:
                return elements
            # Try with namespace stripping
            elements = root.findall(f'.//{{*}}{tag}')
            if elements:
                return elements
        return []

    def _get_text(self, element, possible_tags: List[str]) -> Optional[str]:
        """Get text from a child element, trying multiple tag names."""
        for tag in possible_tags:
            child = element.find(tag)
            if child is not None and child.text:
                return child.text.strip()
            child = element.find(f'{{*}}{tag}')
            if child is not None and child.text:
                return child.text.strip()
        return None

    def _get_attr(self, element, possible_attrs: List[str]) -> Optional[str]:
        """Get an attribute, trying multiple possible names."""
        for attr in possible_attrs:
            if attr in element.attrib:
                return element.attrib[attr]
        return None

    def _extract_client(self, root) -> Dict[str, Any]:
        """Extract client information from XML."""
        client = {
            'name': '',
            'address': '',
            'phone': '',
            'email': '',
            'reference': '',
        }

        # Try various possible structures
        client_elements = self._find_elements(root, ['client', 'Client', 'customer', 'Customer', 'beneficiaire'])
        if client_elements:
            elem = client_elements[0]
            client['name'] = self._get_text(elem, ['name', 'nom', 'Name', 'Nom', 'fullName', 'raisonSociale']) or ''
            client['address'] = self._get_text(elem, ['address', 'adresse', 'Adresse', 'adresse1']) or ''
            client['phone'] = self._get_text(elem, ['phone', 'telephone', 'tel', 'Telephone']) or ''
            client['email'] = self._get_text(elem, ['email', 'mail', 'Email']) or ''
            client['reference'] = self._get_text(elem, ['reference', 'ref', 'Reference', 'code']) or ''
        else:
            # Try attributes on root
            client['name'] = self._get_attr(root, ['clientName', 'client', 'nomClient']) or ''
            logger.warning("No client element found in XML, trying root attributes")

        return client

    def _extract_project_info(self, root) -> Dict[str, Any]:
        """Extract project metadata."""
        info = {
            'name': '',
            'reference': '',
            'date': '',
            'store': '',
            'commercial': '',
            'version': '',
        }

        project_elements = self._find_elements(root, ['project', 'Project', 'projet', 'Projet', 'dossier', 'Dossier'])
        if project_elements:
            elem = project_elements[0]
            info['name'] = self._get_text(elem, ['name', 'nom', 'Name', 'Nom', 'titre']) or ''
            info['reference'] = self._get_text(elem, ['reference', 'ref', 'Reference', 'code', 'numero']) or ''
            info['date'] = self._get_text(elem, ['date', 'Date', 'dateCreation', 'dateModif']) or ''
            info['store'] = self._get_text(elem, ['store', 'magasin', 'Magasin', 'enseigne']) or ''
            info['commercial'] = self._get_text(elem, ['commercial', 'vendeur', 'Vendeur', 'commercialName']) or ''
            info['version'] = self._get_text(elem, ['version', 'Version']) or ''
        else:
            # Try root attributes
            info['name'] = self._get_attr(root, ['projectName', 'name', 'nom']) or ''
            info['reference'] = self._get_attr(root, ['reference', 'ref', 'code']) or ''

        return info

    def _extract_rooms(self, root) -> List[Dict[str, Any]]:
        """Extract room/layout information."""
        rooms = []
        room_elements = self._find_elements(root, ['room', 'Room', 'piece', 'Piece', 'espace', 'cuisine'])

        for elem in room_elements:
            room = {
                'name': self._get_text(elem, ['name', 'nom', 'Name', 'Nom', 'type']) or 'Cuisine',
                'length': self._get_text(elem, ['length', 'longueur', 'Longueur', 'profondeur']) or '',
                'width': self._get_text(elem, ['width', 'largeur', 'Largeur', 'largeurPiece']) or '',
                'height': self._get_text(elem, ['height', 'hauteur', 'Hauteur', 'hauteurSousPlafond']) or '',
                'shape': self._get_text(elem, ['shape', 'forme', 'Forme']) or '',
            }
            rooms.append(room)

        return rooms

    def _extract_cabinets(self, root) -> List[Dict[str, Any]]:
        """Extract cabinet list with references and dimensions."""
        cabinets = []
        cabinet_elements = self._find_elements(root, ['cabinet', 'Cabinet', 'meuble', 'Meuble', 'element', 'Element', 'module'])

        for elem in cabinet_elements:
            ref = self._get_text(elem, ['reference', 'ref', 'Reference', 'code', 'codeArticle']) or \
                  self._get_attr(elem, ['ref', 'reference', 'code', 'id']) or ''

            decoded = self._decode_cabinet_ref(ref)

            cabinet = {
                'reference': ref,
                'type': decoded['type'],
                'category': decoded['category'],
                'width': self._get_text(elem, ['width', 'largeur', 'Largeur', 'largeurModule']) or decoded['width'],
                'height': self._get_text(elem, ['height', 'hauteur', 'Hauteur']) or '',
                'depth': self._get_text(elem, ['depth', 'profondeur', 'Profondeur']) or '',
                'quantity': self._get_text(elem, ['quantity', 'quantite', 'Quantite', 'qte']) or '1',
                'description': self._get_text(elem, ['description', 'libelle', 'Libelle', 'designation']) or decoded['type'],
                'finish_code': self._get_text(elem, ['finish', 'finition', 'Finition', 'color', 'couleur']) or '',
                'position': self._get_text(elem, ['position', 'Position', 'x', 'posX']) or '',
            }
            cabinets.append(cabinet)

        if not cabinets:
            logger.warning("No cabinet elements found in XML")

        return cabinets

    def _decode_cabinet_ref(self, ref: str) -> Dict[str, Any]:
        """Decode a SCHMIDT cabinet reference code."""
        result = {'type': 'Inconnu', 'category': 'unknown', 'width': ''}

        if not ref or len(ref) < 2:
            return result

        prefix = ref[0].upper()
        if prefix in self.CABINET_PREFIXES:
            info = self.CABINET_PREFIXES[prefix]
            result['type'] = info['type']
            result['category'] = info['category']

            # Try to decode width from second character
            if len(ref) > 1 and ref[1].isdigit():
                width_cm = int(ref[1]) * 10
                result['width'] = f"{width_cm} mm"

        return result

    def _extract_finishes(self, root) -> List[Dict[str, Any]]:
        """Extract finish/door/color information."""
        finishes = []
        finish_elements = self._find_elements(root, ['finish', 'Finish', 'finition', 'Finition', 'color', 'Color', 'porte', 'Porte'])

        for elem in finish_elements:
            code = self._get_text(elem, ['code', 'Code', 'reference', 'ref']) or \
                   self._get_attr(elem, ['code', 'ref', 'reference']) or ''
            name = self._get_text(elem, ['name', 'nom', 'Nom', 'libelle']) or ''

            # Look up in known codes
            known = self.FINISH_CODES.get(code.upper(), {})
            if known and not name:
                name = known['name']

            finishes.append({
                'code': code,
                'name': name or f'Finition {code}',
                'category': known.get('category', 'unknown'),
            })

        return finishes

    def _extract_handles(self, root) -> List[Dict[str, Any]]:
        """Extract handle information."""
        handles = []
        handle_elements = self._find_elements(root, ['handle', 'Handle', 'poignee', 'Poignee', 'accessoire'])

        for elem in handle_elements:
            code = self._get_text(elem, ['code', 'Code', 'reference', 'ref']) or \
                   self._get_attr(elem, ['code', 'ref']) or ''
            name = self.HANDLE_CODES.get(code.upper(), f'Poignée {code}')

            handles.append({
                'code': code,
                'name': name,
                'quantity': self._get_text(elem, ['quantity', 'quantite', 'qte']) or '1',
            })

        return handles

    def _extract_worktops(self, root) -> List[Dict[str, Any]]:
        """Extract worktop/countertop information."""
        worktops = []
        worktop_elements = self._find_elements(root, ['worktop', 'Worktop', 'plan', 'Plan', 'planTravail', 'countertop', 'planDeTravail'])

        for elem in worktop_elements:
            material = self._get_text(elem, ['material', 'materiau', 'Materiau', 'type', 'Type']) or ''
            color = self._get_text(elem, ['color', 'couleur', 'Couleur']) or ''
            ref = self._get_text(elem, ['reference', 'ref', 'Reference', 'code']) or ''

            # Look up material
            material_lower = material.lower()
            known_material = None
            for key, info in self.WORKTOP_MATERIALS.items():
                if key in material_lower or material_lower in key:
                    known_material = info
                    break

            worktops.append({
                'material': material,
                'name': known_material['name'] if known_material else material or 'Plan de travail',
                'type': known_material['type'] if known_material else 'unknown',
                'color': color,
                'reference': ref,
                'length': self._get_text(elem, ['length', 'longueur', 'Longueur']) or '',
                'width': self._get_text(elem, ['width', 'largeur', 'Largeur']) or '',
                'thickness': self._get_text(elem, ['thickness', 'epaisseur', 'Epaisseur']) or '',
            })

        return worktops

    def _extract_appliances(self, root) -> List[Dict[str, Any]]:
        """Extract appliance/electroménager information."""
        appliances = []
        appliance_elements = self._find_elements(root, ['appliance', 'Appliance', 'electromenager', 'Electromenager', 'appareil', 'Appareil'])

        for elem in appliance_elements:
            ref = self._get_text(elem, ['reference', 'ref', 'Reference', 'code', 'codeArticle']) or \
                  self._get_attr(elem, ['ref', 'reference', 'code']) or ''
            appliance_type = self._get_text(elem, ['type', 'Type', 'category', 'categorie']) or ''
            brand = self._get_text(elem, ['brand', 'marque', 'Marque']) or ''
            model = self._get_text(elem, ['model', 'modele', 'Modele']) or ''

            appliances.append({
                'reference': ref,
                'type': appliance_type,
                'brand': brand,
                'model': model,
                'description': self._get_text(elem, ['description', 'libelle', 'designation']) or '',
            })

        return appliances

    def _extract_sinks(self, root) -> List[Dict[str, Any]]:
        """Extract sink information."""
        sinks = []
        sink_elements = self._find_elements(root, ['sink', 'Sink', 'evier', 'Evier'])

        for elem in sink_elements:
            sinks.append({
                'reference': self._get_text(elem, ['reference', 'ref', 'code']) or '',
                'brand': self._get_text(elem, ['brand', 'marque']) or 'Franke',
                'model': self._get_text(elem, ['model', 'modele']) or '',
                'material': self._get_text(elem, ['material', 'materiau']) or '',
                'bowls': self._get_text(elem, ['bowls', 'bacs', 'nombreBacs']) or '',
            })

        return sinks

    def _extract_faucets(self, root) -> List[Dict[str, Any]]:
        """Extract faucet/mitigeur information."""
        faucets = []
        faucet_elements = self._find_elements(root, ['faucet', 'Faucet', 'mitigeur', 'Mitigeur', 'robinet', 'Robinet'])

        for elem in faucet_elements:
            faucets.append({
                'reference': self._get_text(elem, ['reference', 'ref', 'code']) or '',
                'brand': self._get_text(elem, ['brand', 'marque']) or 'Franke',
                'model': self._get_text(elem, ['model', 'modele']) or '',
                'finish': self._get_text(elem, ['finish', 'finition']) or '',
            })

        return faucets

    def parse_summary(self, project: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the parsed project."""
        lines = []
        lines.append(f"Client: {project['client']['name']}")
        lines.append(f"Projet: {project['project_info']['name']}")
        lines.append(f"Pièces: {len(project['rooms'])}")
        lines.append(f"Meubles: {len(project['cabinets'])}")
        lines.append(f"Finitions: {len(project['finishes'])}")
        lines.append(f"Plans de travail: {len(project['worktops'])}")
        lines.append(f"Électroménager: {len(project['appliances'])}")
        lines.append(f"Éviers: {len(project['sinks'])}")
        lines.append(f"Mitigeurs: {len(project['faucets'])}")
        return '\n'.join(lines)
