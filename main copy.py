from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from typing import List
import pandas as pd
import os
from app.models.resume_parser import ResumeParser

app = FastAPI()

# Create uploads directory if it doesn't exist
os.makedirs("app/uploads", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Initialize parser
parser = ResumeParser()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_files(
    resumes: List[UploadFile] = File(...),
    job_description: UploadFile = File(...)
):
    try:
        # Save files
        resume_paths = []
        for resume in resumes:
            file_path = os.path.join("app/uploads", resume.filename)
            with open(file_path, "wb") as f:
                content = await resume.read()
                f.write(content)
            resume_paths.append(file_path)
        
        # Save job description
        jd_path = os.path.join("app/uploads", job_description.filename)
        with open(jd_path, "wb") as f:
            content = await job_description.read()
            f.write(content)

        # Read files for processing
        resume_contents = [open(path, "rb").read() for path in resume_paths]
        resume_extensions = [resume.filename.split('.')[-1] for resume in resumes]
        resume_names = [resume.filename for resume in resumes]
        jd_content = open(jd_path, "rb").read()
        jd_extension = job_description.filename.split('.')[-1]

        # Process files
        results_df = parser.parse_resumes(
            resume_contents,
            resume_extensions,
            jd_content,
            jd_extension
        )

        # Add resume file names and links
        results_df['resume_file_name'] = resume_names
        results_df['resume_file_link'] = [f"/download/{name}" for name in resume_names]

        # Sort by similarity score
        results_df = results_df.sort_values('Similarity', ascending=False)

        # Convert to dict for JSON response
        results = results_df.to_dict(orient='records')
        return JSONResponse(content={"results": results})

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join("app/uploads", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)