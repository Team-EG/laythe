"""
    laythe
    Copyright (C) 2021 Team EG

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import logging
from module import LaytheClient

print(r"""
 _                    _    _           
| |                  | |  | |          
| |      __ _  _   _ | |_ | |__    ___ 
| |     / _` || | | || __|| '_ \  / _ \
| |____| (_| || |_| || |_ | | | ||  __/
\_____/ \__,_| \__, | \__||_| |_| \___|
                __/ |                  
               |___/                   
""")

logger = logging.getLogger('laythe')
logging.basicConfig(level=logging.INFO)  # DEBUG/INFO/WARNING/ERROR/CRITICAL
handler = logging.FileHandler(filename=f'laythe.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

bot = LaytheClient(logger=logger)
bot.load_extension("core.core")
[bot.load_extension(f"cogs.{x.replace('.py', '')}") for x in os.listdir("./cogs") if x.endswith('.py') and not x.startswith("_")]
bot.run()
