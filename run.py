from uvicorn import run
from config import PORT, RELOAD

if __name__ == "__main__":
    run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=RELOAD,
        workers=1
    )