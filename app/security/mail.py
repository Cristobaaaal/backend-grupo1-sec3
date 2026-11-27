import os
import smtplib
from email.message import EmailMessage
from urllib.parse import quote


def enviar_recuperacion(destinatario: str, token: str) -> None:
    base = os.getenv("PASSWORD_RESET_URL", "http://127.0.0.1:8000/auth/reset-password")
    # El fragmento no viaja al servidor ni aparece en sus logs de acceso.
    enlace = f"{base}#token={quote(token, safe='')}"
    mensaje = EmailMessage()
    mensaje["Subject"] = "Recuperación de contraseña"
    mensaje["From"] = os.getenv("SMTP_FROM", "no-reply@pokemon.local")
    mensaje["To"] = destinatario
    mensaje.set_content(
        "Solicitaste cambiar tu contraseña. Abre este enlace de un solo uso:\n"
        f"{enlace}\n\nSi no lo solicitaste, ignora este mensaje."
    )
    with smtplib.SMTP(
        os.getenv("SMTP_HOST", "127.0.0.1"),
        int(os.getenv("SMTP_PORT", "1025")),
        timeout=10,
    ) as smtp:
        if os.getenv("SMTP_STARTTLS", "false").lower() == "true":
            smtp.starttls()
        usuario = os.getenv("SMTP_USER")
        if usuario:
            smtp.login(usuario, os.environ["SMTP_PASSWORD"])
        smtp.send_message(mensaje)
