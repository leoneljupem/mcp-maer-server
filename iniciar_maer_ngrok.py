#!/usr/bin/env python3
"""
MAER 4.0 — Iniciador con túnel ngrok para acceso desde Chrome Extension y celular.

Uso:
  python iniciar_maer_ngrok.py

Para configurar ngrok con tu cuenta gratuita (opcional pero recomendado):
  1. Regístrate en https://ngrok.com (gratis)
  2. Copia tu authtoken del dashboard
  3. Crea un archivo .env en la carpeta raíz de MAER y agrega:
       NGROK_AUTHTOKEN=tu_token_aqui

Sin authtoken funciona con sesión temporal (60 min).
"""

import os
import sys
import time
import threading
import subprocess
from pathlib import Path

# ── Cargar .env ──
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

PORT = int(os.environ.get("MAER_WEB_PORT", "8765"))

def iniciar_servidor():
    """Inicia el servidor FastAPI en background."""
    server_script = Path(__file__).parent / "maer_backend" / "web_ui" / "server.py"
    subprocess.Popen(
        [sys.executable, str(server_script)],
        cwd=str(Path(__file__).parent)
    )
    time.sleep(3)
    print(f"✅ Servidor MAER iniciado en http://localhost:{PORT}")

def iniciar_ngrok():
    """Crea un túnel ngrok público hacia el servidor MAER."""
    try:
        from pyngrok import ngrok, conf

        # Configurar authtoken si existe
        authtoken = os.environ.get("NGROK_AUTHTOKEN", "")
        if authtoken:
            conf.get_default().auth_token = authtoken
            print(f"✅ ngrok configurado con authtoken")
        else:
            print("⚠️  Sin NGROK_AUTHTOKEN — usando sesión temporal (60 min)")
            print("   Para sesión ilimitada: regístrate en https://ngrok.com (gratis)")
            print("   y agrega NGROK_AUTHTOKEN=tu_token en el archivo .env")

        # Crear túnel
        tunnel = ngrok.connect(PORT, "http")
        url_publica = tunnel.public_url

        print("\n" + "═"*60)
        print(f"🦁 MAER accesible en:")
        print(f"\n   📱 URL pública (celular/Chrome): {url_publica}")
        print(f"   💻 Local (este equipo):          http://localhost:{PORT}")
        print("\n" + "═"*60)
        print("\n💡 Para Chrome Extension:")
        print(f"   Usa esta URL en lugar de localhost: {url_publica}")
        print("\n💡 Para instalar en celular (PWA):")
        print(f"   Abre {url_publica} en Chrome Mobile")
        print("   → Menú → Añadir a pantalla de inicio")
        print("\n⏳ Manteniendo túnel activo... (Ctrl+C para detener)\n")

        # Guardar URL en archivo para referencia
        url_file = Path(__file__).parent / ".maer_ngrok_url.txt"
        url_file.write_text(url_publica)

        return url_publica

    except ImportError:
        print("⚠️  pyngrok no instalado. Instala con: pip install pyngrok")
        print(f"   MAER disponible solo en: http://localhost:{PORT}")
        return None
    except Exception as e:
        print(f"⚠️  Error ngrok: {e}")
        print(f"   MAER disponible solo en: http://localhost:{PORT}")
        return None

def main():
    print("🦁 MAER 4.0 — Iniciando servidor + túnel ngrok...")
    print("─" * 60)

    # Iniciar servidor en thread separado
    t = threading.Thread(target=iniciar_servidor, daemon=True)
    t.start()

    # Crear túnel ngrok
    url = iniciar_ngrok()

    if url:
        try:
            # Mantener activo hasta Ctrl+C
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Deteniendo MAER y ngrok...")
            from pyngrok import ngrok
            ngrok.kill()
    else:
        print(f"\n✅ Servidor local activo en http://localhost:{PORT}")
        print("⏳ Ctrl+C para detener.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Deteniendo MAER...")

if __name__ == "__main__":
    main()
