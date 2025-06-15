# services/package_service.py
from bson import ObjectId
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from schemas.package_schema import PackageInDB, PackageCreate, PackageUpdate
from utils.logger import logger

class PackageService:
    def __init__(self, mongo):
        self.packages_collection = mongo["packages"]

    async def get_packages(
            self,
            page: int = 1,
            limit: int = 10,
            search: Optional[str] = None,
            sort: Optional[str] = None,
            filters: Optional[Dict] = None
    ) -> Tuple[List[PackageInDB], Dict]:
        query = {}
        skip = (page - 1) * limit

        # Build query filters
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"stripe_price_id": {"$regex": search, "$options": "i"}}
            ]

        if filters:
            if 'is_active' in filters:
                query["is_active"] = filters['is_active']
            if 'type' in filters:
                query["type"] = filters['type']

        # Build sort
        sort_by = [("created_at", -1)]  # Default sort
        if sort:
            sort_field = sort.lstrip('-')
            sort_dir = -1 if sort.startswith("-") else 1
            sort_by = [(sort_field, sort_dir)]

        # Execute query
        total = await self.packages_collection.count_documents(query)
        packages = await self.packages_collection.find(query) \
            .sort(sort_by) \
            .skip(skip) \
            .limit(limit) \
            .to_list(length=limit)

        total_pages = (total + limit - 1) // limit
        next_page = page + 1 if page < total_pages else None

        pagination = {
            "current_page": page,
            "next_page": next_page,
            "total_pages": total_pages,
            "total_items": total
        }

        for package in packages:
            package["_id"] = str(package["_id"])

        return [PackageInDB(**package) for package in packages], pagination

    async def get_package_by_id(self, package_id: str) -> Optional[PackageInDB]:
        try:
            package = await self.packages_collection.find_one({"_id": ObjectId(package_id)})
            logger.info("Package data fetched successfully")
            package["_id"] = str(package["_id"])
            return PackageInDB(**package) if package else None
        except Exception as e:
            logger.error(str(e))
            return None

    async def create_new_package(self, package_data: PackageCreate) -> PackageInDB:
        # Check for existing package with same name
        if await self.packages_collection.find_one({"name": package_data.name}):
            raise ValueError("Package with this name already exists")

        # Prepare package document
        package_dict = package_data.dict()
        package_dict.update({
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

        # Insert and return created package
        result = await self.packages_collection.insert_one(package_dict)
        created_package = await self.packages_collection.find_one({"_id": result.inserted_id})
        created_package["_id"] = str(created_package["_id"])
        return PackageInDB(**created_package)

    async def update_package_details(self, package_id: str, package_data: PackageUpdate) -> Optional[PackageInDB]:
        update_data = package_data.dict(exclude_unset=True)

        if not update_data:
            return None

        update_data["updated_at"] = datetime.utcnow()

        await self.packages_collection.update_one(
            {"_id": ObjectId(package_id)},
            {"$set": update_data}
        )

        updated_package = await self.packages_collection.find_one({"_id": ObjectId(package_id)})
        updated_package["_id"] = str(updated_package["_id"])
        return PackageInDB(**updated_package) if updated_package else None

    async def change_package_status(self, package_id: str, is_active: bool) -> Optional[PackageInDB]:
        await self.packages_collection.update_one(
            {"_id": ObjectId(package_id)},
            {"$set": {
                "is_active": is_active,
                "updated_at": datetime.utcnow()
            }}
        )

        updated_package = await self.packages_collection.find_one({"_id": ObjectId(package_id)})
        updated_package["_id"] = str(updated_package["_id"])
        return PackageInDB(**updated_package) if updated_package else None

    async def remove_package(self, package_id: str) -> bool:
        result = await self.packages_collection.delete_one({"_id": ObjectId(package_id)})
        return result.deleted_count > 0