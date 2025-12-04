import pytest
import mongomock
from unittest.mock import MagicMock, AsyncMock
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

import database

class AsyncMockCollection:
    def __init__(self, collection):
        self.collection = collection

    async def find_one(self, *args, **kwargs):
        return self.collection.find_one(*args, **kwargs)

    async def insert_one(self, *args, **kwargs):
        result = self.collection.insert_one(*args, **kwargs)
        return MagicMock(inserted_id=result.inserted_id)

    async def update_one(self, *args, **kwargs):
        return self.collection.update_one(*args, **kwargs)
        
    async def count_documents(self, *args, **kwargs):
        return self.collection.count_documents(*args, **kwargs)
        
    def find(self, *args, **kwargs):
        cursor = self.collection.find(*args, **kwargs)
        return AsyncMockCursor(cursor)
        
    def create_indexes(self, *args, **kwargs):
        # AsyncMock to simulate await
        async def _create(*a, **kw):
            pass
        return _create()

class AsyncMockCursor:
    def __init__(self, cursor):
        self.cursor = cursor
        
    def __aiter__(self):
        return self
        
    async def __anext__(self):
        try:
            return self.cursor.next()
        except StopIteration:
            raise StopAsyncIteration
            
    def to_list(self, length=None):
        async def _to_list(*args, **kwargs):
            return list(self.cursor)
        return _to_list()

class AsyncMockDatabase:
    def __init__(self, db):
        self.db = db
        self.collections = {}

    def __getattr__(self, name):
        if name not in self.collections:
            self.collections[name] = AsyncMockCollection(self.db[name])
        return self.collections[name]
        
    def __getitem__(self, name):
        return self.__getattr__(name)
        
    async def command(self, *args, **kwargs):
        return {"ok": 1}

@pytest.fixture(scope="session", autouse=True)
def mock_mongo():
    mock_client = mongomock.MongoClient()
    mock_db = AsyncMockDatabase(mock_client.aisj_connect)
    
    # Patch database.db
    database.db = mock_db
    
    # Patch connect_to_mongo to do nothing
    async def mock_connect():
        pass
    database.connect_to_mongo = mock_connect
    
    # Patch close_mongo_connection
    async def mock_close():
        pass
    database.close_mongo_connection = mock_close
    
    return mock_db
