import typing
import discord


class AuthorEmbed(discord.Embed):
    def __init__(self, author: typing.Union[discord.User, discord.Member], **kwargs):
        author_as_display = kwargs.get("author_as_display", True)
        display_footer = kwargs.get("display_footer", False)
        self.set_author(name=author.display_name if author_as_display else str(author),
                        icon_url=author.avatar_url) if not display_footer else \
            self.set_footer(icon_url=author.avatar_url, text=author.display_name if author_as_display else str(author))
        super().__init__(**kwargs)


class GuildEmbed(discord.Embed):
    def __init__(self, guild: discord.Guild, **kwargs):
        display_footer = kwargs.get("display_footer", False)
        self.set_author(name=guild.name, icon_url=guild.icon_url) if not display_footer else self.set_footer(icon_url=guild.icon_url, text=guild.name)
        super().__init__(**kwargs)


class EmbedColor:
    NEUTRAL = discord.Color.lighter_grey()
    NEGATIVE = discord.Color.red()
    POSITIVE = discord.Color.green()
    DEFAULT = discord.Color.from_rgb(225, 225, 225)
