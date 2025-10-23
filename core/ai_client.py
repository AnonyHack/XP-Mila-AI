import requests
import json
import logging
from typing import List, Dict
from config import OPENROUTER_API_KEY, GIRLFRIEND_SYSTEM_PROMPT

class VeniceAI:
    def __init__(self):
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "X-Title": "AI Girlfriend Bot"
        }

    def prepare_payload(self, prompt: List[Dict], user_message: str, user_first_name: str = None):
        # Personalize the prompt with user’s first name
        system_prompt = GIRLFRIEND_SYSTEM_PROMPT.format(user_name=user_first_name or 'darling')
        current_prompt = [{"role": "system", "content": system_prompt}] + prompt + [{"role": "user", "content": user_message}]
        
        payload = {
            "model": "deepseek/deepseek-chat-v3.1:free",
            "messages": current_prompt,
            "temperature": 0.8,  # Slightly higher for more playful responses
            "max_tokens": 100,  # Limit to short, casual replies
            "top_p": 0.9  # Slightly lower for more focused responses
        }
        return payload

    def get_ai_response(self, conversation_history: List[Dict], user_message: str, user_first_name: str = None) -> str:
        try:
            payload = self.prepare_payload(conversation_history, user_message, user_first_name)
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if response.status_code != 200:
                logging.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                return "Oh, sweetie, I'm having a little trouble right now. Can we try again in a moment? 😘"
            
            # Ensure UTF-8 decoding
            response.encoding = 'utf-8'
            data = response.json()
            
            # Log raw response for debugging
            logging.debug(f"Raw API response: {data}")
            
            if "choices" in data and data["choices"]:
                full_text = data["choices"][0]["message"]["content"]
                
                # Clean up DeepSeek-specific tokens
                full_text = full_text.replace("<｜begin▁of▁sentence｜>", "").replace("<｜end▁of▁sentence｜>", "").strip()
                
                # Clean up any malformed characters
                full_text = full_text.encode('utf-8', errors='replace').decode('utf-8')
                
                # Replace known emoji escape sequences
                emoji_fixes = {
                    r'\U0001F618': '😘',
                    r'\U0001F496': '💖',
                    r'\U0001F60A': '😊'
                }
                for escape, emoji in emoji_fixes.items():
                    full_text = full_text.replace(escape, emoji)
                
                if not full_text.strip():
                    return "Hmm, I'm feeling a bit shy today, darling. Could you say that again? 😊"
                return full_text.strip()
            else:
                error_msg = data.get('error', {}).get('message', 'Unknown error')
                logging.error(f"API response error: {error_msg}")
                return "Oh no, something went wrong, love. Let’s try that again, okay? 💖"
                
        except requests.exceptions.Timeout:
            logging.error("OpenRouter API timeout")
            return "Oh no, I'm blushing too hard to respond right now! Give me a sec, okay? 😅"
        except requests.exceptions.ConnectionError:
            logging.error("OpenRouter API connection error")
            return "Oops, my heart skipped a beat and lost connection! Can we try again, love? 💖"
        except Exception as e:
            logging.error(f"OpenRouter API error: {e}")
            return "Something went wrong, sweetie. Let's try that again, shall we? 😘"
