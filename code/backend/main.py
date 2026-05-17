import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
	sys.path.insert(0, str(BASE_DIR))

from app import create_app


app = create_app()


if __name__ == "__main__":
	host = os.getenv("APP_HOST", "0.0.0.0")
	port = int(os.getenv("APP_PORT", "5000"))
	debug = os.getenv("APP_DEBUG", "0") == "1"
	app.run(host=host, port=port, debug=debug)