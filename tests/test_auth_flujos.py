"""Flujos de seguridad sobre SQLite aislado y SMTP local de prueba."""
import os
import re
import socketserver
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email import policy
from email.parser import BytesParser
from pathlib import Path
from unittest.mock import patch

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from app.infrastructure.database import Base, get_db
from app.infrastructure.models import RefreshTokenORM, UsuarioORM, PasswordResetTokenORM
from app.main import app
from app.security.tokens import crear_reset_token


class SMTPHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.wfile.write(b'220 localhost test SMTP\r\n')
        while line := self.rfile.readline():
            comando = line.upper()
            if comando.startswith((b'EHLO', b'HELO')):
                self.wfile.write(b'250 localhost\r\n')
            elif comando.startswith(b'DATA'):
                self.wfile.write(b'354 Send data\r\n')
                partes = []
                while (linea := self.rfile.readline()) not in (b'.\r\n', b''):
                    partes.append(linea[1:] if linea.startswith(b'..') else linea)
                self.server.mensajes.append(b''.join(partes))
                self.wfile.write(b'250 Accepted\r\n')
            elif comando.startswith(b'QUIT'):
                self.wfile.write(b'221 Bye\r\n')
                return
            else:
                self.wfile.write(b'250 OK\r\n')


class AuthFlujosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.smtp = socketserver.ThreadingTCPServer(('127.0.0.1', 0), SMTPHandler)
        cls.smtp.mensajes = []
        cls.hilo = threading.Thread(target=cls.smtp.serve_forever, daemon=True)
        cls.hilo.start()

    @classmethod
    def tearDownClass(cls):
        cls.smtp.shutdown()
        cls.smtp.server_close()
        cls.hilo.join()

    def setUp(self):
        self.entorno = patch.dict(os.environ, {
            'DATABASE_URL': 'sqlite://',
            'JWT_SECRET': 'clave-exclusiva-pruebas-de-autenticacion-0123456789',
            'JWT_ALGORITHM': 'HS256', 'ACCESS_TOKEN_EXPIRE_SECONDS': '30',
            'PASSWORD_RESET_EXPIRE_SECONDS': '900',
            'PASSWORD_RESET_URL': 'http://testserver/auth/reset-password',
            'SMTP_HOST': '127.0.0.1', 'SMTP_PORT': str(self.smtp.server_address[1]),
            'SMTP_USER': '', 'SMTP_PASSWORD': '', 'SMTP_STARTTLS': 'false',
        })
        self.entorno.start()
        self.addCleanup(self.entorno.stop)
        self.directorio = tempfile.TemporaryDirectory()
        self.motor = create_engine(f"sqlite:///{Path(self.directorio.name) / 'auth.db'}",
                                   connect_args={'check_same_thread': False, 'timeout': 15})
        @event.listens_for(self.motor, 'connect')
        def claves(conn, record):
            conn.execute('PRAGMA foreign_keys=ON')
        Base.metadata.create_all(self.motor)
        def sesion():
            with Session(self.motor) as db:
                yield db
        app.dependency_overrides[get_db] = sesion
        self.cliente = TestClient(app)
        self.smtp.mensajes.clear()
        self.email = 'simon@example.com'
        self.password = 'ClaveDePrueba123!'
        r = self.cliente.post('/auth/register', json={
            'email': self.email, 'password': self.password, 'nombre_completo': 'Simon',
        })
        self.assertEqual(r.status_code, 201, r.text)
        self.uid = r.json()['id']

    def tearDown(self):
        self.cliente.close()
        app.dependency_overrides.clear()
        self.motor.dispose()
        self.directorio.cleanup()

    def login(self, password=None):
        r = self.cliente.post('/auth/login', json={
            'email': self.email, 'password': password or self.password,
        })
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def me(self, token):
        return self.cliente.get('/auth/me', headers={'Authorization': f'Bearer {token}'})

    def refresh(self, token):
        return self.cliente.post('/auth/refresh', json={'refresh_token': token})

    def solicitar(self, email=None):
        return self.cliente.post('/auth/forgot-password', json={'email': email or self.email})

    def reset_token(self):
        self.assertEqual(self.solicitar().status_code, 202)
        mensaje = BytesParser(policy=policy.default).parsebytes(self.smtp.mensajes[-1])
        cuerpo = mensaje.get_body(preferencelist=('plain',)).get_content()
        return re.search(r'#token=([A-Za-z0-9_.-]+)', cuerpo).group(1)

    def reset(self, token, password='NuevaClaveSegura123!'):
        return self.cliente.post('/auth/reset-password', json={'token': token, 'password': password})

    def test_access_dura_30_segundos_y_expirado_se_rechaza(self):
        tokens = self.login()
        claims = jwt.decode(tokens['access_token'], os.environ['JWT_SECRET'], algorithms=['HS256'])
        self.assertEqual(claims['exp'] - claims['iat'], 30)
        self.assertEqual(self.me(tokens['access_token']).status_code, 200)
        claims['exp'] = int(datetime.now(timezone.utc).timestamp()) - 1
        expirado = jwt.encode(claims, os.environ['JWT_SECRET'], algorithm='HS256')
        self.assertEqual(self.me(expirado).status_code, 401)

    def test_e2e_refresh_rota_y_reutilizacion_revoca_solo_su_familia(self):
        primero = self.login()
        otra_sesion = self.login()
        r = self.refresh(primero['refresh_token'])
        self.assertEqual(r.status_code, 200, r.text)
        nuevo = r.json()
        self.assertNotEqual(nuevo['refresh_token'], primero['refresh_token'])
        self.assertEqual(self.me(nuevo['access_token']).status_code, 200)
        self.assertEqual(self.refresh(primero['refresh_token']).status_code, 401)
        self.assertEqual(self.refresh(nuevo['refresh_token']).status_code, 401)
        self.assertEqual(self.me(nuevo['access_token']).status_code, 401)
        self.assertEqual(self.me(otra_sesion['access_token']).status_code, 200)
        self.assertEqual(self.refresh(otra_sesion['refresh_token']).status_code, 200)

    def test_e2e_logout_revoca_access_y_refresh(self):
        t = self.login()
        for _ in range(2):
            r = self.cliente.post('/auth/logout', json={'refresh_token': t['refresh_token']})
            self.assertEqual(r.status_code, 204)
            self.assertEqual(r.content, b'')
        self.assertEqual(self.me(t['access_token']).status_code, 401)
        self.assertEqual(self.refresh(t['refresh_token']).status_code, 401)

    def test_refresh_caducado_y_desconocido(self):
        t = self.login()
        with Session(self.motor) as db:
            registro = db.scalar(select(RefreshTokenORM))
            registro.expira_en = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
            db.commit()
        self.assertEqual(self.refresh(t['refresh_token']).status_code, 401)
        self.assertEqual(self.refresh('inventado').status_code, 401)

    def test_e2e_correo_cambio_password_e_invalidacion_total(self):
        t1 = self.login()
        t2 = self.login()
        token = self.reset_token()
        claims = jwt.decode(token, os.environ['JWT_SECRET'], algorithms=['HS256'])
        self.assertEqual(claims['type'], 'password_reset')
        self.assertEqual(self.me(token).status_code, 401)
        self.assertEqual(self.cliente.get('/auth/reset-password').status_code, 200)
        r = self.reset(token)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.reset(token).status_code, 401)
        for t in (t1, t2):
            self.assertEqual(self.me(t['access_token']).status_code, 401)
            self.assertEqual(self.refresh(t['refresh_token']).status_code, 401)
        r = self.cliente.post('/auth/login', json={'email': self.email, 'password': self.password})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(self.me(self.login('NuevaClaveSegura123!')['access_token']).status_code, 200)
        with Session(self.motor) as db:
            usuario = db.get(UsuarioORM, self.uid)
            self.assertTrue(usuario.password_hash.startswith('$argon2id$'))
            self.assertEqual(usuario.token_version, 1)

    def test_reset_rechaza_firma_proposito_caducidad_y_password_corta(self):
        t = self.login()
        self.assertEqual(self.reset(t['access_token']).status_code, 401)
        token = self.reset_token()
        partes = token.split('.')
        partes[2] = ('A' if partes[2][0] != 'A' else 'B') + partes[2][1:]
        self.assertEqual(self.reset('.'.join(partes)).status_code, 401)
        claims = jwt.decode(token, os.environ['JWT_SECRET'], algorithms=['HS256'])
        claims['exp'] = int(datetime.now(timezone.utc).timestamp()) - 1
        vencido = jwt.encode(claims, os.environ['JWT_SECRET'], algorithm='HS256')
        self.assertEqual(self.reset(vencido).status_code, 401)
        self.assertEqual(self.reset(token, 'corta').status_code, 422)
        self.assertEqual(self.reset(token).status_code, 200)

    def test_reset_nuevo_invalida_anterior_y_otra_version(self):
        anterior = self.reset_token()
        nuevo = self.reset_token()
        self.assertEqual(self.reset(anterior).status_code, 401)
        self.assertEqual(self.reset(nuevo).status_code, 200)
        self.assertEqual(self.reset(anterior).status_code, 401)
        # Incluso un JWT firmado de la versión anterior queda invalidado.
        from uuid import UUID
        viejo = crear_reset_token(UUID(self.uid), 0)
        self.assertEqual(self.reset(viejo).status_code, 401)

    def test_solicitud_generica_limita_y_no_revela_cuenta(self):
        desconocido = self.solicitar('nadie@example.com')
        esperado = desconocido.json()
        self.assertEqual(desconocido.status_code, 202)
        self.assertEqual(len(self.smtp.mensajes), 0)
        for _ in range(5):
            r = self.solicitar()
            self.assertEqual(r.status_code, 202)
            self.assertEqual(r.json(), esperado)
        self.assertEqual(len(self.smtp.mensajes), 3)

    def test_reset_limita_intentos_de_confirmacion(self):
        for _ in range(20):
            self.assertEqual(self.reset('inventado').status_code, 401)
        self.assertEqual(self.reset('inventado').status_code, 429)

    def test_rotacion_simultanea_no_entrega_dos_sesiones(self):
        t = self.login()
        with ThreadPoolExecutor(max_workers=2) as pool:
            respuestas = list(pool.map(lambda _: self.refresh(t['refresh_token']), range(2)))
        self.assertEqual(sorted(r.status_code for r in respuestas), [200, 401])
        exitoso = next(r for r in respuestas if r.status_code == 200).json()
        self.assertEqual(self.me(exitoso['access_token']).status_code, 401)

    def test_reset_simultaneo_solo_se_consume_una_vez(self):
        token = self.reset_token()
        with ThreadPoolExecutor(max_workers=2) as pool:
            respuestas = list(pool.map(lambda _: self.reset(token), range(2)))
        self.assertEqual(sorted(r.status_code for r in respuestas), [200, 401])


if __name__ == '__main__':
    unittest.main()
