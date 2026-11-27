"""Configuración SMTP y transporte seguro del enlace, sin conexión de red."""

import smtplib
from unittest.mock import call, create_autospec
from urllib.parse import parse_qs, urlsplit

import pytest

from app.security import mail

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("tls", [False, True], ids=["sin-tls", "con-tls"])
@pytest.mark.parametrize("autenticado", [False, True], ids=["anonimo", "autenticado"])
def test_correo_respeta_configuracion_y_conserva_token_en_fragmento(
    monkeypatch, tls, autenticado
):
    """TLS precede al login y el token con caracteres reservados llega intacto."""
    fabrica = create_autospec(smtplib.SMTP, spec_set=True)
    smtp = fabrica.return_value
    smtp.__enter__.return_value = smtp
    monkeypatch.setattr(mail.smtplib, "SMTP", fabrica)
    configuracion = {
        "PASSWORD_RESET_URL": "https://pruebas.example/auth/reset-password",
        "SMTP_HOST": "smtp.example",
        "SMTP_PORT": "2525",
        "SMTP_FROM": "no-reply@example.com",
        "SMTP_STARTTLS": str(tls).lower(),
        "SMTP_USER": "usuario-prueba" if autenticado else "",
        "SMTP_PASSWORD": "clave-ficticia",
    }
    for nombre, valor in configuracion.items():
        monkeypatch.setenv(nombre, valor)
    token = "token+con/barra?y=parametro&otro=#fragmento"

    mail.enviar_recuperacion("ash@example.com", token)

    fabrica.assert_called_once_with("smtp.example", 2525, timeout=10)
    assert smtp.starttls.call_count == int(tls)
    if autenticado:
        smtp.login.assert_called_once_with("usuario-prueba", "clave-ficticia")
    else:
        smtp.login.assert_not_called()
    smtp.send_message.assert_called_once()
    mensaje = smtp.send_message.call_args.args[0]
    assert mensaje["To"] == "ash@example.com"
    assert mensaje["From"] == "no-reply@example.com"
    assert mensaje["Subject"] == "Recuperación de contraseña"
    enlace = next(
        linea
        for linea in mensaje.get_content().splitlines()
        if linea.startswith("https://")
    )
    url = urlsplit(enlace)
    assert url.path == "/auth/reset-password"
    assert url.query == ""
    assert parse_qs(url.fragment) == {"token": [token]}
    esperadas = ([call.starttls()] if tls else []) + (
        [call.login("usuario-prueba", "clave-ficticia")] if autenticado else []
    )
    assert smtp.method_calls == [*esperadas, call.send_message(mensaje)]
    smtp.__exit__.assert_called_once_with(None, None, None)
