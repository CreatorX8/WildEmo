import datetime
from typing import TYPE_CHECKING

from dateutil.parser import ParserError, parse
from redbot.core.commands import BadArgument, Context, Converter

from .vexutils import get_vex_logger

log = get_vex_logger(__name__)


if TYPE_CHECKING:
    BirthdayConverter = datetime.datetime
    TimeConverter = datetime.datetime
else:

    class BirthdayConverter(Converter):
        async def convert(self, ctx: Context, argument: str) -> datetime.datetime:
            log.trace("attempting to parse date %s", argument)
            try:
                default = datetime.datetime(year=1, month=1, day=1)
                log.trace("parsed date: %s", argument)
                out = parse(argument, default=default, ignoretz=True, dayfirst=True).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )

                return out
            except ParserError:
                raise BadArgument("Невалидна дата. Пример: `30/1` или `30/1/2001`.")

    class TimeConverter(Converter):
        async def convert(self, ctx: Context, argument: str) -> datetime.datetime:
            log.trace("attempting to parse time %s", argument)
            try:
                out = parse(argument, ignoretz=True).replace(
                    year=1, month=1, day=1, minute=0, second=0, microsecond=0
                )
                log.trace("parsed time: %s", argument)
                return out
            except ParserError:
                raise BadArgument("Невалидно време. Пример: `12 AM`.")
