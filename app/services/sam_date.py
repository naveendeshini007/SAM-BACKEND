from datetime import datetime, timedelta


class SamDateService:

    @staticmethod
    def get_first_sunday(year: int, month: int) -> str:
        """
        Returns file_date in format YYYYMMDD
        where DD is first Sunday of the month
        """
        first_day = datetime(year, month, 1)
        days_to_sunday = (6 - first_day.weekday()) % 7
        first_sunday = first_day + timedelta(days=days_to_sunday)

        return first_sunday.strftime("%Y%m%d")