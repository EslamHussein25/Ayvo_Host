#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import json
import os
import sys
from urllib.parse import urlparse

class PythonExecutorHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/run-python':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                script_name = data.get('script', '')
                
                if not os.path.exists(script_name):
                    self.send_error_response(f"Script {script_name} not found")
                    return
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                
                # Use virtual environment Python if available
                python_executable = self.get_python_executable()
                
                self.wfile.write(f"Using Python: {python_executable}\n".encode('utf-8'))
                self.wfile.flush()
                
                # Execute Python script
                process = subprocess.Popen(
                    [python_executable, script_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1,
                    cwd=os.getcwd(),
                    env=os.environ.copy()
                )
                
                for line in process.stdout:
                    if line.strip():
                        self.wfile.write(line.encode('utf-8'))
                        self.wfile.flush()
                
                return_code = process.wait()
                
                if return_code != 0:
                    error_msg = f"\nScript exited with code {return_code}\n"
                    self.wfile.write(error_msg.encode('utf-8'))
                    
            except Exception as e:
                self.send_error_response(f"Server error: {str(e)}")
    
    def get_python_executable(self):
        """Find the best Python executable to use"""
        
        # Option 1: Check for virtual environment in 'env' folder
        env_paths = [
            os.path.join(os.getcwd(), 'env', 'Scripts', 'python.exe'),  # Windows
            os.path.join(os.getcwd(), 'env', 'bin', 'python'),         # Linux/Mac
            os.path.join(os.getcwd(), 'venv', 'Scripts', 'python.exe'), # Windows venv
            os.path.join(os.getcwd(), 'venv', 'bin', 'python'),        # Linux/Mac venv
        ]
        
        for path in env_paths:
            if os.path.exists(path):
                return path
        
        # Option 2: Check if we're already in a virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            return sys.executable
        
        # Option 3: Use system Python
        return sys.executable
    
    def send_error_response(self, message):
        self.send_response(500)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))
    
    def log_message(self, format, *args):
        pass

def main():
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, PythonExecutorHandler)
    
    print("🐍 Python Execution Server with Environment Support")
    print("=" * 60)
    print(f"Server running on http://localhost:8000")
    print(f"Working directory: {os.getcwd()}")
    
    # Check for virtual environment
    env_paths = [
        os.path.join(os.getcwd(), 'env', 'Scripts', 'python.exe'),
        os.path.join(os.getcwd(), 'env', 'bin', 'python'),
        os.path.join(os.getcwd(), 'venv', 'Scripts', 'python.exe'),
        os.path.join(os.getcwd(), 'venv', 'bin', 'python'),
    ]
    
    env_found = False
    for path in env_paths:
        if os.path.exists(path):
            print(f"✅ Virtual environment found: {path}")
            env_found = True
            break
    
    if not env_found:
        print("⚠️  No virtual environment found. Using system Python.")
        print("💡 To use virtual environment, create 'env' or 'venv' folder")
    
    print("Ready to execute Python scripts...")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        httpd.server_close()

if __name__ == '__main__':
    main()
