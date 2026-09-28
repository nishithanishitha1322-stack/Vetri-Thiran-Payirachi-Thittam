from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.pdf_service import extract_text_from_pdf
from services.gemini_service import analyze_legal_document
from models.schemas import LegalAnalysisResponse

app = FastAPI(title="LegalEase API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "LegalEase API Running"}

@app.post("/analyze-pdf", response_model=LegalAnalysisResponse)
async def analyze_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    try:
        file_bytes = await file.read()
        text = extract_text_from_pdf(file_bytes)
        if len(text) < 50:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        result = analyze_legal_document(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-text", response_model=LegalAnalysisResponse)
async def analyze_text(data: dict):
    text = data.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    result = analyze_legal_document(text)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)