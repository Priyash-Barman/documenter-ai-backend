from bson import ObjectId
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from utils.logger import logger

class ConverterService:
    def __init__(self, mongo):
        self.logs_collection = mongo["logs"]

    async def convert_image(self, image_data: bytes, model: str) -> bytes:
        processed_image_data = image_data
        # print(processed_image_data)
        return processed_image_data