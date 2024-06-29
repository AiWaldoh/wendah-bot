from discord import DiscordBot
from config import Config
import asyncio

if __name__ == "__main__":
    config = Config()
    bot = DiscordBot(config)
    asyncio.run(bot.start())
