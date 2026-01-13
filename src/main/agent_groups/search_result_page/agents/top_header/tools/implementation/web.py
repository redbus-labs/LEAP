from datetime import datetime, timedelta
from typing import Annotated

import core_agentic.agentic_base as agentic_base
from core_agentic import run_configs
from ..definition.agent_locator_tools import mweb as LocatorToolsMweb
from ..definition.agent_locator_tools import dweb as LocatorToolsDweb
from ..definition.agent_function_tools import mweb as FunctionToolsMweb
from ..definition.agent_function_tools import dweb as FunctionToolsDweb

class top_header(LocatorToolsMweb, LocatorToolsDweb, FunctionToolsDweb, FunctionToolsMweb):
    def src(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'labelCityWrapper_')])[1]")

    def dest(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'labelCityWrapper_')])[2]")

    def citySuggestionsInDropDown(self, position: Annotated[
        int, "1-based index of the location suggestion in the dropdown list (default=1)"]):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'listHeader_')])[{position}]")

    def swap_locations_button(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'swapIcon_')])[1]")

    def remove_return_date_button(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'removeReturnIcon_')])[1]")

    def passenger_selection_section_opener(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'label_')])[last()]")

    def adult_decrease_button(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'icon_')])[5]")

    def passenger_selection_section_closer(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'paxWrapper_')]//button[contains(@class,'primaryButton_')])[1]")

    def adult_increase_button(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'icon_')])[6]")

    def first_child_add_button(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'addBtn_')])[1]")

    def subsequent_child_add_button(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'icon_')])[8]")

    def child_decrease_button(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'icon_')])[7]")

    def search_ferries_button(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'primaryButton_')])[1]")

    def departure_date_calendar(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'dojWrapper_')])[1]")

    def return_date_calendar(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'dojWrapper_')])[2]")

    def from_input_section(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'labelCityWrapper_')])[1]")

    def to_input_section(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='modifySearch']//*[contains(@class,'labelCityWrapper_')])[2]")

    def calender_header_text(self):
        return agentic_base.helper.selfHealWithoutParent("Field which displays Month and Year",
                                                      "(//*[@data-autoid='modifySearch']//*[contains(@class,'monthYear_')])[1]")

    def calender_forward_button(self):
        return agentic_base.helper.selfHealWithoutParent("Right arrow button to navigate to next month in calendar",
                                                      "(//*[@data-autoid='modifySearch']//*[contains(@class,'icon icon-arrow arrow_')])[2]")

    def selectDate(self, date: Annotated[int, "Day of the month (DD, e.g., 01 for 1st)"],
                   month: Annotated[str, "Month (MMM, e.g., Jan for January). Default: `NA`"],
                   year: Annotated[int, "Month (YYYY, e.g., 2025). Default: 0"]):
        if run_configs.dryRun == False:
            if month.upper().strip() == "NA":
                month = datetime.now().strftime("%b")
                print("Month not provided, using current month:", month)
            if year == 0:
                year = datetime.now().strftime("%Y")
                print("Year not provided, using current year:", year)
            # print(f"Selecting date: {date}, month: {month}, year: {year}")
            count = 0
            current_calendar_text = agentic_base.helper.getTextPure(self.calender_header_text())
            currentMonthYear = current_calendar_text.strip().split(" ")
            current_month: str = currentMonthYear[0]
            current_year: int = int(currentMonthYear[1].strip())
            while int(current_year) != int(year) or current_month[:3].lower() != month[:3].lower():
                if count > 12:
                    break
                agentic_base.helper.click(self.calender_forward_button())
                current_calendar_text = agentic_base.helper.getTextPure(self.calender_header_text())
                currentMonthYear = current_calendar_text.strip().split(" ")
                current_month: str = currentMonthYear[0]
                current_year: int = int(currentMonthYear[1].strip())
                count += 1
            agentic_base.helper.click(self.date(date))
            pass

    def date(self, date: int):
        date = str(date)
        return agentic_base.helper.selfHealWithoutParent("Exact Date on the calendar which is open",
                                                      "(//*[@data-autoid='modifySearch']//*[contains(@class,'date_')]/span[text()='{date}'])[1]",
                                                      date)

    def selectDateWhichIsXDaysFromToday(self, days_from_today):
        future_date = datetime.now() + timedelta(days=days_from_today)
        day = future_date.strftime("%d")
        month = future_date.strftime("%b")
        year = future_date.strftime("%Y")
        # print(f"Selecting date which is {days_from_today} days from today: {day}-{month}-{year}")
        self.selectDate(int(day), str(month), int(year))

    def __init__(self):
        run_configs.SECTION_AUTO_ID = ["//*[@data-autoid='topNavContainer']", "//*[@data-autoid='modifySearch']"]

    def back_navigation_button(self):
        run_configs.setRef("home_page")
        return agentic_base.helper.selfHeal("//*[@data-autoid='topNavContainer']//*[contains(@class,'actionButton_')]")

    def modify_button(self):
        run_configs.setRef("home_page")
        return agentic_base.helper.selfHeal("(//*[@data-autoid='topNavContainer']//*[contains(@class,'modifyButton_')])[1]")

    def close_modify_button(self):
        run_configs.setRef("search_result_page")
        return agentic_base.helper.selfHeal("(//*[@data-autoid='bottom-sheet']//*[contains(@class,'actionButton_')])[1]")



