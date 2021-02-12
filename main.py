import os
from module import JBotClient

bot = JBotClient()
bot.load_extension("core.core")
[bot.load_extension(f"cogs.{x.replace('.py', '')}") for x in os.listdir("./cogs") if x.endswith('.py') and not x.startswith("_")]
bot.run()
