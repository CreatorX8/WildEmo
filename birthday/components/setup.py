from __future__ import annotations

import datetime

import discord
from dateutil.parser import ParserError, parse
from redbot.core import Config
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, warning

from ..consts import MAX_BDAY_MSG_LEN
from ..utils import format_bday_message


class SetupView(discord.ui.View):
    def __init__(self, author: discord.Member, bot: Red, config: Config):
        super().__init__()

        self.author = author

        self.bot = bot
        self.config = config

    @discord.ui.button(label="Start setup", style=discord.ButtonStyle.blurple)
    async def btn_start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupModal(self.bot, self.config))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("Достъп отказан за използването на този бутон.")
            return False
        else:
            return True


class SetupModal(discord.ui.Modal):
    message_w_year = discord.ui.TextInput(
        label="Съобщение за рожден ден с година",
        max_length=MAX_BDAY_MSG_LEN,
        style=discord.TextStyle.long,
        placeholder=(
            "Може да използвате {mention}, {name} и {new_age}\nПример:\n{mention}"
            " стана на {new_age} години!"
        ),
    )

    message_wo_year = discord.ui.TextInput(
        label="Съобщение за рожден ден без година",
        max_length=MAX_BDAY_MSG_LEN,
        style=discord.TextStyle.long,
        placeholder=(
            "Може да използвате {mention} име {name}.\nПример:\nРождения ден на {mention}"
            " е днес! Честит рожден ден!"
        ),
    )

    time = discord.ui.TextInput(
        label="Време от деня, в което да бъдат изпратени съобщенията",
        style=discord.TextStyle.short,
        placeholder="Часовете са в UTC. Примери: 12AM, 5AM",
    )

    # below was valid then discord decided nope

    # time = discord.ui.Select(
    #     placeholder="Time of day to send messages",
    #     options=[
    #         discord.SelectOption(label=str(i) + ":00 UTC", value=str(i * 60 * 60))
    #         for i in range(24)
    #     ],
    # )

    def __init__(self, bot: Red, config: Config):
        super().__init__(title="Нстройка на рождени дни")

        self.bot = bot
        self.config = config

    async def on_submit(self, interaction: discord.Interaction) -> None:
        def get_reminder() -> str:
            return (
                    "Нищо не е запазено, опитайте отново.\n\nЕто вашите съобщения, за да не се налага"
                    " да ги пишете отново.\n\nС година:\n"
                    + box(self.message_w_year.value or "Не е зададено")
                    + "\nБез година:\n"
                    + box(self.message_wo_year.value or "Не е зададено")
            )

        try:
            time_utc = parse(
                self.time.value,
                ignoretz=True,
                default=datetime.datetime(year=1, month=1, day=1),
            ).replace(year=1, month=1, day=1, minute=0, second=0, microsecond=0)
            midnight = datetime.datetime.utcnow().replace(
                year=1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )

            time_utc_s = int((time_utc - midnight).total_seconds())
        except ParserError:
            await interaction.response.send_message("Това е невалидно време.", ephemeral=True)
            return

        try:
            format_bday_message(self.message_w_year.value, interaction.user, 1)
        except KeyError as e:
            await interaction.response.send_message(
                warning(
                    "Съобщението за рождени дни **с година** може да съдържа само `{mention}`, `{name}`"
                    " и `{new_age}`. Не може да имате нищо друго в `{}`. Вие сте написали"
                    f" `{{{e.args[0]}}}`, което е навалидно.\n\n{get_reminder()}"
                ),
                ephemeral=True,
            )
            return

        try:
            format_bday_message(self.message_wo_year.value, interaction.user)
        except KeyError as e:
            await interaction.response.send_message(
                warning(
                    "Съобщението за рождени дни **без година** може да съдържа само `{mention}` и"
                    " `{name}`. Не може да имате нищо друго в `{}`. Вие сте написали"
                    f" `{{{e.args[0]}}}`, което е навалидно.\n\n{get_reminder()}"
                ),
                ephemeral=True,
            )
            return

        async with self.config.guild(interaction.guild).all() as conf:
            conf["time_utc_s"] = time_utc_s
            conf["message_w_year"] = self.message_w_year.value
            conf["message_wo_year"] = self.message_wo_year.value
            conf["setup_state"] += 3
            if conf["setup_state"] > 5:
                conf["setup_state"] = 5

            state = conf["setup_state"]

        if state == 5:
            await interaction.response.send_message(
                "Всичко е готово! Потребителите могат да зададат рождените си дни с `birthday set`"
            )
        else:
            await interaction.response.send_message(
                "Готово, но все още не сме напълно готови. Само задайте текстови канал и роля с "
                "`bdset role` и `bdset channel` след това рождените дни ще бъдат настроени успено. Вие "
                "може да проверите настройките с `bdset settings`"
            )
