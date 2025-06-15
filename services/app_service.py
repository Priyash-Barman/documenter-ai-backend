# services/app_service.py
from bson import ObjectId
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from schemas.app_schema import AppInDB, AppCreate, AppUpdate
from utils.logger import logger

class AppService:
    def __init__(self, mongo):
        self.apps_collection = mongo["apps"]

    async def get_apps(
        self,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        sort: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> Tuple[List[AppInDB], Dict]:
        query = {}
        skip = (page - 1) * limit

        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]

        if filters:
            if 'is_active' in filters:
                query["is_active"] = filters['is_active']
            if 'owner_id' in filters:
                query["owner_id"] = filters['owner_id']

        sort_by = [("created_at", -1)]
        if sort:
            sort_field = sort.lstrip('-')
            sort_dir = -1 if sort.startswith("-") else 1
            sort_by = [(sort_field, sort_dir)]

        total = await self.apps_collection.count_documents(query)
        apps = await self.apps_collection.find(query) \
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

        for app in apps:
            app["_id"] = str(app["_id"])

        return [AppInDB(**app) for app in apps], pagination

    async def get_app_by_id(self, app_id: str) -> Optional[AppInDB]:
        try:
            app = await self.apps_collection.find_one({"_id": ObjectId(app_id)})
            if app:
                app["_id"] = str(app["_id"])
                return AppInDB(**app)
            return None
        except Exception as e:
            logger.error(f"Error getting app: {str(e)}")
            return None

    async def create_new_app(self, app_data: AppCreate) -> AppInDB:
        if await self.apps_collection.find_one({"name": app_data.name}):
            raise ValueError("App with this name already exists")

        app_dict = app_data.dict()
        app_dict.update({
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

        result = await self.apps_collection.insert_one(app_dict)
        created_app = await self.apps_collection.find_one({"_id": result.inserted_id})
        created_app["_id"] = str(created_app["_id"])
        return AppInDB(**created_app)

    async def update_app_details(self, app_id: str, app_data: AppUpdate) -> Optional[AppInDB]:
        update_data = app_data.dict(exclude_unset=True)
        if not update_data:
            return None

        update_data["updated_at"] = datetime.utcnow()

        await self.apps_collection.update_one(
            {"_id": ObjectId(app_id)},
            {"$set": update_data}
        )

        updated_app = await self.apps_collection.find_one({"_id": ObjectId(app_id)})
        if updated_app:
            updated_app["_id"] = str(updated_app["_id"])
            return AppInDB(**updated_app)
        return None

    async def change_app_status(self, app_id: str, is_active: bool) -> Optional[AppInDB]:
        await self.apps_collection.update_one(
            {"_id": ObjectId(app_id)},
            {"$set": {
                "is_active": is_active,
                "updated_at": datetime.utcnow()
            }}
        )

        updated_app = await self.apps_collection.find_one({"_id": ObjectId(app_id)})
        if updated_app:
            updated_app["_id"] = str(updated_app["_id"])
            return AppInDB(**updated_app)
        return None

    async def remove_app(self, app_id: str) -> bool:
        result = await self.apps_collection.delete_one({"_id": ObjectId(app_id)})
        return result.deleted_count > 0