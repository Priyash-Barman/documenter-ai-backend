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