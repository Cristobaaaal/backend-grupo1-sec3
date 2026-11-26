"""Capturador SMTP local reutilizable, basado en el incorporado por Simón."""

import re
import socketserver
import threading
from contextlib import contextmanager
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
from urllib.parse import parse_qs, urlsplit


class SMTPHandler(socketserver.StreamRequestHandler):
    """Recibe mensajes por TCP/SMTP y los conserva sin reenviarlos."""

    def handle(self):
        self.request.settimeout(10)
        self.wfile.write(b"220 localhost test SMTP\r\n")
        while line := self.rfile.readline():
            comando = line.upper()
            if comando.startswith((b"EHLO", b"HELO")):
                self.wfile.write(b"250 localhost\r\n")
            elif comando.startswith(b"DATA"):
                self.wfile.write(b"354 Send data\r\n")
                partes = []
                while (linea := self.rfile.readline()) not in (b".\r\n", b""):
                    partes.append(linea[1:] if linea.startswith(b"..") else linea)
                self.server.mensajes.append(b"".join(partes))
                self.wfile.write(b"250 Accepted\r\n")
            elif comando.startswith(b"QUIT"):
                self.wfile.write(b"221 Bye\r\n")
                return
            else:
                self.wfile.write(b"250 OK\r\n")


@contextmanager
def smtp_capture():
    """Abre un puerto local libre y garantiza el cierre de servidor e hilo."""
    with socketserver.ThreadingTCPServer(("127.0.0.1", 0), SMTPHandler) as server:
        server.daemon_threads = True
        server.mensajes = []
        thread = threading.Thread(
            target=lambda: server.serve_forever(poll_interval=0.05), daemon=True
        )
        thread.start()
        try:
            yield server
        finally:
            server.shutdown()
            thread.join(timeout=5)
            if thread.is_alive():
                raise RuntimeError("El capturador SMTP no terminó correctamente.")


def enlace_del_correo(server, destinatario):
    """Obtiene el enlace del mensaje realmente recibido por el destinatario."""
    for raw in reversed(server.mensajes):
        mensaje = BytesParser(policy=policy.default).parsebytes(raw)
        destinos = {
            email.lower() for _, email in getaddresses(mensaje.get_all("To", []))
        }
        if destinatario.lower() not in destinos:
            continue
        cuerpo = mensaje.get_body(preferencelist=("plain",))
        assert cuerpo is not None, "El correo de recuperación no contiene texto."
        enlace = re.search(r"https?://[^\s]+", cuerpo.get_content())
        assert enlace is not None, "El correo no contiene un enlace de recuperación."
        return enlace.group(0)
    raise AssertionError("No llegó un correo al destinatario de prueba.")


def token_del_correo(server, destinatario):
    """Extrae un único JWT del fragmento del enlace recibido, nunca de la query."""
    url = urlsplit(enlace_del_correo(server, destinatario))
    assert "token" not in parse_qs(url.query)
    tokens = parse_qs(url.fragment).get("token", [])
    assert len(tokens) == 1, "El enlace no contiene un único token."
    return tokens[0]
