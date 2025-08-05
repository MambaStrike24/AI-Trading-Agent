import os
from pathlib import Path
from dotenv import load_dotenv

def load_env_once():
    if "OPENAI_API_KEY" not in os.environ:
        # Dynamically resolve the path to the root folder (2 levels up from here)
        env_path = Path(__file__).resolve().parents[1] / ".env"
        env_loaded = load_dotenv(dotenv_path=env_path)
        if not env_loaded:
            raise RuntimeError(f"Failed to load .env file from {env_path}")
