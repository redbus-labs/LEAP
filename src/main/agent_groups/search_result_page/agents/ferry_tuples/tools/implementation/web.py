from typing import Annotated

import core_agentic.agentic_base as agentic_base
from ..definition.agent_locator_tools import mweb as LocatorToolsMweb
from ..definition.agent_locator_tools import dweb as LocatorToolsDweb
from ..definition.agent_function_tools import mweb as FunctionToolsMweb
from ..definition.agent_function_tools import dweb as FunctionToolsDweb
from core_agentic import run_configs
class ferry_tuples(LocatorToolsMweb, LocatorToolsDweb, FunctionToolsDweb, FunctionToolsMweb):
    def __init__(self):
        run_configs.SECTION_AUTO_ID = ["//*[@data-autoid='inventoryList']"]

    def ferryTupleByFerryName(self, ferryName: Annotated[str, "Name"], ferryOccurence: Annotated[
        int, "Position among multiple ferries of same name/operator name, Default: 1"]):
        run_configs.setRef("time_selection_page")
        return agentic_base.helper.selfHeal("(//*[@data-autoid='inventoryList']//*[contains(@class,'travelsName_') and text()='{ferryName}']//ancestor::*[contains(@class,'tupleWrapper_')])[{ferryOccurence}]", ferryName, ferryOccurence)


