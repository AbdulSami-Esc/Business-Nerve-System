import os
from dotenv import load_dotenv

success = load_dotenv()
print(f"Did .env load successfully? {success}")
print(f"Address: {os.getenv('GMAIL_ADDRESS')}")