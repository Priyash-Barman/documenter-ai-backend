# services/history_service.py
from bson import ObjectId
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timezone, timedelta
from schemas.history_schema import HistoryInDB
from utils.logger import logger

# Define IST timezone (UTC + 5:30)
IST = timezone(timedelta(hours=5, minutes=30))

class HistoryService:
    def __init__(self, mongo):
        self.histories_collection = mongo["histories"]
        self.conversion_history_collection = mongo["conversion_history"]
        self.users_collection = mongo["users"]

    def _convert_to_ist(self, utc_datetime):
        """Convert UTC datetime to IST"""
        if utc_datetime.tzinfo is None:
            utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
        return utc_datetime.astimezone(IST)

    async def get_histories(
        self,
        page: int = 1,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> Tuple[List[HistoryInDB], Dict]:
        # Read directly from conversion_history instead of histories collection
        query = {}
        skip = (page - 1) * limit

        # Apply filters based on conversion_history fields
        if filters:
            if 'req_from' in filters and filters['req_from'] == 'user':
                # All conversions are from users, so this doesn't filter anything
                pass
            elif 'req_from' in filters and filters['req_from'] == 'app':
                # No conversions from apps in conversion_history, return empty
                return [], {"current_page": 1, "total_pages": 0, "total_items": 0}
            if 'user_id' in filters:
                query["user_id"] = filters['user_id']
            # app_id filter doesn't apply to conversion_history

        sort_by = [("created_at", -1)]

        try:
            total = await self.conversion_history_collection.count_documents(query)
            logger.info(f"Total documents in conversion_history collection: {total}")
            
            conversions = await self.conversion_history_collection.find(query) \
                .sort(sort_by) \
                .skip(skip) \
                .limit(limit) \
                .to_list(length=limit)

            logger.info(f"Retrieved {len(conversions)} conversion documents")

            total_pages = (total + limit - 1) // limit
            pagination = {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total
            }

            # Convert conversion_history documents to HistoryInDB format
            histories = []
            for conversion in conversions:
                # Format the conversion data as history data
                user_id = conversion.get("user_id")
                filename = conversion.get("filename", "unknown_file")
                model = conversion.get("model_used", "gemini")
                success = conversion.get("success", False)
                extracted_text = conversion.get("extracted_text", "")
                processing_time = conversion.get("processing_time", 0)
                
                # Use the actual created_at from conversion, not utcnow()
                created_at = conversion.get("created_at")
                if not created_at:
                    # Only fallback to current time if created_at is truly missing
                    created_at = datetime.utcnow()
                elif not isinstance(created_at, datetime):
                    # Handle potential string timestamps
                    try:
                        if isinstance(created_at, str):
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except:
                        created_at = datetime.utcnow()
                
                # Convert to IST for display
                created_at_ist = self._convert_to_ist(created_at)
                
                # Format request and response text
                req_text = f"Document conversion request - File: {filename}, Model: {model}"
                if success:
                    res_text = f"Successfully converted document using {model}. Processing time: {processing_time:.2f}s. Extracted text length: {len(extracted_text)} characters."
                else:
                    res_text = f"Conversion failed: {extracted_text}"
                
                # Create history-like structure
                history_data = {
                    "_id": str(conversion["_id"]),
                    "req_text": req_text,
                    "req_file_url": None,
                    "res_text": res_text,
                    "res_file_url": None,
                    "req_from": "user",
                    "user_id": user_id,
                    "app_id": None,
                    "timestamp": created_at_ist,
                    "conversion_id": str(conversion["_id"])  # Link to original conversion
                }
                
                histories.append(HistoryInDB(**history_data))

            return histories, pagination
        except Exception as e:
            logger.error(f"Error in get_histories: {str(e)}")
            return [], {"current_page": 1, "total_pages": 0, "total_items": 0}

    async def create_history(self, history_data: dict) -> HistoryInDB:
        history_data["timestamp"] = datetime.utcnow()
        result = await self.histories_collection.insert_one(history_data)
        created_history = await self.histories_collection.find_one({"_id": result.inserted_id})
        created_history["_id"] = str(created_history["_id"])
        return HistoryInDB(**created_history)

    async def get_history_by_id(self, history_id: str) -> Optional[HistoryInDB]:
        try:
            # First try to find in conversion_history (most likely)
            conversion = await self.conversion_history_collection.find_one({"_id": ObjectId(history_id)})
            if conversion:
                # Format conversion as history
                user_id = conversion.get("user_id")
                filename = conversion.get("filename", "unknown_file")
                model = conversion.get("model_used", "gemini")
                success = conversion.get("success", False)
                extracted_text = conversion.get("extracted_text", "")
                processing_time = conversion.get("processing_time", 0)
                
                # Use the actual created_at from conversion
                created_at = conversion.get("created_at")
                if not created_at:
                    created_at = datetime.utcnow()
                elif not isinstance(created_at, datetime):
                    try:
                        if isinstance(created_at, str):
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except:
                        created_at = datetime.utcnow()
                
                # Convert to IST for display
                created_at_ist = self._convert_to_ist(created_at)
                
                req_text = f"Document conversion request - File: {filename}, Model: {model}"
                if success:
                    res_text = f"Successfully converted document using {model}. Processing time: {processing_time:.2f}s. Extracted text length: {len(extracted_text)} characters."
                else:
                    res_text = f"Conversion failed: {extracted_text}"
                
                history_data = {
                    "_id": str(conversion["_id"]),
                    "req_text": req_text,
                    "req_file_url": None,
                    "res_text": res_text,
                    "res_file_url": None,
                    "req_from": "user",
                    "user_id": user_id,
                    "app_id": None,
                    "timestamp": created_at_ist,
                    "conversion_id": str(conversion["_id"])
                }
                
                return HistoryInDB(**history_data)
            
            # If not found in conversion_history, try regular histories collection
            history = await self.histories_collection.find_one({"_id": ObjectId(history_id)})
            if history:
                history["_id"] = str(history["_id"])
                # Convert timestamp to IST if it exists
                if "timestamp" in history:
                    history["timestamp"] = self._convert_to_ist(history["timestamp"])
                return HistoryInDB(**history)
            
            return None
        except Exception as e:
            logger.error(f"Error getting history: {str(e)}")
            return None

    async def get_conversion_history_stats(self) -> Dict:
        """Get statistics for conversion history"""
        try:
            total_conversions = await self.conversion_history_collection.count_documents({})
            successful_conversions = await self.conversion_history_collection.count_documents({"success": True})
            failed_conversions = await self.conversion_history_collection.count_documents({"success": False})
            
            # Get recent activity (last 24 hours)
            yesterday = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            recent_activity = await self.conversion_history_collection.count_documents({
                "created_at": {"$gte": yesterday}
            })
            
            return {
                "total_conversions": total_conversions,
                "successful_conversions": successful_conversions,
                "failed_conversions": failed_conversions,
                "success_rate": (successful_conversions / total_conversions * 100) if total_conversions > 0 else 0,
                "recent_activity": recent_activity
            }
        except Exception as e:
            logger.error(f"Error getting conversion stats: {str(e)}")
            return {
                "total_conversions": 0,
                "successful_conversions": 0,
                "failed_conversions": 0,
                "success_rate": 0,
                "recent_activity": 0
            }

    async def get_dashboard_stats(self) -> Dict:
        """Get comprehensive dashboard statistics"""
        try:
            # Get conversion stats
            conversion_stats = await self.get_conversion_history_stats()
            
            # Get total users
            total_users = await self.users_collection.count_documents({})
            active_users = await self.users_collection.count_documents({"is_active": True})
            
            # Get active sessions (conversions in last hour)
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            active_sessions = await self.conversion_history_collection.count_documents({
                "created_at": {"$gte": one_hour_ago}
            })
            
            # Get recent errors (failed conversions in last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_errors = await self.conversion_history_collection.count_documents({
                "success": False,
                "created_at": {"$gte": yesterday}
            })
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "active_sessions": active_sessions,
                "total_conversions": conversion_stats["total_conversions"],
                "successful_conversions": conversion_stats["successful_conversions"],
                "failed_conversions": conversion_stats["failed_conversions"],
                "success_rate": conversion_stats["success_rate"],
                "recent_errors": recent_errors,
                "recent_activity": conversion_stats["recent_activity"]
            }
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
            return {
                "total_users": 0,
                "active_users": 0,
                "active_sessions": 0,
                "total_conversions": 0,
                "successful_conversions": 0,
                "failed_conversions": 0,
                "success_rate": 0,
                "recent_errors": 0,
                "recent_activity": 0
            }

    async def get_60_day_conversion_growth(self) -> Dict:
        """Get 60-day conversion history growth data for dashboard chart"""
        try:
            # Calculate date range for last 60 days
            end_date = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
            start_date = end_date - timedelta(days=59)  # 60 days including today
            
            # Aggregate conversions by day
            pipeline = [
                {
                    "$match": {
                        "created_at": {
                            "$gte": start_date,
                            "$lte": end_date
                        }
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$created_at"},
                            "month": {"$month": "$created_at"},
                            "day": {"$dayOfMonth": "$created_at"}
                        },
                        "total_conversions": {"$sum": 1},
                        "successful_conversions": {
                            "$sum": {"$cond": [{"$eq": ["$success", True]}, 1, 0]}
                        },
                        "failed_conversions": {
                            "$sum": {"$cond": [{"$eq": ["$success", False]}, 1, 0]}
                        }
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]
            
            results = await self.conversion_history_collection.aggregate(pipeline).to_list(length=None)
            
            # Create a complete 60-day dataset with zeros for missing days
            daily_data = {}
            current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Initialize all days with zero values
            for i in range(60):
                date_key = current_date.strftime("%Y-%m-%d")
                daily_data[date_key] = {
                    "date": date_key,
                    "total_conversions": 0,
                    "successful_conversions": 0,
                    "failed_conversions": 0
                }
                current_date += timedelta(days=1)
            
            # Fill in actual data
            for result in results:
                date_obj = datetime(
                    year=result["_id"]["year"],
                    month=result["_id"]["month"],
                    day=result["_id"]["day"]
                )
                date_key = date_obj.strftime("%Y-%m-%d")
                
                if date_key in daily_data:
                    daily_data[date_key]["total_conversions"] = result["total_conversions"]
                    daily_data[date_key]["successful_conversions"] = result["successful_conversions"]
                    daily_data[date_key]["failed_conversions"] = result["failed_conversions"]
            
            # Convert to sorted list
            growth_data = list(daily_data.values())
            growth_data.sort(key=lambda x: x["date"])
            
            # Format for chart.js
            labels = [item["date"] for item in growth_data]
            total_data = [item["total_conversions"] for item in growth_data]
            success_data = [item["successful_conversions"] for item in growth_data]
            failed_data = [item["failed_conversions"] for item in growth_data]
            
            return {
                "labels": labels,
                "datasets": {
                    "total_conversions": total_data,
                    "successful_conversions": success_data,
                    "failed_conversions": failed_data
                },
                "summary": {
                    "total_period_conversions": sum(total_data),
                    "total_period_success": sum(success_data),
                    "total_period_failed": sum(failed_data),
                    "period_success_rate": (sum(success_data) / sum(total_data) * 100) if sum(total_data) > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting 60-day conversion growth: {str(e)}")
            return {
                "labels": [],
                "datasets": {
                    "total_conversions": [],
                    "successful_conversions": [],
                    "failed_conversions": []
                },
                "summary": {
                    "total_period_conversions": 0,
                    "total_period_success": 0,
                    "total_period_failed": 0,
                    "period_success_rate": 0
                }
            }

    async def get_recent_activity_feed(self, page: int = 1, limit: int = 10) -> Tuple[List[Dict], Dict]:
        """Get recent activity feed for dashboard with pagination"""
        try:
            # Calculate skip for pagination
            skip = (page - 1) * limit
            
            # Get total count
            total = await self.conversion_history_collection.count_documents({})
            
            # Get recent conversions with pagination
            conversions = await self.conversion_history_collection.find().sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
            
            activity_feed = []
            for conversion in conversions:
                user_id = conversion.get("user_id", "Unknown")
                filename = conversion.get("filename", "unknown_file")
                success = conversion.get("success", False)
                created_at = conversion.get("created_at", datetime.utcnow())
                
                # Convert to IST for display
                created_at_ist = self._convert_to_ist(created_at)
                
                activity = {
                    "type": "conversion",
                    "message": f"{'Successful' if success else 'Failed'} conversion of '{filename}' by user {user_id}",
                    "timestamp": created_at_ist,
                    "success": success,
                    "user_id": user_id,
                    "filename": filename
                }
                activity_feed.append(activity)

            # Calculate pagination
            total_pages = (total + limit - 1) // limit
            next_page = page + 1 if page < total_pages else None
            prev_page = page - 1 if page > 1 else None

            pagination = {
                "current_page": page,
                "next_page": next_page,
                "prev_page": prev_page,
                "total_pages": total_pages,
                "total_items": total
            }
            
            return activity_feed, pagination
            
        except Exception as e:
            logger.error(f"Error getting recent activity feed: {str(e)}")
            # Return empty pagination for error case
            empty_pagination = {
                "current_page": 1,
                "next_page": None,
                "prev_page": None,
                "total_pages": 1,
                "total_items": 0
            }
            return [], empty_pagination
