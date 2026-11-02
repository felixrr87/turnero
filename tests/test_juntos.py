# -*- coding: utf-8 -*-
"""Los dos a la vez, que es como se usan de verdad."""
import asyncio

from turnero import Turnero, UnViaje


async def test_veinte_visitantes_pidiendo_cinco_cosas_gastan_cinco_turnos():
    """El caso real: mucha gente mirando las mismas pocas páginas.

    Sin agrupar serían veinte turnos y se comerían el límite. Con los
    dos juntos son cinco, uno por cosa distinta.
    """
    turnero = Turnero(cuantas=9, ventana=60.0)
    viajes = UnViaje()

    async def traer(clave):
        await turnero.turno()
        await asyncio.sleep(0.02)
        return clave

    async def pedir(clave):
        return await viajes.haz(clave, lambda: traer(clave))

    peticiones = [pedir(f"cosa{i % 5}") for i in range(20)]
    res = await asyncio.gather(*peticiones)

    assert len(res) == 20
    assert turnero.en_la_ventana == 5
