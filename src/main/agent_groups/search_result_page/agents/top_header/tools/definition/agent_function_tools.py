from abc import abstractmethod
from typing import Annotated

class common:
    pass

class mweb(common):
    pass

class dweb(common):
    @abstractmethod
    def selectDate(self, date: Annotated[int, "Day of the month (DD, e.g., 01 for 1st)"],
                   month: Annotated[str, "Month (MMM, e.g., Jan for January). Default: `NA`"],
                   year: Annotated[int, "Month (YYYY, e.g., 2025). Default: 0"]):
        '''Selects required date from the calendar which is already open, based on date provided.'''

    @abstractmethod
    def selectDateWhichIsXDaysFromToday(self, days: Annotated[
        int, "Number of days from today to select the date. Default is 0 (today)"]):
        '''Selects required date from the calendar which is already open, based on X days from today'''


class android(common):
    pass

class ios(common):
    pass

