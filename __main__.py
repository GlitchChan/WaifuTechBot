from naff import Intents

from config import TOKEN
from core import Megumin

if __name__ == "__main__":
    client = Megumin(intents=Intents.ALL)
    client.start(TOKEN)
