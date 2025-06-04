from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from middlewares.exception_handler import ExceptionHandlerMiddleware
from routes import register_routes

app = FastAPI(title="Documentor AI APIs")

# Global Exception Handler Middleware
app.add_middleware(ExceptionHandlerMiddleware)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Register all routes
register_routes(app)