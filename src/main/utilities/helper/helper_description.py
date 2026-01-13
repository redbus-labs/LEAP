from abc import ABC, abstractmethod
from typing import Annotated

class HelperAgent:
    
    def __init__(self):
        pass

    @abstractmethod
    def click(self, element: Annotated[str, "Locator of the WebElement"]):
        '''Click on the element/Select an element'''

    @abstractmethod
    def type(self, element: Annotated[str, "Locator of the WebElement"], text: Annotated[str, "Text to be entered"]):
        '''Mimics keyboard input on the provided web element'''

    @abstractmethod
    def clickAndVerifyGAEvent(self, element: Annotated[str, "Locator of the WebElement to click upon which the GA event which needs to be verified will be triggered"], gaID: Annotated[list, "list of GA event IDs to be verified after clicking the element"], dynamicParams: Annotated[dict, "Dictionary of dynamic parameters to be passed to the GA event verification function. Pass empty python dictionary if no dynamic parameters are required"]):
        '''To click on the element and verify the GA event triggered by clicking the element.'''

    @abstractmethod
    def getText(self,
                element: Annotated[
                str, "Locator of the WebElement"
                     "If you cannot find a suitable locator but if the Agent and it's Description is relevant for the text to capture,"
                     "Pass `None` but never skip/terminate in this case"
                ],
                textDescription: Annotated[
                    str,
                    "Describe the text context of the element to be captured"
                ],
                keyName: Annotated[
                    str,
                    "Meaningful key name to store the extracted value in `variables` dictionary for future use. "
                    "Pass `None` if noting down the value is not required"
                ]) -> str:
        '''Extracts the text context. If required, stores it in `variables` dictionary with a meaningful key. STRICTLY DO NOT use this for assertions
        If the text extracted will be instantly used for verification, use assertionVisual() instead as it optimizes the workflow by combining text extraction and verification in one step.'''

    @abstractmethod
    def assertion(self, assertion: Annotated[str,"derived strictly from the user-provided task and the values from `variables` dictionary if applicable"]):
        '''
        Use this assertion to verify/compare two values that are BOTH already captured/noted in the `variables` dictionary, or to compare one noted value from `variables` with a hardcoded constant value that you know without needing to read from the UI.

        This function does NOT read or verify anything currently displayed on the UI. It only works with:
        1. Two noted values: variables['value1'] vs variables['value2']
        2. One noted value vs a constant: variables['value1'] vs "Expected Constant"

        If you need to verify what's currently displayed/visible on the UI, use assertionVisual() instead.

        Ensure that the assertion is strictly derived from the user-provided task. Strictly DO NOT have a vague or generic assertion.

        Example:
            variables: dict = {'name1': 'Krishna Hegde', 'name2': 'Krishna Hegde', 'expected_price': '500'}
            assertion = f"Verify that the noted name {variables['name1']} matches {variables['name2']}" -> Correct (both are noted values)
            assertion = f"Verify that the noted price {variables['expected_price']} is 500" -> Correct (noted value vs constant)
            assertion = "Verify that the displayed name matches the expected name" -> Wrong (requires UI reading, use assertionVisual)

        Note: For any config related assertion (e.g, verify if the value is same as config), you must fetch the config value using getConfig()


    IMPORTANT: Make sure to justify if you followed all specified assertion rules in your reasoning.
        '''

    @abstractmethod
    def assertionVisual(self,
                        element: Annotated[
                      str, "Locator Preference Rules:\n\n"
                           "1. Preference 1 – Exact Locator of Target Web Element\n   "
                           "    - If verifying a specific element (e.g., 'verify if A is displayed') and the exact locator of the target element (A) is available, always use that locator.\n\n"
                           "2. Preference 2 – Exact Locator of Reference Web Element\n   "
                           "    - If the target element’s locator is not available, but a related/reference element’s locator is available (e.g., 'verify if A is above B' and locator of B is available), then use the reference element’s locator.\n\n"
                           "3. Preference 3 – None as Locator\n   "
                           "    - If neither the target element’s locator nor any reference element’s locator is available, but the relevant Agent and its Description apply to the assertion, then pass `None` as the locator.\n   "
                           "    - Important: Never skip or terminate the assertion in this case. Always proceed with `None`."
                  ],
                        assertion: Annotated[
                      str,
                      "derived strictly from the user-provided task. Strictly DO NOT have a vague or genric assertion. Example of bad assertion: Verify that the search results page loads successfully with buses displayed for the selected route and date. - This is a bad because route and date are not specified. Also, do not specify the actions which were performed previously or the actions which will be performed post assertion. It should strictly be only the assertion"
                  ]
                        ):
        '''
        Execute a visual assertion that reads/verifies what is currently displayed or visible on the UI. Use this when you need to:
1. Verify if something is displayed/visible on the screen
2. Compare a displayed UI value with a noted value from variables
3. Check UI state, presence of elements, or visual content

This function CAN read from the UI and compare with stored values or constants.

If this assertion depends on values captured earlier during the workflow, ensure you retrieve those values from the `variables` dictionary and explicitly reference them in your prompt.

Example:
variables = {"expected_name": "Krishna Hegde"}
assertion = f"Verify that the displayed name is {variables['expected_name']}" -> Correct (UI verification)
assertion = "Verify that the login button is visible" -> Correct (UI state check)
assertion = f"Verify that {variables['name1']} equals {variables['name2']}" -> Wrong (no UI reading needed, use assertion)

If you want to verify if a date is 'x' days from today, calculate the date by referring to the current date in `variables` and pass the calculated date in the assertion.

Assertion should never have action. Example: verify x after performing/selecting y, select x and verify y, etc.
The pending action takes the priority over the assertion. Skip performing assertion at this point and make sure to perform the action first.

NOTE: Locator purpose does not matter. If a locator is used for selection, comparison, etc., it can still be used for assertion. The only thing that matters is whether the locator is available or not.

CRITICAL CHECK: Ensure Locator Preference Rules are strictly followed. First you should always attempt Preference 1, if not possible then Preference 2, and only if neither is possible, use Preference 3.
IMPORTANT: Make sure to justify if you followed all specified assertion rules in your reasoning along with CRITICAL CHECK'''
    @abstractmethod
    def clearText(self, element: Annotated[str, "Locator of the WebElement"]):
        '''Clear the text in an input field '''

    @abstractmethod
    def refreshPage(self):
        '''Refresh the current page'''

    @abstractmethod
    def verifyBrokenLink(self, locator: Annotated[str, "Exact Locator which contains the links to be verified for broken link"]):
        '''Verifies if the links available at the given web element are broken or not. Passing None is PROHIBITED. You have to pass the locator. If you cannot find a suitable locator, you must skip the broken link verification instead of passing None'''

    @abstractmethod
    def wait_pause(self, seconds: Annotated[int, "Number of seconds to pause/wait (default 5)"]):
        '''Pause/wait for the specified number of seconds. Make sure to use this only when the necessary pre requisite action is performed. Else we would end up waiting for the wrong element. Following task sequence becomes mandatory for this. This rule overrides any other rule specified w.r.t task order to follow'''
