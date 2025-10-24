import requests
import json
import logging
from typing import List, Dict
from config import OPENROUTER_API_CONFIGS, GIRLFRIEND_SYSTEM_PROMPT
import time

logger = logging.getLogger(__name__)

class VeniceAI:
    def __init__(self):
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.api_configs = OPENROUTER_API_CONFIGS
        if not self.api_configs:
            logger.error("No valid OpenRouter API configurations provided")
            raise ValueError("At least one OpenRouter API configuration is required")
        for config in self.api_configs:
            if not config.get("key") or not config.get("model"):
                logger.error(f"Invalid API config: {config}")
                raise ValueError("Each API config must have a valid key and model")
        self.current_config_index = 0
        self.max_retries = len(self.api_configs)  # One retry per config

    def _get_headers(self):
        """Get headers with the current API key."""
        return {
            "Authorization": f"Bearer {self.api_configs[self.current_config_index]['key']}",
            "Content-Type": "application/json",
            "X-Title": "AI Girlfriend Bot"
        }

    def prepare_payload(self, prompt: List[Dict], user_message: str, user_first_name: str = None):
        system_prompt = GIRLFRIEND_SYSTEM_PROMPT.format(user_name=user_first_name or 'darling')
        current_prompt = [{"role": "system", "content": system_prompt}] + prompt + [{"role": "user", "content": user_message}]
        
        payload = {
            "model": self.api_configs[self.current_config_index]["model"],
            "messages": current_prompt,
            "temperature": 0.8,
            "max_tokens": 100,
            "top_p": 0.9
        }
        return payload

    def get_ai_response(self, conversation_history: List[Dict], user_message: str, user_first_name: str = None) -> str:
        payload = self.prepare_payload(conversation_history, user_message, user_first_name)
        retries = 0
        original_config_index = self.current_config_index

        while retries < self.max_retries:
            try:
                logger.debug(f"Attempting API call with config {self.current_config_index + 1}/{len(self.api_configs)} (model: {self.api_configs[self.current_config_index]['model']})")
                response = requests.post(
                    self.base_url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 429:  # Rate limit error
                    logger.warning(f"Rate limit hit for config {self.current_config_index + 1} (model: {self.api_configs[self.current_config_index]['model']}). Switching to next config.")
                    self.current_config_index = (self.current_config_index + 1) % len(self.api_configs)
                    retries += 1
                    time.sleep(1)
                    continue
                
                if response.status_code != 200:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                    self.current_config_index = (self.current_config_index + 1) % len(self.api_configs)
                    retries += 1
                    time.sleep(1)
                    continue
                
                response.encoding = 'utf-8'
                data = response.json()
                logger.debug(f"Raw API response: {data}")
                
                if "choices" in data and data["choices"]:
                    full_text = data["choices"][0]["message"]["content"]
                    full_text = full_text.replace("<｜begin▁of▁sentence｜>", "").replace("<｜end▁of▁sentence｜>", "").strip()
                    full_text = full_text.encode('utf-8', errors='replace').decode('utf-8')
                    
                    emoji_fixes = {
                        r'\U0001F618': '😘',
                        r'\U0001F496': '💖',
                        r'\U0001F60A': '😊'
                    }
                    for escape, emoji in emoji_fixes.items():
                        full_text = full_text.replace(escape, emoji)
                    
                    if not full_text.strip():
                        return "Hmm, I'm feeling a bit shy today, darling. Could you say that again? 😊"
                    logger.info(f"Successful response with config {self.current_config_index + 1} (model: {self.api_configs[self.current_config_index]['model']})")
                    return full_text.strip()
                else:
                    error_msg = data.get('error', {}).get('message', 'Unknown error')
                    logger.error(f"API response error: {error_msg}")
                    self.current_config_index = (self.current_config_index + 1) % len(self.api_configs)
                    retries += 1
                    time.sleep(1)
                    continue
                
            except requests.exceptions.Timeout:
                logger.error(f"OpenRouter API timeout with config {self.current_config_index + 1} (model: {self.api_configs[self.current_config_index]['model']})")
                return "Oh no, I'm blushing too hard to respond right now! Give me a sec, okay? 😅"
            except requests.exceptions.ConnectionError:
                logger.error(f"OpenRouter API connection error with config {self.current_config_index + 1} (model: {self.api_configs[self.current_config_index]['model']})")
                return "Oops, my heart skipped a beat and lost connection! Can we try again, love? 💖"
            except Exception as e:
                logger.error(f"OpenRouter API error with config {self.current_config_index + 1} (model: {self.api_configs[self.current_config_index]['model']}): {e}")
                self.current_config_index = (self.current_config_index + 1) % len(self.api_configs)
                retries += 1
                time.sleep(1)
                continue
        
        # If all retries fail
        logger.error(f"All API configs exhausted after {retries} attempts")
        self.current_config_index = original_config_index  # Reset to original config
        return "Oh, darling, I'm swamped with love notes! Can we chat again soon? 😘"
