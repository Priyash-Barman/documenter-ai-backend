import google.generativeai as genai
import io
import base64
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
from typing import Optional, Dict, Any
from utils.logger import logger
import config

class GeminiAIService:
    def __init__(self):
        """Initialize Gemini service with API key"""
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
            logger.info("Gemini service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Gemini service: {str(e)}")
            raise
        
    async def digitize_handwritten_text(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze handwritten text in image and convert to digital format
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            logger.info(f"Processing image of size: {image.size}")
            
            # Prompt for text extraction and digitization
            prompt = """
            Analyze this image carefully. If it contains handwritten text, typed text, or any readable content:
            1. Extract ALL the text accurately, preserving the exact wording
            2. Maintain the original formatting and structure as much as possible
            3. If there are multiple sections, preserve their layout and hierarchy
            4. Include punctuation and special characters exactly as they appear
            5. If there are lists, tables, or structured data, maintain that structure
            6. Preserve line breaks and paragraph separations
            
            Please provide the extracted text in a clean, readable format that maintains the document's original structure.
            
            If the image doesn't contain readable text, please describe what you see in the image instead.
            """
            
            response = self.model.generate_content([prompt, image])
            extracted_text = response.text
            logger.info(f"Successfully extracted text: {len(extracted_text)} characters")
            
            digitized_image = self._create_digitized_document(extracted_text, image.size)
            
            img_byte_arr = io.BytesIO()
            digitized_image.save(img_byte_arr, format='PNG')
            digitized_bytes = img_byte_arr.getvalue()
            
            return {
                'success': True,
                'extracted_text': extracted_text,
                'digitized_image': digitized_bytes,
                'original_size': image.size
            }
            
        except Exception as e:
            logger.error(f"Error in Gemini text extraction: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'extracted_text': '',
                'digitized_image': image_data 
            }
    
    def _create_digitized_document(self, text: str, original_size: tuple) -> Image.Image:
        """
        Create a clean, digitized version of the document
        """
        try:
            width = max(800, original_size[0])
            height = max(1000, original_size[1])
            
            if width < 800:
                width = 800
            if height < 1000:
                height = 1000
                
            image = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(image)
            
            try:
                font_paths = [
                    "arial.ttf",  # Windows
                    "/System/Library/Fonts/Arial.ttf",  # macOS
                    "/usr/share/fonts/truetype/arial.ttf",  # Linux
                    "C:/Windows/Fonts/arial.ttf"  # Windows absolute path
                ]
                
                font = None
                title_font = None
                
                for font_path in font_paths:
                    try:
                        font = ImageFont.truetype(font_path, 20)
                        title_font = ImageFont.truetype(font_path, 24)
                        break
                    except:
                        continue
                
                if not font:
                    font = ImageFont.load_default()
                    title_font = ImageFont.load_default()
                    
            except Exception as e:
                logger.warning(f"Could not load custom fonts: {str(e)}")
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()
            
            header_text = "DIGITIZED DOCUMENT"
            header_bbox = draw.textbbox((0, 0), header_text, font=title_font)
            header_width = header_bbox[2] - header_bbox[0]
            header_x = (width - header_width) // 2
            
            draw.text((header_x, 30), header_text, fill='#2c3e50', font=title_font)
            
            draw.line([(50, 70), (width-50, 70)], fill='#bdc3c7', width=2)
            
            info_text = "Processed with Google Gemini"
            draw.text((50, 80), info_text, fill='#7f8c8d', font=font)
            
            y_position = 120
            line_height = 30
            margin_left = 50
            margin_right = 50
            max_width = width - margin_left - margin_right
            
            lines = self._split_text_to_lines(text, font, max_width, draw)
            
            for line in lines:
                if y_position + line_height > height - 80:  

                    draw.text((margin_left, y_position), "... (text continues)", fill='#7f8c8d', font=font)
                    break
                
                draw.text((margin_left, y_position), line, fill='#2c3e50', font=font)
                y_position += line_height
            
            footer_y = height - 50
            footer_text = f"Generated on: {self._get_current_datetime()} | Lines: {len(lines)}"
            draw.text((50, footer_y), footer_text, fill='#95a5a6', font=font)
            
            logger.info(f"Created digitized document with {len(lines)} lines")
            return image
            
        except Exception as e:
            logger.error(f"Error creating digitized document: {str(e)}")

            error_image = Image.new('RGB', (800, 600), 'white')
            error_draw = ImageDraw.Draw(error_image)
            error_draw.text((50, 50), f"Error creating digitized version: {str(e)}", fill='red')
            return error_image
    
    def _split_text_to_lines(self, text: str, font, max_width: int, draw) -> list:
        """Split text into lines that fit within the specified width"""
        lines = []
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                lines.append("") 
                continue
                
            words = paragraph.split()
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                
                try:
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    line_width = bbox[2] - bbox[0]
                    
                    if line_width <= max_width:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                except:
                    if len(test_line) <= 80:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
            
            if current_line:
                lines.append(current_line)
        
        return lines
    
    def _get_current_datetime(self) -> str:
        """Get current datetime as formatted string"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    async def analyze_document_structure(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze document structure and layout
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            
            prompt = """
            Analyze this document image and provide:
            1. Document type (letter, form, receipt, note, etc.)
            2. Main sections or components identified
            3. Overall layout description
            4. Any special formatting or structure elements
            5. Estimated number of words or text blocks
            6. Quality assessment of the image for text extraction
            
            Provide a detailed analysis in a structured format.
            """
            
            response = self.model.generate_content([prompt, image])
            
            return {
                'success': True,
                'analysis': response.text
            }
            
        except Exception as e:
            logger.error(f"Error in document analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }