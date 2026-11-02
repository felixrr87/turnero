# -*- coding: utf-8 -*-
"""Un viaje por petición: si varios piden lo mismo a la vez, sale una.

ESTO AHORRA MÁS TURNOS QUE EL PROPIO LÍMITE
-------------------------------------------
Lo normal, en una web abierta, es que todo el mundo mire las mismas
cosas. Si cinco visitantes abren la misma página en el mismo segundo,
el turnero reparte cinco turnos para traer cinco veces lo mismo.

Con esto sale UNA petición y las otras cuatro se cuelgan de ella. En
producción ahorró más peticiones que el limitador, de largo.

POR QUÉ `shield`
----------------
Si el primero que pidió se cancela —cierra la pestaña, se le va la
conexión—, los otros cuatro NO pueden quedarse colgados de una tarea
muerta. `asyncio.shield` hace que cancelar la espera no cancele el
viaje: el que se va se va, y los que quedan reciben su respuesta.
"""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict, Hashable


class UnViaje:
    """Agrupa llamadas idénticas simultáneas en una sola.

        viajes = UnViaje()
        datos = await viajes.haz("equipo:81", lambda: traer(81))

    Lo que agrupa es la CLAVE: dos llamadas con la misma clave a la vez
    comparten resultado; con claves distintas, no se tocan.
    """

    def __init__(self) -> None:
        self._en_vuelo: Dict[Hashable, asyncio.Future] = {}

    @property
    def en_vuelo(self) -> int:
        """Cuántas peticiones distintas están saliendo ahora mismo."""
        return len(self._en_vuelo)

    async def haz(self, clave: Hashable,
                  hacer: Callable[[], Awaitable[Any]]) -> Any:
        """Ejecuta `hacer()` una sola vez por clave simultánea.

        `hacer` es una función SIN argumentos que devuelve una
        corutina. Se pide así, y no la corutina ya creada, porque si
        hay que descartarla quedaría una corutina sin esperar y Python
        avisa por consola.
        """
        pendiente = self._en_vuelo.get(clave)
        if pendiente is not None:
            return await asyncio.shield(pendiente)

        tarea = asyncio.ensure_future(hacer())
        self._en_vuelo[clave] = tarea
        try:
            return await asyncio.shield(tarea)
        finally:
            # Sólo lo quita quien lo puso: si el primero se canceló y
            # otro ya empezó un viaje nuevo con la misma clave, borrar
            # a ciegas tiraría el viaje bueno.
            if self._en_vuelo.get(clave) is tarea:
                self._en_vuelo.pop(clave, None)
