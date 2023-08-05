from redbot.core import commands, Config
import discord

class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=927537080882561025)
        default_guild = {
            "counting_channel": None,
            "current_count": 0,
            "count_board": {},
            "last_counter": None
        }
        self.config.register_guild(**default_guild)

    @commands.mod_or_can_manage_channel()
    @commands.hybrid_command()
    async def setcounting(self, ctx, channel: discord.TextChannel):
        """Set a counting channel for the game to began!"""
        await self.config.guild(ctx.guild).counting_channel.set(channel.id)
        embed = discord.Embed(title="Игра на броене", description=f"Канала за броене е зададен до {channel.mention}.", color=0x2b2d31)
        response = await ctx.channel.send(embed=embed)
        await response.delete(delay=10)

    @commands.mod_or_can_manage_channel()
    @commands.hybrid_command()
    async def setcurrentcount(self, ctx, number: int):
        """Set the current count"""
        await self.config.guild(ctx.guild).current_count.set(number)
        embed = discord.Embed(title="Игра на броене", description=f"Зададохте текущото число до {number}.", color=0x2b2d31)
        response = await ctx.channel.send(embed=embed)
        await response.delete(delay=5)

    @commands.hybrid_command()
    async def currentcount(self, ctx):
        """Display the current count"""
        count = await self.config.guild(ctx.guild).current_count()
        embed = discord.Embed(title="Игра на броене", description=f"Стигнали сме до {count}.", color=0x2b2d31)
        response = await ctx.channel.send(embed=embed)
        await response.delete(delay=5)

    @commands.mod_or_can_manage_channel()
    @commands.hybrid_command()
    async def resetcountchannel(self, ctx):
        """Reset the counting!"""
        await self.config.guild(ctx.guild).counting_channel.set(None)
        embed = discord.Embed(title="Игра на броене", description="Канала за броене бе нулиран.",
                              color=0x2b2d31)
        response = await ctx.channel.send(embed=embed)
        await response.delete(delay=10)

    @commands.hybrid_command()
    async def countrules(self, ctx):
        """Display the rules for counting."""
        embed = discord.Embed(title="Игра на броене", description="Правила", color=0x2b2d31)
        embed.add_field(name="1", value="Един и същ потребител не може да брои два пъти подред", inline=False)
        embed.add_field(name="2", value="За всяко число потребителите трабва да се редуват", inline=False)
        embed.add_field(name="3", value="Трябва да се брои правилно", inline=False)
        response = await ctx.channel.send(embed=embed)
        await response.delete(delay=10)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        guild_data = self.config.guild(message.guild)
        counting_channel = await guild_data.counting_channel()
        if message.channel.id == counting_channel:
            try:
                number = int(message.content)
                current_count = await guild_data.current_count()
                last_counter = await guild_data.last_counter()
                if message.author.id == last_counter:
                    try:
                        await message.delete()
                    except discord.Forbidden:
                        await message.channel.send(
                            "Нямам права да изтривам съобщения. Моля уверете се, че имам права за 'Управление на съобщения'.")
                        return
                    embed = discord.Embed(title="Игра на броене", description="Не може да броите два пъти подред!", color=0x2b2d31)
                    response = await message.channel.send(embed=embed)
                    await response.delete(delay=5)
                elif number != current_count + 1:
                    try:
                        await message.delete()
                    except discord.Forbidden:
                        await message.channel.send(
                            "Нямам права да изтривам съобщения. Моля уверете се, че имам права за 'Управление на съобщения'.")
                        return
                    embed = discord.Embed(title="Игра на броене",
                                          description=f"Грешно число! Стигнали сме до {current_count}.",
                                          color=0x2b2d31)
                    response = await message.channel.send(embed=embed)
                    await response.delete(delay=5)
                else:
                    await guild_data.current_count.set(number)
                    await guild_data.last_counter.set(message.author.id)
                    board = await guild_data.count_board()
                    board[message.author.id] = board.get(str(message.author.id), 0) + 1
                    await guild_data.count_board.set(board)
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
        if not await self.config.guild(guild).counting_channel() == channel_id:
            return

        message = payload.cached_message
        guild_data = self.config.guild(guild)
        current_count = await guild_data.current_count()
        if message is None:
            return
        elif message.content == str(current_count):
            await message_channel.send(f"{current_count} (Изтрито съобщение изпратено от {message.author.mention}).")
