import streamlit as st
import numpy as np
import cv2
from src.regex_parser import parse_packaging_text, generate_compliance_report
from paddleocr import PaddleOCR

# Page configuration
st.set_page_config(page_title="Legal Metrology Compliance", page_icon="📦")
st.title("📦 Legal Metrology Compliance Inspector")

# Cache PaddleOCR model to optimize memory usage
@st.cache_resource
def load_ocr():
    return PaddleOCR(use_angle_cls=False, lang='en', enable_mkldnn=False)

ocr = load_ocr()

uploaded_file = st.file_uploader("Upload Packaging Image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Read image into OpenCV format
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

    if st.button("Analyze Package"):
        with st.spinner("Processing image with PaddleOCR..."):
            # Run OCR prediction
            results = ocr.predict(image)
            extracted_fields = parse_packaging_text(results)
            report = generate_compliance_report(extracted_fields)

        st.subheader("Inspection Summary")
        if report["compliance_status"] == "COMPLIANT":
            st.success(f"Status: {report['compliance_status']}")
        else:
            st.error(f"Status: {report['compliance_status']}")

        st.json(report)