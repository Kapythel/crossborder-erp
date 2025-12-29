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
        self.tesseract_config = '--oem 3 --psm 3 -l eng+spa'  # LSTM, auto segment, English + Spanish
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy using Pillow"""
        # 1. Upscale if image is small (helps Tesseract with small fonts)
        width, height = image.size
        if width < 1000:
            scale = 2000 / width
            image = image.resize((int(width * scale), int(height * scale)), Image.LANCZOS)
            
        # 2. Convert to grayscale
        image = image.convert('L')
        
        # 3. Enhance Contrast & Sharpness
        from PIL import ImageEnhance, ImageFilter
        
        # Sharpen the image
        image = image.filter(ImageFilter.SHARPEN)
        
        # High contrast (almost binarization)
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(3.0)
        
        # 4. Optional: Denoise with a small blur if too grainy
        # image = image.filter(ImageFilter.MedianFilter(size=3))
        
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
        # Common date formats: MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD, etc.
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', # 12/31/2023 or 31-12-23
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})', # 2023-12-31
            r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2},?\s+\d{4}', # Jan 31, 2023
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def extract_vendor(self, text: str) -> Optional[str]:
        """Extract vendor name (usually first line with text)"""
        # Skip common generic headings
        SKIP_LIST = ['invoice', 'factura', 'receipt', 'recibo', 'ticket', 'nota', 'original']
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines[:8]:  # Check first 8 lines
            if len(line) >= 3 and not re.match(r'^[\d\s\$\.,\-\/]+$', line):
                if not any(skip in line.lower() for skip in SKIP_LIST):
                    return line[:255]
        
        # Fallback to first line if everything was skipped
        return lines[0][:255] if lines else None
    
    def extract_fields(self, text: str, currency: str) -> Dict:
        """Extract structured fields from OCR text"""
        fields = {
            'vendor': self.extract_vendor(text),
            'date': self.extract_date(text),
        }
        
        # Extract total (look for the largest amount near keywords or the last numeric value)
        total_patterns = [
            r'(?:total|total amount|amount due|balance|total a pagar|importe total)[:\s]*\$?\s*([\d,]+\.\d{2})',
            r'[\$]\s*([\d,]+\.\d{2})(?:\s*total)?',
        ]
        
        all_amounts = []
        # Find all monetary-looking values in the text
        monetary_matches = re.finditer(r'\$?\s*([\d,]+\.\d{2})', text)
        for m in monetary_matches:
            try:
                val = float(m.group(1).replace(',', ''))
                all_amounts.append(val)
            except ValueError:
                continue

        for pattern in total_patterns:
            amount = self.extract_amount(text, pattern)
            if amount:
                fields['total'] = amount
                break
        
        # If no total found via keyword, try the largest amount found (heuristic)
        if 'total' not in fields and all_amounts:
            fields['total'] = max(all_amounts)

        # Extract tax
        tax_amount = None
        if currency == "USD":
            tax_patterns = [
                r'(?:sales tax|tax|tax amount|stax)[:\s]*\$?\s*([\d,]+\.\d{2})',
            ]
        else:  # MXN
            tax_patterns = [
                r'(?:iva|i\.v\.a\.|impuesto)[:\s]*\$?\s*([\d,]+\.\d{2})',
            ]
        
        for pattern in tax_patterns:
            amount = self.extract_amount(text, pattern)
            if amount:
                tax_amount = amount
                break
        
        # Texas-specific logic: If currency is USD and we have a total but no tax, 
        # check if 8.25% of any sub-amount matches
        if currency == "USD" and not tax_amount and 'total' in fields:
            texas_rate = 0.0825
            estimated_subtotal = fields['total'] / (1 + texas_rate)
            estimated_tax = fields['total'] - estimated_subtotal
            
            # Check if any found amount matches the 8.25% tax
            for amt in all_amounts:
                if abs(amt - estimated_tax) < 0.05: # Allow 5 cents difference for rounding
                    tax_amount = amt
                    break
        
        if tax_amount:
            fields['tax'] = tax_amount
        
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
