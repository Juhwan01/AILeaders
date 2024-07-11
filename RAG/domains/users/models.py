from sqlalchemy import Column, DateTime, String, Integer, func


from dependencies.database import Base

class ChainStore:
    def __init__(self):
        self.chain = None

    def set_chain(self, chain):
        self.chain = chain

    def get_chain(self):
        return self.chain
    
