from datetime import datetime, timedelta

import core_agentic.agentic_base as agentic_base
from core_agentic import run_configs
from ..definition.agent_locator_tools import mweb as LocatorToolsMweb
from ..definition.agent_locator_tools import dweb as LocatorToolsDweb
from ..definition.agent_function_tools import mweb as FunctionToolsMweb
from ..definition.agent_function_tools import dweb as FunctionToolsDweb

class search_widget(LocatorToolsMweb, LocatorToolsDweb, FunctionToolsDweb, FunctionToolsMweb):
    def __init__(self):
        if run_configs.channel == "dweb":
            run_configs.SECTION_AUTO_ID = ["//*[contains(@class,'searchWidgetWrapper_')]"]
        else:
            run_configs.SECTION_AUTO_ID = ["//*[contains(@class,'searchWidgetWrapper_')]",
                                       "//*[@data-autoid='bottom-sheet']"]

    def subsequent_child_add_button(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'icon_')])[8]")

    def child_decrease_button(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'icon_')])[7]")

    def src(self):
        if run_configs.channel == "dweb":
            return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'labelCityWrapper_')])[1]")
        return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'searchInput_')])[1]")

    def from_input_section(self):
        if run_configs.channel == "dweb":
            return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'labelCityWrapper_')])[1]")
        return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'label_')])[1]")

    def citySuggestionsInDropDown(self, position):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'listHeader_')])[{position}]")

    def dest(self):
        if run_configs.channel == "dweb":
            return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'labelCityWrapper_')])[2]")
        return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'searchInput_')])[1]")

    def clear_src(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'icon-close')])[1]")

    def back_navigation_button(self):
        return agentic_base.helper.selfHeal("//*[@data-autoid='searchWidget']//*[contains(@class,'icon-arrow_back')]")

    def to_input_section(self):
        if run_configs.channel == "dweb":
            return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'labelCityWrapper_')])[2]")
        return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'label_')])[2]")

    def swap_locations_button(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'swapIcon_')])[1]")

    def remove_return_date_button(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'removeReturnIcon_')])[1]")

    def adult_decrease_button(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'icon_')])[5]")

    def adult_increase_button(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'icon_')])[6]")

    def first_child_add_button(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'addBtn_')])[1]")

    def search_ferries_button(self):
        run_configs.setRef("search_result_page")
        return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'primaryButton_')])[1]")

    def departure_date_calendar(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'dojWrapper_')])[1]")

    def return_date_calendar(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='searchWidget']//*[contains(@class,'dojWrapper_')])[2]")

    def date(self, date: int):
        date = str(date)
        if run_configs.channel == "dweb":
            return agentic_base.helper.selfHealWithoutParent("Exact Date on the calendar which is open",
                                                     "(//*[@data-autoid='searchWidget']//*[contains(@class,'date_')]/span[text()='{date}'])[1]",
                                                     date)
        return agentic_base.helper.selfHealWithoutParent("Exact Date on the calendar which is open",
                                                 "(//*[@data-autoid='bottom-sheet']//*[contains(@class,'date_')]/span[text()='{date}'])[1]",
                                                 date)

    def calender_header_text(self):
        if run_configs.channel == "dweb":
            return agentic_base.helper.selfHealWithoutParent("Field which displays Month and Year",
                                                     "(//*[@data-autoid='searchWidget']//*[contains(@class,'monthYear_')])[1]")
        return agentic_base.helper.selfHealWithoutParent("Field which displays Month and Year",
                                                 "(//*[@data-autoid='bottom-sheet']//*[contains(@class,'monthYear_')])[1]")

    def calender_forward_button(self):
        if run_configs.channel == "dweb":
            return agentic_base.helper.selfHealWithoutParent("Right arrow button to navigate to next month in calendar",
                                                     "(//*[@data-autoid='searchWidget']//*[contains(@class,'icon icon-arrow arrow_')])[2]")
        return agentic_base.helper.selfHealWithoutParent("Right arrow button to navigate to next month in calendar",
                                                 "(//*[@data-autoid='bottom-sheet']//*[contains(@class,'icon icon-arrow arrow_')])[2]")

    #
    def selectDate(self, date: int, month="NA", year=0):
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

    def selectDateWhichIsXDaysFromToday(self, days_from_today):
        future_date = datetime.now() + timedelta(days=days_from_today)
        day = future_date.strftime("%d")
        month = future_date.strftime("%b")
        year = future_date.strftime("%Y")
        # print(f"Selecting date which is {days_from_today} days from today: {day}-{month}-{year}")
        self.selectDate(int(day), str(month), int(year))

    def captureDisappearingErrorMessage(self):
        run_configs.setRef("home_page")
        run_configs.variables['error_message'] = agentic_base.helper.getTextPure(
            "//*[contains(@class,'searchWidgetWrapper_')]//*[contains(@class,'message_')]")
        print("Error message captured:", run_configs.variables['error_message'])


