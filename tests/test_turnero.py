# -*- coding: utf-8 -*-
"""Pruebas del turnero.

Sin red y sin esperas largas: las ventanas son de décimas de segundo.
Cada prueba se escribió rompiendo el código a propósito primero, para
comprobar que se ponía roja. Lo que rompió cada una está anotado.
"""
import asyncio
import time

import pytest

from turnero import Turnero, HayCola


async def test_por_debajo_del_limite_no_se_espera():
    t = Turnero(cuantas=5, ventana=60.0)
    ini = time.monotonic()
    for _ in range(5):
        await t.turno()
    assert time.monotonic() - ini < 0.2


async def test_pasado_el_limite_se_espera_lo_justo():
    """SABOTAJE: quitar el `+ 0.05` del cálculo de `falta` dejaba que
    la cuarta saliera un pelo antes de que caducara la primera."""
    t = Turnero(cuantas=3, ventana=0.5)
    for _ in range(3):
        await t.turno()
    ini = time.monotonic()
    await t.turno()
    esperado = time.monotonic() - ini
    assert 0.3 < esperado < 1.2, f"esperó {esperado:.2f}s"


async def test_la_ventana_se_vacia_sola():
    t = Turnero(cuantas=2, ventana=0.3)
    await t.turno(); await t.turno()
    assert t.en_la_ventana == 2
    await asyncio.sleep(0.35)
    assert t.en_la_ventana == 0
    assert t.espera_estimada() == 0.0


async def test_si_la_cola_es_absurda_se_avisa_en_vez_de_colgar():
    """SABOTAJE: devolver None en vez de lanzar hacía que la petición
    saliera igual, saltándose el límite en silencio."""
    t = Turnero(cuantas=1, ventana=60.0, espera_maxima=1.0)
    await t.turno()
    with pytest.raises(HayCola) as e:
        await t.turno()
    assert e.value.espera > 1.0
    assert e.value.cuantas == 1


async def test_el_aviso_trae_los_numeros_para_el_usuario():
    t = Turnero(cuantas=2, ventana=30.0, espera_maxima=0.5)
    await t.turno(); await t.turno()
    with pytest.raises(HayCola) as e:
        await t.turno()
    texto = str(e.value)
    assert "2" in texto and "30" in texto


async def test_la_espera_estimada_no_pide_turno():
    """SABOTAJE: si espera_estimada apuntara la salida, consultar el
    estado gastaría turnos y la web se limitaría a sí misma."""
    t = Turnero(cuantas=3, ventana=60.0)
    for _ in range(10):
        t.espera_estimada()
    assert t.en_la_ventana == 0
    for _ in range(3):
        await t.turno()
    assert t.espera_estimada() > 0


async def test_el_limite_se_respeta_con_muchos_a_la_vez():
    """Veinte tareas a la vez contra un límite de cinco: salen cinco.
    SABOTAJE: quitar el cerrojo dejaba pasar a varias entre el mirar
    y el apuntar, y salían siete u ocho."""
    t = Turnero(cuantas=5, ventana=60.0, espera_maxima=0.2)
    async def intentar():
        try:
            await t.turno()
            return True
        except HayCola:
            return False
    salidas = await asyncio.gather(*[intentar() for _ in range(20)])
    assert sum(salidas) == 5
    assert t.en_la_ventana == 5


async def test_sirve_como_gestor_de_contexto():
    t = Turnero(cuantas=2, ventana=60.0)
    async with t:
        pass
    assert t.en_la_ventana == 1


# AQUÍ HABÍA UNA PRUEBA QUE NO PROTEGÍA NADA
#
# Se llamaba test_no_duerme_con_el_cerrojo_cogido y decía comprobar que
# el `await asyncio.sleep(...)` de Turnero.turno() está FUERA del
# `async with self._cerrojo`.
#
# Al sabotear el código —metiendo el sleep dentro del cerrojo— la
# prueba siguió en VERDE. O sea que no comprobaba lo que decía.
#
# El motivo: con una ventana corta, cuando el que duerme se despierta
# la ventana ya ha caducado entera, así que el siguiente entra rápido
# de las dos maneras. Los tiempos salen casi iguales con el código
# bueno y con el roto.
#
# La razón de tener el sleep fuera del cerrojo sigue siendo buena —si
# durmiera dentro, el turnero dejaría de ser concurrente y se
# convertiría en una cola de uno en uno— pero es un argumento de
# diseño que NO he sabido fijar con una prueba. Antes que dejar una
# prueba verde que miente, se borra y se dice.
#
# Está en el README, en «lo que no está probado».


@pytest.mark.parametrize("cuantas,ventana", [(0, 60), (-1, 60), (5, 0), (5, -1)])
async def test_configuracion_imposible_se_rechaza_al_construir(cuantas, ventana):
    """Mejor reventar al arrancar que a las tres de la mañana."""
    with pytest.raises(ValueError):
        Turnero(cuantas=cuantas, ventana=ventana)


async def test_el_repr_dice_el_estado():
    t = Turnero(cuantas=4, ventana=10.0)
    await t.turno()
    assert "cuantas=4" in repr(t) and "en_la_ventana=1" in repr(t)
