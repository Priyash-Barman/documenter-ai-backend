from uvicorn import run
from config import PORT, RELOAD

if __name__ == "__main__":
    run(
        "main:app",
        host="127.0.0.1",
        port=PORT,
        reload=RELOAD,
        workers=1
    )