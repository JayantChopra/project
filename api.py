"""FastAPI application with security checks for data processing."""
import os
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field, validator

from processor import DataProcessor
from utils import load_csv, save_json, file_hash
from logger import get_logger
from config import Config
from analyzer import DataAnalyzer
from security import (
    validate_path_traversal,
    sanitize_query,
    validate_file_extension,
    validate_file_size,
    validate_numeric_input,
    verify_api_key,
)

logger = get_logger("api")

# Initialize FastAPI app
app = FastAPI(
    title="Data Processing API",
    description="Secure API for data processing operations",
    version="1.0.0"
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
if Config.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=Config.ALLOWED_ORIGINS if '*' not in Config.ALLOWED_ORIGINS else ["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

# Security scheme
security_scheme = HTTPBearer(auto_error=False)


# Request/Response models
class SummarizeRequest(BaseModel):
    path: str = Field(..., description="Path to CSV file")
    output_path: Optional[str] = Field(None, description="Output path for summary JSON")
    
    @validator('path')
    def validate_path(cls, v):
        return validate_path_traversal(v, base_dir="data")


class AnalyzeRequest(BaseModel):
    path: str = Field(..., description="Path to CSV file")
    threshold: float = Field(3.0, ge=0.0, le=10.0, description="Z-score threshold")
    
    @validator('path')
    def validate_path(cls, v):
        return validate_path_traversal(v, base_dir="data")


class FilterRequest(BaseModel):
    path: str = Field(..., description="Path to CSV file")
    query: str = Field(..., description="Pandas query string")
    output_path: Optional[str] = Field(None, description="Output path for filtered CSV")
    
    @validator('path')
    def validate_path(cls, v):
        return validate_path_traversal(v, base_dir="data")
    
    @validator('query')
    def validate_query(cls, v):
        return sanitize_query(v)


class SampleRequest(BaseModel):
    path: str = Field(..., description="Path to CSV file")
    n: Optional[int] = Field(None, ge=1, le=10000, description="Number of rows to sample")
    frac: Optional[float] = Field(None, ge=0.0, le=1.0, description="Fraction of rows to sample")
    seed: int = Field(42, ge=0, description="Random seed")
    output_path: Optional[str] = Field(None, description="Output path for sampled CSV")
    
    @validator('path')
    def validate_path(cls, v):
        return validate_path_traversal(v, base_dir="data")


class DescribeRequest(BaseModel):
    path: str = Field(..., description="Path to CSV file")
    output_path: Optional[str] = Field(None, description="Output path for describe JSON")
    
    @validator('path')
    def validate_path(cls, v):
        return validate_path_traversal(v, base_dir="data")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"}
    )


# Health check endpoint (no auth required)
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Data processing endpoints
@app.post("/api/v1/summarize")
@limiter.limit(f"{Config.RATE_LIMIT_PER_MINUTE}/minute")
async def summarize(
    request: Request,
    req: SummarizeRequest,
    _: bool = Depends(verify_api_key)
):
    """Summarize dataset."""
    try:
        data_path = req.path
        output_path = req.output_path or Config.OUTPUT_PATH
        
        # Validate paths
        validate_path_traversal(data_path, base_dir="data")
        validate_path_traversal(os.path.dirname(output_path), base_dir="output")
        
        if not os.path.exists(data_path):
            raise HTTPException(status_code=404, detail="Data file not found")
        
        data = load_csv(data_path)
        processor = DataProcessor(data)
        summary = processor.summarize()
        
        save_json(summary, output_path)
        
        return {
            "success": True,
            "summary": summary,
            "output_path": output_path,
            "file_hash": file_hash(output_path)
        }
    except Exception as e:
        logger.error(f"Error in summarize: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analyze")
@limiter.limit(f"{Config.RATE_LIMIT_PER_MINUTE}/minute")
async def analyze(
    request: Request,
    req: AnalyzeRequest,
    _: bool = Depends(verify_api_key)
):
    """Detect anomalies in dataset."""
    try:
        data_path = req.path
        threshold = validate_numeric_input(req.threshold, min_val=0.0, max_val=10.0, param_name="threshold")
        
        validate_path_traversal(data_path, base_dir="data")
        
        if not os.path.exists(data_path):
            raise HTTPException(status_code=404, detail="Data file not found")
        
        data = load_csv(data_path)
        processor = DataProcessor(data)
        anomalies = processor.detect_anomalies(z_threshold=threshold)
        
        return {
            "success": True,
            "anomalies": anomalies,
            "threshold": threshold,
            "anomaly_count": sum(len(v) for v in anomalies.values())
        }
    except Exception as e:
        logger.error(f"Error in analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/correlate")
@limiter.limit(f"{Config.RATE_LIMIT_PER_MINUTE}/minute")
async def correlate(
    request: Request,
    path: str = Form(...),
    output_path: Optional[str] = Form(None),
    _: bool = Depends(verify_api_key)
):
    """Calculate correlation matrix."""
    try:
        data_path = validate_path_traversal(path, base_dir="data")
        corr_output_path = output_path or "output/correlation.json"
        validate_path_traversal(os.path.dirname(corr_output_path), base_dir="output")
        
        if not os.path.exists(data_path):
            raise HTTPException(status_code=404, detail="Data file not found")
        
        data = load_csv(data_path)
        processor = DataProcessor(data)
        processor.clean()
        analyzer = DataAnalyzer(processor.get_data())
        corr = analyzer.correlation_matrix()
        
        if corr:
            save_json(corr, corr_output_path)
            return {
                "success": True,
                "correlation_matrix": corr,
                "output_path": corr_output_path,
                "file_hash": file_hash(corr_output_path)
            }
        else:
            return {
                "success": True,
                "message": "No numeric data available for correlation analysis",
                "correlation_matrix": {}
            }
    except Exception as e:
        logger.error(f"Error in correlate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/filter")
@limiter.limit(f"{Config.RATE_LIMIT_PER_MINUTE}/minute")
async def filter_data(
    request: Request,
    req: FilterRequest,
    _: bool = Depends(verify_api_key)
):
    """Filter rows using pandas query."""
    try:
        data_path = req.path
        query = req.query
        output_path = req.output_path or "output/filtered.csv"
        
        validate_path_traversal(data_path, base_dir="data")
        validate_path_traversal(os.path.dirname(output_path), base_dir="output")
        
        if not os.path.exists(data_path):
            raise HTTPException(status_code=404, detail="Data file not found")
        
        data = load_csv(data_path)
        processor = DataProcessor(data)
        processor.clean()
        
        df = processor.get_data()
        try:
            filtered = df.query(query, engine="python")
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Query execution failed: {str(exc)}")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        filtered.to_csv(output_path, index=False)
        
        return {
            "success": True,
            "rows_filtered": len(filtered),
            "output_path": output_path,
            "file_hash": file_hash(output_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in filter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/sample")
@limiter.limit(f"{Config.RATE_LIMIT_PER_MINUTE}/minute")
async def sample_data(
    request: Request,
    req: SampleRequest,
    _: bool = Depends(verify_api_key)
):
    """Sample rows from dataset."""
    try:
        data_path = req.path
        output_path = req.output_path or "output/sampled.csv"
        
        validate_path_traversal(data_path, base_dir="data")
        validate_path_traversal(os.path.dirname(output_path), base_dir="output")
        
        if not os.path.exists(data_path):
            raise HTTPException(status_code=404, detail="Data file not found")
        
        if req.n is None and req.frac is None:
            n = 5
        else:
            n = req.n
        
        data = load_csv(data_path)
        processor = DataProcessor(data)
        processor.clean()
        
        df = processor.get_data()
        sampled = df.sample(n=n, frac=req.frac, random_state=req.seed) if req.frac else df.sample(n=n, random_state=req.seed)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        sampled.to_csv(output_path, index=False)
        
        return {
            "success": True,
            "rows_sampled": len(sampled),
            "output_path": output_path,
            "file_hash": file_hash(output_path)
        }
    except Exception as e:
        logger.error(f"Error in sample: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/v1/describe")
@limiter.limit(f"{Config.RATE_LIMIT_PER_MINUTE}/minute")
async def describe_data(
    request: Request,
    req: DescribeRequest,
    _: bool = Depends(verify_api_key)
):
    """Generate full dataset description."""
    try:
        data_path = req.path
        output_path = req.output_path or "output/describe.json"
        
        # Validate paths
        validate_path_traversal(data_path, base_dir="data")
        validate_path_traversal(os.path.dirname(output_path), base_dir="output")
        
        if not os.path.exists(data_path):
            raise HTTPException(status_code=404, detail="Data file not found")
        
        data = load_csv(data_path)
        processor = DataProcessor(data)
        description = processor.describe()
        
        save_json(description, output_path)
        
        return {
            "success": True,
            "description": description,
            "output_path": output_path,
            "file_hash": file_hash(output_path)
        }
    except Exception as e:
        logger.error(f"Error in describe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/upload")
@limiter.limit(f"{Config.RATE_LIMIT_PER_MINUTE}/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    _: bool = Depends(verify_api_key)
):
    """Upload and validate a CSV file."""
    try:
        from security import validate_file_extension, validate_file_size
        
        # Validate file extension
        validate_file_extension(file.filename)
        
        # Read file content to validate size
        content = await file.read()
        validate_file_size(len(content), max_size_mb=Config.MAX_FILE_SIZE_MB)
        
        # Save file to data directory
        save_path = os.path.join("data", validate_file_extension(file.filename))
        os.makedirs("data", exist_ok=True)
        
        with open(save_path, "wb") as f:
            f.write(content)
        
        # Verify file was saved correctly
        file_hash_value = file_hash(save_path)
        
        return {
            "success": True,
            "filename": file.filename,
            "saved_path": save_path,
            "size_bytes": len(content),
            "file_hash": file_hash_value
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/info")
@limiter.limit(f"{Config.RATE_LIMIT_PER_MINUTE}/minute")
async def get_info(
    request: Request,
    path: str,
    _: bool = Depends(verify_api_key)
):
    """Get file information."""
    try:
        data_path = validate_path_traversal(path, base_dir="data")
        
        if not os.path.exists(data_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        stat = os.stat(data_path)
        info = {
            "path": data_path,
            "size_bytes": stat.st_size,
            "modified_time": stat.st_mtime,
            "sha256": file_hash(data_path),
        }
        
        return {
            "success": True,
            "file_info": info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

