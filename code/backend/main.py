import os
import sys
from pathlib import Path

from app import create_app


BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


app = create_app()


def main():
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "5000"))
    debug = os.getenv("APP_DEBUG", "0") == "1"

    app.run(
        host=host,
        port=port,
        debug=debug,
    )


if __name__ == "__main__":
    main()