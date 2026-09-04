import re

def parse_packaging_text(ocr_text_lines):
    full_text = " ".join(ocr_text_lines)
    
    # Improved Regex Patterns
    patterns = {
        "mrp": r"(?:Rs\.?|MRP|₹)\s*(\d+(?:\.\d{1,2})?)",
        "net_quantity": r"(?i)(?:NET|VOL|QTY|WEIGHT)?\.?\s*(\d+\s*(?:ml|l|g|kg|pcs|n))\b",
        "mfg_expiry_date": r"(\d{2}/\d{2,4}\s*[-–]\s*\d{2}/\d{2,4}|\b(?:MFG|EXP|BEST BEFORE)\b[^,.]+)",
        "country_of_origin": r"(?i)(MADE\s*IN\s*INDIA|COUNTRY\s*OF\s*ORIGIN)",
        "consumer_email": r"[\w\.-]+@[\w\.-]+\.\w+",
        "consumer_phone": r"(?:1800\d+|[\d\s-]{10,12})"
    }
    
    extracted_data = {}
    
    for field, pattern in patterns.items():
        match = re.search(pattern, full_text)
        if match:
            extracted_data[field] = match.group(0).strip()
        else:
            extracted_data[field] = None
            
    # Check for tax declaration
    extracted_data["tax_declaration"] = bool(re.search(r"(?i)incl(?:usive)?\.?\s*of\s*all\s*taxes", full_text))
            
    return extracted_data

def generate_compliance_report(extracted_data):
    violations = []
    
    if not extracted_data["mrp"]:
        violations.append("CRITICAL: MRP is missing from packaging.")
    elif not extracted_data["tax_declaration"]:
        violations.append("HIGH: MRP does not explicitly declare 'Inclusive of all taxes'.")
        
    if not extracted_data["net_quantity"]:
        violations.append("CRITICAL: Net Quantity / Volume declaration is missing.")
        
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