from typing import Annotated
import core_agentic.agentic_base as agentic_base
from core_agentic import run_configs
from ..definition.agent_locator_tools import android as LocatorTools
from ..definition.agent_function_tools import android as FunctionTools

class top_header(LocatorTools, FunctionTools):
    def __init__(self):
        run_configs.SECTION_AUTO_ID = []
 
