import subprocess
import sys
import signal
import time
import os
import shutil

def kill_port(port):
    try:
        output = subprocess.check_output(["lsof", "-t", f"-i:{port}"]).decode().strip()
        if output:
            for pid in output.split('\n'):
                if pid:
                    subprocess.call(["kill", "-9", pid])
                    print(f"[!] Killed existing process on port {port} (PID: {pid})")
    except subprocess.CalledProcessError:
        pass
    except Exception as e:
        print(f"[-] Could not check port {port}: {e}")

def run_backend():
    print("[+] Starting Subconscious Backend...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    python_bin = os.path.join(base_dir, ".venv", "bin", "python")
    if not os.path.exists(python_bin):
        python_bin = "python3" # Fallback
    server_script = os.path.join(base_dir, "backend", "server.py")
    return subprocess.Popen([python_bin, server_script], cwd=base_dir)

def run_frontend():
    print("[+] Starting Subconscious Frontend (Next.js)...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(base_dir, "frontend")
    
    # Clear Next.js cache to avoid ENOENT errors
    next_cache = os.path.join(frontend_dir, ".next")
    if os.path.exists(next_cache):
        try:
            shutil.rmtree(next_cache)
            print("[+] Cleared .next cache")
        except Exception:
            pass

    env = os.environ.copy()
    env["PORT"] = "3000"
    return subprocess.Popen(["npm", "run", "dev"], cwd=frontend_dir, env=env)

if __name__ == "__main__":
    print("=========================================")
    print("🧠 Subconscious AI - Fullstack Process")
    print("=========================================\n")
    
    kill_port(8000)
    kill_port(3000)

    backend_proc = run_backend()
    time.sleep(1) # Give backend a second to initialize
    frontend_proc = run_frontend()

    print("\n[+] Applications are starting:")
    print("    Backend API & WebSocket -> http://localhost:8000")
    print("    Frontend UI             -> http://localhost:3000")
    print("    Press Ctrl+C to stop both servers at any time.\n")

    def signal_handler(sig, frame):
        print("\n\n[!] Shutting down processes...")
        try:
            backend_proc.terminate()
            frontend_proc.terminate()
            backend_proc.wait(timeout=3)
            frontend_proc.wait(timeout=3)
        except Exception:
            pass
        kill_port(8000)
        kill_port(3000)
        print("[!] Shutdown complete.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
