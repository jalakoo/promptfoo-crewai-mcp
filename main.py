import time
import os
from datetime import datetime
from fastapi import FastAPI, Query, Body, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from crew_manager import run
import uvicorn
from pydantic import BaseModel
from typing import Optional, Dict, Any

class PromptRequest(BaseModel):
    prompt: str
    full_model_name: str = "sambanova/Meta-Llama-3.1-8B-Instruct"

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to log request processing time
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/crewai")
async def get_crewai_endpoint(
    request: Request,
    prompt: str = Query(..., 
        description="The prompt / command to process",
        example="How many records are there?"
    ),
    full_model_name: str = Query(
        default="sambanova/Meta-Llama-3.1-8B-Instruct",
        description="The LLM to use"
    )
):
    """GET endpoint that accepts prompt and llm_name as query parameters"""
    start_time = time.time()
    request_id = request.headers.get('X-Request-ID', 'no-request-id')
    timestamp = datetime.now().isoformat()
    
    print(f'[{timestamp}] [Request-ID: {request_id}] GET /crewai - Processing request')
    print(f'[{timestamp}] [Request-ID: {request_id}] Prompt: {prompt}')
    
    try:
        result = run(prompt, full_model_name)
        process_time = time.time() - start_time
        
        print(f'[{timestamp}] [Request-ID: {request_id}] Request completed in {process_time:.4f}s')
        return result
    except Exception as e:
        process_time = time.time() - start_time
        error_msg = f"Error processing request: {str(e)}"
        print(f'[{timestamp}] [Request-ID: {request_id}] {error_msg}')
        print(f'[{timestamp}] [Request-ID: {request_id}] Request failed after {process_time:.4f}s')
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/crewai")
async def post_crewai_endpoint(request: Request, payload: PromptRequest):
    """POST endpoint that accepts a JSON payload with prompt and llm_name"""
    start_time = time.time()
    request_id = request.headers.get('X-Request-ID', 'no-request-id')
    timestamp = datetime.now().isoformat()
    
    print(f'[{timestamp}] [Request-ID: {request_id}] POST /crewai - Processing request')
    print(f'[{timestamp}] [Request-ID: {request_id}] Prompt: {payload.prompt}')
    
    try:
        result = run(payload.prompt, payload.full_model_name)
        process_time = time.time() - start_time
        
        print(f'[{timestamp}] [Request-ID: {request_id}] Request completed in {process_time:.4f}s')
        return result
    except Exception as e:
        process_time = time.time() - start_time
        error_msg = f"Error processing request: {str(e)}"
        print(f'[{timestamp}] [Request-ID: {request_id}] {error_msg}')
        print(f'[{timestamp}] [Request-ID: {request_id}] Request failed after {process_time:.4f}s')
        raise HTTPException(status_code=500, detail=error_msg)


if __name__ == "__main__":
    port = int(os.getenv("CREWAI_SERVER_PORT", 4000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)