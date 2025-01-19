import uvicorn
from pathlib import Path

ROOT_DIR = Path(__file__).parent

if __name__ == "__main__":
    uvicorn.run("src.server:app", host="0.0.0.0", port=9000, reload=True)
