# services/api_doc_service.py
from bson import ObjectId
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from schemas.api_doc_schema import ApiDocInDB, ApiDocCreate, ApiDocUpdate
from utils.logger import logger

class ApiDocService:
    def __init__(self, mongo):
        self.api_docs_collection = mongo["api_docs"]

    async def get_api_docs(
        self,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        sort: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> Tuple[List[ApiDocInDB], Dict]:
        query = {}
        skip = (page - 1) * limit

        if search:
            query["$or"] = [
                {"url": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]

        if filters:
            if 'is_active' in filters:
                query["is_active"] = filters['is_active']
            if 'method' in filters:
                query["method"] = filters['method']

        sort_by = [("created_at", -1)]
        if sort:
            sort_field = sort.lstrip('-')
            sort_dir = -1 if sort.startswith("-") else 1
            sort_by = [(sort_field, sort_dir)]

        total = await self.api_docs_collection.count_documents(query)
        api_docs = await self.api_docs_collection.find(query) \
            .sort(sort_by) \
            .skip(skip) \
            .limit(limit) \
            .to_list(length=limit)

        total_pages = (total + limit - 1) // limit
        pagination = {
            "current_page": page,
            "total_pages": total_pages,
            "total_items": total
        }

        for doc in api_docs:
            doc["_id"] = str(doc["_id"])

        return [ApiDocInDB(**doc) for doc in api_docs], pagination

    async def get_api_doc_by_id(self, doc_id: str) -> Optional[ApiDocInDB]:
        try:
            doc = await self.api_docs_collection.find_one({"_id": ObjectId(doc_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                return ApiDocInDB(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting API doc: {str(e)}")
            return None

    async def create_new_api_doc(self, doc_data: ApiDocCreate) -> ApiDocInDB:
        doc_dict = doc_data.dict()
        doc_dict.update({
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

        result = await self.api_docs_collection.insert_one(doc_dict)
        created_doc = await self.api_docs_collection.find_one({"_id": result.inserted_id})
        created_doc["_id"] = str(created_doc["_id"])
        return ApiDocInDB(**created_doc)

    async def update_api_doc(self, doc_id: str, doc_data: ApiDocUpdate) -> Optional[ApiDocInDB]:
        update_data = doc_data.dict(exclude_unset=True)
        if not update_data:
            return None

        update_data["updated_at"] = datetime.utcnow()

        await self.api_docs_collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": update_data}
        )

        updated_doc = await self.api_docs_collection.find_one({"_id": ObjectId(doc_id)})
        if updated_doc:
            updated_doc["_id"] = str(updated_doc["_id"])
            return ApiDocInDB(**updated_doc)
        return None

    async def remove_api_doc(self, doc_id: str) -> bool:
        result = await self.api_docs_collection.delete_one({"_id": ObjectId(doc_id)})
        return result.deleted_count > 0