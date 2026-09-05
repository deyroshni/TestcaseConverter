# config.py
import os
from dotenv import load_dotenv
load_dotenv()

# Generative Engine Configurations
GENERATIVE_ENGINE_API_KEY = os.getenv("api-key")
GENERATIVE_ENGINE_ASSET_API_KEY = os.getenv("asset-api-key")

# Generative Engine Endpoints
GENERATIVE_ENGINE_IMAGE_GENERATION_URL = "https://assets.generative.engine.capgemini.com/v1/generate"
GENERATIVE_ENGINE_UPLOAD_URL = "https://api.generative.engine.capgemini.com/v1/file/upload"
GENERATIVE_ENGINE_ANALYZE_URL = "https://api.generative.engine.capgemini.com/v2/llm/invoke"
GENERATIVE_ENGINE_OPENAI_URL = "https://openai.generative.engine.capgemini.com/v1"

# Model Configuration
DEPLOYMENT_MODEL = "amazon.nova-2-lite-v1:0"