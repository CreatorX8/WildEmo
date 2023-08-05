from redbot.core import commands, Config
import discord

class WordGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=927537080882561025)
        default_guild = {
            "word_game_channel": None,
            "last_word": None,
            "word_board": {},
            "last_word_sayer": None
        }
        self.config.register_guild(**default_guild)

    @commands.mod_or_can_manage_channel()
    @commands.hybrid_command()
    async def setwordgame(self, ctx, channel: discord.TextChannel):
        """Set a word game channel for the game to began!"""
        await self.config.guild(ctx.guild).word_game_channel.set(channel.id)
        embed = discord.Embed(title="Игра на думи", description=f"Канала за игра на думи е зададен до {channel.mention}.", color=0x2b2d31)
        response = await ctx.channel.send(embed=embed)
        await response.delete(delay=10)

    @commands.mod_or_can_manage_channel()
    @commands.hybrid_command()
    async def setlastword(self, ctx, word: str):
        """Set the last word"""
        await self.config.guild(ctx.guild).last_word.set(word)
        embed = discord.Embed(title="Игра на думи", description=f"Зададохте последната дума до {word}.", color=0x2b2d31)
        response = await ctx.channel.send(embed=embed)
        await response.delete(delay=5)

    @commands.hybrid_command()
    async def lastword(self, ctx):
        """Display the last word"""
        word = await self.config.guild(ctx.guild).last_word()
        embed = discord.Embed(title="Игра на думи", description=f"Последната дума е {word}.", color=0x2b2d31)
        response = await ctx.channel.send(embed=embed)
        await response.delete(delay=5)

    @commands.mod_or_can_manage_channel()
    @commands.hybrid_command()
    async def resetwordgamechannel(self, ctx):
        """Reset the word game!"""
        await self.config.guild(ctx.guild).word_game_channel.set(None)
        embed = discord.Embed(title="Игра на думи", description="Канала за игра на думи бе нулиран.",
                              color=0x2b2d31)
        response = await ctx.channel.send(embed=embed)
        await response.delete(delay=10)

    @commands.hybrid_command()
    async def wordgamerules(self, ctx):
        """Display the rules for word game."""
        embed = discord.Embed(title="Игра на думи", description="Правила", color=0x2b2d31)
        embed.add_field(name="1", value="Един и същ потребител не може да казва дума два пъти подред", inline=False)
        embed.add_field(name="2", value="За всяка дума потребителите трабва да се редуват", inline=False)
        embed.add_field(name="3", value="Трябва следващата дума да започва с буквата, с която завършва предишната дума", inline=False)
        embed.add_field(name="4", value="Трябва да е само една цяла дума", inline=False)
        response = await ctx.channel.send(embed=embed)
        await response.delete(delay=10)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        guild_data = self.config.guild(message.guild)
        word_game_channel = await guild_data.word_game_channel()
        if message.channel.id == word_game_channel:
            try:
                word = message.content
                last_word = await guild_data.last_word()
                last_word_sayer = await guild_data.last_word_sayer()
                if message.author.id == last_word_sayer:
                    try:
                        await message.delete()
                    except discord.Forbidden:
                        await message.channel.send(
                            "Нямам права да изтривам съобщения. Моля уверете се, че имам права за 'Управление на съобщения'.")
                        return
                    embed = discord.Embed(title="Игра на думи", description="Не може да казвате дума два пъти подред!", color=0x2b2d31)
                    response = await message.channel.send(embed=embed)
                    await response.delete(delay=5)
                elif len(word.split()) > 1:
                    try:
                        await message.delete()
                    except discord.Forbidden:
                        await message.channel.send(
                            "Нямам права да изтривам съобщения. Моля уверете се, че имам права за 'Управление на съобщения'.")
                        return
                    embed = discord.Embed(title="Игра на думи",
                                          description=f"Трябва да напишете само една дума! Последната дума е {last_word}.",
                                          color=0x2b2d31)
                    response = await message.channel.send(embed=embed)
                    await response.delete(delay=5)
                elif word[0].lower() != last_word[-1].lower():
                    try:
                        await message.delete()
                    except discord.Forbidden:
                        await message.channel.send(
                            "Нямам права да изтривам съобщения. Моля уверете се, че имам права за 'Управление на съобщения'.")
                        return
                    embed = discord.Embed(title="Игра на думи",
                                          description=f"Грешна дума! Последната дума е {last_word}.",
                                          color=0x2b2d31)
                    response = await message.channel.send(embed=embed)
                    await response.delete(delay=5)
                else:
                    await guild_data.last_word.set(word)
                    await guild_data.last_word_sayer.set(message.author.id)
                    board = await guild_data.word_board()
                    board[message.author.id] = board.get(str(message.author.id), 0) + 1
                    await guild_data.word_board.set(board)
                    await message.add_reaction("✅")

            except ValueError:
                await message.delete()

    @commands.Cog.listener(name="on_raw_message_delete")
    async def on_raw_message_delete_listener(
            self, payload: discord.RawMessageDeleteEvent
    ) -> None:
        # custom name of method used, because this is only supported in Red 3.1+
        guild_id = payload.guild_id
        if guild_id is None:
            return
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return
        if await self.bot.cog_disabled_in_guild(self, guild):
            return
        if guild.me.is_timed_out():
            return
        channel_id = payload.channel_id

        message_channel = guild.get_channel_or_thread(channel_id)
        if message_channel is None:
            return
        if not await self.config.guild(guild).word_game_channel() == channel_id:
            return

        message = payload.cached_message
        guild_data = self.config.guild(guild)
        last_word = await guild_data.last_word()
        if message is None:
            return
        elif message.content == str(last_word):
            await message_channel.send(f"{last_word} (Изтрито съобщение изпратено от {message.author.mention}).")

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        guild = before.guild
        if guild is None:
            return
        if await self.bot.cog_disabled_in_guild(self, guild):
            return
        if guild.me.is_timed_out():
            return
        if before.content == after.content:
            return

        guild_data = self.config.guild(guild)
        last_word = await guild_data.last_word()
        if before.content == str(last_word):
            try:
                await after.delete()
                await before.channel.send(f"{last_word} (Радактирано съобщение изпратено от {before.author.mention}).")
            except discord.Forbidden:
                await after.channel.send(
                    "Нямам права да изтривам съобщения. Моля уверете се, че имам права за 'Управление на съобщения'.")
                return
