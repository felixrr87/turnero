# -*- coding: utf-8 -*-
"""turnero — límite por ventana y un viaje por petición, para asyncio.

    from turnero import Turnero, UnViaje, HayCola

    turnero = Turnero(cuantas=9, ventana=60)   # nueve de diez: el margen
    viajes  = UnViaje()

    async def traer(id):
        return await viajes.haz(id, lambda: _traer_de_verdad(id))

    async def _traer_de_verdad(id):
        await turnero.turno()
        ...

Lo que NO resuelve, y está escrito también en el README: el turnero
vive en la memoria de UN proceso. Con dos procesos o dos máquinas, cada
uno lleva su cuenta y entre los dos se pasan del límite. Para eso hace
falta algo compartido (Redis o similar) y esto no lo es.
"""
from .errores import HayCola
from ._turnero import Turnero, ESPERA_MAXIMA_POR_DEFECTO
from ._un_viaje import UnViaje

__all__ = ["Turnero", "UnViaje", "HayCola", "ESPERA_MAXIMA_POR_DEFECTO"]
__version__ = "0.1.0"
