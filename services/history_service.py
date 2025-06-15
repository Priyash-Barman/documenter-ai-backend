# services/history_service.py
from bson import ObjectId
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from schemas.history_schema import HistoryInDB
from utils.logger import logger

class HistoryService:
    def __init__(self, mongo):
        self.histories_collection = mongo["histories"]

    async def get_histories(
        self,
        page: int = 1,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> Tuple[List[HistoryInDB], Dict]:
        query = {}
        skip = (page - 1) * limit

        if filters:
            if 'req_from' in filters:
                query["req_from"] = filters['req_from']
            if 'user_id' in filters:
                query["user_id"] = filters['user_id']
            if 'app_id' in filters:
                query["app_id"] = filters['app_id']

        sort_by = [("timestamp", -1)]

        total = await self.histories_collection.count_documents(query)
        histories = await self.histories_collection.find(query) \
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

        for history in histories:
            history["_id"] = str(history["_id"])

        return [HistoryInDB(**history) for history in histories], pagination

    async def create_history(self, history_data: dict) -> HistoryInDB:
        history_data["timestamp"] = datetime.utcnow()
        result = await self.histories_collection.insert_one(history_data)
        created_history = await self.histories_collection.find_one({"_id": result.inserted_id})
        created_history["_id"] = str(created_history["_id"])
        return HistoryInDB(**created_history)

    async def get_history_by_id(self, history_id: str) -> Optional[HistoryInDB]:
        try:
            history = await self.histories_collection.find_one({"_id": ObjectId(history_id)})
            if history:
                history["_id"] = str(history["_id"])
                return HistoryInDB(**history)
            return None
        except Exception as e:
            logger.error(f"Error getting history: {str(e)}")
            return None