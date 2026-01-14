from datetime import datetime, timedelta
from typing import Annotated

import core_agentic.agentic_base as agentic_base
from core_agentic import run_configs
from ..definition.agent_locator_tools import android as LocatorTools
from ..definition.agent_function_tools import android as FunctionTools

class search_widget(LocatorTools, FunctionTools):
    pass