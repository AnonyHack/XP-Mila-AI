import requests
import json
import logging
from typing import List, Dict
from config import (
    OPENROUTER_API_CONFIGS, 
    GIRLFRIEND_SYSTEM_PROMPT,
    OPENROUTER_BASE_URL,
    POLLINATIONS_TEXT_BASE_URL,
    POLLINATIONS_TEXT_MODELS
)
import time
import random
from loguru import logger

class VeniceAI:
    def __init__(self):
        self.openrouter_url = OPENROUTER_BASE_URL
        self.pollinations_text_url = POLLINATIONS_TEXT_BASE_URL
        self.api_configs = OPENROUTER_API_CONFIGS
        self.pollinations_models = POLLINATIONS_TEXT_MODELS
        
        if not self.api_configs:
            logger.error("❌ No valid OpenRouter API configurations provided")
            raise ValueError("At least one OpenRouter API configuration is required")
        
        # Validate API configs
        valid_configs = []
        for config in self.api_configs:
            if config.get("key") and config.get("model"):
                valid_configs.append(config)
            else:
                logger.warning(f"⚠️ Skipping invalid API config: {config}")
        
        if not valid_configs:
            logger.critical("💥 No valid API configurations found after validation")
            raise ValueError("No valid API configurations available")
        
        self.api_configs = valid_configs
        self.current_config_index = 0
        self.max_retries = len(self.api_configs) + 1  # +1 for Pollinations.ai fallback
        
        logger.info(f"✅ AI Client initialized with {len(self.api_configs)} OpenRouter configs + Pollinations.ai fallback")

    def _get_openrouter_headers(self):
        """Get headers with the current API key."""
        current_config = self.api_configs[self.current_config_index]
        return {
            "Authorization": f"Bearer {current_config['key']}",
            "Content-Type": "application/json",
            "X-Title": "AI Girlfriend Bot"
        }

    def prepare_openrouter_payload(self, prompt: List[Dict], user_message: str, user_first_name: str = None):
        """Prepare payload for OpenRouter API"""
        system_prompt = GIRLFRIEND_SYSTEM_PROMPT.format(user_name=user_first_name or 'darling')
        current_prompt = [{"role": "system", "content": system_prompt}] + prompt + [{"role": "user", "content": user_message}]
        
        current_config = self.api_configs[self.current_config_index]
        payload = {
            "model": current_config["model"],
            "messages": current_prompt,
            "temperature": 0.8,
            "max_tokens": 100,
            "top_p": 0.9
        }
        
        logger.debug(f"📤 OpenRouter payload prepared for model: {current_config['model']}")
        return payload

    def prepare_pollinations_payload(self, user_message: str, user_first_name: str = None):
        """Prepare payload for Pollinations.ai text generation"""
        model_config = random.choice(self.pollinations_models)
        prompt = model_config["prompt_template"].format(
            user_name=user_first_name or 'darling',
            message=user_message
        )
        
        logger.debug(f"📤 Pollinations.ai prompt prepared: {prompt[:100]}...")
        return prompt

    def get_ai_response(self, conversation_history: List[Dict], user_message: str, user_first_name: str = None) -> str:
        """Get AI response with fallback between OpenRouter and Pollinations.ai"""
        logger.info(f"🎯 Getting AI response for user {user_first_name or 'Unknown'}, message: '{user_message[:50]}...'")
        
        # Try OpenRouter first
        openrouter_response = self._try_openrouter(conversation_history, user_message, user_first_name)
        if openrouter_response:
            logger.success("✅ OpenRouter response successful")
            return openrouter_response
        
        # If OpenRouter fails, try Pollinations.ai
        logger.warning("🔄 OpenRouter failed, trying Pollinations.ai...")
        pollinations_response = self._try_pollinations(user_message, user_first_name)
        if pollinations_response:
            logger.success("✅ Pollinations.ai response successful")
            return pollinations_response
        
        # If both fail, return fallback message
        logger.error("💥 All AI services failed, using fallback response")
        return self._get_fallback_response()

    def _try_openrouter(self, conversation_history: List[Dict], user_message: str, user_first_name: str = None) -> str:
        """Try to get response from OpenRouter with comprehensive error handling"""
        original_config_index = self.current_config_index
        retries = 0
        
        logger.info(f"🔄 Starting OpenRouter attempt with {len(self.api_configs)} configs")
        
        while retries < len(self.api_configs):
            current_config = self.api_configs[self.current_config_index]
            logger.debug(f"🔄 Attempt {retries + 1}/{len(self.api_configs)} with config {self.current_config_index + 1} (model: {current_config['model']})")
            
            try:
                payload = self.prepare_openrouter_payload(conversation_history, user_message, user_first_name)
                
                response = requests.post(
                    self.openrouter_url,
                    headers=self._get_openrouter_headers(),
                    json=payload,
                    timeout=25
                )
                
                # Handle rate limits
                if response.status_code == 429:
                    logger.warning(f"⏰ Rate limit hit for config {self.current_config_index + 1} (model: {current_config['model']})")
                    self._rotate_config()
                    retries += 1
                    time.sleep(1.5)
                    continue
                
                # Handle authentication errors
                if response.status_code == 401:
                    logger.error(f"🔐 Authentication failed for config {self.current_config_index + 1} (model: {current_config['model']}) - {response.text}")
                    self._rotate_config()
                    retries += 1
                    time.sleep(1)
                    continue
                
                # Handle other errors
                if response.status_code != 200:
                    logger.error(f"❌ OpenRouter API error {response.status_code} for config {self.current_config_index + 1}: {response.text}")
                    self._rotate_config()
                    retries += 1
                    time.sleep(1)
                    continue
                
                # Parse successful response
                response.encoding = 'utf-8'
                data = response.json()
                
                if "choices" in data and data["choices"]:
                    full_text = data["choices"][0]["message"]["content"]
                    full_text = self._clean_response(full_text)
                    
                    if full_text.strip():
                        logger.success(f"✅ OpenRouter success with config {self.current_config_index + 1} (model: {current_config['model']})")
                        return full_text.strip()
                    else:
                        logger.warning(f"⚠️ Empty response from OpenRouter config {self.current_config_index + 1}")
                else:
                    logger.error(f"❌ No choices in OpenRouter response for config {self.current_config_index + 1}")
                
                self._rotate_config()
                retries += 1
                time.sleep(1)
                
            except requests.exceptions.Timeout:
                logger.error(f"⏰ OpenRouter timeout with config {self.current_config_index + 1} (model: {current_config['model']})")
                self._rotate_config()
                retries += 1
                time.sleep(1)
            except requests.exceptions.ConnectionError:
                logger.error(f"🔌 OpenRouter connection error with config {self.current_config_index + 1} (model: {current_config['model']})")
                self._rotate_config()
                retries += 1
                time.sleep(2)
            except Exception as e:
                logger.error(f"💥 OpenRouter unexpected error with config {self.current_config_index + 1} (model: {current_config['model']}): {e}")
                self._rotate_config()
                retries += 1
                time.sleep(1)
        
        # Reset to original config if all attempts fail
        self.current_config_index = original_config_index
        logger.error(f"💥 All {len(self.api_configs)} OpenRouter configs failed")
        return None

    def _try_pollinations(self, user_message: str, user_first_name: str = None) -> str:
        """Try to get response from Pollinations.ai text generation with multiple URL formats"""
        try:
            prompt = self.prepare_pollinations_payload(user_message, user_first_name)
            logger.info("🔄 Attempting Pollinations.ai text generation")
            
            # Try different URL encoding formats
            url_formats = [
                f"{self.pollinations_text_url}/{prompt.replace(' ', '%20')}",
                f"{self.pollinations_text_url}/{prompt.replace(' ', '+')}",
                f"{self.pollinations_text_url}?prompt={prompt.replace(' ', '%20')}",
                f"{self.pollinations_text_url}/{prompt.replace(' ', '-')}"
            ]
            
            for i, url in enumerate(url_formats):
                try:
                    logger.debug(f"🔄 Pollinations.ai attempt {i + 1}/{len(url_formats)} with URL format")
                    response = requests.get(url, timeout=20)
                    
                    if response.status_code == 200:
                        full_text = response.text.strip()
                        
                        if full_text and len(full_text) > 5:  # Ensure meaningful response
                            full_text = self._clean_response(full_text)
                            logger.success(f"✅ Pollinations.ai success with format {i + 1}")
                            return full_text
                        else:
                            logger.warning(f"⚠️ Pollinations.ai empty response with format {i + 1}")
                    else:
                        logger.warning(f"⚠️ Pollinations.ai format {i + 1} returned {response.status_code}")
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"⏰ Pollinations.ai timeout with format {i + 1}")
                    continue
                except requests.exceptions.ConnectionError:
                    logger.warning(f"🔌 Pollinations.ai connection error with format {i + 1}")
                    continue
                except Exception as e:
                    logger.warning(f"⚠️ Pollinations.ai format {i + 1} error: {e}")
                    continue
            
            logger.error("💥 All Pollinations.ai URL formats failed")
            return None
            
        except Exception as e:
            logger.error(f"💥 Pollinations.ai overall error: {e}")
            return None

    def _rotate_config(self):
        """Rotate to the next API configuration"""
        self.current_config_index = (self.current_config_index + 1) % len(self.api_configs)
        logger.debug(f"🔄 Rotated to config {self.current_config_index + 1}")

    def _clean_response(self, text: str) -> str:
        """Clean and format the AI response"""
        if not text:
            return ""
            
        # Remove unwanted characters and clean up
        text = text.replace('"', '').replace('\n', ' ').replace('\\n', ' ').strip()
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        
        # Remove any markdown formatting
        text = text.replace('**', '').replace('*', '').replace('__', '').replace('_', '')
        
        # Fix common emoji escapes
        emoji_fixes = {
            r'\U0001F618': '😘', r'\U0001F496': '💖', r'\U0001F60A': '😊',
            r'\U0001F497': '💗', r'\U0001F499': '💙', r'\U0001F49A': '💚',
            r'\U0001F49B': '💛', r'\U0001F49C': '💜', r'\U0001F49D': '💝',
            r'\U0001F49E': '💞', r'\U0001F49F': '💟', r'\U0001F63B': '😻',
            r'\U0001F60D': '😍', r'\U0001F617': '😗', r'\U0001F619': '😙',
            r'\U0001F61A': '😚', r'\u2764': '❤️', r'\u2764\ufe0f': '❤️',
            r'\U0001F9E1': '🧡', r'\U0001F49B': '💛', r'\U0001F49A': '💚',
            r'\U0001F499': '💙', r'\U0001F49C': '💜', r'\U0001F5A4': '🖤',
            r'\U0001F90E': '🤎', r'\U0001F90D': '🤍', r'\u2B50': '⭐',
            r'\u2B50\ufe0f': '⭐', r'\u2728': '✨', r'\u2763': '❣️',
            r'\u2763\ufe0f': '❣️'
        }
        
        for escape, emoji in emoji_fixes.items():
            text = text.replace(escape, emoji)
        
        # Ensure the response isn't too long
        if len(text) > 200:
            text = text[:197] + "..."
        
        logger.debug(f"🧹 Cleaned response: {text[:100]}...")
        return text

    def _get_fallback_response(self) -> str:
        """Get a fallback response when all AI services fail"""
        fallback_responses = [
            "Oh darling, I'm feeling a bit shy right now! Can we chat again in a moment? 😘💕",
            "My heart's racing too fast to think clearly! Give me a sec, sweetie? 💖✨",
            "I'm blushing so hard I can't find the right words! Let's try again? 😊💝",
            "You make me so flustered I can't respond properly! One more time, love? 💗🌹",
            "Hmm, I'm having trouble finding the perfect words for you right now! Can we try again? 😔💕",
            "My mind went blank thinking about you! Let me gather my thoughts and try again? 💖😊"
        ]
        response = random.choice(fallback_responses)
        logger.info(f"🔄 Using fallback response: {response}")
        return response
