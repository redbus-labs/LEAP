from core_agentic import run_configs

class SearchResultPage_POR():
    obj_ferry_tuples = None
    obj_quick_filters = None
    obj_top_header = None
    obj_oops = None

    def ferry_tuples(self):
        if SearchResultPage_POR.obj_ferry_tuples is None:
            if run_configs.channel == "dweb" or run_configs.channel == "mweb":
                from src.main.agent_groups.search_result_page.agents.ferry_tuples.tools.implementation.web import ferry_tuples
                SearchResultPage_POR.obj_ferry_tuples = ferry_tuples()
        return SearchResultPage_POR.obj_ferry_tuples

    def quick_filters(self):
        if SearchResultPage_POR.obj_quick_filters is None:
            if run_configs.channel == "dweb" or run_configs.channel == "mweb":
                from src.main.agent_groups.search_result_page.agents.quick_filters.tools.implementation.web import quick_filters
                SearchResultPage_POR.obj_quick_filters = quick_filters()
        return SearchResultPage_POR.obj_quick_filters

    def top_header(self):
        if SearchResultPage_POR.obj_top_header is None:
            if run_configs.channel == "dweb" or run_configs.channel == "mweb":
                from src.main.agent_groups.search_result_page.agents.top_header.tools.implementation.web import top_header
                SearchResultPage_POR.obj_top_header = top_header()
        return SearchResultPage_POR.obj_top_header

    def oops(self):
        if SearchResultPage_POR.obj_oops is None:
            if run_configs.channel == "dweb" or run_configs.channel == "mweb":
                from src.main.agent_groups.search_result_page.agents.oops.tools.implementation.web import oops
                SearchResultPage_POR.obj_oops = oops()
        return SearchResultPage_POR.obj_oops

