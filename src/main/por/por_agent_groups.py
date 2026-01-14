from src.main.por.por_home_page import HomePage_POR
from src.main.por.por_search_result_page import SearchResultPage_POR


class Agents_POR():
    obj_home_page: HomePage_POR = None
    obj_search_result_page: SearchResultPage_POR = None

    def home_page(self):
        if Agents_POR.obj_home_page is None:
            Agents_POR.obj_home_page = HomePage_POR()
        return Agents_POR.obj_home_page

    def search_result_page(self):
         if Agents_POR.obj_search_result_page is None:
             Agents_POR.obj_search_result_page = SearchResultPage_POR()
         return Agents_POR.obj_search_result_page
