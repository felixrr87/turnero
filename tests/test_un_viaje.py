# -*- coding: utf-8 -*-
"""Pruebas de «un viaje por petición»."""
import asyncio

import pytest

from turnero import UnViaje


async def test_cinco_a_la_vez_son_un_solo_viaje():
    """SABOTAJE: quitar el registro en `_en_vuelo` → salieron cinco."""
    viajes = UnViaje()
    salidas = 0

    async def traer():
        nonlocal salidas
        salidas += 1
        await asyncio.sleep(0.05)
        return "dato"

    res = await asyncio.gather(*[viajes.haz("a", traer) for _ in range(5)])
    assert salidas == 1
    assert res == ["dato"] * 5


async def test_claves_distintas_son_viajes_distintos():
    viajes = UnViaje()
    salidas = 0

    async def traer():
        nonlocal salidas
        salidas += 1
        await asyncio.sleep(0.02)
        return salidas

    await asyncio.gather(viajes.haz("a", traer), viajes.haz("b", traer))
    assert salidas == 2


async def test_despues_de_acabar_el_siguiente_vuelve_a_salir():
    """Agrupar sólo vale para lo SIMULTÁNEO. Esto no es una caché.
    SABOTAJE: no limpiar `_en_vuelo` al acabar → la segunda tanda
    devolvía el dato viejo para siempre."""
    viajes = UnViaje()
    salidas = 0

    async def traer():
        nonlocal salidas
        salidas += 1
        return salidas

    assert await viajes.haz("a", traer) == 1
    assert await viajes.haz("a", traer) == 2
    assert viajes.en_vuelo == 0


async def test_si_el_primero_se_cancela_los_demas_cobran():
    """La razón de `asyncio.shield`.
    SABOTAJE: quitar el shield → al cancelar el primero, los otros dos
    se quedaron con CancelledError sin haber pedido nada."""
    viajes = UnViaje()

    async def traer():
        await asyncio.sleep(0.1)
        return "llegó"

    primero = asyncio.create_task(viajes.haz("a", traer))
    await asyncio.sleep(0.01)
    otros = [asyncio.create_task(viajes.haz("a", traer)) for _ in range(2)]
    await asyncio.sleep(0.01)
    primero.cancel()
    assert await asyncio.gather(*otros) == ["llegó", "llegó"]


async def test_un_fallo_llega_a_todos_los_que_esperan():
    viajes = UnViaje()

    async def traer():
        await asyncio.sleep(0.02)
        raise RuntimeError("la fuente ha dicho que no")

    with pytest.raises(RuntimeError):
        await asyncio.gather(*[viajes.haz("a", traer) for _ in range(3)])
    assert viajes.en_vuelo == 0


async def test_el_contador_de_en_vuelo_es_de_verdad():
    viajes = UnViaje()

    async def traer():
        await asyncio.sleep(0.05)
        return 1

    t = [asyncio.create_task(viajes.haz(k, traer)) for k in ("a", "b", "c")]
    await asyncio.sleep(0.01)
    assert viajes.en_vuelo == 3
    await asyncio.gather(*t)
    assert viajes.en_vuelo == 0
