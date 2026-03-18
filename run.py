"""
Laplacian AI - Entry Point
Run this file to start the application server.
"""
import os
from app import create_app

# Determine environment
env = os.getenv('APP_ENV', 'development')

# Create application
app = create_app(env)

if __name__ == '__main__':
    import uvicorn

    debug = os.getenv('APP_DEBUG', 'True') == 'True'
    host = os.getenv('APP_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT', 5000))

    import socket

    # Get local/private IP
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    local_ip = get_local_ip()

    print("=" * 50)
    print("Laplacian AI Code Assistant by Perfionix AI")
    print("=" * 50)
    print(f"  Local:   http://localhost:{port}")
    print(f"  Network: http://{local_ip}:{port}")
    print("=" * 50)

    uvicorn.run("run:app", host=host, port=port, reload=debug)
