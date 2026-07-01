"""
Arme Fatale — Générateur PPTX
Génère des présentations PowerPoint à partir des données de projet parsées.
"""

import os
import tempfile
import logging
from typing import Dict, List, Any, Optional
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image

logger = logging.getLogger(__name__)

# SCHMIDT brand colors
SCHMIDT_COLORS = {
    'dark_grey': RGBColor(0x33, 0x33, 0x33),
    'medium_grey': RGBColor(0x66, 0x66, 0x66),
    'light_grey': RGBColor(0xF5, 0xF5, 0xF5),
    'white': RGBColor(0xFF, 0xFF, 0xFF),
    'orange': RGBColor(0xE8, 0x6A, 0x1E),
    'orange_light': RGBColor(0xF5, 0xB0, 0x6B),
    'black': RGBColor(0x1A, 0x1A, 0x1A),
    'accent_blue': RGBColor(0x2C, 0x5F, 0x8A),
}

# Slide dimensions (16:9 widescreen)
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)


class PPTXGenerator:
    """
    Générateur de présentations PPTX pour SCHMIDT.
    
    Crée une présentation complète avec:
    - Page de couverture (client, projet, date)
    - Vue d'ensemble du plan
    - Renders 3D photoréalistes
    - Vues linéaires (étagères)
    - Liste des meubles avec références
    - Section plan de travail
    - Section électroménager (BSH)
    - Section sanitaire (Franke)
    - Finitions et couleurs
    - Page de clôture
    """

    def __init__(self, catalog_manager=None, image_handler=None):
        self.catalog = catalog_manager
        self.image_handler = image_handler

    def generate(self, project: Dict[str, Any], images: List[Any], options: Dict[str, Any]) -> str:
        """
        Generate a PPTX presentation from project data.
        
        Args:
            project: Parsed project data from InSituXMLParser
            images: List of image dicts with 'path', 'name', 'type'
            options: Generation options
            
        Returns:
            Path to the generated PPTX file
        """
        prs = Presentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT

        # Use blank layout
        blank_layout = prs.slide_layouts[6]

        # --- Slide 1: Cover page ---
        self._add_cover_slide(prs, blank_layout, project)

        # --- Slide 2: Project overview ---
        self._add_overview_slide(prs, blank_layout, project)

        # --- Slide 3+: 3D renders ---
        render_images = [img for img in images if img.get('type') == 'render' or 'render' in img.get('name', '').lower() or '3d' in img.get('name', '').lower()]
        if not render_images:
            # If no specific renders identified, use first few images
            render_images = images[:4]
        self._add_render_slides(prs, blank_layout, project, render_images)

        # --- Slide: Linéaires ---
        lineaire_images = [img for img in images if 'lineaire' in img.get('name', '').lower() or 'shelf' in img.get('name', '').lower() or 'rang' in img.get('name', '').lower()]
        if lineaire_images:
            self._add_lineaire_slides(prs, blank_layout, project, lineaire_images)

        # --- Slide: Cabinet list ---
        if project.get('cabinets'):
            self._add_cabinet_list_slide(prs, blank_layout, project)

        # --- Slide: Finishes ---
        if project.get('finishes'):
            self._add_finishes_slide(prs, blank_layout, project)

        # --- Slide: Worktops ---
        if project.get('worktops'):
            self._add_worktop_slide(prs, blank_layout, project)

        # --- Slide: Appliances (BSH) ---
        if project.get('appliances'):
            self._add_appliance_slide(prs, blank_layout, project)

        # --- Slide: Sinks & Faucets (Franke) ---
        if project.get('sinks') or project.get('faucets'):
            self._add_sanitaire_slide(prs, blank_layout, project)

        # --- Slide: Closing ---
        self._add_closing_slide(prs, blank_layout, project)

        # Save
        output_dir = tempfile.gettempdir()
        client_name = project.get('client', {}).get('name', 'client').replace(' ', '_')
        output_path = os.path.join(output_dir, f"Presentation_{client_name}.pptx")
        prs.save(output_path)

        logger.info(f"PPTX generated: {output_path}")
        return output_path

    def _add_background(self, slide, color=RGBColor(0xFF, 0xFF, 0xFF)):
        """Set slide background color."""
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = color

    def _add_textbox(self, slide, left, top, width, height, text, font_size=18,
                     color=RGBColor(0x33, 0x33, 0x33), bold=False, alignment=PP_ALIGN.LEFT,
                     font_name='Arial'):
        """Add a text box to a slide."""
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.font.bold = bold
        p.font.name = font_name
        p.alignment = alignment
        return txBox

    def _add_rect(self, slide, left, top, width, height, fill_color, line_color=None):
        """Add a rectangle shape."""
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
        if line_color:
            shape.line.color.rgb = line_color
        else:
            shape.line.fill.background()
        return shape

    def _add_image_safe(self, slide, image_path, left, top, width, height):
        """Add an image to a slide, handling errors gracefully."""
        try:
            if os.path.exists(image_path):
                slide.shapes.add_picture(image_path, left, top, width, height)
                return True
            else:
                logger.warning(f"Image not found: {image_path}")
                # Add placeholder
                self._add_rect(slide, left, top, width, height, SCHMIDT_COLORS['light_grey'])
                self._add_textbox(slide, left, top, width, height, "Image non disponible",
                                  font_size=14, color=SCHMIDT_COLORS['medium_grey'],
                                  alignment=PP_ALIGN.CENTER)
                return False
        except Exception as e:
            logger.error(f"Error adding image {image_path}: {e}")
            return False

    def _add_cover_slide(self, prs, layout, project):
        """Add the cover page slide."""
        slide = prs.slides.add_slide(layout)
        self._add_background(slide, SCHMIDT_COLORS['dark_grey'])

        # Orange accent bar
        self._add_rect(slide, Inches(0), Inches(0), Inches(0.3), SLIDE_HEIGHT, SCHMIDT_COLORS['orange'])

        # SCHMIDT logo placeholder
        self._add_textbox(slide, Inches(1), Inches(0.8), Inches(4), Inches(0.6),
                         "SCHMIDT", font_size=28, color=SCHMIDT_COLORS['white'], bold=True)

        # Client name
        client_name = project.get('client', {}).get('name', 'Client')
        self._add_textbox(slide, Inches(1), Inches(2.5), Inches(11), Inches(1),
                         f"Projet Cuisine — {client_name}",
                         font_size=36, color=SCHMIDT_COLORS['white'], bold=True)

        # Project reference
        ref = project.get('project_info', {}).get('reference', '')
        if ref:
            self._add_textbox(slide, Inches(1), Inches(3.8), Inches(6), Inches(0.5),
                             f"Référence : {ref}",
                             font_size=16, color=SCHMIDT_COLORS['orange_light'])

        # Date
        date = project.get('project_info', {}).get('date', '')
        if date:
            self._add_textbox(slide, Inches(1), Inches(4.3), Inches(6), Inches(0.5),
                             f"Date : {date}",
                             font_size=16, color=SCHMIDT_COLORS['orange_light'])

        # Store name
        store = project.get('project_info', {}).get('store', 'SCHMIDT Augny')
        self._add_textbox(slide, Inches(1), Inches(6.5), Inches(6), Inches(0.5),
                         store,
                         font_size=14, color=SCHMIDT_COLORS['medium_grey'])

    def _add_overview_slide(self, prs, layout, project):
        """Add project overview slide."""
        slide = prs.slides.add_slide(layout)
        self._add_background(slide, SCHMIDT_COLORS['white'])

        # Title bar
        self._add_rect(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(1), SCHMIDT_COLORS['dark_grey'])
        self._add_textbox(slide, Inches(0.5), Inches(0.2), Inches(12), Inches(0.6),
                         "Vue d'ensemble du projet",
                         font_size=24, color=SCHMIDT_COLORS['white'], bold=True)

        # Project details
        y = Inches(1.5)
        details = [
            ("Client", project.get('client', {}).get('name', '')),
            ("Adresse", project.get('client', {}).get('address', '')),
            ("Téléphone", project.get('client', {}).get('phone', '')),
            ("Référence", project.get('project_info', {}).get('reference', '')),
            ("Commercial", project.get('project_info', {}).get('commercial', '')),
        ]

        for label, value in details:
            if value:
                self._add_textbox(slide, Inches(0.5), y, Inches(3), Inches(0.4),
                                 label, font_size=14, color=SCHMIDT_COLORS['medium_grey'], bold=True)
                self._add_textbox(slide, Inches(3.5), y, Inches(8), Inches(0.4),
                                 value, font_size=14, color=SCHMIDT_COLORS['dark_grey'])
                y += Inches(0.5)

        # Room info
        rooms = project.get('rooms', [])
        if rooms:
            y += Inches(0.3)
            self._add_textbox(slide, Inches(0.5), y, Inches(12), Inches(0.4),
                             "Dimensions de la pièce",
                             font_size=16, color=SCHMIDT_COLORS['orange'], bold=True)
            y += Inches(0.5)
            for room in rooms:
                room_text = f"{room.get('name', 'Cuisine')}: "
                dims = []
                if room.get('length'): dims.append(f"L: {room['length']}")
                if room.get('width'): dims.append(f"l: {room['width']}")
                if room.get('height'): dims.append(f"H: {room['height']}")
                room_text += " × ".join(dims) if dims else "N/A"
                self._add_textbox(slide, Inches(1), y, Inches(10), Inches(0.4),
                                 room_text, font_size=14, color=SCHMIDT_COLORS['dark_grey'])
                y += Inches(0.4)

    def _add_render_slides(self, prs, layout, project, images):
        """Add 3D render slides."""
        if not images:
            # Add placeholder slide
            slide = prs.slides.add_slide(layout)
            self._add_background(slide, SCHMIDT_COLORS['white'])
            self._add_rect(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(1), SCHMIDT_COLORS['dark_grey'])
            self._add_textbox(slide, Inches(0.5), Inches(0.2), Inches(12), Inches(0.6),
                             "Perspectives 3D",
                             font_size=24, color=SCHMIDT_COLORS['white'], bold=True)
            self._add_textbox(slide, Inches(2), Inches(3), Inches(9), Inches(1),
                             "Aucun visuel 3D disponible",
                             font_size=18, color=SCHMIDT_COLORS['medium_grey'],
                             alignment=PP_ALIGN.CENTER)
            return

        # One or two images per slide
        images_per_slide = 1 if len(images) <= 2 else 2

        for i in range(0, len(images), images_per_slide):
            slide = prs.slides.add_slide(layout)
            self._add_background(slide, SCHMIDT_COLORS['white'])

            # Title bar
            self._add_rect(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(1), SCHMIDT_COLORS['dark_grey'])
            self._add_textbox(slide, Inches(0.5), Inches(0.2), Inches(12), Inches(0.6),
                             f"Perspective 3D — Vue {i // images_per_slide + 1}",
                             font_size=24, color=SCHMIDT_COLORS['white'], bold=True)

            # Add images
            batch = images[i:i + images_per_slide]
            if len(batch) == 1:
                # Single large image
                img = batch[0]
                img_path = img.get('path', img) if isinstance(img, dict) else img
                self._add_image_safe(slide, img_path, Inches(1), Inches(1.3), Inches(11.3), Inches(5.8))
            else:
                # Two images side by side
                for j, img in enumerate(batch):
                    img_path = img.get('path', img) if isinstance(img, dict) else img
                    left = Inches(0.5 + j * 6.3)
                    self._add_image_safe(slide, img_path, left, Inches(1.3), Inches(5.8), Inches(5.8))

    def _add_lineaire_slides(self, prs, layout, project, images):
        """Add linéaire (shelf) view slides."""
        slide = prs.slides.add_slide(layout)
        self._add_background(slide, SCHMIDT_COLORS['white'])

        # Title bar
        self._add_rect(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(1), SCHMIDT_COLORS['dark_grey'])
        self._add_textbox(slide, Inches(0.5), Inches(0.2), Inches(12), Inches(0.6),
                         "Linéaires — Vues détaillées",
                         font_size=24, color=SCHMIDT_COLORS['white'], bold=True)

        # Add images in grid
        for i, img in enumerate(images[:4]):
            img_path = img.get('path', img) if isinstance(img, dict) else img
            row = i // 2
            col = i % 2
            left = Inches(0.5 + col * 6.3)
            top = Inches(1.3 + row * 3)
            self._add_image_safe(slide, img_path, left, top, Inches(5.8), Inches(2.8))

    def _add_cabinet_list_slide(self, prs, layout, project):
        """Add cabinet list slide with table."""
        slide = prs.slides.add_slide(layout)
        self._add_background(slide, SCHMIDT_COLORS['white'])

        # Title bar
        self._add_rect(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(1), SCHMIDT_COLORS['dark_grey'])
        self._add_textbox(slide, Inches(0.5), Inches(0.2), Inches(12), Inches(0.6),
                         "Liste des meubles",
                         font_size=24, color=SCHMIDT_COLORS['white'], bold=True)

        cabinets = project.get('cabinets', [])
        if not cabinets:
            self._add_textbox(slide, Inches(2), Inches(3), Inches(9), Inches(1),
                             "Aucun meuble dans le projet",
                             font_size=18, color=SCHMIDT_COLORS['medium_grey'],
                             alignment=PP_ALIGN.CENTER)
            return

        # Create table
        rows = min(len(cabinets) + 1, 12)  # Header + max 11 rows
        cols = 5
        left = Inches(0.5)
        top = Inches(1.3)
        width = Inches(12.3)
        height = Inches(5.5)

        table = slide.shapes.add_table(rows, cols, left, top, width, height).table

        # Set column widths
        table.columns[0].width = Inches(2)
        table.columns[1].width = Inches(2.5)
        table.columns[2].width = Inches(2)
        table.columns[3].width = Inches(1.5)
        table.columns[4].width = Inches(4.3)

        # Header row
        headers = ['Référence', 'Type', 'Largeur', 'Qté', 'Description']
        for i, header in enumerate(headers):
            cell = table.cell(0, i)
            cell.text = header
            cell.fill.solid()
            cell.fill.fore_color.rgb = SCHMIDT_COLORS['dark_grey']
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(12)
                p.font.color.rgb = SCHMIDT_COLORS['white']
                p.font.bold = True

        # Data rows
        for i, cabinet in enumerate(cabinets[:11]):
            row_idx = i + 1
            values = [
                cabinet.get('reference', ''),
                cabinet.get('type', ''),
                cabinet.get('width', ''),
                cabinet.get('quantity', '1'),
                cabinet.get('description', ''),
            ]
            for j, value in enumerate(values):
                cell = table.cell(row_idx, j)
                cell.text = str(value)
                cell.fill.solid()
                cell.fill.fore_color.rgb = SCHMIDT_COLORS['light_grey'] if i % 2 == 0 else SCHMIDT_COLORS['white']
                for p in cell.text_frame.paragraphs:
                    p.font.size = Pt(11)
                    p.font.color.rgb = SCHMIDT_COLORS['dark_grey']

    def _add_finishes_slide(self, prs, layout, project):
        """Add finishes/colors slide."""
        slide = prs.slides.add_slide(layout)
        self._add_background(slide, SCHMIDT_COLORS['white'])

        # Title bar
        self._add_rect(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(1), SCHMIDT_COLORS['dark_grey'])
        self._add_textbox(slide, Inches(0.5), Inches(0.2), Inches(12), Inches(0.6),
                         "Finitions & Portes",
                         font_size=24, color=SCHMIDT_COLORS['white'], bold=True)

        finishes = project.get('finishes', [])
        for i, finish in enumerate(finishes[:6]):
            row = i // 3
            col = i % 3
            left = Inches(0.5 + col * 4.2)
            top = Inches(1.5 + row * 2.8)

            # Color swatch placeholder
            self._add_rect(slide, left, top, Inches(3.8), Inches(2), SCHMIDT_COLORS['light_grey'],
                          SCHMIDT_COLORS['medium_grey'])

            # Finish code
            self._add_textbox(slide, left, top + Inches(0.3), Inches(3.8), Inches(0.5),
                             finish.get('code', ''),
                             font_size=20, color=SCHMIDT_COLORS['dark_grey'], bold=True,
                             alignment=PP_ALIGN.CENTER)

            # Finish name
            self._add_textbox(slide, left, top + Inches(0.9), Inches(3.8), Inches(0.5),
                             finish.get('name', ''),
                             font_size=16, color=SCHMIDT_COLORS['medium_grey'],
                             alignment=PP_ALIGN.CENTER)

            # Category
            self._add_textbox(slide, left, top + Inches(1.4), Inches(3.8), Inches(0.4),
                             finish.get('category', ''),
                             font_size=12, color=SCHMIDT_COLORS['orange'],
                             alignment=PP_ALIGN.CENTER)

    def _add_worktop_slide(self, prs, layout, project):
        """Add worktop/countertop slide."""
        slide = prs.slides.add_slide(layout)
        self._add_background(slide, SCHMIDT_COLORS['white'])

        # Title bar
        self._add_rect(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(1), SCHMIDT_COLORS['dark_grey'])
        self._add_textbox(slide, Inches(0.5), Inches(0.2), Inches(12), Inches(0.6),
                         "Plan de travail",
                         font_size=24, color=SCHMIDT_COLORS['white'], bold=True)

        worktops = project.get('worktops', [])
        for i, wt in enumerate(worktops[:4]):
            y = Inches(1.5 + i * 1.3)

            # Material name
            self._add_textbox(slide, Inches(0.5), y, Inches(4), Inches(0.5),
                             wt.get('name', wt.get('material', '')),
                             font_size=20, color=SCHMIDT_COLORS['dark_grey'], bold=True)

            # Type
            self._add_textbox(slide, Inches(4.5), y, Inches(3), Inches(0.5),
                             wt.get('type', ''),
                             font_size=16, color=SCHMIDT_COLORS['orange'])

            # Dimensions
            dims = []
            if wt.get('length'): dims.append(f"L: {wt['length']}")
            if wt.get('width'): dims.append(f"l: {wt['width']}")
            if wt.get('thickness'): dims.append(f"é: {wt['thickness']}")
            if dims:
                self._add_textbox(slide, Inches(7.5), y, Inches(5), Inches(0.5),
                                 " × ".join(dims),
                                 font_size=14, color=SCHMIDT_COLORS['medium_grey'])

            # Reference
            if wt.get('reference'):
                self._add_textbox(slide, Inches(0.5), y + Inches(0.5), Inches(8), Inches(0.4),
                                 f"Référence: {wt['reference']}",
                                 font_size=12, color=SCHMIDT_COLORS['medium_grey'])

    def _add_appliance_slide(self, prs, layout, project):
        """Add appliance (electroménager) slide."""
        slide = prs.slides.add_slide(layout)
        self._add_background(slide, SCHMIDT_COLORS['white'])

        # Title bar
        self._add_rect(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(1), SCHMIDT_COLORS['dark_grey'])
        self._add_textbox(slide, Inches(0.5), Inches(0.2), Inches(12), Inches(0.6),
                         "Électroménager",
                         font_size=24, color=SCHMIDT_COLORS['white'], bold=True)

        # BSH logo placeholder
        self._add_textbox(slide, Inches(11), Inches(0.2), Inches(2), Inches(0.6),
                         "BSH", font_size=16, color=SCHMIDT_COLORS['orange_light'], bold=True,
                         alignment=PP_ALIGN.RIGHT)

        appliances = project.get('appliances', [])
        if not appliances:
            self._add_textbox(slide, Inches(2), Inches(3), Inches(9), Inches(1),
                             "Aucun électroménager dans le projet",
                             font_size=18, color=SCHMIDT_COLORS['medium_grey'],
                             alignment=PP_ALIGN.CENTER)
            return

        # Create table
        rows = min(len(appliances) + 1, 10)
        cols = 4
        left = Inches(0.5)
        top = Inches(1.3)
        width = Inches(12.3)
        height = Inches(5.5)

        table = slide.shapes.add_table(rows, cols, left, top, width, height).table

        # Column widths
        table.columns[0].width = Inches(2.5)
        table.columns[1].width = Inches(2)
        table.columns[2].width = Inches(3)
        table.columns[3].width = Inches(4.8)

        # Header
        headers = ['Type', 'Marque', 'Modèle', 'Description']
        for i, header in enumerate(headers):
            cell = table.cell(0, i)
            cell.text = header
            cell.fill.solid()
            cell.fill.fore_color.rgb = SCHMIDT_COLORS['dark_grey']
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(12)
                p.font.color.rgb = SCHMIDT_COLORS['white']
                p.font.bold = True

        # Data
        for i, app in enumerate(appliances[:9]):
            row_idx = i + 1
            values = [
                app.get('type', ''),
                app.get('brand', ''),
                app.get('model', ''),
                app.get('description', ''),
            ]
            for j, value in enumerate(values):
                cell = table.cell(row_idx, j)
                cell.text = str(value)
                cell.fill.solid()
                cell.fill.fore_color.rgb = SCHMIDT_COLORS['light_grey'] if i % 2 == 0 else SCHMIDT_COLORS['white']
                for p in cell.text_frame.paragraphs:
                    p.font.size = Pt(11)
                    p.font.color.rgb = SCHMIDT_COLORS['dark_grey']

    def _add_sanitaire_slide(self, prs, layout, project):
        """Add sink & faucet (sanitaire) slide."""
        slide = prs.slides.add_slide(layout)
        self._add_background(slide, SCHMIDT_COLORS['white'])

        # Title bar
        self._add_rect(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(1), SCHMIDT_COLORS['dark_grey'])
        self._add_textbox(slide, Inches(0.5), Inches(0.2), Inches(12), Inches(0.6),
                         "Sanitaire — Évier & Mitigeur",
                         font_size=24, color=SCHMIDT_COLORS['white'], bold=True)

        # Franke logo placeholder
        self._add_textbox(slide, Inches(11), Inches(0.2), Inches(2), Inches(0.6),
                         "FRANKE", font_size=16, color=SCHMIDT_COLORS['orange_light'], bold=True,
                         alignment=PP_ALIGN.RIGHT)

        y = Inches(1.5)

        # Sinks
        sinks = project.get('sinks', [])
        if sinks:
            self._add_textbox(slide, Inches(0.5), y, Inches(12), Inches(0.5),
                             "Éviers",
                             font_size=18, color=SCHMIDT_COLORS['orange'], bold=True)
            y += Inches(0.6)
            for sink in sinks[:3]:
                text = f"• {sink.get('brand', 'Franke')} {sink.get('model', '')} — {sink.get('material', '')} ({sink.get('bowls', '?')} bac(s))"
                self._add_textbox(slide, Inches(1), y, Inches(11), Inches(0.4),
                                 text, font_size=14, color=SCHMIDT_COLORS['dark_grey'])
                y += Inches(0.4)
            y += Inches(0.3)

        # Faucets
        faucets = project.get('faucets', [])
        if faucets:
            self._add_textbox(slide, Inches(0.5), y, Inches(12), Inches(0.5),
                             "Mitigeurs / Robinetterie",
                             font_size=18, color=SCHMIDT_COLORS['orange'], bold=True)
            y += Inches(0.6)
            for faucet in faucets[:3]:
                text = f"• {faucet.get('brand', 'Franke')} {faucet.get('model', '')} — {faucet.get('finish', '')}"
                self._add_textbox(slide, Inches(1), y, Inches(11), Inches(0.4),
                                 text, font_size=14, color=SCHMIDT_COLORS['dark_grey'])
                y += Inches(0.4)

    def _add_closing_slide(self, prs, layout, project):
        """Add closing slide."""
        slide = prs.slides.add_slide(layout)
        self._add_background(slide, SCHMIDT_COLORS['dark_grey'])

        # Orange accent bar
        self._add_rect(slide, Inches(0), Inches(0), Inches(0.3), SLIDE_HEIGHT, SCHMIDT_COLORS['orange'])

        # Thank you
        self._add_textbox(slide, Inches(1), Inches(2.5), Inches(11), Inches(1),
                         "Merci pour votre confiance",
                         font_size=36, color=SCHMIDT_COLORS['white'], bold=True)

        # Store info
        store = project.get('project_info', {}).get('store', 'SCHMIDT Augny')
        self._add_textbox(slide, Inches(1), Inches(4), Inches(8), Inches(0.5),
                         store,
                         font_size=18, color=SCHMIDT_COLORS['orange_light'])

        # Commercial
        commercial = project.get('project_info', {}).get('commercial', '')
        if commercial:
            self._add_textbox(slide, Inches(1), Inches(4.5), Inches(8), Inches(0.5),
                             f"Votre conseiller : {commercial}",
                             font_size=16, color=SCHMIDT_COLORS['medium_grey'])

        # Contact
        self._add_textbox(slide, Inches(1), Inches(6), Inches(8), Inches(0.5),
                         "SCHMIDT — Cuisiniste depuis 1959",
                         font_size=14, color=SCHMIDT_COLORS['medium_grey'])
