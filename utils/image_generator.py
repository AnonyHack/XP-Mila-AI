import aiohttp
import random
import json
import asyncio
from loguru import logger
from typing import Optional
from config import POLLINATIONS_IMAGE_BASE_URL, AI_IMAGE_PROMPTS, AI_IMAGE_STYLE_MODIFIERS, AI_IMAGE_DEFAULT_WIDTH, AI_IMAGE_DEFAULT_HEIGHT

class PollinationsImageGenerator:
    def __init__(self):
        self.base_url = POLLINATIONS_IMAGE_BASE_URL
        self.default_prompts = AI_IMAGE_PROMPTS
        self.style_modifiers = AI_IMAGE_STYLE_MODIFIERS
        self.default_width = AI_IMAGE_DEFAULT_WIDTH
        self.default_height = AI_IMAGE_DEFAULT_HEIGHT

    def build_prompt(self, category: str = None, user_input: str = None) -> str:
        """Build an image generation prompt"""
        try:
            if category and category in self.default_prompts:
                base_prompt = random.choice(self.default_prompts[category])
            else:
                # Combine all prompts for random selection
                all_prompts = []
                for prompts in self.default_prompts.values():
                    all_prompts.extend(prompts)
                base_prompt = random.choice(all_prompts)
            
            # Add style modifier
            style = random.choice(self.style_modifiers)
            
            # If user provided specific request, incorporate it
            if user_input and len(user_input) < 50:  # Only use if it's not too long
                enhanced_prompt = f"{user_input}, {base_prompt}, {style}"
            else:
                enhanced_prompt = f"{base_prompt}, {style}"
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error building prompt: {e}")
            return "cute anime girl, kawaii style, pastel colors, soft lighting, high quality"

    async def generate_image(self, prompt: str, width: int = None, height: int = None) -> Optional[str]:
        """Generate image using Pollinations.ai API"""
        try:
            # Use defaults if not specified
            if width is None:
                width = self.default_width
            if height is None:
                height = self.default_height
            
            # Clean and encode the prompt
            clean_prompt = prompt.replace(' ', '%20')
            
            # Build the API URL
            url = f"{self.base_url}/prompt/{clean_prompt}"
            
            # Add parameters
            params = {
                "width": width,
                "height": height,
                "nofetch": "true",
                "seed": random.randint(1, 1000000)  # Random seed for variety
            }
            
            logger.info(f"🖼️ Generating image with prompt: {prompt}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        # Pollinations returns the image directly
                        image_url = str(response.url)
                        logger.success(f"✅ Image generated successfully: {image_url}")
                        return image_url
                    else:
                        logger.error(f"❌ API returned status {response.status}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("❌ Image generation timeout")
            return None
        except Exception as e:
            logger.error(f"❌ Image generation error: {e}")
            return None

    async def generate_for_category(self, category: str = None, user_input: str = None) -> Optional[str]:
        """Generate image for specific category"""
        prompt = self.build_prompt(category, user_input)
        return await self.generate_image(prompt)

# Global instance

image_generator = PollinationsImageGenerator()
