"""MongoDB repository for chat history, codes, images, and PDFs."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

from ...models.mongo_models import (
    ChatHistory, ChatMessage, CodeSnippet, 
    ImageDocument, PDFDocument, UserStatistics, APIUsage
)
from ...config.database import get_mongo_db


class MongoRepository:
    """Base MongoDB repository."""
    
    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str):
        self.db = db
        self.collection: AsyncIOMotorCollection = db[collection_name]
    
    async def create_indexes(self):
        """Create database indexes."""
        pass  # To be implemented by subclasses


class ChatRepository(MongoRepository):
    """Repository for chat history operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "chats")
    
    async def create_indexes(self):
        """Create indexes for chat history collection."""
        await self.collection.create_index("user_id")
        await self.collection.create_index("created_at")
        await self.collection.create_index([("user_id", 1), ("created_at", -1)])
    
    async def create_chat(self, user_id: str, title: str) -> str:
        """Create a new chat."""
        chat = ChatHistory(
            user_id=user_id,
            title=title,
            messages=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        result = await self.collection.insert_one(chat.dict(by_alias=True))
        return str(result.inserted_id)
    
    async def get_chat_by_id(self, chat_id: str) -> Optional[ChatHistory]:
        """Get chat by ID."""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(chat_id)})
            if doc:
                return ChatHistory(**doc)
            return None
        except Exception:
            return None
    
    async def get_user_chats(self, user_id: str, limit: int = 20, offset: int = 0) -> List[ChatHistory]:
        """Get user's chats."""
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).skip(offset).limit(limit)
        chats = []
        async for doc in cursor:
            chats.append(ChatHistory(**doc))
        return chats
    
    async def add_message(self, chat_id: str, message: ChatMessage) -> bool:
        """Add a message to a chat."""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(chat_id)},
                {
                    "$push": {"messages": message.dict()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def update_chat_title(self, chat_id: str, title: str) -> bool:
        """Update chat title."""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(chat_id)},
                {
                    "$set": {
                        "title": title,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def delete_chat(self, chat_id: str, user_id: str) -> bool:
        """Delete a chat (user must own it)."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(chat_id),
                "user_id": user_id
            })
            return result.deleted_count > 0
        except Exception:
            return False
    
    async def archive_chat(self, chat_id: str, user_id: str) -> bool:
        """Archive a chat."""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(chat_id), "user_id": user_id},
                {
                    "$set": {
                        "is_archived": True,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False


class CodeRepository(MongoRepository):
    """Repository for code snippets."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "codes")
    
    async def create_indexes(self):
        """Create indexes for codes collection."""
        await self.collection.create_index("user_id")
        await self.collection.create_index("language")
        await self.collection.create_index("created_at")
        await self.collection.create_index([("user_id", 1), ("created_at", -1)])
    
    async def create_code(self, code_data: Dict[str, Any]) -> str:
        """Create a new code snippet."""
        code = CodeSnippet(**code_data)
        result = await self.collection.insert_one(code.dict(by_alias=True))
        return str(result.inserted_id)
    
    async def get_code_by_id(self, code_id: str) -> Optional[CodeSnippet]:
        """Get code by ID."""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(code_id)})
            if doc:
                return CodeSnippet(**doc)
            return None
        except Exception:
            return None
    
    async def get_user_codes(self, user_id: str, limit: int = 20, offset: int = 0) -> List[CodeSnippet]:
        """Get user's code snippets."""
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).skip(offset).limit(limit)
        codes = []
        async for doc in cursor:
            codes.append(CodeSnippet(**doc))
        return codes
    
    async def update_code(self, code_id: str, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update code snippet."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"_id": ObjectId(code_id), "user_id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def delete_code(self, code_id: str, user_id: str) -> bool:
        """Delete code snippet."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(code_id),
                "user_id": user_id
            })
            return result.deleted_count > 0
        except Exception:
            return False
    
    async def save_code_snippet(self, user_id: str, code_snippet: CodeSnippet) -> str:
        """Save a code snippet and return its ID."""
        code_data = code_snippet.dict()
        code_data["user_id"] = user_id
        code_data["created_at"] = datetime.utcnow()
        code_data["updated_at"] = datetime.utcnow()
        
        result = await self.collection.insert_one(code_data)
        return str(result.inserted_id)
    
    async def get_user_code_snippets(self, user_id: str, limit: int = 20, offset: int = 0, language: Optional[str] = None) -> List[CodeSnippet]:
        """Get user's code snippets with optional language filter."""
        filter_dict = {"user_id": user_id}
        if language:
            filter_dict["language"] = language
            
        cursor = self.collection.find(filter_dict).sort("created_at", -1).skip(offset).limit(limit)
        codes = []
        async for doc in cursor:
            codes.append(CodeSnippet(**doc))
        return codes
    
    async def delete_code_snippet(self, snippet_id: str, user_id: str) -> bool:
        """Delete a code snippet by ID and user ID."""
        return await self.delete_code(snippet_id, user_id)


class ImageRepository(MongoRepository):
    """Repository for image documents."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "images")
    
    async def create_indexes(self):
        """Create indexes for images collection."""
        await self.collection.create_index("user_id")
        await self.collection.create_index("created_at")
        await self.collection.create_index([("user_id", 1), ("created_at", -1)])
    
    async def create_image(self, image_data: Dict[str, Any]) -> str:
        """Create a new image document."""
        image = ImageDocument(**image_data)
        result = await self.collection.insert_one(image.dict(by_alias=True))
        return str(result.inserted_id)
    
    async def get_image_by_id(self, image_id: str) -> Optional[ImageDocument]:
        """Get image by ID."""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(image_id)})
            if doc:
                return ImageDocument(**doc)
            return None
        except Exception:
            return None
    
    async def get_user_images(self, user_id: str, limit: int = 20, offset: int = 0) -> List[ImageDocument]:
        """Get user's images."""
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).skip(offset).limit(limit)
        images = []
        async for doc in cursor:
            images.append(ImageDocument(**doc))
        return images
    
    async def delete_image(self, image_id: str, user_id: str) -> bool:
        """Delete image document."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(image_id),
                "user_id": user_id
            })
            return result.deleted_count > 0
        except Exception:
            return False


class PDFRepository(MongoRepository):
    """Repository for PDF documents."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "pdfs")
    
    async def create_indexes(self):
        """Create indexes for PDFs collection."""
        await self.collection.create_index("user_id")
        await self.collection.create_index("created_at")
        await self.collection.create_index([("user_id", 1), ("created_at", -1)])
        await self.collection.create_index([("title", "text"), ("text_content", "text")])
    
    async def create_pdf(self, pdf_data: Dict[str, Any]) -> str:
        """Create a new PDF document."""
        pdf = PDFDocument(**pdf_data)
        result = await self.collection.insert_one(pdf.dict(by_alias=True))
        return str(result.inserted_id)
    
    async def get_pdf_by_id(self, pdf_id: str) -> Optional[PDFDocument]:
        """Get PDF by ID."""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(pdf_id)})
            if doc:
                return PDFDocument(**doc)
            return None
        except Exception:
            return None
    
    async def get_user_pdfs(self, user_id: str, limit: int = 20, offset: int = 0) -> List[PDFDocument]:
        """Get user's PDFs."""
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).skip(offset).limit(limit)
        pdfs = []
        async for doc in cursor:
            pdfs.append(PDFDocument(**doc))
        return pdfs
    
    async def search_pdfs(self, user_id: str, query: str, limit: int = 10) -> List[PDFDocument]:
        """Search PDFs by text content."""
        cursor = self.collection.find({
            "user_id": user_id,
            "$text": {"$search": query}
        }).sort("created_at", -1).limit(limit)
        
        pdfs = []
        async for doc in cursor:
            pdfs.append(PDFDocument(**doc))
        return pdfs
    
    async def delete_pdf(self, pdf_id: str, user_id: str) -> bool:
        """Delete PDF document."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(pdf_id),
                "user_id": user_id
            })
            return result.deleted_count > 0
        except Exception:
            return False


class UserStatsRepository(MongoRepository):
    """Repository for user statistics."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "user_stats")
    
    async def create_indexes(self):
        """Create indexes for user stats collection."""
        await self.collection.create_index("user_id", unique=True)
    
    async def get_user_stats(self, user_id: str) -> Optional[UserStatistics]:
        """Get user statistics."""
        doc = await self.collection.find_one({"user_id": user_id})
        if doc:
            return UserStatistics(**doc)
        return None
    
    async def update_user_stats(self, user_id: str, stats_update: Dict[str, Any]) -> bool:
        """Update user statistics."""
        try:
            stats_update["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"user_id": user_id},
                {"$set": stats_update},
                upsert=True
            )
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception:
            return False
    
    async def increment_stats(self, user_id: str, field: str, increment: int = 1) -> bool:
        """Increment a specific statistic."""
        try:
            result = await self.collection.update_one(
                {"user_id": user_id},
                {
                    "$inc": {field: increment},
                    "$set": {"updated_at": datetime.utcnow()}
                },
                upsert=True
            )
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception:
            return False


class APIRepository(MongoRepository):
    """Repository for API usage tracking."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "api's")
    
    async def create_indexes(self):
        """Create indexes for API usage collection."""
        await self.collection.create_index("user_id")
        await self.collection.create_index("endpoint")
        await self.collection.create_index("timestamp")
        await self.collection.create_index([("user_id", 1), ("timestamp", -1)])
    
    async def log_api_usage(self, user_id: str, endpoint: str, method: str, 
                          response_status: int, response_time: float, 
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log API usage."""
        api_usage = APIUsage(
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            response_status=response_status,
            response_time=response_time,
            metadata=metadata or {},
            timestamp=datetime.utcnow()
        )
        
        result = await self.collection.insert_one(api_usage.dict(by_alias=True))
        return str(result.inserted_id)
    
    async def get_user_api_usage(self, user_id: str, limit: int = 100, 
                               offset: int = 0) -> List[APIUsage]:
        """Get user's API usage history."""
        cursor = self.collection.find({"user_id": user_id}).sort("timestamp", -1).skip(offset).limit(limit)
        usage_logs = []
        async for doc in cursor:
            usage_logs.append(APIUsage(**doc))
        return usage_logs
    
    async def get_api_stats(self, user_id: str, start_date: Optional[datetime] = None, 
                          end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get API usage statistics."""
        match_filter = {"user_id": user_id}
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            match_filter["timestamp"] = date_filter
        
        pipeline = [
            {"$match": match_filter},
            {"$group": {
                "_id": None,
                "total_requests": {"$sum": 1},
                "avg_response_time": {"$avg": "$response_time"},
                "success_rate": {
                    "$avg": {"$cond": [{"$lt": ["$response_status", 400]}, 1, 0]}
                }
            }}
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(1)
        if result:
            return result[0]
        return {"total_requests": 0, "avg_response_time": 0, "success_rate": 0}


class RepositoryManager:
    """Manager for all MongoDB repositories."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.chat_repo = ChatRepository(db)
        self.code_repo = CodeRepository(db)
        self.image_repo = ImageRepository(db)
        self.pdf_repo = PDFRepository(db)
        self.stats_repo = UserStatsRepository(db)
        self.api_repo = APIRepository(db)
    
    async def create_all_indexes(self):
        """Create all database indexes."""
        await self.chat_repo.create_indexes()
        await self.code_repo.create_indexes()
        await self.image_repo.create_indexes()
        await self.pdf_repo.create_indexes()
        await self.stats_repo.create_indexes()
        await self.api_repo.create_indexes()


# Global repository manager
repo_manager: Optional[RepositoryManager] = None


async def get_repository_manager() -> RepositoryManager:
    """Get repository manager instance."""
    global repo_manager
    if repo_manager is None:
        db = await get_mongo_db()
        repo_manager = RepositoryManager(db)
        await repo_manager.create_all_indexes()
    return repo_manager