"""
Subconscious — Launcher

Tek komutla hem Web Dashboard hem CLI'yı başlatır.
Kullanım:
    python start.py          # Web dashboard (varsayılan)
    python start.py cli      # Sadece CLI
    python start.py all      # İkisi birden
"""
import sys
import os
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def start_web(port=3000, shared_engine=None):
    """Web dashboard'u başlat."""
    if shared_engine:
        import server
        server.set_engine(shared_engine)

    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False, log_level="info")


def start_cli(shared_engine=None):
    """CLI'yı başlat."""
    from cli import main
    main(engine=shared_engine)


def main():
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "web"

    if mode == "cli":
        print("🧠 CLI başlatılıyor...")
        start_cli()

    elif mode == "web":
        print(f"🌐 Web Dashboard → http://localhost:3000")
        start_web()

    elif mode == "all":
        # Tek bir engine oluştur, her ikisiyle paylaş
        from subconscious.engine import SubconsciousEngine
        shared = SubconsciousEngine()

        print(f"🌐 Web Dashboard → http://localhost:3000")
        print("🧠 CLI de başlatılıyor...")
        print()

        # Web'i arka planda başlat (aynı engine ile)
        web_thread = threading.Thread(target=start_web, args=(3000, shared), daemon=True)
        web_thread.start()
        time.sleep(2)  # Web'in açılmasını bekle

        # CLI'yı ön planda başlat (aynı engine ile)
        start_cli(shared_engine=shared)

    else:
        print("Kullanım:")
        print("  python start.py          # Web dashboard")
        print("  python start.py cli      # Sadece CLI")
        print("  python start.py all      # İkisi birden")


if __name__ == "__main__":
    main()
