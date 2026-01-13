import core_agentic.agentic_base as agentic_base
from ..definition.agent_locator_tools import mweb as LocatorToolsMweb
from ..definition.agent_locator_tools import dweb as LocatorToolsDweb
from ..definition.agent_function_tools import mweb as FunctionToolsMweb
from ..definition.agent_function_tools import dweb as FunctionToolsDweb
from core_agentic import run_configs
class lob(LocatorToolsMweb, LocatorToolsDweb, FunctionToolsDweb, FunctionToolsMweb):
    def __init__(self):
        run_configs.SECTION_AUTO_ID = ["//*[@data-autoid='header']"]

    def bus(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='header']//*[contains(@class,'lobContainer_')])[1]")

    def ferry(self):
        return agentic_base.helper.selfHeal("(//*[@data-autoid='header']//*[contains(@class,'lobContainer_')])[2]")



