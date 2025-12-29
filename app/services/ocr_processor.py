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
            logger.info("--- RAW OCR TEXT START ---")
            logger.info(text)
            logger.info("--- RAW OCR TEXT END ---")
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
        from datetime import datetime
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', # 12/31/2023 or 31/12/2023
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', # 2023-12-31
        ]
        
        # Try to parse and convert to ISO YYYY-MM-DD
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                parts = match.groups()
                try:
                    # Case 1: YYYY-MM-DD
                    if len(parts[0]) == 4:
                        return f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
                    # Case 2: MM/DD/YY(YY) or DD/MM/YY(YY) - Try both
                    year = parts[2]
                    if len(year) == 2: year = "20" + year
                    
                    # Heuristic for US vs MX (default to MM/DD for now as per user preference)
                    return f"{year}-{int(parts[0]):02d}-{int(parts[1]):02d}"
                except Exception:
                    continue
                    
        return None
    
    def extract_vendor(self, text: str) -> Optional[str]:
        """Extract vendor name (usually first line with text)"""
        # Common stop-words for vendors (slogans, etc.)
        SKIP_LIST = ['invoice', 'factura', 'receipt', 'recibo', 'ticket', 'nota', 'original', 'servicio', 'service']
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Candidates for vendor
        candidates = []
        for line in lines[:10]:
            if len(line) >= 3 and not re.match(r'^[\d\s\$\.,\-\/]+$', line):
                if not any(skip in line.lower() for skip in SKIP_LIST):
                    # Prefer shorter lines for vendor name (slogans are usually longer)
                    candidates.append(line)
        
        # Clean vendor name from strange prefix/suffix (like [ or | from logos)
        if candidates:
            vendor = candidates[0]
            for c in candidates:
                if len(c) < 30:
                    vendor = c
                    break
            
            # Clean non-alphanumeric noise from start/end
            vendor = re.sub(r'^[^a-zA-Z0-9]+', '', vendor)
            vendor = re.sub(r'[^a-zA-Z0-9\s\.]+$', '', vendor)
            return vendor[:255].strip()
            
        return lines[0][:255] if lines else None
    
    def extract_fields(self, text: str, currency: str) -> Dict:
        """Extract structured fields from OCR text"""
        fields = {
            'vendor': self.extract_vendor(text),
            'date': self.extract_date(text),
        }
        
        # 1. Look for all amounts in the text
        all_amounts = []
        monetary_matches = re.finditer(r'\$?\s*([\d,]+\.\d{2})', text)
        for m in monetary_matches:
            try:
                val = float(m.group(1).replace(',', ''))
                all_amounts.append(val)
            except ValueError:
                continue

        # 2. Extract Total using more specific patterns
        total_patterns = [
            r'(?:total|total\s+amount|amount\s+due|balance|total\s+a\s+pagar|importe\s+total)[:\s]*\$?\s*([\d,]+\.\d{2})',
        ]
        
        extracted_total = None
        for pattern in total_patterns:
            # Find all matches and take the LAST one (totals are usually at the bottom)
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    # Clean up commas and convert to float
                    extracted_total = float(matches[-1].replace(',', ''))
                    break
                except ValueError:
                    continue
        
        if extracted_total:
            fields['total'] = extracted_total
        elif all_amounts:
            # Heuristic: The total is almost always the largest amount on the page
            fields['total'] = max(all_amounts)

        # 3. Extract Tax
        tax_amount = None
        tax_patterns = [
            r'(?:sales\s+tax|tax|tax\s+amount|stax|iva|i\.v\.a\.|impuesto)[:\s]*\$?\s*([\d,]+\.\d{2})',
        ]
        
        for pattern in tax_patterns:
            # Match the one with the tax keyword
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    tax_amount = float(matches[-1].replace(',', ''))
                    break
                except ValueError:
                    continue
        
        # Texas-specific logic fallback
        if currency == "USD" and not tax_amount and 'total' in fields:
            texas_rate = 0.0825
            for amt in all_amounts:
                # Check if this amount is roughly 8.25% of the rest
                if abs(amt - (fields['total'] - amt) * texas_rate) < 0.10:
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
