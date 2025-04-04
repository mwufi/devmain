from scrapybara import Scrapybara
from dotenv import load_dotenv
import os

load_dotenv()

client = Scrapybara(api_key=os.getenv("SCRAPYBARA_API_KEY"))

