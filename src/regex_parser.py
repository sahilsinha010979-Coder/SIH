import re

def parse_packaging_text(ocr_text_lines):
    full_text = " ".join(ocr_text_lines)
    
    # Regex Patterns for real-world packaging variations
    patterns = {
        # 1. Matches MRP attached to text OR standalone currency/price figures (e.g., 235.00, Rs 235, 249:00)
        "mrp": r"(?:M\.?R\.?P\.?|Rs\.?|₹|\bMRP\b)[\s\:\=]*[\(\)a-zA-Z\s]*(\d+(?:\.\d{1,2})?)|(?:\₹|Rs\.?)\s*(\d+(?:\.\d{1,2})?)|\b\d{2,4}[\:\.]\d{2}\b",
        
        # 2. Matches volume/weight formats (e.g., 100 g, 80ml, 50g)
        "net_quantity": r"(?i)(?:NET|VOL|QTY|WEIGHT|CONTENTS)?\.?\s*(\d+\s*(?:g|kg|ml|l|pcs|n))\b",
        
        # 3. Matches ranges (03/25-02/28) OR standalone month/year dates (e.g., 04/26, 04/2026)
        "mfg_expiry_date": r"\b\d{2}/\d{2,4}\b(?:\s*[-–]\s*\d{2}/\d{2,4})?",
        
        # 4. Matches explicit "MADE IN INDIA" or checks Indian manufacturer addresses / Pin Codes
        "country_of_origin": r"(?i)(MADE\s*IN\s*INDIA|COUNTRY\s*OF\s*ORIGIN|NEW\s*DELHI|HARIDWAR|UTTARAKHAND|INDIA)",
        
        # 5. Email matching
        "consumer_email": r"[\w\.-]+@[\w\.-]+\.\w+",
        
        # 6. Toll-free numbers or phone formats
        "consumer_phone": r"(?:1800\s*\d+|\b\d{10,12}\b|\d{4}\s*\d{3}\s*\d{3})"
    }
    
    extracted_data = {}
    
    for field, pattern in patterns.items():
        match = re.search(pattern, full_text)
        if match:
            extracted_data[field] = match.group(0).strip()
        else:
            extracted_data[field] = None
            
    # Check for tax declaration anywhere in full text
    extracted_data["tax_declaration"] = bool(re.search(r"(?i)(incl|inclusive)\.?\s*(of)?\s*all\s*taxes", full_text))
            
    return extracted_data

def generate_compliance_report(extracted_data):
    violations = []
    
    if not extracted_data["mrp"]:
        violations.append("CRITICAL: MRP is missing from packaging.")
    elif not extracted_data["tax_declaration"]:
        violations.append("HIGH: MRP does not explicitly declare 'Inclusive of all taxes'.")
        
    if not extracted_data["net_quantity"]:
        violations.append("CRITICAL: Net Quantity / Volume declaration is missing.")
        
    if not extracted_data["mfg_expiry_date"]:
        violations.append("MEDIUM: Manufacturing / Expiry date declaration not found.")
        
    if not extracted_data["country_of_origin"]:
        violations.append("MEDIUM: Country of Origin declaration not found.")

    if not extracted_data["consumer_email"] and not extracted_data["consumer_phone"]:
        violations.append("HIGH: No Consumer Care contact details (Email or Phone) detected.")
        
    status = "NON-COMPLIANT" if violations else "COMPLIANT"
    
    return {
        "status": status,
        "extracted_fields": extracted_data,
        "violations": violations
    }