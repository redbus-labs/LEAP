from typing import Annotated
import core_agentic.agentic_base as agentic_base
from core_agentic import run_configs
from ..definition.agent_locator_tools import ios as LocatorTools
from ..definition.agent_function_tools import ios as FunctionTools

class top_header(LocatorTools, FunctionTools):
    def __init__(self):
        run_configs.SECTION_AUTO_ID = []
 
