from abc import abstractmethod
from typing import Annotated

class common:
    @abstractmethod
    def ferryTupleByFerryName(self, ferryName: Annotated[str, "Name of the Ferry"],
                              ferryOccurence: Annotated[int, "Position among multiple ferries, Default: 1"]):
        '''Ferry tuple by Ferry name or ferry operator name'''

class mweb(common):
    pass

class dweb(common):
    pass

class android(common):
    pass

class ios(common):
    pass

