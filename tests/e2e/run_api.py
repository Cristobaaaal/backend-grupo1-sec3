"""Arranca la app real en un puerto libre y termina cuando el padre cierra stdin."""

import json
import os
import socket
import sys
import threading
from pathlib import Path

import uvicorn


def main():
    estado = Path(sys.argv[1])
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(128)
        port = listener.getsockname()[1]
        os.environ["PASSWORD_RESET_URL"] = (
            f"http://127.0.0.1:{port}/auth/reset-password"
        )
        servidor = uvicorn.Server(
            uvicorn.Config(
                "app.main:app",
                host="127.0.0.1",
                port=port,
                access_log=False,
                log_level="warning",
                timeout_graceful_shutdown=5,
            )
        )

        def esperar_cierre_del_padre():
            sys.stdin.buffer.read()
            servidor.should_exit = True

        threading.Thread(target=esperar_cierre_del_padre, daemon=True).start()
        estado.write_text(
            json.dumps({"pid": os.getpid(), "port": port}), encoding="utf-8"
        )
        servidor.run(sockets=[listener])


if __name__ == "__main__":
    main()
