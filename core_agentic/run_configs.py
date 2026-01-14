import os
from pathlib import Path
from enum import Enum

class LLM_Provider(Enum):
    PERPLEXITY = "perplexity"
    AWS_BEDROCK = "bedrock"
    GEMINI = "gemini"
    OPENAI_INTERNAL = "openai_internal"

class LLM_MODEL(Enum):
    GPT_4O = "gpt-4O"
    SONNET_4_5 = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
    OPUS_4_5 = "global.anthropic.claude-opus-4-5-20251101-v1:0"
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_3 = "gemini-3-pro-preview"

from playwright.sync_api import Page, Browser, Playwright

channel = "mweb" # Options: "mweb", "dweb", "android", "ios"
url = "https://www.redbus.com.kh/ferry"
dryRun = False  # Set to True for dry run, False for actual execution
eventValidationGA = False  # Set to True to enable GA event validation
exactMatch = False  # When False it enables AI choose closest match for given text instead opf failing (Eg: Tamil Nadu -> Tamilnadu)
pageRef = "home_page"  # Initial page reference
llm_provider = LLM_Provider.GEMINI # Options: "openai", "gemini", "anthropic"
llm_model = LLM_MODEL.GEMINI_2_5_PRO
project_root_folder_name = 'leap'

## Variables used internally during execution
thinking = True
ref = 'home_page'
SECTION_AUTO_ID = []
pendingTask = []
completedSubtasks = []
countOfConsecutiveFailures = 0
codeStorage = []
variables = {}
agent = None
agentReasoning = ""
failedSubTask = "None"
orchestratorExecutionCount = 0
learnerList = {}
start_time = None
end_time = None
llmResponseTime = []
llmTokens = []
mobile_driver = None
page: Page = None  # type: Page
browser: Browser = None  # type: Browser
playwright: Playwright = None  # type: Playwright
newRef = None
mandatoryElement = True

swipe_start_vertical = 0.75
swipe_end_vertical = 0.25

rules_helper = None
sampleList = []

def get_project_root(start_path: str = None) -> str:
    """
    Finds and returns the project root directory path.
    
    Searches upward from the starting path for:
    1. A directory matching project_root_folder_name
    2. A directory containing 'src' folder (fallback)
    3. Current working directory (final fallback)
    
    Args:
        start_path: Starting directory path. Defaults to os.getcwd() if None.
    
    Returns:
        str: Absolute path to the project root directory
    """
    if start_path is None:
        start_path = os.getcwd()
    
    current_path = Path(start_path)
    
    # Strategy 1: Search upwards for the project root folder name
    for parent in [current_path] + list(current_path.parents):
        if parent.name == project_root_folder_name:
            return str(parent)
    
    # Strategy 2: Fallback - look for a directory containing 'src'
    for parent in [current_path] + list(current_path.parents):
        if (parent / 'src').exists():
            return str(parent)
    
    # Strategy 3: Final fallback - use starting path's parent or cwd
    if os.path.isdir(start_path):
        return start_path
    return os.path.dirname(start_path) if start_path != os.getcwd() else start_path

def getRef():
    return ref

def setRef(new_ref):
    global newRef
    newRef = new_ref

def getNewRef():
    global newRef
    return newRef

def reset_global_variables():
    """
        Resets all global variables back to their original values.
    """
    global dryRun, exactMatch, pageRef
    global ref, SECTION_AUTO_ID, pendingTask
    global completedSubtasks, countOfConsecutiveFailures, codeStorage, variables
    global agent, agentReasoning, failedSubTask, orchestratorExecutionCount
    global learnerList, start_time, end_time, llmResponseTime, llmTokens
    global page, browser, playwright, newRef, mandatoryElement, sampleList, mobile_driver
    ref = None
    SECTION_AUTO_ID = []
    pendingTask = []
    completedSubtasks = []
    countOfConsecutiveFailures = 0
    codeStorage = []
    variables = {}
    agent = None
    agentReasoning = ""
    failedSubTask = "None"
    orchestratorExecutionCount = 0
    learnerList = {}
    start_time = None
    end_time = None
    llmResponseTime = []
    llmTokens = []
    page = None
    browser = None
    playwright = None
    mobile_driver = None
    newRef = None
    mandatoryElement = True
    sampleList = []
