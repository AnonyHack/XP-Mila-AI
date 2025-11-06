import random
from typing import List
from loguru import logger
from utils.image_generator import image_generator
from config import STATIC_IMAGES, DEFAULT_IMAGES

class ImageGallery:
    def __init__(self):
        self.static_images = STATIC_IMAGES
        self.default_images = DEFAULT_IMAGES

    async def get_image(self, category: str = None, user_input: str = None, use_ai: bool = True) -> str:
        """Get image - try AI generation first, then fallback to static images"""
        try:
            # Try AI generation if enabled
            if use_ai:
                ai_image = await image_generator.generate_for_category(category, user_input)
                if ai_image:
                    logger.info("✅ Using AI generated image")
                    return ai_image
                else:
                    logger.warning("⚠️ AI generation failed, using static image")
            
            # Fallback to static images
            if category and category in self.static_images:
                images = self.static_images[category]
            else:
                # Combine all static images
                images = []
                for cat_images in self.static_images.values():
                    images.extend(cat_images)
            
            if not images:
                images = self.default_images
                
            return random.choice(images)
            
        except Exception as e:
            logger.error(f"❌ Error getting image: {e}")
            return random.choice(self.default_images)

    def get_categories(self) -> List[str]:
        """Get list of available categories"""
        return list(self.static_images.keys())

# Global instance
image_gallery = ImageGallery()