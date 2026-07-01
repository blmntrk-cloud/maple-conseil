# Arme Fatale — Générateur de présentations clients SCHMIDT

## Vue d'ensemble

**Arme Fatale** est un outil logiciel local qui génère automatiquement des présentations commerciales clients à partir des exports XML du logiciel **In Situ** utilisé par les magasins SCHMIDT.

### Workflow
1. **Importer** un fichier XML In Situ (données du projet cuisine)
2. **Importer** un dossier de visuels photoréalistes (renders 3D, linéaires)
3. **Générer** une présentation PPTX prête à présenter au client

## Architecture

```
arme-fatale/
├── backend/
│   ├── app.py                  # Serveur Flask (API REST)
│   ├── xml_parser.py           # Parseur XML In Situ
│   ├── pptx_generator.py       # Générateur PPTX (python-pptx)
│   ├── catalog.py              # Catalogues BSH & Franke
│   ├── image_handler.py        # Traitement et redimensionnement d'images
│   └── data/
│       ├── bsh_catalog.json    # Catalogue électroménager BSH
│       └── franke_catalog.json # Catalogue sanitaire Franke
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Application React
│   │   ├── components/
│   │   │   ├── FileUpload.tsx       # Drag & drop XML + images
│   │   │   ├── ProjectPreview.tsx   # Aperçu du projet parsé
│   │   │   ├── SlidePreview.tsx     # Aperçu des slides générées
│   │   │   └── GenerateButton.tsx   # Bouton de génération
│   │   └── api/
│   │       └── client.ts       # Client API
│   └── package.json
├── templates/
│   └── (template PPTX généré programmatiquement)
└── README.md
```

## Stack technique

- **Backend** : Python 3.11+, Flask, python-pptx, lxml, Pillow
- **Frontend** : React 18, TypeScript, Tailwind CSS
- **Déploiement** : Local (chaque magasin), pas de serveur central

## Installation

```bash
# Backend
cd backend
pip install -r requirements.txt
python app.py

# Frontend (dans un autre terminal)
cd frontend
npm install
npm run dev
```

L'application est accessible sur `http://localhost:5173` (frontend) et `http://localhost:5000` (API).

## Codes de référence SCHMIDT

### Types de meubles
| Préfixe | Type | Largeur |
|---------|------|---------|
| L | Meuble bas | 1er chiffre × 10 cm |
| H | Meuble mural | 1er chiffre × 10 cm |
| M | Meuble colonne | 1er chiffre × 10 cm |

### Finitions / Portes
| Code | Désignation |
|------|-------------|
| 7H | Laquée |
| 5C | Chêne |
| 2E | Érable |
| 7S | Satin |
| 3P | Plastique |

### Poignées
| Code | Type |
|------|------|
| 8O | Poignée bouton |
| 8I | Poignée intégrée |
| 8J | Poignée profil |
| 9A | Poignée barre |

### Plans de travail
| Matériau | Référence |
|----------|-----------|
| Statuario | KSXSTEA |
| Portoro | KSXPORA |
| Caliza Avorio | — |
| Noir Zimbabwe | — |
| Vermont | — |

## Catalogues intégrés

### BSH (Bosch / Siemens / Gaggenau / Neff)
- Fours encastrables
- Hottes
- Réfrigérateurs
- Lave-vaisselle

### Franke
- Éviers
- Mitigeurs / Robinetterie

## Évolution prévue

- [ ] Intégration du vrai template PPTX "COPIE - COLLER ARME FATALE SCH 2025"
- [ ] Parsing complet du format XML In Situ (en attente de l'exemple réel)
- [ ] Catalogues BSH et Franke complets
- [ ] Module de tarification
- [ ] Export PDF en plus du PPTX
- [ ] Mode sombre / clair

## Licence

Propriétaire — SCHMIDT Augny
