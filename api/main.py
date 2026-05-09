"""Application entry point — run with ``python main.py`` or ``uvicorn main:app``."""

import os
import uvicorn
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
