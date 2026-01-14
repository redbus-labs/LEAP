from core_agentic import run_configs

class HomePage_POR():
    obj_lob = None
    obj_search_widget = None
    obj_offers = None

    def lob(self):
        if HomePage_POR.obj_lob is None:
            if run_configs.channel == "dweb" or run_configs.channel == "mweb":
                from src.main.agent_groups.home_page.agents.lob.tools.implementation.web import lob
                HomePage_POR.obj_lob = lob()
        return HomePage_POR.obj_lob

    def search_widget(self):
        if HomePage_POR.obj_search_widget is None:
            if run_configs.channel == "dweb" or run_configs.channel == "mweb":
                from src.main.agent_groups.home_page.agents.search_widget.tools.implementation.web import search_widget
                HomePage_POR.obj_search_widget = search_widget()
            elif run_configs.channel.lower().strip() == "android":
                from src.main.agent_groups.home_page.agents.search_widget.tools.implementation.android import search_widget
                HomePage_POR.obj_search_widget = search_widget()
        return HomePage_POR.obj_search_widget

    def offers(self):
        if HomePage_POR.obj_offers is None:
            if run_configs.channel == "dweb" or run_configs.channel == "mweb":
                from src.main.agent_groups.home_page.agents.offers.tools.implementation.web import offers
                HomePage_POR.obj_offers = offers()
        return HomePage_POR.obj_offers
