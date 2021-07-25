import typing
import discord
import lavalink


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


class TrackEmbed(GuildEmbed):
    def __init__(self, track: lavalink.AudioTrack, guild: discord.Guild, **kwargs):
        kwargs.setdefault("color", EmbedColor.NEGATIVE)
        super().__init__(guild, **kwargs)
        self.description = f"업로더: `{track.author}`\n제목: [`{track.title}`]({track.uri})"
        self.set_image(url=f"https://img.youtube.com/vi/{track.identifier}/hqdefault.jpg")
        requester = guild.get_member(track.requester)
        if requester and kwargs.get("show_requester", True):
            self.set_footer(text=f"요청자: {requester.display_name}", icon_url=requester.avatar_url)
