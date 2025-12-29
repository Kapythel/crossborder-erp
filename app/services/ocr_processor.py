import pytesseract
from PIL import Image
import re
from typing import Dict, Optional, Tuple
import io
from pdf2image import convert_from_bytes
import logging

logger = logging.getLogger(__name__)


class OCRProcessor:
    """OCR processing service for receipts and documents"""
    
    # Currency detection keywords
    USD_KEYWORDS = ['usd', 'dollar', 'sales tax', '$', 'us']
    MXN_KEYWORDS = ['mxn', 'peso', 'iva', 'rfc', 'mx']
    
    def __init__(self):
        """Initialize OCR processor"""
        self.tesseract_config = '--oem 3 --psm 6'  # LSTM OCR, assume uniform block of text
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy"""
        # Convert to grayscale
        image = image.convert('L')
        
        # Enhance contrast (simple threshold)
        # For production, consider using adaptive thresholding
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        return image
    
    def extract_text_from_image(self, image_bytes: bytes) -> str:
        """Extract text from image bytes"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image = self.preprocess_image(image)
            text = pytesseract.image_to_string(image, config=self.tesseract_config)
            return text
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise
    
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF"""
        try:
            # Convert PDF to images
            images = convert_from_bytes(pdf_bytes)
            
            text_parts = []
            for image in images:
                image = self.preprocess_image(image)
                text = pytesseract.image_to_string(image, config=self.tesseract_config)
                text_parts.append(text)
            
            return "\n\n--- PAGE BREAK ---\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    def detect_currency(self, text: str) -> str:
        """Detect currency from text content"""
        text_lower = text.lower()
        
        # Count keyword occurrences
        usd_score = sum(1 for keyword in self.USD_KEYWORDS if keyword in text_lower)
        mxn_score = sum(1 for keyword in self.MXN_KEYWORDS if keyword in text_lower)
        
        # Default to USD if unclear
        return "MXN" if mxn_score > usd_score else "USD"
    
    def extract_amount(self, text: str, pattern: str) -> Optional[float]:
        """Extract amount using regex pattern"""
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extract the numeric part
                amount_str = match.group(2) if len(match.groups()) >= 2 else match.group(1)
                # Remove commas and convert to float
                amount_str = amount_str.replace(',', '')
                return float(amount_str)
        except (ValueError, AttributeError) as e:
            logger.debug(f"Could not extract amount with pattern {pattern}: {e}")
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """Extract date from text"""
        # US format: MM/DD/YYYY or MM-DD-YYYY
        us_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        # MX format: DD/MM/YYYY
        match = re.search(us_pattern, text)
        if match:
            return match.group(1)
        return None
    
    def extract_vendor(self, text: str) -> Optional[str]:
        """Extract vendor name (usually first line with text)"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        # Return first non-empty line that has at least 3 characters
        for line in lines[:5]:  # Check first 5 lines
            if len(line) >= 3 and not re.match(r'^[\d\s\$\.,\-\/]+$', line):
                return line[:255]  # Limit to 255 chars
        return None
    
    def extract_fields(self, text: str, currency: str) -> Dict:
        """Extract structured fields from OCR text"""
        fields = {
            'vendor': self.extract_vendor(text),
            'date': self.extract_date(text),
        }
        
        # Extract total
        total_patterns = [
            r'(total|TOTAL)[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
            r'(amount due|AMOUNT DUE)[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
            r'(balance|BALANCE)[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
        ]
        for pattern in total_patterns:
            amount = self.extract_amount(text, pattern)
            if amount:
                fields['total'] = amount
                break
        
        # Extract tax
        if currency == "USD":
            tax_patterns = [
                r'(sales tax|tax|TAX)[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
            ]
        else:  # MXN
            tax_patterns = [
                r'(iva|IVA)[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
            ]
        
        for pattern in tax_patterns:
            amount = self.extract_amount(text, pattern)
            if amount:
                fields['tax'] = amount
                break
        
        # Extract tip
        tip_patterns = [
            r'(tip|propina|PROPINA|TIP)[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
            r'(gratuity|GRATUITY)[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
        ]
        for pattern in tip_patterns:
            amount = self.extract_amount(text, pattern)
            if amount:
                fields['tip'] = amount
                break
        
        # Calculate subtotal if we have total and tax
        if 'total' in fields and 'tax' in fields:
            fields['subtotal'] = fields['total'] - fields['tax']
            if 'tip' in fields:
                fields['subtotal'] -= fields['tip']
        
        return fields
    
    def process(self, file_bytes: bytes, content_type: str) -> Tuple[str, str, Dict]:
        """
        Main processing method
        
        Returns:
            Tuple of (raw_text, currency, extracted_fields)
        """
        # Extract text based on content type
        if content_type.startswith('image/'):
            raw_text = self.extract_text_from_image(file_bytes)
        elif content_type == 'application/pdf':
            raw_text = self.extract_text_from_pdf(file_bytes)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
        
        # Detect currency
        currency = self.detect_currency(raw_text)
        
        # Extract fields
        extracted_fields = self.extract_fields(raw_text, currency)
        
        return raw_text, currency, extracted_fields
