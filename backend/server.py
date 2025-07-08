import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI, APIRouter, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from dotenv import load_dotenv
import os
import structlog
from contextlib import asynccontextmanager
from database.connection import close_db_connections
from api.auth import router as auth_router
from api.companies import router as companies_router
from api.accounts import router as accounts_router
from api.customers import router as customers_router
from api.vendors import router as vendors_router
from api.items import router as items_router
from api.employees import router as employees_router
from api.transactions import router as transactions_router
from api.invoices import router as invoices_router
from api.bills import router as bills_router
from api.payments import router as payments_router
from api.reports import router as reports_router
from api.banking import router as banking_router
from api.bank_rules import router as bank_rules_router
from api.bank_reconciliation import router as bank_reconciliation_router
from api.payroll import router as payroll_router
from api.inventory import router as inventory_router
from api.inventory_adjustments import router as inventory_adjustments_router
from api.purchase_orders import router as purchase_orders_router
from api.inventory_receipts import router as inventory_receipts_router
from api.inventory_locations import router as inventory_locations_router
from api.inventory_assemblies import router as inventory_assemblies_router
from api.inventory_reorder import router as inventory_reorder_router
from api.notifications import router as notifications_router
from api.email_management import router as email_management_router
from api.webhooks import router as webhooks_router
from api.sms_management import router as sms_management_router
from api.notification_preferences import router as notification_preferences_router
from api.audit import router as audit_router
from api.security import router as security_router
import uuid
from datetime import datetime

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    logger.info("Starting QuickBooks Clone API")
    yield
    logger.info("Shutting down QuickBooks Clone API")
    await close_db_connections()

# Create FastAPI app
app = FastAPI(
    title="QuickBooks Clone API",
    description="Comprehensive accounting and business management API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure properly in production
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API router
api_router = APIRouter(prefix="/api")

# Basic health check endpoint
@api_router.get("/health")
@limiter.limit("30/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Root endpoint
@api_router.get("/")
@limiter.limit("30/minute")
async def root(request: Request):
    """Root API endpoint"""
    return {
        "message": "QuickBooks Clone API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }

# Include authentication routes
api_router.include_router(auth_router)

# Include company management routes
api_router.include_router(companies_router)

# Include list management routes
api_router.include_router(accounts_router)
api_router.include_router(customers_router)
api_router.include_router(vendors_router)
api_router.include_router(items_router)
api_router.include_router(employees_router)

# Include transaction management routes
api_router.include_router(transactions_router)
api_router.include_router(invoices_router)
api_router.include_router(bills_router)
api_router.include_router(payments_router)

# Include reporting routes
api_router.include_router(reports_router)

# Include banking routes
api_router.include_router(banking_router)
api_router.include_router(bank_rules_router)
api_router.include_router(bank_reconciliation_router)

# Include payroll routes
api_router.include_router(payroll_router)

# Include inventory management routes
api_router.include_router(inventory_router)
api_router.include_router(inventory_adjustments_router)
api_router.include_router(purchase_orders_router)
api_router.include_router(inventory_receipts_router)
api_router.include_router(inventory_locations_router)
api_router.include_router(inventory_assemblies_router)
api_router.include_router(inventory_reorder_router)

# Include notification & communication routes
api_router.include_router(notifications_router)
api_router.include_router(email_management_router)
api_router.include_router(webhooks_router)
api_router.include_router(sms_management_router)
api_router.include_router(notification_preferences_router)

# Include the API router in the main app
app.include_router(api_router)

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler"""
    logger.error(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": request.url.path
        }
    )

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = datetime.utcnow()
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    
    response = await call_next(request)
    
    # Calculate processing time
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    # Log response
    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=process_time
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8001,
        reload=True if os.getenv("DEBUG") == "true" else False,
        log_level="info"
    )
