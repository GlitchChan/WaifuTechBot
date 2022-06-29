import sys

from naff import Intents
from secrets import TOKEN, DEV_TOKEN
from core import Megumin

if __name__ == "__main__":
    client = Megumin(intents=Intents.ALL)
    if len(sys.argv) > 1 and sys.argv[1] == 'dev':
        client.start(DEV_TOKEN)
    elif len(sys.argv) < 1 or sys.argv[1] == 'main':
        client.start(TOKEN)
    else:
        client.logger.error("Unknown arg given on startup")
