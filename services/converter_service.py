from bson import ObjectId
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from utils.logger import logger
from .gemini_ai_service import GeminiAIService
import asyncio

class ConverterService:
    def __init__(self, mongo):
        self.logs_collection = mongo["logs"]
        self.history_collection = mongo["conversion_history"]
        self.gemini_service = GeminiAIService()

    async def convert_image(self, image_data: bytes, model: str, user_id: str = None, filename: str = None) -> bytes:
        """
        Convert image using specified AI model
        """
        conversion_id = ObjectId()
        start_time = datetime.utcnow()
        
        try:

            await self._log_conversion_start(conversion_id, model, user_id, filename)
            
            if model.lower() == "gemini":

                result = await self.gemini_service.digitize_handwritten_text(image_data)
                
                if result['success']:
                    processed_image_data = result['digitized_image']
                    extracted_text = result.get('extracted_text', '')
                    
                    await self._save_conversion_history(
                        conversion_id, user_id, filename, model, 
                        extracted_text, True, start_time
                    )
                    
                    logger.info(f"Gemini conversion successful for {filename}")
                    return processed_image_data
                else:

                    await self._save_conversion_history(
                        conversion_id, user_id, filename, model, 
                        f"Error: {result.get('error', 'Unknown error')}", False, start_time
                    )
                    logger.error(f"Gemini conversion failed: {result.get('error')}")
                    return image_data
            else:

                await self._save_conversion_history(
                    conversion_id, user_id, filename, model, 
                    "Model not implemented", False, start_time
                )
                logger.warning(f"Model {model} not implemented, returning original image")
                return image_data
                
        except Exception as e:
            logger.error(f"Error in convert_image: {str(e)}")
            await self._save_conversion_history(
                conversion_id, user_id, filename, model, 
                f"Exception: {str(e)}", False, start_time
            )
            return image_data

    async def _log_conversion_start(self, conversion_id: ObjectId, model: str, user_id: str, filename: str):
        """Log conversion start"""
        try:
            log_entry = {
                "_id": ObjectId(),
                "conversion_id": conversion_id,
                "user_id": user_id,
                "filename": filename,
                "model": model,
                "status": "started",
                "timestamp": datetime.utcnow(),
                "message": f"Starting conversion with {model}"
            }
            await self.logs_collection.insert_one(log_entry)
        except Exception as e:
            logger.error(f"Error logging conversion start: {str(e)}")

    async def _save_conversion_history(self, conversion_id: ObjectId, user_id: str, filename: str, 
                                     model: str, extracted_text: str, success: bool, start_time: datetime):
        """Save conversion to history"""
        try:
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            history_entry = {
                "_id": conversion_id,
                "user_id": user_id,
                "filename": filename,
                "model_used": model,
                "extracted_text": extracted_text,
                "success": success,
                "processing_time": processing_time,
                "created_at": start_time,
                "completed_at": end_time,
                "status": "completed" if success else "failed"
            }
            
            await self.history_collection.insert_one(history_entry)
            logger.info(f"Saved conversion history for {filename}")
            
        except Exception as e:
            logger.error(f"Error saving conversion history: {str(e)}")

    async def get_user_conversion_history(self, user_id: str, limit: int = 10, skip: int = 0) -> Tuple[List[Dict], int]:
        """Get user's conversion history with total count"""
        try:
            # Get total count for pagination
            total_count = await self.history_collection.count_documents({"user_id": user_id})
            
            cursor = self.history_collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(limit).skip(skip)
            
            history = []
            async for doc in cursor:
                # Convert ObjectId to string for JSON serialization
                doc["_id"] = str(doc["_id"])
                history.append(doc)
            
            return history, total_count
            
        except Exception as e:
            logger.error(f"Error getting conversion history: {str(e)}")
            return [], 0

    async def get_conversion_details(self, conversion_id: str, user_id: str) -> Optional[Dict]:
        """Get detailed information about a specific conversion"""
        try:
            doc = await self.history_collection.find_one({
                "_id": ObjectId(conversion_id),
                "user_id": user_id
            })
            
            if doc:
                doc["_id"] = str(doc["_id"])
                return doc
            return None
            
        except Exception as e:
            logger.error(f"Error getting conversion details: {str(e)}")
            return None