"""Base repository pattern for database operations"""

from typing import Generic, TypeVar, Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository class with common CRUD operations"""

    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str):
        """
        Initialize repository with database and collection.

        Args:
            db: Motor database instance
            collection_name: Name of the MongoDB collection
        """
        self.db = db
        self.collection = db[collection_name]
        self.collection_name = collection_name

    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Find a document by its ID.

        Args:
            id: Document ID as string

        Returns:
            Document dict or None if not found
        """
        try:
            document = await self.collection.find_one({"_id": ObjectId(id)})
            if document:
                document["_id"] = str(document["_id"])
            return document
        except Exception as e:
            logger.error(f"Error finding document by id {id} in {self.collection_name}: {e}")
            return None

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a single document matching the query.

        Args:
            query: MongoDB query dict

        Returns:
            Document dict or None if not found
        """
        try:
            document = await self.collection.find_one(query)
            if document and "_id" in document:
                document["_id"] = str(document["_id"])
            return document
        except Exception as e:
            logger.error(f"Error finding document in {self.collection_name}: {e}")
            return None

    async def find_many(
        self,
        query: Dict[str, Any],
        limit: int = 100,
        skip: int = 0,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents matching the query.

        Args:
            query: MongoDB query dict
            limit: Maximum number of documents to return
            skip: Number of documents to skip
            sort: List of (field, direction) tuples for sorting

        Returns:
            List of document dicts
        """
        try:
            cursor = self.collection.find(query).skip(skip).limit(limit)
            if sort:
                cursor = cursor.sort(sort)

            documents = await cursor.to_list(length=limit)
            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
            return documents
        except Exception as e:
            logger.error(f"Error finding documents in {self.collection_name}: {e}")
            return []

    async def count(self, query: Dict[str, Any] = None) -> int:
        """
        Count documents matching the query.

        Args:
            query: MongoDB query dict (default: empty dict for all documents)

        Returns:
            Number of matching documents
        """
        try:
            return await self.collection.count_documents(query or {})
        except Exception as e:
            logger.error(f"Error counting documents in {self.collection_name}: {e}")
            return 0

    async def insert_one(self, data: Dict[str, Any]) -> str:
        """
        Insert a single document.

        Args:
            data: Document data to insert

        Returns:
            Inserted document ID as string
        """
        try:
            # Add timestamps
            now = datetime.utcnow()
            data.setdefault("created_at", now)
            data.setdefault("updated_at", now)

            result = await self.collection.insert_one(data)
            logger.info(f"Inserted document in {self.collection_name}: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting document in {self.collection_name}: {e}")
            raise

    async def insert_many(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple documents.

        Args:
            data_list: List of document dicts to insert

        Returns:
            List of inserted document IDs as strings
        """
        try:
            # Add timestamps to all documents
            now = datetime.utcnow()
            for data in data_list:
                data.setdefault("created_at", now)
                data.setdefault("updated_at", now)

            result = await self.collection.insert_many(data_list)
            logger.info(f"Inserted {len(result.inserted_ids)} documents in {self.collection_name}")
            return [str(id) for id in result.inserted_ids]
        except Exception as e:
            logger.error(f"Error inserting documents in {self.collection_name}: {e}")
            raise

    async def update_one(
        self,
        id: str,
        data: Dict[str, Any],
        upsert: bool = False
    ) -> bool:
        """
        Update a single document by ID.

        Args:
            id: Document ID as string
            data: Update data
            upsert: Create document if it doesn't exist

        Returns:
            True if document was modified, False otherwise
        """
        try:
            # Update timestamp
            data["updated_at"] = datetime.utcnow()

            result = await self.collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": data},
                upsert=upsert
            )
            logger.info(f"Updated document {id} in {self.collection_name}: modified={result.modified_count}")
            return result.modified_count > 0 or (upsert and result.upserted_id is not None)
        except Exception as e:
            logger.error(f"Error updating document {id} in {self.collection_name}: {e}")
            raise

    async def update_many(
        self,
        query: Dict[str, Any],
        data: Dict[str, Any]
    ) -> int:
        """
        Update multiple documents matching the query.

        Args:
            query: MongoDB query dict
            data: Update data

        Returns:
            Number of documents modified
        """
        try:
            # Update timestamp
            data["updated_at"] = datetime.utcnow()

            result = await self.collection.update_many(
                query,
                {"$set": data}
            )
            logger.info(f"Updated {result.modified_count} documents in {self.collection_name}")
            return result.modified_count
        except Exception as e:
            logger.error(f"Error updating documents in {self.collection_name}: {e}")
            raise

    async def delete_one(self, id: str) -> bool:
        """
        Delete a single document by ID.

        Args:
            id: Document ID as string

        Returns:
            True if document was deleted, False otherwise
        """
        try:
            result = await self.collection.delete_one({"_id": ObjectId(id)})
            logger.info(f"Deleted document {id} from {self.collection_name}: deleted={result.deleted_count}")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document {id} from {self.collection_name}: {e}")
            raise

    async def delete_many(self, query: Dict[str, Any]) -> int:
        """
        Delete multiple documents matching the query.

        Args:
            query: MongoDB query dict

        Returns:
            Number of documents deleted
        """
        try:
            result = await self.collection.delete_many(query)
            logger.info(f"Deleted {result.deleted_count} documents from {self.collection_name}")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting documents from {self.collection_name}: {e}")
            raise

    async def exists(self, query: Dict[str, Any]) -> bool:
        """
        Check if a document matching the query exists.

        Args:
            query: MongoDB query dict

        Returns:
            True if at least one matching document exists
        """
        try:
            count = await self.collection.count_documents(query, limit=1)
            return count > 0
        except Exception as e:
            logger.error(f"Error checking existence in {self.collection_name}: {e}")
            return False
