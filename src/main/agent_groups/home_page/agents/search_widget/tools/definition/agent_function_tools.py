from abc import abstractmethod
from typing import Annotated


class common:
    @abstractmethod
    def selectDate(self, date: Annotated[int, "Day of the month (DD, e.g., 01 for 1st)"],
                   month: Annotated[str, "Month (MMM, e.g., Jan for January). Default: `NA`"],
                   year: Annotated[int, "Month (YYYY, e.g., 2025). Default: 0"]):
        '''Selects required date from the calendar which is already open, based on date provided.'''

    @abstractmethod
    def selectDateWhichIsXDaysFromToday(self, days: Annotated[
        int, "Number of days from today to select the date. Default is 0 (today)"]):
        '''Selects required date from the calendar which is already open, based on X days from today'''

    @abstractmethod
    def captureDisappearingErrorMessage(self):
        '''Notes down the error message displayed on the Search Widget, if any. Use this function immediately after performing an action which is expected to throw an error message. Note: Use this function only if user has explicitly asked to capture the error message. Else never use this function'''

class mweb(common):
    pass

class dweb(common):
    pass

class android(common):
    pass

class ios(common):
    pass

