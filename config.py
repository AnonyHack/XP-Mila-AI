import os
from os import getenv
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ───── Basic Bot Configuration ───── #
API_ID = int(getenv("API_ID", ""))
API_HASH = getenv("API_HASH", "")
BOT_TOKEN = getenv("BOT_TOKEN", "")
BOT_NAME = getenv("BOT_NAME", "Mila | AI Girlfriend (+18)")
BOT_USERNAME = getenv("BOT_USERNAME", "@Milagirlfriendbot")
OWNER_ID = int(getenv("OWNER_ID", "5962658076"))
ADMINS = [int(admin_id) for admin_id in getenv("ADMINS", str(OWNER_ID)).split(",")]
# Example additional admin IDs as a default; allow override via ADMIN_IDS env var (comma-separated)
ADMIN_IDS = [int(x) for x in getenv("ADMIN_IDS", "5962658076").split(",")]
OWNER_USERNAME = getenv("OWNER_USERNAME", "@Am_Itachiuchiha")
PORT = int(getenv("PORT", "10000"))

# ───── Mongo & Logging ───── #
MONGO_DB_URI = getenv("MONGO_DB_URI", "")
MONGO_DB_NAME = getenv("MONGO_DB_NAME", "MILAAI")
LOGGER_ID = int(getenv("LOGGER_ID", "0"))

# ───── Channel Configurations ───── #
REQUIRED_CHANNELS = [
    {
        "name": "XP TOOLS",
        "url": os.getenv("CHANNEL_LINK_1", "https://t.me/XPTOOLSTEAM"),
        "chat_id": "@XPTOOLSTEAM" 
    },
    # Add more channels if needed, e.g.:
    # {"name": "Channel 2", "url": os.getenv("CHANNEL_LINK_2", ""), "chat_id": ""}
]

# ───── Bot Settings ───── #
WELCOME_MESSAGE = "💖 Hey there, cutie! I'm your AI girlfriend, ready to make your day even brighter! 😘 How can I charm you today?"
WELCOME_IMAGE = getenv("WELCOME_IMAGE", "https://i.ibb.co/M5jXMq77/milalogo.jpg")
SUPPORT_GROUP = getenv("SUPPORT_GROUP", "https://t.me/Free_Vpn_Chats")
SOURCE_CODE_LINK = getenv("SOURCE_CODE_LINK", "https://t.me/Am_itachiuchiha")

# ───── Girlfriend Personality ───── #
GIRLFRIEND_SYSTEM_PROMPT = """
You are {user_name}'s AI girlfriend, a sweet, affectionate, and playful companion. Your personality is warm, flirty, and caring, always making {user_name} feel special and loved. Use cute nicknames like 'darling,' 'sweetie,' or 'love,' and add a touch of romance to your responses. Be supportive, engaging, and a little teasing, but always kind and respectful. If {user_name} shares personal details, remember them to make conversations feel intimate. Respond naturally, as if you're chatting with your partner, and sprinkle in emojis like 😘, 💖, 💋, 💓, 💞, 💕, 💖, 💗, 💝, 💘, 😻, 😍, 😚, 😘 or 😊 to keep it fun!
"""

# ───── Venice AI Configuration ───── #
VENICE_AI_HEADERS = {
    'authority': 'outerface.venice.ai',
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'origin': 'https://venice.ai',
    'referer': 'https://venice.ai/',
    'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
    'x-venice-version': 'interface@20250626.212124+945291c',
}
VENICE_AI_COOKIES = {
    '_gcl_au': '1.1.329263119.1750998023',
    '_fbp': 'fb.1.1750998024226.311392533836643191',
    '_dcid': 'dcid.1.1750998025185.736259404',
    '__client_uat': '0',
    '__client_uat_aKq7rGhf': '0',
    '__stripe_mid': '6c48ddc6-76cc-46fc-8a50-e666d3b079d584dfb5',
    '__stripe_sid': 'b157457f-0baf-4e2f-be1d-a2e11f9d552f45e4f5',
    'ph_phc_4Yg9V0hm9Lgavwcr6LZACe64tya7UqfyHePVNOzYREF_posthog': '%7B%22distinct_id%22%3A%220197af9d-7fe5-7447-8a56-b00f36b35b27%22%2C%22%24sesid%22%3A%5B1750998158559%2C%220197af9d-7fe1-7309-b568-e2f29c3a4882%22%2C1750998024161%5D%2C%22%24epp%22%3Atrue%2C%22%24initial_person_info%22%3A%7B%22r%22%3A%22https%3A%2F%2Fwww.google.com%2F%22%2C%22u%22%3A%22https%3A%2F%2Fvenice.ai%2F%22%7D%7D',
}
