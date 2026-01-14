from abc import abstractmethod
from typing import Annotated

class common:
    @abstractmethod
    def back_navigation_button(self):
        '''Navigates back to the previous home page'''

class mweb(common):
    @abstractmethod
    def modify_button(self):
        '''Opens SearchWidget section to modify journey details'''

    @abstractmethod
    def close_modify_button(self):
        '''Closes the opened SearchWidget section and this causes journey details remain unchanged'''


class dweb(common):
    @abstractmethod
    def src(self):
        """
        Locates the text input element within the departure section to modify and enter the starting location.
        This field becomes interactive only after activating 'from_input_section()'.
        """
        pass

    @abstractmethod
    def dest(self):
        """
        Locates the text input element within the arrival section to modify and enter the ending location.
        This field becomes interactive only after activating 'to_input_section()'.
        """
        pass

    @abstractmethod
    def citySuggestionsInDropDown(
            self, position: Annotated[int, "1-based index of the location suggestion in the dropdown list (default=1)"]
    ):
        """
        Selects a location suggestion from the  dropdown that appears after typing text in either 'src()' or 'dest()' fields, thereby completing the location selection process.
         **USAGE RULE**:
            - When requirement is to **"Enter the location"** - do NOT use this function. Only type in src() or dest().
            - When requirement is to **"Select the location"** - this function is MANDATORY after typing.
        """
        pass

    @abstractmethod
    def swap_locations_button(self):
        '''to swap the from and to locations'''

    @abstractmethod
    def remove_return_date_button(self):
        '''remove/clear the return date selection post modifying return date'''

    @abstractmethod
    def passenger_selection_section_opener(self):
        '''Opens the passenger selection section to modify passenger count'''

    @abstractmethod
    def passenger_selection_section_closer(self):
        '''Closes the passenger selection section if already opened. Without closing this nothing else can be done'''

    @abstractmethod
    def adult_decrease_button(self):
        '''Button to modify and decrease adult passenger count'''

    @abstractmethod
    def adult_increase_button(self):
        '''Button to modify and increase adult passenger count. Note: By default one adult is already added. So consider this while increasing adult count'''

    @abstractmethod
    def first_child_add_button(self):
        '''Button to modify and add only the first child passenger. By default no child is added. So consider this while adding child passenger'''

    @abstractmethod
    def subsequent_child_add_button(self):
        '''Button to modify and add subsequent child passengers post adding at least one child passenger'''

    @abstractmethod
    def child_decrease_button(self):
        '''Button to modify and decrease child passenger count. Note: This button appears after adding atleast one child passenger'''

    @abstractmethod
    def search_ferries_button(self):
        '''initiates ferry search post modification'''

    @abstractmethod
    def departure_date_calendar(self):
        '''Opens Calendar to select/modify the departure date. Also this field displays the departure/onward journey date post selection'''

    @abstractmethod
    def return_date_calendar(self):
        '''Opens Calendar to select/modify the return date'. Also this field displays the return date post selection'''

    @abstractmethod
    def from_input_section(self):
        """
        Locates the interactive container/region for modifying the departure location.
        This container must be clicked before interacting with the 'src()' input element.
        """
        pass

    @abstractmethod
    def to_input_section(self):
        """
        Locates the interactive container/region for modifying the arrival location.
        This container must be clicked before interacting with the 'dest()' input element.
        """
        pass

class android(common):
    pass

class ios(common):
    pass

