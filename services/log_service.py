# services/log_service.py
from bson import ObjectId
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from schemas.log_schema import LogInDB
from utils.logger import logger

class LogService:
    def __init__(self, mongo):
        self.logs_collection = mongo["logs"]

    async def get_logs(
        self,
        page: int = 1,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> Tuple[List[LogInDB], Dict]:
        query = {}
        skip = (page - 1) * limit

        if filters:
            if 'type' in filters:
                query["type"] = filters['type']
            if 'created_by' in filters:
                query["created_by"] = filters['created_by']

        sort_by = [("created_at", -1)]

        total = await self.logs_collection.count_documents(query)
        logs = await self.logs_collection.find(query) \
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

        for log in logs:
            log["_id"] = str(log["_id"])

        return [LogInDB(**log) for log in logs], pagination

    async def create_log(self, log_data: dict) -> LogInDB:
        log_data["created_at"] = datetime.utcnow()
        result = await self.logs_collection.insert_one(log_data)
        created_log = await self.logs_collection.find_one({"_id": result.inserted_id})
        created_log["_id"] = str(created_log["_id"])
        return LogInDB(**created_log)

    async def get_log_by_id(self, log_id: str) -> Optional[LogInDB]:
        try:
            log = await self.logs_collection.find_one({"_id": ObjectId(log_id)})
            if log:
                log["_id"] = str(log["_id"])
                return LogInDB(**log)
            return None
        except Exception as e:
            logger.error(f"Error getting log: {str(e)}")
            return None