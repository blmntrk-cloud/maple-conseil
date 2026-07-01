"""
Arme Fatale — Parseur XML In Situ (format réel validé)
"""
import os, logging
from lxml import etree
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class InSituXMLParser:
    """Parseur pour les fichiers XML d'export In Situ."""

    FINISH_CODES = {
        '7H': {'name': 'Laquée', 'category': 'laque'},
        '7S': {'name': 'Satin', 'category': 'mat'},
        '7C': {'name': 'Laquée couleur', 'category': 'laque'},
        '5C': {'name': 'Chêne', 'category': 'wood'},
        '5E': {'name': 'Frêne', 'category': 'wood'},
        '5P': {'name': 'Pin', 'category': 'wood'},
        '5S': {'name': 'Sapin', 'category': 'wood'},
        '5O': {'name': 'Olivier', 'category': 'wood'},
        '2E': {'name': 'Érable', 'category': 'wood'},
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
        'FOX': {'name': 'Fox', 'category': 'wood'},
        'EVE': {'name': 'Everest', 'category': 'wood'},
        'SLO': {'name': 'Sloane', 'category': 'wood'},
        'TRZ': {'name': 'Terra', 'category': 'wood'},
        'UPD': {'name': 'Updoor', 'category': 'wood'},
        'VAO': {'name': 'Vao', 'category': 'wood'},
        'MUR': {'name': 'Muron', 'category': 'wood'},
        'MGN': {'name': 'Magnon', 'category': 'wood'},
        'MLH': {'name': 'Mahler', 'category': 'wood'},
        'MRM': {'name': 'Maron', 'category': 'wood'},
        'MVL': {'name': 'Mavel', 'category': 'wood'},
        'NGR': {'name': 'Nogaro', 'category': 'wood'},
        'POK': {'name': 'Poker', 'category': 'wood'},
        'RAN': {'name': 'Ranch', 'category': 'wood'},
        'RCG': {'name': 'Racing', 'category': 'wood'},
        'SOG': {'name': 'Sogn', 'category': 'wood'},
        'VSN': {'name': 'Vision', 'category': 'wood'},
        'LVT': {'name': 'Levant', 'category': 'wood'},
        'MLA': {'name': 'Malaga', 'category': 'wood'},
        'MEX': {'name': 'Mexique', 'category': 'wood'},
        'HAR': {'name': 'Harrison', 'category': 'wood'},
        'ICL': {'name': 'Icon', 'category': 'wood'},
        'KGY': {'name': 'Kongo', 'category': 'wood'},
        'CAM': {'name': 'Camden', 'category': 'wood'},
        'CLT': {'name': 'Clifton', 'category': 'wood'},
        'CLY': {'name': 'Clay', 'category': 'wood'},
        'EMS': {'name': 'Emerson', 'category': 'wood'},
        'ETG': {'name': 'Eton', 'category': 'wood'},
        'GTA': {'name': 'Gatsby', 'category': 'wood'},
        'LIK': {'name': 'Lincoln', 'category': 'wood'},
        'LIN': {'name': 'Lindon', 'category': 'wood'},
        'LOR': {'name': 'Lormont', 'category': 'wood'},
        'LOT': {'name': 'Loton', 'category': 'wood'},
        'MOO': {'name': 'Moon', 'category': 'wood'},
        'NSO': {'name': 'Nordic Oak', 'category': 'wood'},
        'NSR': {'name': 'Nordic Stone', 'category': 'wood'},
        'NVY': {'name': 'Navy', 'category': 'wood'},
        'OKA': {'name': 'Oka', 'category': 'wood'},
        'OXB': {'name': 'Oxford Blue', 'category': 'wood'},
        'OXR': {'name': 'Oxford Red', 'category': 'wood'},
        'SCA': {'name': 'Scala', 'category': 'wood'},
        'SVC': {'name': 'Savannah', 'category': 'wood'},
        'TAV': {'name': 'Tavor', 'category': 'wood'},
        'TBC': {'name': 'Tabac', 'category': 'wood'},
        'TOK': {'name': 'Tokyo', 'category': 'wood'},
        'TWI': {'name': 'Twist', 'category': 'wood'},
        'UPL': {'name': 'Upland', 'category': 'wood'},
        'BA7': {'name': 'Basalt', 'category': 'wood'},
        'BKR': {'name': 'Bark', 'category': 'wood'},
        'BOK': {'name': 'Boker', 'category': 'wood'},
        'BRK': {'name': 'Brick', 'category': 'wood'},
        'BWK': {'name': 'Brewer', 'category': 'wood'},
        'CAY': {'name': 'Cayenne', 'category': 'wood'},
        'CBA': {'name': 'Cuba', 'category': 'wood'},
        'CGC': {'name': 'Congo', 'category': 'wood'},
        'CRL': {'name': 'Carlton', 'category': 'wood'},
        'JUN': {'name': 'Juniper', 'category': 'wood'},
        'AIR': {'name': 'Air', 'category': 'wood'},
        'AMA': {'name': 'Amalfi', 'category': 'wood'},
        'ARM': {'name': 'Armor', 'category': 'wood'},
        'AUS': {'name': 'Austin', 'category': 'wood'},
        'AVE': {'name': 'Avenue', 'category': 'wood'},
        'ACO': {'name': 'Acoma', 'category': 'wood'},
        'Sen': {'name': 'Senja', 'category': 'wood'},
        'BOT': {'name': 'Botanic', 'category': 'wood'},
    }

    HANDLE_CODES = {
        '8O': 'Poignée bouton', '8I': 'Poignée intégrée', '8J': 'Poignée profil',
        '8L': 'Poignée coquille', '8M': 'Poignée manette', '8P': 'Poignée tube',
        '8Q': 'Poignée carrée', '8T': 'Poignée T', '9A': 'Poignée barre alu',
        '9G': 'Poignée barre inox', '9I': 'Poignée intégrée G', '9U': 'Poignée U',
        '9X': 'Poignée X design', '9Z': 'Poignée Z', '91': 'Poignée 1',
        '92': 'Poignée 2', '93': 'Poignée 3', '96': 'Poignée 6',
        '65H': 'Poignée 65H (horizontale)', '65V': 'Poignée 65V (verticale)',
        '499': 'Pas de poignée', 'LLL': 'Laqué laiton et laiton antique',
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
        'SUT': {'name': 'Plan de travail standard', 'type': 'stratifié'},
    }

    LAYER_MAPPING = {
        'Meubles bas': {'category': 'Meuble bas'},
        'Meubles hauts': {'category': 'Meuble haut'},
        'Armoires': {'category': 'Meuble colonne'},
        'Panneaux': {'category': 'Panneau / Joue'},
        'Socle': {'category': 'Socle'},
        'Plaques': {'category': 'Plaque de cuisson'},
        'Froid': {'category': 'Réfrigération'},
        'Lave-vaisselle': {'category': 'Lave-vaisselle'},
        'Aspiration': {'category': 'Hotte / Aspiration'},
        'Accessoires': {'category': 'Accessoire'},
        'Four': {'category': 'Four'},
        'Robinet': {'category': 'Robinet'},
        'Evier': {'category': 'Évier'},
    }

    def parse(self, xml_path):
        if not os.path.exists(xml_path):
            raise FileNotFoundError(f"XML file not found: {xml_path}")
        tree = etree.parse(xml_path)
        root = tree.getroot()
        logger.info(f"XML root: {root.tag}, attribs: {dict(root.attrib)}")
        return {
            'source_file': os.path.basename(xml_path),
            'scene_code': root.get('Code', ''),
            'scene_name': root.get('Name', ''),
            'client': self._extract_client(root),
            'seller': self._extract_seller(root),
            'project_info': self._extract_project_info(root),
            'prices': self._extract_prices(root),
            'items': self._extract_all_items(root),
            'cabinets': self._extract_cabinets(root),
            'finishes': self._extract_finishes(root),
            'handles': self._extract_handles(root),
            'worktops': self._extract_worktops(root),
            'appliances': self._extract_appliances(root),
            'sanitary': self._extract_sanitary(root),
            'technical_docs': self._extract_technical_docs(root),
            'financing': self._extract_financing(root),
            'details': self._extract_all_details(root),
        }

    def _get_text(self, root, tag):
        el = root.find(tag)
        return el.text.strip() if el is not None and el.text else None

    def _extract_client(self, root):
        fn = self._get_text(root, 'CustomerFirstName') or ''
        ln = self._get_text(root, 'CustomerName') or ''
        return {
            'name': ln, 'first_name': fn,
            'address': self._get_text(root, 'CustomerAddress1') or '',
            'zip_code': self._get_text(root, 'CustomerZipCode') or '',
            'city': self._get_text(root, 'CustomerCity') or '',
            'phone': self._get_text(root, 'CustomerTel1') or '',
            'email': self._get_text(root, 'CustomerEmail') or '',
            'full_name': ' '.join(filter(None, [fn, ln])),
        }

    def _extract_seller(self, root):
        fn = self._get_text(root, 'SellerFirstName') or ''
        ln = self._get_text(root, 'SellerName') or ''
        return {
            'name': ln, 'first_name': fn,
            'initials': self._get_text(root, 'SellerInitials') or '',
            'full_name': ' '.join(filter(None, [fn, ln])),
        }

    def _extract_project_info(self, root):
        subject = root.find('Subject')
        return {
            'name': root.get('Name', ''), 'code': root.get('Code', ''),
            'subject': subject.text if subject is not None else '',
            'subject_code': subject.get('Code', '') if subject is not None else '',
        }

    def _extract_prices(self, root):
        prices = {}
        for sp in root.findall('SellPrice'):
            key = f"{sp.get('Type', '')}_{'with_tax' if sp.get('WithTax') == '1' else 'without_tax'}"
            prices[key] = sp.text or '0'
        for heading in root.findall('.//Heading'):
            hname = heading.get('Name', '')
            for sp in heading.findall('SellPrice'):
                key = f"{hname}_{sp.get('Type', '')}_{'with_tax' if sp.get('WithTax') == '1' else 'without_tax'}"
                prices[key] = sp.text or '0'
        return prices

    def _extract_all_items(self, root):
        items = []
        for item in root.findall('.//Item'):
            dx = item.find('Dx'); dy = item.find('Dy'); dz = item.find('Dz')
            topic = item.find('Topic'); layer = item.find('Layer')
            desc = item.find('Description'); qty = item.find('Quantity')
            prices = {}
            for sp in item.findall('SellPrice'):
                key = f"{sp.get('Type', '')}_{'ttc' if sp.get('WithTax') == '1' else 'ht'}"
                prices[key] = sp.text or '0'
            item_details = []
            for d in item.findall('Detail'):
                c = d.find('Code'); n = d.find('Name')
                item_details.append({'type': d.get('Type', ''), 'title': d.get('Title', ''),
                    'code': c.text if c is not None else '', 'name': n.text if n is not None else ''})
            items.append({
                'reference': item.get('Reference', ''), 'key_ref': item.get('KeyRef', ''),
                'description': desc.text if desc is not None else '',
                'quantity': qty.text if qty is not None else '1',
                'dimensions': {'dx': dx.text if dx is not None else '', 'dy': dy.text if dy is not None else '', 'dz': dz.text if dz is not None else ''},
                'topic': topic.text if topic is not None else '',
                'layer': layer.text if layer is not None else '',
                'prices': prices, 'details': item_details,
            })
        return items

    def _extract_cabinets(self, root):
        cabinets = []
        for item in root.findall('.//Item'):
            topic = item.find('Topic')
            if topic is None or topic.text != 'Mobilier de cuisine': continue
            ref = item.get('Reference', '')
            desc = item.find('Description'); layer = item.find('Layer'); qty = item.find('Quantity')
            dx = item.find('Dx'); dy = item.find('Dy'); dz = item.find('Dz')
            price_ttc = None
            for sp in item.findall('SellPrice'):
                if sp.get('Type') == 'Net' and sp.get('WithTax') == '1': price_ttc = sp.text; break
            finish_code = finish_name = ''
            for d in item.findall('Detail'):
                title = d.get('Title', ''); c = d.find('Code'); n = d.find('Name')
                code = c.text if c is not None else ''; name = n.text if n is not None else ''
                if 'Coloris façade' in title or 'Coloris tour' in title:
                    finish_code = code; finish_name = name
                elif 'Coloris caisson' in title and not finish_code:
                    finish_code = code; finish_name = name
            layer_text = layer.text if layer is not None else ''
            cabinets.append({
                'reference': ref, 'type': self._decode_cabinet_type(ref, layer_text),
                'layer': layer_text, 'description': desc.text if desc is not None else '',
                'quantity': qty.text if qty is not None else '1',
                'width': dx.text if dx is not None else '', 'height': dz.text if dz is not None else '',
                'depth': dy.text if dy is not None else '', 'price_ttc': price_ttc,
                'finish_code': finish_code, 'finish_name': finish_name,
            })
        return cabinets

    def _decode_cabinet_type(self, ref, layer):
        info = self.LAYER_MAPPING.get(layer, {})
        if info: return info['category']
        if not ref: return 'Inconnu'
        p = ref[0].upper()
        return {'B': 'Meuble bas', 'H': 'Meuble haut', 'A': 'Meuble colonne', 'P': 'Panneau', 'S': 'Socle'}.get(p, 'Meuble')

    def _extract_finishes(self, root):
        finishes = []; seen = set()
        for d in root.findall('.//Detail'):
            title = d.get('Title', '')
            if not any(k in title.lower() for k in ['coloris façade', 'coloris tour', 'coloris caisson', 'coloris panneaux']): continue
            c = d.find('Code'); n = d.find('Name')
            code = c.text if c is not None else ''; name = n.text if n is not None else ''
            if code and code not in seen and code != '___':
                seen.add(code)
                known = self.FINISH_CODES.get(code, {})
                finishes.append({'code': code, 'name': name or known.get('name', f'Finition {code}'), 'category': known.get('category', 'unknown')})
        return finishes

    def _extract_handles(self, root):
        handles = []; seen = set()
        for d in root.findall('.//Detail'):
            title = d.get('Title', '')
            if 'poignée' not in title.lower() and 'poignee' not in title.lower(): continue
            c = d.find('Code'); n = d.find('Name')
            code = c.text if c is not None else ''; name = n.text if n is not None else ''
            if code and code not in seen and code != '499':
                seen.add(code)
                handles.append({'code': code, 'name': self.HANDLE_CODES.get(code, name or f'Poignée {code}')})
        return handles

    def _extract_worktops(self, root):
        worktops = []
        for item in root.findall('.//Item'):
            ref = item.get('Reference', '')
            layer_el = item.find('Layer'); layer = layer_el.text if layer_el is not None else ''
            desc = item.find('Description'); desc_text = desc.text if desc is not None else ''
            is_wt = False; mat_code = ''; mat_name = ''
            for d in item.findall('Detail'):
                title = d.get('Title', ''); c = d.find('Code'); n = d.find('Name')
                code = c.text if c is not None else ''; name = n.text if n is not None else ''
                if 'Panneau' in title and code == 'SUT': is_wt = True
                if 'Coloris' in title and 'panneau' in title.lower(): mat_code = code; mat_name = name
            for key, info in self.WORKTOP_MATERIALS.items():
                if key.lower() in ref.lower(): is_wt = True; mat_code = key; mat_name = info['name']; break
            if is_wt or (layer == 'Panneaux' and 'JOUE' not in desc_text.upper() and 'SOCLE' not in desc_text.upper()):
                dx = item.find('Dx'); dy = item.find('Dy'); dz = item.find('Dz')
                known = None
                for key, info in self.WORKTOP_MATERIALS.items():
                    if key.lower() == mat_code.lower() or key.lower() in mat_name.lower(): known = info; break
                worktops.append({
                    'reference': ref, 'material_code': mat_code, 'material_name': mat_name,
                    'name': known['name'] if known else mat_name or 'Plan de travail',
                    'type': known['type'] if known else 'unknown', 'description': desc_text,
                    'thickness': dz.text if dz is not None else '', 'width': dx.text if dx is not None else '',
                    'length': dy.text if dy is not None else '',
                })
        return worktops

    def _extract_appliances(self, root):
        appliances = []
        for item in root.findall('.//Item'):
            topic = item.find('Topic')
            if topic is None or topic.text != 'Electroménager': continue
            ref = item.get('Reference', '')
            desc = item.find('Description'); layer = item.find('Layer')
            desc_text = desc.text if desc is not None else ''
            layer_text = layer.text if layer is not None else ''
            price_ttc = None
            for sp in item.findall('SellPrice'):
                if sp.get('Type') == 'Net' and sp.get('WithTax') == '1': price_ttc = sp.text; break
            brand = self._detect_brand(desc_text)
            cat = self.LAYER_MAPPING.get(layer_text, {}).get('category', layer_text)
            appliances.append({'reference': ref, 'category': cat, 'layer': layer_text, 'description': desc_text, 'brand': brand, 'price_ttc': price_ttc})
        return appliances

    def _detect_brand(self, desc):
        dl = desc.lower()
        for k, b in {'bosch': 'Bosch', 'siemens': 'Siemens', 'neff': 'Neff', 'gaggenau': 'Gaggenau', 'samsung': 'Samsung', 'lg ': 'LG', 'miele': 'Miele', 'elica': 'Elica', 'franke': 'Franke'}.items():
            if k in dl: return b
        return ''

    def _extract_sanitary(self, root):
        sanitary = []
        for item in root.findall('.//Item'):
            topic = item.find('Topic')
            if topic is None or topic.text != 'Sanitaires': continue
            ref = item.get('Reference', '')
            desc = item.find('Description'); layer = item.find('Layer')
            desc_text = desc.text if desc is not None else ''
            price_ttc = None
            for sp in item.findall('SellPrice'):
                if sp.get('Type') == 'Net' and sp.get('WithTax') == '1': price_ttc = sp.text; break
            t = 'Sanitaire'
            if 'robinet' in desc_text.lower() or 'mitigeur' in desc_text.lower(): t = 'Robinet'
            elif 'evier' in desc_text.lower() or 'évier' in desc_text.lower(): t = 'Évier'
            sanitary.append({'reference': ref, 'type': t, 'layer': layer.text if layer is not None else '', 'description': desc_text, 'price_ttc': price_ttc})
        return sanitary

    def _extract_technical_docs(self, root):
        docs = {'plan_name': '', 'views': []}
        for td in root.findall('.//TechnicalDocument'):
            fn = td.find('TechnicalPlanFileName')
            if fn is not None: docs['plan_name'] = fn.text or ''
            for v in td.findall('Vue'):
                vt = v.find('Type'); vf = v.find('FileName'); vs = v.find('ScaleFactor')
                docs['views'].append({
                    'type': vt.text if vt is not None else '', 'file_name': vf.text if vf is not None else '',
                    'scale': vs.text if vs is not None else '',
                })
        return docs

    def _extract_financing(self, root):
        financing = []
        for bb in root.findall('.//BillBook'):
            term = bb.get('Term', ''); term_date = ''
            if term and len(term) == 8:
                try: term_date = datetime.strptime(term, '%Y%m%d').strftime('%d/%m/%Y')
                except: term_date = term
            financing.append({'code': bb.get('Code', ''), 'name': bb.get('Name', ''), 'percentage': bb.get('Percentage', ''), 'term': term, 'term_date': term_date, 'amount': bb.text or '0'})
        return financing

    def _extract_all_details(self, root):
        details = []; seen = set()
        for d in root.findall('.//Detail'):
            c = d.find('Code'); n = d.find('Name')
            code = c.text if c is not None else ''; name = n.text if n is not None else ''
            key = f"{d.get('Title', '')}|{code}|{name}"
            if key not in seen:
                seen.add(key)
                details.append({'type': d.get('Type', ''), 'title': d.get('Title', ''), 'code': code, 'name': name})
        return details

    def parse_summary(self, project):
        c = project.get('client', {}); s = project.get('seller', {})
        lines = [f"Client: {c.get('full_name', 'N/A')}", f"Vendeur: {s.get('full_name', 'N/A')}",
                 f"Projet: {project.get('scene_name', 'N/A')}",
                 f"Meubles: {len(project.get('cabinets', []))}", f"Finitions: {len(project.get('finishes', []))}",
                 f"Poignées: {len(project.get('handles', []))}", f"Électroménager: {len(project.get('appliances', []))}",
                 f"Plans de travail: {len(project.get('worktops', []))}", f"Sanitaire: {len(project.get('sanitary', []))}"]
        for k, v in project.get('prices', {}).items():
            lines.append(f"Prix {k}: {v} EUR")
        return '\n'.join(lines)