"""
launcher.py — Entry point for the packaged .exe
Starts the Streamlit server and opens the browser automatically.
"""

import os
import sys
import threading
import webbrowser
import time
import socket


def _find_free_port(start=8501):
    """Find a free port starting from `start`."""
    for port in range(start, start + 20):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            continue
    return start


def _open_browser(port: int):
    """Wait for server to be ready, then open the browser."""
    for _ in range(30):
        time.sleep(0.5)
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                break
        except OSError:
            pass
    webbrowser.open(f"http://localhost:{port}")


if __name__ == "__main__":
    # When frozen by PyInstaller, resources live in sys._MEIPASS
    if getattr(sys, "frozen", False):
        bundle_dir = sys._MEIPASS
    else:
        bundle_dir = os.path.dirname(os.path.abspath(__file__))

    # Ensure bundled modules are importable
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)

    port = _find_free_port(8501)

    # Open browser once server is up
    t = threading.Thread(target=_open_browser, args=(port,), daemon=True)
    t.start()

    # Launch Streamlit
    from streamlit.web import cli as stcli

    app_path = os.path.join(bundle_dir, "app.py")

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",   # ✅ critical fix
    ]

    sys.exit(stcli.main())