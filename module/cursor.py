import asyncio
import math
import typing
import discord
from discord_slash.utils import manage_components
from .client import LaytheClient


class Cursor:
    def __init__(self,
                 client: LaytheClient,
                 message: discord.Message,
                 items: typing.List[str],
                 base_embed: discord.Embed,
                 max_per_page: int = 5,
                 as_reply: bool = True,
                 mention_author: bool = True,
                 timeout: int = 30,
                 extra_button=None):  # Passing extra_button will enable async generator mode.
        self.client = client
        self.message = message
        self.items = items,
        self.base_embed = base_embed
        self.max_per_page = max_per_page
        self.as_reply = as_reply
        self.mention_author = mention_author
        self.timeout = timeout
        self.extra_button = extra_button

        self.next_item = manage_components.create_button(style=2, label="다음", emoji="⬇", custom_id=f"next{message.id}")
        self.prev_item = manage_components.create_button(style=2, label="이전", emoji="⬆", custom_id=f"prev{message.id}")
        self.select = manage_components.create_button(style=3, label="선택", emoji="✅", custom_id=f"select{message.id}")
        self.abort = manage_components.create_button(style=4, label="취소", emoji="❌", custom_id=f"abort{message.id}")
        __control_row = [self.prev_item, self.next_item, self.select, self.abort]
        if self.extra_button:
            __control_row.append(self.extra_button)
        self.control_row = manage_components.create_actionrow(*__control_row)

        self.next_page = manage_components.create_button(style=2, label="다음 페이지", emoji="➡", custom_id=f"npage{message.id}")
        self.prev_page = manage_components.create_button(style=2, label="이전 페이지", emoji="⬅", custom_id=f"ppage{message.id}")

        __custom_ids = ["next", "prev", "select", "abort", "npage", "ppage"]
        if self.extra_button:
            __custom_ids.append(self.extra_button.custom_id)
            self.extra_button.custom_id += str(message.id)
        self.custom_ids = [x+str(message.id) for x in __custom_ids]

        self.current_page = 0
        self.selected = 0
        self.page_index = 0
        self.pages = [[] for _ in range(math.ceil(len(items)/max_per_page))]

        self.result = ()

        for n, x in enumerate(items):
            self.pages[n//5].append(x)

    @property
    def page_row(self):
        cpage = manage_components.create_button(style=2, label=f"페이지 {self.current_page+1}/{len(self.pages)}", custom_id="cpage", disabled=True)
        return manage_components.create_actionrow(self.prev_page, cpage, self.next_page)

    @property
    def all_disabled(self):
        next_item = manage_components.create_button(style=2, label="다음", emoji="⬇", custom_id=f"next{self.message.id}", disabled=True)
        prev_item = manage_components.create_button(style=2, label="이전", emoji="⬆", custom_id=f"prev{self.message.id}", disabled=True)
        select = manage_components.create_button(style=3, label="선택", emoji="✅", custom_id=f"select{self.message.id}", disabled=True)
        abort = manage_components.create_button(style=4, label="취소", emoji="❌", custom_id=f"abort{self.message.id}", disabled=True)
        custom = self.extra_button.copy()
        custom["disabled"] = True
        control_row_up = manage_components.create_actionrow(prev_item, next_item, select, abort, custom)

        next_page = manage_components.create_button(style=2, label="다음 페이지", emoji="➡", custom_id=f"npage{self.message.id}", disabled=True)
        prev_page = manage_components.create_button(style=2, label="이전 페이지", emoji="⬅", custom_id=f"ppage{self.message.id}", disabled=True)
        cpage = manage_components.create_button(style=2, label=f"페이지 {self.current_page+1}/{len(self.pages)}", custom_id="cpage", disabled=True)
        control_row_down = manage_components.create_actionrow(prev_page, cpage, next_page)

        return [control_row_up, control_row_down]

    @property
    def current_max(self):
        return len(self.pages[self.current_page]) - 1

    def run_next_item(self):
        self.selected += 1
        if self.page_index < self.current_max:
            self.page_index += 1
        else:
            self.page_index = 0
            if self.current_page == len(self.pages) - 1:
                self.current_page = 0
                self.selected = 0
            else:
                self.current_page += 1

    def run_prev_item(self):
        self.selected -= 1
        if self.page_index == 0:
            if self.current_page == 0:
                self.current_page = len(self.pages) - 1
                self.page_index = self.current_max
                self.selected = len(self.items) - 1
            else:
                self.current_page -= 1
                self.page_index = self.current_max
        else:
            self.page_index -= 1

    def run_next_page(self):
        self.page_index = 0
        if self.current_page == len(self.pages) - 1:
            self.current_page = 0
        else:
            self.current_page += 1
        self.selected = self.current_page*self.max_per_page

    def run_prev_page(self):
        self.page_index = 0
        if self.current_page == 0:
            self.current_page = len(self.pages) - 1
        else:
            self.current_page -= 1
        self.selected = self.current_page*self.max_per_page

    async def start(self):
        async for _ in self.start_as_generator():
            pass
        return self.result

    async def start_as_generator(self):
        msg = await self.message.reply("잠시만 기다려주세요...", mention_author=self.mention_author)

        while True:
            embed = self.base_embed.copy()
            [embed.add_field(name=("▶" if a == self.page_index else "")+f"#{a+1+(self.current_page*self.max_per_page)}", value=b, inline=False) for a, b in enumerate(self.pages[self.current_page])]
            await msg.edit(content="", embed=embed, components=[self.control_row, self.page_row])
            try:
                ctx = await manage_components.wait_for_component(
                    self.client,
                    [msg],
                    [self.control_row, self.page_row],
                    check=lambda comp_ctx: int(comp_ctx.author_id) == int(self.message.author.id),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                await msg.edit(components=[])
                self.result = (msg, None)
                break
            await ctx.defer(edit_origin=True)
            custom_id = ctx.custom_id
            if custom_id.startswith("next"):
                self.run_next_item()
            elif custom_id.startswith("prev"):
                self.run_prev_item()
            elif custom_id.startswith("npage"):
                self.run_next_page()
            elif custom_id.startswith("ppage"):
                self.run_prev_page()
            elif custom_id.startswith("select"):
                await msg.edit(components=[])
                self.result = (msg, self.selected)
                break
            elif custom_id.startswith("abort"):
                await msg.edit(components=[])
                self.result = (msg, None)
                break
            else:
                yield ctx, self.selected
