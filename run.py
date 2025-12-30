"""
Laplacian AI - Entry Point
Run this file to start the application server.
"""
import os
from app import create_app

# Determine environment
env = os.getenv('FLASK_ENV', 'development')

# Create application
app = create_app(env)

if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'True') == 'True'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))

    print("=" * 50)
    print("Laplacian AI Code Assistant by Perfionix AI")
    print("=" * 50)
    print(f"Open http://localhost:{port} in your browser")
    print("=" * 50)

    app.run(debug=debug, host=host, port=port)
