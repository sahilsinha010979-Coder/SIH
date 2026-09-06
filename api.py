import os
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from paddleocr import PaddleOCR

# Import your existing compliance logic
from src.regex_parser import parse_packaging_text, generate_compliance_report

os.environ['FLAGS_use_mkldnn'] = '0'

app = FastAPI(
    title="Legal Metrology Compliance API",
    description="API for detecting Legal Metrology violations on packaged commodities using PaddleOCR & Regex",
    version="1.0.0"
)

# Enable CORS so your frontend team (React/Streamlit/Mobile) can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global OCR engine instance to avoid re-initializing on every request
ocr_engine = None

@app.on_event("startup")
def load_model():
    global ocr_engine
    print("Loading PaddleOCR model into memory...")
    ocr_engine = PaddleOCR(use_textline_orientation=True, lang='en', enable_mkldnn=False)
    print("PaddleOCR model ready!")


@app.get("/")
def health_check():
    return {"status": "healthy", "service": "Legal Metrology Compliance Engine API"}


@app.post("/api/v1/inspect")
async def inspect_packaging(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image (JPEG, PNG, etc.).")

    try:
        # Read image bytes directly from request payload
        contents = await file.read()
        np_arr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode uploaded image.")

        # Execute OCR
        results = ocr_engine.predict(image)

        extracted_lines = []
        if results:
            for res in results:
                rec_texts = res.get('rec_texts', []) if isinstance(res, dict) else getattr(res, 'rec_texts', [])
                extracted_lines.extend(rec_texts)

        # Execute Regex Parsing & Rule Validation
        parsed_fields = parse_packaging_text(extracted_lines)
        report = generate_compliance_report(parsed_fields)

        return {
            "filename": file.filename,
            "compliance_status": report["status"],
            "extracted_fields": report["extracted_fields"],
            "violations": report["violations"],
            "raw_ocr_lines": extracted_lines
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")