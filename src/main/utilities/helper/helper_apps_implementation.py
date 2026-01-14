from typing import Annotated

from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.webdriver import WebDriver
from selenium.common import NoSuchElementException
from selenium.webdriver import ActionChains

from core_agentic import run_configs
from src.main.utilities.helper.helper_common import HelperInterface

mobile_driver: WebDriver = None

class HelperApps(HelperInterface):
    def __init__(self, mobile_driver_obj: WebDriver):
        global mobile_driver
        mobile_driver = mobile_driver_obj

    def find_element(self, element):
        return self.scrollToElement(element)

    def swipe_up(self):
        """Perform a universal W3C swipe (works for iOS + Android)."""
        size = mobile_driver.get_window_size()
        start_x = size["width"] / 2
        start_y = size["height"] * run_configs.swipe_start_vertical
        end_x = size["width"] / 2
        end_y = size["height"] * run_configs.swipe_end_vertical

        actions = ActionChains(mobile_driver)
        actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.move_to_location(end_x, end_y)
        actions.w3c_actions.pointer_action.release()
        actions.perform()

    def scrollToElement(self, element):
        if run_configs.dryRun == False:
            max_swipes = 10
            for _ in range(max_swipes):
                try:
                    return mobile_driver.find_element(AppiumBy.XPATH, element)
                except Exception:
                    self.swipe_up()
            raise Exception(f"Element not found after {max_swipes} swipes: {element}")

    def click(self, element: Annotated[str, "Locator of the WebElement"]):
        if run_configs.dryRun == False:
            self.find_element(element).click()

    def type(self, element: Annotated[str, "Locator of the WebElement"], text: Annotated[str, "Text to be entered"]):
        if run_configs.dryRun == False:
            self.find_element(element).send_keys(text)

    def clearText(self, locator: Annotated[str, "Locator of the WebElement"]):
        if run_configs.dryRun == False:
            self.find_element(locator).clear()

    def verifyBrokenLink(self, locator: Annotated[
        str, "Exact Locator which contains the links to be verified for broken link"]):
        pass

    def mock_api(self, api_key: str, mock_file: str):
        pass

    def navigateBack(self):
        if run_configs.dryRun == False:
            if run_configs.channel.lower().strip() == "android":
                mobile_driver.back()
            else:
                # iOS
                mobile_driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Back").click()

    def getTextPure(self, locator):
        if run_configs.dryRun == False:
            return self.find_element(locator).text

    def is_broken_link(self, url: str) -> bool:
        pass

    def getAllTexts(self, locator) -> list[str]:
        if run_configs.dryRun == False:
            elements = mobile_driver.find_elements(AppiumBy.XPATH, locator)
            texts = [el.text for el in elements]
            return texts

    def locatorCount(self, locator) -> int:
        if run_configs.dryRun == False:
            return len(mobile_driver.find_elements(AppiumBy.XPATH, locator))

    def scroll_the_element_to_top(self, element):
        pass

    def scroll_to_bottom_of_page(self):
        pass

    def is_locator_present(self, element):
        if run_configs.dryRun == False:
            count = len(mobile_driver.find_elements(AppiumBy.XPATH, element))
            return count > 0

    def take_screenshot_as_base64(self) -> str:
        if run_configs.dryRun == False:
            return mobile_driver.get_screenshot_as_base64()