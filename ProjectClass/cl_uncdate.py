from datetime import datetime, timezone, timedelta
import pytz

from ProjectClass.cl_printmsg import CLPrintMsg


class CLUNCDate:
    @classmethod
    def get_moscow_tz(cls, printmsg: CLPrintMsg):
        try:
            from zoneinfo import ZoneInfo  # py3.9+
            try:
                return ZoneInfo("Europe/Moscow")
            except Exception as ex:
                # printmsg.print_error(f'zoneinfo доступен, но нет tzdata — продолжим к pytz/fallback: {ex}')
                pass
        except Exception as ex:
            # printmsg.print_error(f'zoneinfo недоступен — продолжим к pytz/fallback: {ex}')
            pass
        try:
            return pytz.timezone("Europe/Moscow")
        except Exception as ex:
            # printmsg.print_error(f'Encode moscow_tz: {ex}')
            return timezone(timedelta(hours=3))

    @classmethod
    def unc_to_moskow(cls, dt: datetime, printmsg: CLPrintMsg)->datetime:
        try:
            if dt is not None:
                # Устанавливаем mtime по UTC-метке MDTM — достаточно dt_utc.timestamp()
                # и дополнительно формируем представление в московской зоне для вывода.
                moscow = cls.get_moscow_tz(printmsg)
                return dt.astimezone(moscow)
            else:
                return dt
        except Exception as ex:
            # printmsg.print_error(f'Encode moscow_tz: {ex}')
            return dt.astimezone(timezone(timedelta(hours=3)))

    @staticmethod
    def get_only_date(dt: datetime)->datetime:
        return datetime(dt.year, dt.month, dt.day)
