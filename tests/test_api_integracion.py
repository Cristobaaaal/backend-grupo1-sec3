"""Casos reproducibles del contrato HTTP y la persistencia de la API."""

import tempfile
import unittest
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.infrastructure.database import Base, get_db
from app.main import app


ID_INEXISTENTE = "00000000-0000-0000-0000-000000000000"


class APIIntegracionTests(unittest.TestCase):
    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()
        self.url = f"sqlite:///{Path(self.directorio.name) / 'pruebas.db'}"
        self._abrir_motor()
        Base.metadata.create_all(self.motor)
        app.dependency_overrides[get_db] = self._sesion
        self.cliente = TestClient(app)

    def tearDown(self):
        self.cliente.close()
        app.dependency_overrides.clear()
        self.motor.dispose()
        self.directorio.cleanup()

    def _abrir_motor(self):
        self.motor = create_engine(
            self.url, connect_args={"check_same_thread": False}
        )

    def _sesion(self):
        with Session(self.motor) as db:
            yield db

    def _crear_entrenador(self, nombre="Ash"):
        respuesta = self.cliente.post("/entrenadores/", json={
            "nombre": nombre,
            "nivel_experiencia": 10,
            "region_origen": "Kanto",
            "medallas_obtenidas": 3,
        })
        self.assertEqual(respuesta.status_code, 201, respuesta.text)
        return respuesta.json()

    def _crear_pokemon(self, nombre="Pikachu", tipo="ELECTRICO", nivel=10, entrenador_id=None):
        respuesta = self.cliente.post("/pokemones/", json={
            "nombre": nombre,
            "tipo_principal": tipo,
            "nivel": nivel,
            "puntos_vida": 40,
            "entrenador_id": entrenador_id,
        })
        self.assertEqual(respuesta.status_code, 201, respuesta.text)
        return respuesta.json()

    def test_crud_entrenador(self):
        self.assertEqual(self.cliente.get("/").status_code, 200)
        entrenador = self._crear_entrenador()
        ruta = f"/entrenadores/{entrenador['id']}"
        self.assertEqual(self.cliente.get(ruta).json()["nombre"], "Ash")

        actualizado = self.cliente.put(ruta, json={
            "nombre": "Ash Ketchum",
            "nivel_experiencia": 15,
            "region_origen": "Kanto",
            "medallas_obtenidas": 4,
        })
        self.assertEqual(actualizado.status_code, 200, actualizado.text)
        self.assertEqual(actualizado.json()["nombre"], "Ash Ketchum")
        self.assertEqual(len(self.cliente.get("/entrenadores/").json()), 1)
        self.assertEqual(self.cliente.delete(ruta).status_code, 204)
        self.assertEqual(self.cliente.get(ruta).status_code, 404)

    def test_datos_invalidos_devuelven_422_uniforme(self):
        respuesta = self.cliente.post("/pokemones/", json={
            "nombre": "",
            "tipo_principal": "FUEGO",
            "nivel": 999,
            "puntos_vida": 40,
        })
        self.assertEqual(respuesta.status_code, 422)
        self.assertEqual(respuesta.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertTrue(respuesta.json()["error"]["details"])

    def test_recurso_inexistente_devuelve_404_uniforme(self):
        respuesta = self.cliente.get(f"/entrenadores/{ID_INEXISTENTE}")
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.json()["error"]["code"], "RESOURCE_NOT_FOUND")

    def test_regla_de_negocio_devuelve_400(self):
        entrenador = self._crear_entrenador()
        pokemon = self._crear_pokemon(entrenador_id=entrenador["id"])
        respuesta = self.cliente.patch(
            f"/pokemones/{pokemon['id']}/asignar/{entrenador['id']}"
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"]["code"], "BUSINESS_RULE_VIOLATION")

    def test_borrado_con_relacion_devuelve_409(self):
        entrenador = self._crear_entrenador()
        self._crear_pokemon(entrenador_id=entrenador["id"])
        respuesta = self.cliente.delete(f"/entrenadores/{entrenador['id']}")
        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(respuesta.json()["error"]["code"], "RESOURCE_CONFLICT")

    def test_filtro_orden_y_paginacion_sobre_datos_guardados(self):
        self._crear_pokemon(nombre="Pikachu", nivel=10)
        self._crear_pokemon(nombre="Raichu", nivel=35)
        self._crear_pokemon(nombre="Charmander", tipo="FUEGO", nivel=50)
        respuesta = self.cliente.get(
            "/pokemones/?tipo=ELECTRICO&ordenar_por=nivel&direccion=desc&pagina=1&limite=1"
        )
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        datos = respuesta.json()
        self.assertEqual([p["nombre"] for p in datos["items"]], ["Raichu"])
        self.assertEqual(datos["total"], 2)
        self.assertEqual(datos["total_paginas"], 2)
        self.assertEqual(datos["pagina"], 1)
        self.assertEqual(datos["limite"], 1)

    def test_datos_persisten_tras_reabrir_conexion(self):
        entrenador = self._crear_entrenador()
        self.motor.dispose()
        self._abrir_motor()
        respuesta = self.cliente.get(f"/entrenadores/{entrenador['id']}")
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        self.assertEqual(respuesta.json()["nombre"], entrenador["nombre"])

    def test_asignar_transferir_liberar_y_actualizar_pokemon(self):
        primero = self._crear_entrenador("Ash")
        segundo = self._crear_entrenador("Misty")
        pokemon = self._crear_pokemon()
        ruta = f"/pokemones/{pokemon['id']}"
        self.assertEqual(self.cliente.get(ruta).status_code, 200)
        self.assertEqual(len(self.cliente.get("/pokemones/sin-entrenador").json()), 1)
        self.assertEqual(len(self.cliente.get("/pokemones/tipo/ELECTRICO").json()), 1)

        asignado = self.cliente.patch(f"{ruta}/asignar/{primero['id']}")
        self.assertEqual(asignado.status_code, 200, asignado.text)
        self.assertEqual(asignado.json()["entrenador_id"], primero["id"])
        self.assertEqual(len(self.cliente.get(f"/pokemones/entrenador/{primero['id']}").json()), 1)

        transferido = self.cliente.patch(f"{ruta}/transferir/{segundo['id']}")
        self.assertEqual(transferido.status_code, 200, transferido.text)
        self.assertEqual(transferido.json()["entrenador_id"], segundo["id"])
        estadisticas = self.cliente.patch(f"{ruta}/stats?nivel=25&puntos_vida=90")
        self.assertEqual(estadisticas.status_code, 200, estadisticas.text)
        self.assertEqual(estadisticas.json()["nivel"], 25)

        actualizado = self.cliente.put(ruta, json={
            "nombre": "Raichu",
            "tipo_principal": "ELECTRICO",
            "nivel": 35,
            "puntos_vida": 95,
            "entrenador_id": segundo["id"],
        })
        self.assertEqual(actualizado.status_code, 200, actualizado.text)
        self.assertEqual(actualizado.json()["nombre"], "Raichu")
        self.assertIsNone(self.cliente.patch(f"{ruta}/liberar").json()["entrenador_id"])
        self.assertEqual(self.cliente.delete(ruta).status_code, 204)
        self.assertEqual(self.cliente.get(ruta).status_code, 404)

    def test_centros_y_registros_crud_con_reglas_de_borrado(self):
        centro = self.cliente.post("/centros-pokemon/", json={
            "nombre": "Centro Norte",
            "ciudad": "Temuco",
            "capacidad_maxima": 10,
            "en_servicio": True,
        })
        self.assertEqual(centro.status_code, 201, centro.text)
        centro_id = centro.json()["id"]
        ruta_centro = f"/centros-pokemon/{centro_id}"
        self.assertEqual(self.cliente.get(ruta_centro).status_code, 200)
        self.assertEqual(len(self.cliente.get("/centros-pokemon/").json()), 1)
        self.assertEqual(len(self.cliente.get("/centros-pokemon/ciudad/temuco").json()), 1)
        actualizado = self.cliente.put(ruta_centro, json={
            "nombre": "Centro Norte",
            "ciudad": "Temuco",
            "capacidad_maxima": 15,
            "en_servicio": True,
        })
        self.assertEqual(actualizado.status_code, 200, actualizado.text)
        self.assertEqual(actualizado.json()["capacidad_maxima"], 15)

        pokemon = self._crear_pokemon()
        datos = {
            "pokemon_id": pokemon["id"],
            "centro_id": centro_id,
            "diagnostico": "Agotamiento",
            "fecha_ingreso": date.today().isoformat(),
            "estado": "EN_TRATAMIENTO",
            "costo": 5000,
        }
        registro = self.cliente.post("/registros-medicos/", json=datos)
        self.assertEqual(registro.status_code, 201, registro.text)
        ruta_registro = f"/registros-medicos/{registro.json()['id']}"
        self.assertEqual(self.cliente.get(ruta_registro).status_code, 200)
        self.assertEqual(len(self.cliente.get("/registros-medicos/").json()), 1)
        self.assertEqual(self.cliente.delete(ruta_centro).status_code, 400)

        datos["estado"] = "DADO_DE_ALTA"
        actualizado = self.cliente.put(ruta_registro, json=datos)
        self.assertEqual(actualizado.status_code, 200, actualizado.text)
        self.assertEqual(self.cliente.delete(ruta_centro).status_code, 409)
        self.assertEqual(self.cliente.delete(ruta_registro).status_code, 204)
        self.assertEqual(self.cliente.delete(ruta_centro).status_code, 204)


if __name__ == "__main__":
    unittest.main()
