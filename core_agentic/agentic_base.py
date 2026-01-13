import ast
import csv
import re
import io
from datetime import datetime
import time
import importlib.util
import inspect
import sys
import os
from pathlib import Path
from types import ModuleType
from typing import List, Tuple

import yaml
from appium.webdriver.common.appiumby import AppiumBy
from appium import webdriver
from appium.webdriver.webdriver import WebDriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from playwright.sync_api import sync_playwright, Page, Browser, Playwright
from core_agentic import run_configs
from src.main.utilities.helper.helper_apps_implementation import HelperApps

from src.main.utilities.helper.helper_browser_implementation import HelperBrowser
from src.main.utilities.helper.helper_common import HelperInterface

page: Page = None
playwright: Playwright = None
browser: Browser = None
mobile_driver: WebDriver = None

helper: HelperInterface = HelperInterface()
POR = None

def launch_app():
    global mobile_driver
    if run_configs.channel.lower().strip() == "android":
        print("Android Execution")
        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.device_name = "Pixel 7a"
        options.app_package = ""  # replace with actual package
        options.app_activity = ""  # replace with actual launch activity
        options.no_reset = True
    else:
        print("iOS Execution")
        options = XCUITestOptions()
        options.platform_name = "iOS"
        options.udid = ""
        options.bundle_id = ""
        options.no_reset = True
    mobile_driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
    mobile_driver.implicitly_wait(10)

def launch_browser():
    global page, playwright, browser
    if not run_configs.dryRun:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=False)
        context = None
        if run_configs.channel == "dweb":
            context = browser.new_context()
        elif run_configs.channel == "mweb":
            # dict_keys(['Blackberry PlayBook', 'Blackberry PlayBook landscape', 'BlackBerry Z30', 'BlackBerry Z30 landscape', 'Galaxy Note 3', 'Galaxy Note 3 landscape', 'Galaxy Note II', 'Galaxy Note II landscape', 'Galaxy S III', 'Galaxy S III landscape', 'Galaxy S5', 'Galaxy S5 landscape', 'Galaxy S8', 'Galaxy S8 landscape', 'Galaxy S9+', 'Galaxy S9+ landscape', 'Galaxy S24', 'Galaxy S24 landscape', 'Galaxy A55', 'Galaxy A55 landscape', 'Galaxy Tab S4', 'Galaxy Tab S4 landscape', 'Galaxy Tab S9', 'Galaxy Tab S9 landscape', 'iPad (gen 5)', 'iPad (gen 5) landscape', 'iPad (gen 6)', 'iPad (gen 6) landscape', 'iPad (gen 7)', 'iPad (gen 7) landscape', 'iPad (gen 11)', 'iPad (gen 11) landscape', 'iPad Mini', 'iPad Mini landscape', 'iPad Pro 11', 'iPad Pro 11 landscape', 'iPhone 6', 'iPhone 6 landscape', 'iPhone 6 Plus', 'iPhone 6 Plus landscape', 'iPhone 7', 'iPhone 7 landscape', 'iPhone 7 Plus', 'iPhone 7 Plus landscape', 'iPhone 8', 'iPhone 8 landscape', 'iPhone 8 Plus', 'iPhone 8 Plus landscape', 'iPhone SE', 'iPhone SE landscape', 'iPhone SE (3rd gen)', 'iPhone SE (3rd gen) landscape', 'iPhone X', 'iPhone X landscape', 'iPhone XR', 'iPhone XR landscape', 'iPhone 11', 'iPhone 11 landscape', 'iPhone 11 Pro', 'iPhone 11 Pro landscape', 'iPhone 11 Pro Max', 'iPhone 11 Pro Max landscape', 'iPhone 12', 'iPhone 12 landscape', 'iPhone 12 Pro', 'iPhone 12 Pro landscape', 'iPhone 12 Pro Max', 'iPhone 12 Pro Max landscape', 'iPhone 12 Mini', 'iPhone 12 Mini landscape', 'iPhone 13', 'iPhone 13 landscape', 'iPhone 13 Pro', 'iPhone 13 Pro landscape', 'iPhone 13 Pro Max', 'iPhone 13 Pro Max landscape', 'iPhone 13 Mini', 'iPhone 13 Mini landscape', 'iPhone 14', 'iPhone 14 landscape', 'iPhone 14 Plus', 'iPhone 14 Plus landscape', 'iPhone 14 Pro', 'iPhone 14 Pro landscape', 'iPhone 14 Pro Max', 'iPhone 14 Pro Max landscape', 'iPhone 15', 'iPhone 15 landscape', 'iPhone 15 Plus', 'iPhone 15 Plus landscape', 'iPhone 15 Pro', 'iPhone 15 Pro landscape', 'iPhone 15 Pro Max', 'iPhone 15 Pro Max landscape', 'Kindle Fire HDX', 'Kindle Fire HDX landscape', 'LG Optimus L70', 'LG Optimus L70 landscape', 'Microsoft Lumia 550', 'Microsoft Lumia 550 landscape', 'Microsoft Lumia 950', 'Microsoft Lumia 950 landscape', 'Nexus 10', 'Nexus 10 landscape', 'Nexus 4', 'Nexus 4 landscape', 'Nexus 5', 'Nexus 5 landscape', 'Nexus 5X', 'Nexus 5X landscape', 'Nexus 6', 'Nexus 6 landscape', 'Nexus 6P', 'Nexus 6P landscape', 'Nexus 7', 'Nexus 7 landscape', 'Nokia Lumia 520', 'Nokia Lumia 520 landscape', 'Nokia N9', 'Nokia N9 landscape', 'Pixel 2', 'Pixel 2 landscape', 'Pixel 2 XL', 'Pixel 2 XL landscape', 'Pixel 3', 'Pixel 3 landscape', 'Pixel 4', 'Pixel 4 landscape', 'Pixel 4a (5G)', 'Pixel 4a (5G) landscape', 'Pixel 5', 'Pixel 5 landscape', 'Pixel 7', 'Pixel 7 landscape', 'Moto G4', 'Moto G4 landscape', 'Desktop Chrome HiDPI', 'Desktop Edge HiDPI', 'Desktop Firefox HiDPI', 'Desktop Safari', 'Desktop Chrome', 'Desktop Edge', 'Desktop Firefox'])
            device = playwright.devices['Pixel 7']
            context = browser.new_context(**device)
        context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True  # Optional: include source files
        )
        page = context.new_page()
        page.goto(run_configs.url)

def closeBrowser():
    global page, browser, playwright, mobile_driver, helper
    if "web" in run_configs.channel.lower().strip():
        if run_configs.eventValidationGA:
            helper.clear_events()
        page.close()
        browser.close()
        playwright.stop()
    else:
        mobile_driver.quit()

def getPage() -> Page:
    global page
    return page

def extract_agent_info(file_path: str, channel: str):
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        tree = ast.parse(f.read())

    class_defs = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}

    agent_name = None
    agent_description = None

    # Get common class values
    if 'common' in class_defs:
        for stmt in class_defs['common'].body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "agent_name" and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                            agent_name = stmt.value.value
                        elif target.id == "agent_description" and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                            agent_description = stmt.value.value

    # Check for channel class overrides
    channel_class = class_defs.get(channel)
    if channel_class:
        for stmt in channel_class.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "agent_name" and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                            agent_name = stmt.value.value
                        elif target.id == "agent_description" and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                            agent_description = stmt.value.value

    if agent_name and agent_description:
        return (agent_name, agent_description)
    else:
        # print("⚠️ No valid tools found.")
        return None

def getAgentsBasedOnRef() -> str:
    project_root = run_configs.get_project_root()

    print("Current Agent Group: " + run_configs.ref)

    folder_path = os.path.join(
        project_root,
        "src",
        "main",
        "agent_groups",
        f"{run_configs.ref}" ,
        "agents"
    )

    if not os.path.exists(folder_path):
        return ""

    agents = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file == "agent_details.py":
                full_path = os.path.join(root, file)
                result = extract_agent_info(full_path, run_configs.channel)
                if result:
                    agents.append(result)

    # Write CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["AgentName", "AgentDescription"])
    for name, desc in agents:
        writer.writerow([name, desc.strip()])

    csv_string = output.getvalue()
    output.close()
    return csv_string

def readLearner() -> str:
    project_root = run_configs.get_project_root()

    file_path = os.path.join(project_root, "learner.csv")
    
    if not os.path.exists(file_path):
        return ""

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        output = io.StringIO()
        writer = csv.writer(output)
        for row in reader:
            writer.writerow(row)
        return output.getvalue()

def getTools(toolType:str):
    className = ""
    input_file = ""
    if (toolType.lower().strip() == "helper"):
        input_file = "/src/main/utilities/helper/helper_description.py"
        className = "HelperAgent"
    elif (toolType.lower().strip() == "locator"):
        input_file = f"/src/main/agent_groups/{run_configs.ref}/agents/{run_configs.agent}/tools/definition/agent_locator_tools.py"
        className = run_configs.channel
    elif (toolType.lower().strip() == "function"):
        input_file = f"/src/main/agent_groups/{run_configs.ref}/agents/{run_configs.agent}/tools/definition/agent_function_tools.py"
        className = run_configs.channel

    project_root = run_configs.get_project_root()

    finalString = analyze_abstract_methods(str(project_root) + str(input_file), className)
    return finalString

def get_agents_por():
    module_path = f"src.main.por.por_agent_groups"
    module = importlib.import_module(module_path)
    return getattr(module, "Agents_POR")

def initialSetup():
    global page, helper, POR, mobile_driver
    if "web" in run_configs.channel.lower().strip():
        launch_browser()
        helper = HelperBrowser(page)
    else:
        launch_app()
        helper = HelperApps(mobile_driver)
    Agents_POR_Class = get_agents_por()
    POR = Agents_POR_Class()

def refChangeCheck():
    global helper
    if run_configs.dryRun == False:
        newRef = run_configs.newRef
        oldRef = run_configs.ref
        if oldRef != newRef:
            print("---------------------PAGE CHANGE VALIDATION---------------------")
            desc = newRef
            if newRef == "home_page":
                desc = "Home Page of Ferry booking application. If you find a search widget with Source, Destination, Departure date and Return date fields, you are on the correct page. Important: If the page has a modify search option, on top of search result page, it should still be considered as home page"
            elif newRef == "search_result_page":
                desc = "Displaying ferries available based on search criteria (No ferries available message may be displayed if no ferries are available)"
            elif newRef == "time_selection_page":
                desc = "Displaying list of time slots available for the selected ferry"
            response = helper.visualValidation(helper.take_screenshot_as_base64(),
                                        "Check the entire screenshot and verify if we are on " + newRef + ": " + desc)
            arr = response.split("|")
            check = arr[0].strip().lower()
            reasoning = arr[1].strip()
            if check == "false":
                # setRef(oldRef)
                error_msg = f"❌ PAGE CHANGE VALIDATION FAILED!\n" + \
                           f"───────────────────────────────\n" + \
                           f"Expected Page: {newRef}\n" + \
                           f"Reason: {reasoning}\n"
                print(error_msg)
            else:
                run_configs.ref = newRef
                print("Page changed successfully to: " + newRef + "\nReasoning: " + reasoning)

def afterExecutionCleanup():
    global page
    print("--------------------Cleanup started---------------------------------------------")
    print("Code Storage: ")
    for s in run_configs.codeStorage:
        print("        " + s)
    if "web" in run_configs.channel.lower().strip():
        try:
            page.context.tracing.stop(path="trace.zip")
        except Exception as e:
            pass
    else:
       mobile_driver.quit()
    run_configs.end_time = time.time()
    try:
        page.context.tracing.stop(path="trace.zip")
    except Exception as e:
        pass
    closeBrowser()
    run_configs.end_time = time.time()
    print(f"End time: {datetime.now()}")
    duration = run_configs.end_time - run_configs.start_time
    print(f"Total execution time: {duration:.2f} seconds")
    print("Total LLM calls: " + str(len(run_configs.llmResponseTime)))
    print("Total tokens consumed by all LLM calls: " + str(sum(run_configs.llmTokens)))
    llmTotalTime = sum(run_configs.llmResponseTime)
    print(f"Total time consumed by all LLM calls: {llmTotalTime:.2f} seconds")
    print(f"Portion of execution time consumed by LLM: {(llmTotalTime / duration) * 100:.2f}%")
    run_configs.reset_global_variables()
    print("--------------------Cleanup Done---------------------------------------------")
    print("------------------------------END OF AGENTIC EXECUTION-----------------------------------")

def append_record_to_csv(csv_file_path, record_dict):
    """
    Appends a dictionary record to a CSV file with auto-incrementing ID.

    Args:
        csv_file_path (str): Path to the CSV file
        record_dict (dict): Dictionary containing record data (excluding ID)
                           Expected keys: 'Failed Subtask', 'Failure Reason',
                           'Agent Selected', 'Reasoning for Agent Selection',
                           'Task to be performed'

    Returns:
        int: The ID assigned to the new record

    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        KeyError: If required keys are missing from record_dict
    """

    # Define the expected headers (excluding ID which will be auto-generated)
    expected_keys = [
        'Failed Subtask',
        'Failure Reason',
        'Agent Selected',
        'Reasoning for Agent Selection',
        'Task to Perform'
    ]

    # Validate input dictionary
    missing_keys = [key for key in expected_keys if key not in record_dict]
    if missing_keys:
        raise KeyError(f"Missing required keys in record_dict: {missing_keys}")

    # Check if file exists
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")

    # Read the file to get the last ID and check if file ends with newline
    last_id = 0
    file_needs_newline = False

    try:
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            if rows:
                # Get the last row's ID and convert to int
                last_id = int(rows[-1]['ID'])

        # Check if file ends with newline
        with open(csv_file_path, 'rb') as file:
            file.seek(-1, 2)  # Go to the last byte
            last_char = file.read(1)
            if last_char != b'\n' and last_char != b'\r\n':
                file_needs_newline = True

    except (ValueError, KeyError):
        # If there's an issue reading the last ID, start from 0
        last_id = 0

    # Generate new ID
    new_id = last_id + 1

    # Create the complete record with ID
    complete_record = {'ID': new_id, **record_dict}

    # Append to CSV file
    with open(csv_file_path, 'a', newline='', encoding='utf-8') as file:
        # Add newline if the file doesn't end with one
        if file_needs_newline:
            file.write('\n')

        fieldnames = ['ID'] + expected_keys
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writerow(complete_record)

    return new_id

def findAgentAndDescription(multiline_string, textToStarWith):
    for line in multiline_string.splitlines():
        if line.startswith(textToStarWith):
            return line
    return None  # Return None if no such line is found

def load_module_from_file(filepath: str) -> ModuleType:
    """
    Dynamically loads a Python module from the given file path.
    """
    module_name = os.path.splitext(os.path.basename(filepath))[0]
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def get_abstract_methods(cls: type) -> List[Tuple[str, str, str]]:
    """
    Retrieves all abstract methods in the class.
    Returns a list of tuples: (method_name, signature, docstring)
    """
    abstract_methods_info = []
    for name, member in inspect.getmembers(cls, inspect.isfunction):
        if getattr(member, "__isabstractmethod__", False):
            sig = str(inspect.signature(member))
            doc = inspect.getdoc(member) or ""
            abstract_methods_info.append((name, sig, doc))
    return abstract_methods_info

def analyze_abstract_methods(filepath: str, classname: str):
    """
    Main function to:
    - load the module
    - locate the class
    - instantiate it if possible
    - list abstract methods
    """
    module = load_module_from_file(filepath)
    cls = getattr(module, classname, None)

    if cls is None:
        print(f"Class {classname} not found in {filepath}.")
        return

    # Check if class is abstract
    is_abstract = bool(getattr(cls, "__abstractmethods__", False))

    if is_abstract:
        print(f"Class {classname} is abstract and cannot be instantiated directly.")
    # else:
    # Try instantiating
    # try:
    #     instance = cls()
    #     print(f"Successfully instantiated class {classname}.")
    # except Exception as e:
    #     print(f"Could not instantiate class {classname}: {e}")

    abstract_methods = get_abstract_methods(cls)
    finalString = ""
    if abstract_methods:
        # print(f"\nAbstract methods in class {classname}:")
        for name, sig, doc in abstract_methods:
            finalString = finalString + f"- {name}{sig}"
            finalString = finalString + f"\n  {doc}\n\n"
            # print(f"- {name}{sig}")
            # print(f"  {doc}")
            # print()
    # else:
    # print(f"No abstract methods found in class {classname}.")
    return finalString

def replaceConfigsInString(text: str) -> str:
    """
    Replaces all config placeholders (e.g., <source>, <destination>) in a string 
    with their actual values from YAML files.
    
    Args:
        text: String containing placeholders like <source>, <validEmail>, etc.
    
    Returns:
        String with all placeholders replaced by their config values
    """
    import re
    
    # Find all placeholders in the format <something>
    placeholders = re.findall(r'<[^>]+>', text)
    
    result = text
    for placeholder in placeholders:
        config_value = getConfig(placeholder)
        if config_value is not None:
            result = result.replace(placeholder, str(config_value))
    
    return result

def getConfig(key: str):
    """
    Retrieves test data config values from YAML files with intelligent cascading fallback.
    """
    # Remove angle brackets for YAML lookup
    clean_key = key.replace('<', '').replace('>', '')

    # Find project root
    project_root = run_configs.get_project_root(os.path.dirname(os.path.abspath(__file__)))

    # Build cascading file paths (most specific to least specific)
    base_path = os.path.join(project_root, "src", "resources", "configs")

    file_paths = [
        os.path.join(base_path, f"{run_configs.channel.lower()}_test_data.yaml"),      # 1. channel
        os.path.join(base_path, "common_test_data.yaml"),                               # 2. common
        os.path.join(base_path, f"{run_configs.channel.lower()}_test_data.yaml"),             # 3. common/channel
        os.path.join(base_path, "common_test_data.yaml")                                       # 4. common/common (base)
    ]

    # Try each file in priority order
    for yaml_path in file_paths:
        if not os.path.exists(yaml_path):
            continue

        try:
            with open(yaml_path, 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
                if data and clean_key in data:
                    value = data[clean_key]
                    return value
        except Exception as e:
            print(f"⚠️  Error reading {yaml_path}: {e}")
            continue

    # Not found in any file
    print(f"⚠️  Config not found: {key} (searched {len(file_paths)} files)")
    return None
