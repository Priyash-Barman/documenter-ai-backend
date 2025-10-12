# services/user_service.py
from bson import ObjectId
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from schemas.user_schema import UserInDB, UserCreate, UserUpdate, UserProfileUpdate
from utils.logger import logger

class UserService:
    def __init__(self, mongo):
        self.users_collection = mongo["users"]

    async def get_users(
            self,
            page: int = 1,
            limit: int = 10,
            search: Optional[str] = None,
            sort: Optional[str] = None,
            filters: Optional[Dict] = None
    ) -> Tuple[List[UserInDB], Dict]:
        query = {}
        skip = (page - 1) * limit

        # Build query filters
        if search:
            query["$or"] = [
                {"full_name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]

        if filters:
            if 'is_active' in filters:
                query["is_active"] = filters['is_active']
            if 'role' in filters:
                query["role"] = filters['role']

        # Build sort
        sort_by = [("created_at", -1)]  # Default sort
        if sort:
            sort_field = sort.lstrip('-')
            sort_dir = -1 if sort.startswith("-") else 1
            sort_by = [(sort_field, sort_dir)]

        # Execute query
        total = await self.users_collection.count_documents(query)
        users = await self.users_collection.find(query) \
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

        for user in users:
            user["_id"] = str(user["_id"])

        return [UserInDB(**user) for user in users], pagination

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        try:
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            logger.info("User data fetched successfully")
            user["_id"] = str(user["_id"])
            return UserInDB(**user) if user else None
        except Exception as e:
            logger.error(str(e))
            return None

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        try:
            user = await self.users_collection.find_one({"email": email})
            logger.info("User data fetched successfully")
            user["_id"] = str(user["_id"])
            return UserInDB(**user) if user else None
        except Exception as e:
            logger.error(str(e))
            return None

    async def create_new_user(self, user_data: UserCreate) -> UserInDB:
        # Check for existing user
        if await self.users_collection.find_one({"email": user_data.email}):
            raise ValueError("Email already registered")

        # Prepare user document
        user_dict = user_data.dict()
        user_dict.update({
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

        # Insert and return created user
        result = await self.users_collection.insert_one(user_dict)
        created_user = await self.users_collection.find_one({"_id": result.inserted_id})
        created_user["_id"]=str(created_user["_id"])
        return UserInDB(**created_user)

    async def update_user_details(self, user_id: str, user_data: UserUpdate) -> Optional[UserInDB]:
        update_data = user_data.dict(exclude_unset=True)

        if not update_data:
            return None

        update_data["updated_at"] = datetime.utcnow()

        await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )

        updated_user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        updated_user["_id"] = str(updated_user["_id"])
        return UserInDB(**updated_user) if updated_user else None

    async def update_user_profile(self, user_id: str, profile_data: UserProfileUpdate) -> Optional[UserInDB]:
        """Update user's own profile information"""
        update_data = profile_data.dict(exclude_unset=True)

        if not update_data:
            return None

        # Check if email is being updated and if it already exists
        if 'email' in update_data:
            existing_user = await self.users_collection.find_one({
                "email": update_data['email'],
                "_id": {"$ne": ObjectId(user_id)}
            })
            if existing_user:
                raise ValueError("Email already in use by another account")

        update_data["updated_at"] = datetime.utcnow()

        result = await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )

        if result.modified_count == 0:
            return None

        updated_user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        if updated_user:
            updated_user["_id"] = str(updated_user["_id"])
            return UserInDB(**updated_user)
        return None

    async def update_profile_picture(self, user_id: str, profile_picture_path: str) -> Optional[UserInDB]:
        """Update user's profile picture"""
        update_data = {
            "profile_picture": profile_picture_path,
            "updated_at": datetime.utcnow()
        }

        result = await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )

        if result.modified_count == 0:
            return None

        updated_user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        if updated_user:
            updated_user["_id"] = str(updated_user["_id"])
            return UserInDB(**updated_user)
        return None

    async def remove_profile_picture(self, user_id: str) -> Optional[UserInDB]:
        """Remove user's profile picture"""
        update_data = {
            "profile_picture": None,
            "updated_at": datetime.utcnow()
        }

        result = await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )

        if result.modified_count == 0:
            return None

        updated_user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        if updated_user:
            updated_user["_id"] = str(updated_user["_id"])
            return UserInDB(**updated_user)
        return None

    async def get_user_profile(self, user_id: str) -> Optional[UserInDB]:
        """Get user's profile by ID"""
        return await self.get_user_by_id(user_id)

    async def change_user_status(self, user_id: str, is_active: bool) -> Optional[UserInDB]:
        await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "is_active": is_active,
                "updated_at": datetime.utcnow()
            }}
        )

        updated_user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        updated_user["_id"] = str(updated_user["_id"])
        return UserInDB(**updated_user) if updated_user else None

    async def remove_user(self, user_id: str) -> bool:
        result = await self.users_collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0