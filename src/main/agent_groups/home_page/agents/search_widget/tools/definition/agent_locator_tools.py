from abc import abstractmethod
from typing import Annotated


class common:
    @abstractmethod
    def from_input_section(self):
        """
        Opens the container inside which the source location can be specified."""
        pass

    @abstractmethod
    def to_input_section(self):
        """
        Opens the container inside which the destination location can be specified."""
        pass

    @abstractmethod
    def src(self):
        """
        Input field present inside the container opened by 'from_input_section()' for entering the starting location.
        """
        pass

    @abstractmethod
    def dest(self):
        """
        Input field present inside the container opened by 'to_input_section()' for entering the ending location.
        """
        pass

    @abstractmethod
    def citySuggestionsInDropDown(
            self, position: Annotated[int, "Index of the location suggestion in the dropdown list (default=1)"]
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
        '''remove/clear the return date selection post selecting return date'''

    @abstractmethod
    def adult_decrease_button(self):
        '''Button to decrease adult passenger count'''

    @abstractmethod
    def adult_increase_button(self):
        '''Button to increase adult passenger count. Note: By default one adult is already added. So consider this while increasing adult count'''

    @abstractmethod
    def first_child_add_button(self):
        '''Button to add only the first child passenger. By default no child is added. So consider this while adding child passenger'''

    @abstractmethod
    def subsequent_child_add_button(self):
        '''Button to add subsequent child passengers post adding at least one child passenger'''

    @abstractmethod
    def child_decrease_button(self):
        '''Button to decrease child passenger count. Note: This button appears after adding atleast one child passenger'''

    @abstractmethod
    def search_ferries_button(self):
        '''initiates ferry search '''

    @abstractmethod
    def departure_date_calendar(self):
        '''Opens Calendar to select the departure date. Also this field displays the departure/onward journey date post selection'''

    @abstractmethod
    def return_date_calendar(self):
        '''Opens Calendar to select the return date'. Also this field displays the return date post selection'''


class mweb(common):
    @abstractmethod
    def back_navigation_button(self):
        """Without selecting any location from the city suggestion dropdown, if we have to go back to home page from the src() or dest() input field, this button is to be clicked"""

    def clear_src(self):
        """
        Clicking on this clears any text in the source input field.
        """
        pass

class dweb(common):
    pass

class android(common):
    pass

class ios(common):
    pass

