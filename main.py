import os
import cv2

os.environ['FLAGS_use_mkldnn'] = '0'
from paddleocr import PaddleOCR
from src.regex_parser import parse_packaging_text, generate_compliance_report

def run_pipeline(image_path):
    if not os.path.exists(image_path):
        print(f"Error: Could not find image at {image_path}.")
        return

    print("Running OCR Pipeline...")
    ocr = PaddleOCR(use_textline_orientation=True, lang='en', enable_mkldnn=False)

    image = cv2.imread(image_path)
    results = ocr.predict(image)

    extracted_lines = []
    if results:
        for res in results:
            rec_texts = res.get('rec_texts', []) if isinstance(res, dict) else getattr(res, 'rec_texts', [])
            extracted_lines.extend(rec_texts)

    print("\nParsing Legal Metrology Compliance...")
    data = parse_packaging_text(extracted_lines)
    report = generate_compliance_report(data)

    print("\n" + "="*50)
    print(f"COMPLIANCE STATUS: {report['status']}")
    print("="*50)
    print("Extracted Data:", report['extracted_fields'])
    print("\nViolations Detected:")
    for v in report['violations']:
        print(f" - {v}")
    print("="*50)

if __name__ == "__main__":
    test_image_path = os.path.join("data", "sample1.jpeg")
    run_pipeline(test_image_path)