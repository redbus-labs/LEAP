from abc import abstractmethod

class common:
    @abstractmethod
    def bus(self):
        '''Points to the bus line of business section on the homepage.'''

    @abstractmethod
    def ferry(self):
        '''Points to the ferry line of business section on the homepage. (Selected by default)'''

class mweb(common):
    pass

class dweb(common):
    pass

class android(common):
    pass

class ios(common):
    pass

