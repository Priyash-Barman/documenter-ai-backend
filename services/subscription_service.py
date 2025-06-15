# services/subscription_service.py
from bson import ObjectId
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from schemas.subscription_schema import SubscriptionInDB
from utils.logger import logger

class SubscriptionService:
    def __init__(self, mongo):
        self.subscriptions_collection = mongo["subscriptions"]

    async def get_subscriptions(
        self,
        page: int = 1,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> Tuple[List[SubscriptionInDB], Dict]:
        query = {}
        skip = (page - 1) * limit

        if filters:
            if 'status' in filters:
                query["status"] = filters['status']
            if 'user_id' in filters:
                query["user_id"] = filters['user_id']
            if 'app_id' in filters:
                query["app_id"] = filters['app_id']
            if 'package_id' in filters:
                query["package_id"] = filters['package_id']

        sort_by = [("start_date", -1)]

        total = await self.subscriptions_collection.count_documents(query)
        subscriptions = await self.subscriptions_collection.find(query) \
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

        for sub in subscriptions:
            sub["_id"] = str(sub["_id"])

        return [SubscriptionInDB(**sub) for sub in subscriptions], pagination

    async def get_subscription_by_id(self, sub_id: str) -> Optional[SubscriptionInDB]:
        try:
            sub = await self.subscriptions_collection.find_one({"_id": ObjectId(sub_id)})
            if sub:
                sub["_id"] = str(sub["_id"])
                return SubscriptionInDB(**sub)
            return None
        except Exception as e:
            logger.error(f"Error getting subscription: {str(e)}")
            return None

    async def create_subscription(self, sub_data: dict) -> SubscriptionInDB:
        result = await self.subscriptions_collection.insert_one(sub_data)
        created_sub = await self.subscriptions_collection.find_one({"_id": result.inserted_id})
        created_sub["_id"] = str(created_sub["_id"])
        return SubscriptionInDB(**created_sub)

    async def update_subscription_status(self, sub_id: str, status: str) -> Optional[SubscriptionInDB]:
        await self.subscriptions_collection.update_one(
            {"_id": ObjectId(sub_id)},
            {"$set": {"status": status}}
        )
        updated_sub = await self.subscriptions_collection.find_one({"_id": ObjectId(sub_id)})
        if updated_sub:
            updated_sub["_id"] = str(updated_sub["_id"])
            return SubscriptionInDB(**updated_sub)
        return None

    async def cancel_subscription(self, sub_id: str, cancel_at: datetime) -> Optional[SubscriptionInDB]:
        await self.subscriptions_collection.update_one(
            {"_id": ObjectId(sub_id)},
            {"$set": {
                "cancel_at_period_end": cancel_at,
                "status": "canceled"
            }}
        )
        updated_sub = await self.subscriptions_collection.find_one({"_id": ObjectId(sub_id)})
        if updated_sub:
            updated_sub["_id"] = str(updated_sub["_id"])
            return SubscriptionInDB(**updated_sub)
        return None