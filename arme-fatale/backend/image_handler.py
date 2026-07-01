"""
Arme Fatale — Gestionnaire d'images
Traitement, classification et redimensionnement d'images pour les slides PPTX.
"""

import os
import logging
from PIL import Image as PILImage
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}

# Slide placeholder dimensions (in pixels at 96 DPI)
SLIDE_DIMENSIONS = {
    'full': (1280, 720),      # Full slide image
    'half': (640, 720),      # Half slide (side by side)
    'quarter': (640, 360),   # Quarter slide (2x2 grid)
    'thumbnail': (320, 180), # Thumbnail
}


class ImageHandler:
    """Gestionnaire d'images pour redimensionnement et classification."""

    def classify_image(self, image_path: str) -> str:
        """
        Classify an image based on its filename and dimensions.
        
        Returns:
            'render' for 3D perspective renders
            'lineaire' for shelf/row views
            'plan' for 2D plans
            'other' for other images
        """
        filename = os.path.basename(image_path).lower()

        if 'render' in filename or '3d' in filename or 'perspective' in filename or 'vue' in filename:
            return 'render'
        elif 'lineaire' in filename or 'shelf' in filename or 'rang' in filename or 'linear' in filename:
            return 'lineaire'
        elif 'plan' in filename or 'top' in filename or 'vue_de_dessus' in filename:
            return 'plan'
        else:
            return 'other'

    def resize_for_slide(self, image_path: str, target_type: str = 'full') -> Optional[str]:
        """
        Resize an image to fit a slide placeholder.
        
        Args:
            image_path: Path to the source image
            target_type: One of 'full', 'half', 'quarter', 'thumbnail'
            
        Returns:
            Path to the resized image, or None on error
        """
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return None

        target_size = SLIDE_DIMENSIONS.get(target_type, SLIDE_DIMENSIONS['full'])

        try:
            with PILImage.open(image_path) as img:
                # Convert to RGB if necessary (for WEBP or RGBA)
                if img.mode in ('RGBA', 'P', 'LA'):
                    img = img.convert('RGB')

                # Resize maintaining aspect ratio (contain)
                img.thumbnail(target_size, PILImage.LANCZOS)

                # Save resized image
                base, ext = os.path.splitext(image_path)
                resized_path = f"{base}_resized{ext}"
                img.save(resized_path, quality=95)

                return resized_path
        except Exception as e:
            logger.error(f"Error resizing image {image_path}: {e}")
            return None

    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """Get image metadata."""
        if not os.path.exists(image_path):
            return {'error': 'File not found'}

        try:
            with PILImage.open(image_path) as img:
                return {
                    'path': image_path,
                    'filename': os.path.basename(image_path),
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size_bytes': os.path.getsize(image_path),
                    'classification': self.classify_image(image_path),
                }
        except Exception as e:
            return {'error': str(e)}

    def validate_image(self, image_path: str) -> bool:
        """Check if a file is a valid image."""
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in SUPPORTED_FORMATS:
            return False

        try:
            with PILImage.open(image_path) as img:
                img.verify()
            return True
        except Exception:
            return False
