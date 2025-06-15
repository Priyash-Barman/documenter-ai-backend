# services/transaction_service.py
from bson import ObjectId
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from schemas.transaction_schema import TransactionInDB
from utils.logger import logger

class TransactionService:
    def __init__(self, mongo):
        self.transactions_collection = mongo["transactions"]

    async def get_transactions(
        self,
        page: int = 1,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> Tuple[List[TransactionInDB], Dict]:
        query = {}
        skip = (page - 1) * limit

        if filters:
            if 'status' in filters:
                query["status"] = filters['status']
            if 'subscription_id' in filters:
                query["subscription_id"] = filters['subscription_id']
            if 'is_active' in filters:
                query["is_active"] = filters['is_active']

        sort_by = [("timestamp", -1)]

        total = await self.transactions_collection.count_documents(query)
        transactions = await self.transactions_collection.find(query) \
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

        for tx in transactions:
            tx["_id"] = str(tx["_id"])

        return [TransactionInDB(**tx) for tx in transactions], pagination

    async def get_transaction_by_id(self, tx_id: str) -> Optional[TransactionInDB]:
        try:
            tx = await self.transactions_collection.find_one({"_id": ObjectId(tx_id)})
            if tx:
                tx["_id"] = str(tx["_id"])
                return TransactionInDB(**tx)
            return None
        except Exception as e:
            logger.error(f"Error getting transaction: {str(e)}")
            return None

    async def create_transaction(self, tx_data: dict) -> TransactionInDB:
        tx_data["timestamp"] = datetime.utcnow()
        result = await self.transactions_collection.insert_one(tx_data)
        created_tx = await self.transactions_collection.find_one({"_id": result.inserted_id})
        created_tx["_id"] = str(created_tx["_id"])
        return TransactionInDB(**created_tx)

    async def update_transaction_status(self, tx_id: str, status: str) -> Optional[TransactionInDB]:
        await self.transactions_collection.update_one(
            {"_id": ObjectId(tx_id)},
            {"$set": {"status": status}}
        )
        updated_tx = await self.transactions_collection.find_one({"_id": ObjectId(tx_id)})
        if updated_tx:
            updated_tx["_id"] = str(updated_tx["_id"])
            return TransactionInDB(**updated_tx)
        return None