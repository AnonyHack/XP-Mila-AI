import requests
import json
import logging
import uuid
from typing import List, Dict
from config import VENICE_AI_HEADERS, VENICE_AI_COOKIES, GIRLFRIEND_SYSTEM_PROMPT

class VeniceAI:
    def __init__(self):
        self.base_url = "https://outerface.venice.ai/api/inference/chat"
        self.headers = VENICE_AI_HEADERS
        self.cookies = VENICE_AI_COOKIES

    def generate_ids(self):
        return {
            'requestId': f'req_{str(uuid.uuid4()).replace("-", "")}',
            'messageId': f'msg_{str(uuid.uuid4()).replace("-", "")}',
            'userId': f'user_anon_{str(uuid.uuid4()).replace("-", "")}'
        }

    def prepare_payload(self, prompt: List[Dict], user_message: str, user_first_name: str = None):
        ids = self.generate_ids()
        # Personalize the prompt with user’s first name if available
        system_prompt = GIRLFRIEND_SYSTEM_PROMPT.format(user_name=user_first_name or "darling")
        current_prompt = [{'role': 'system', 'content': system_prompt}] + prompt + [{'role': 'user', 'content': user_message}]
        
        payload = {
            'requestId': ids['requestId'],
            'conversationType': 'text',
            'type': 'text',
            'modelId': 'dolphin-3.0-mistral-24b',
            'modelName': 'Venice Uncensored',
            'modelType': 'text',
            'prompt': current_prompt,
            'systemPrompt': system_prompt,
            'messageId': ids['messageId'],
            'includeVeniceSystemPrompt': False,  # Use custom system prompt
            'isCharacter': True,  # Treat as a character
            'userId': ids['userId'],
            'simpleMode': False,
            'characterId': '',
            'id': '',
            'textToSpeech': {
                'voiceId': 'af_sky',
                'speed': 1,
            },
            'webEnabled': True,
            'reasoning': True,
            'temperature': 0.7,  # Slightly higher for more creative, flirty responses
            'topP': 1,
            'clientProcessingTime': 11,
        }
        return payload

    def get_ai_response(self, conversation_history: List[Dict], user_message: str, user_first_name: str = None) -> str:
        try:
            payload = self.prepare_payload(conversation_history, user_message, user_first_name)
            response = requests.post(
                self.base_url,
                headers=self.headers,
                cookies=self.cookies,
                json=payload,
                timeout=30
            )
            if response.status_code != 200:
                logging.error(f"Venice AI API error: {response.status_code}")
                return "Oh, sweetie, I'm having a little trouble right now. Can we try again in a moment? 😘"
            
            # Ensure UTF-8 decoding
            response.encoding = 'utf-8'
            full_text = ''
            
            # Log raw response for debugging
            logging.debug(f"Raw API response: {response.text}")
            
            # Process streaming response line by line
            for line in response.text.strip().splitlines():
                if line.strip():
                    try:
                        data = json.loads(line.strip())
                        if isinstance(data, dict) and "content" in data:
                            content = data.get("content", "")
                            full_text += content
                    except json.JSONDecodeError as e:
                        logging.warning(f"Failed to parse line: {line} - Error: {e}")
                        continue
            
            # Clean up any malformed characters
            full_text = full_text.encode('utf-8', errors='replace').decode('utf-8')
            
            # Replace known emoji escape sequences (if API sends them)
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
            
        except requests.exceptions.Timeout:
            logging.error("Venice AI API timeout")
            return "Oh no, I'm blushing too hard to respond right now! Give me a sec, okay? 😅"
        except requests.exceptions.ConnectionError:
            logging.error("Venice AI API connection error")
            return "Oops, my heart skipped a beat and lost connection! Can we try again, love? 💖"
        except Exception as e:
            logging.error(f"Venice AI error: {e}")
            return "Something went wrong, sweetie. Let's try that again, shall we? 😘"