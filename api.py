import os
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from paddleocr import PaddleOCR
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.regex_parser import parse_packaging_text, generate_compliance_report
from database import InspectionLog, get_db

os.environ['FLAGS_use_mkldnn'] = '0'

app = FastAPI(
    title="Legal Metrology Compliance API",
    description="API for detecting Legal Metrology violations on packaged commodities using PaddleOCR & Regex",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ocr_engine = None

@app.on_event("startup")
def load_model():
    global ocr_engine
    print("Loading PaddleOCR model into memory...")
    ocr_engine = PaddleOCR(
        use_angle_cls=False,
        lang='en',
        enable_mkldnn=False
    )
    print("PaddleOCR model ready!")


app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/")
def serve_ui():
    return FileResponse("static/index.html")

@app.post("/api/v1/inspect")
async def inspect_packaging(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image (JPEG, PNG, etc.).")

    try:
        contents = await file.read()
        np_arr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode uploaded image.")

        results = ocr_engine.predict(image)

        extracted_lines = []
        if results:
            for res in results:
                rec_texts = res.get('rec_texts', []) if isinstance(res, dict) else getattr(res, 'rec_texts', [])
                extracted_lines.extend(rec_texts)

        parsed_fields = parse_packaging_text(extracted_lines)
        report = generate_compliance_report(parsed_fields)

        # Audit Log Entry
        try:
            db_log = InspectionLog(
                filename=file.filename,
                compliance_status=report["status"],
                extracted_fields=report["extracted_fields"],
                violations=report["violations"]
            )
            db.add(db_log)
            db.commit()
            db.refresh(db_log)
        except Exception as db_err:
            print(f"Database logging warning: {db_err}")
            db.rollback()

        return {
            "filename": file.filename,
            "compliance_status": report["status"],
            "extracted_fields": report["extracted_fields"],
            "violations": report["violations"],
            "raw_ocr_lines": extracted_lines
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.get("/api/v1/logs")
def fetch_logs(limit: int = 10, db: Session = Depends(get_db)):
    return db.query(InspectionLog).order_by(InspectionLog.timestamp.desc()).limit(limit).all()