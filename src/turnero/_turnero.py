# -*- coding: utf-8 -*-
"""El turnero: una ventana deslizante que reparte turnos.

POR QUÉ EXISTE ESTO Y NO USO UN SEMÁFORO
----------------------------------------
Un semáforo limita cuántas cosas pasan A LA VEZ. Lo que limita una API
es cuántas pasan POR MINUTO, que es otra cosa: puedes tener una sola
petición en vuelo y aun así pasarte del límite si haces sesenta
seguidas y rápidas.

Lo que hace falta es una ventana deslizante: recordar cuándo salió
cada petición y no dejar salir la número N+1 hasta que la primera
tenga más de `ventana` segundos. Eso es todo lo que hay aquí.

LA DECISIÓN QUE MÁS SE DISCUTE
------------------------------
Si tu proveedor te deja diez por minuto, configura NUEVE.

Su contador va por su ventana y su reloj; el tuyo va por el tuyo. Dos
peticiones separadas por un cuarto de segundo pueden caer en el mismo
minuto suyo aunque no caigan en el tuyo. Dejar uno de margen cuesta un
turno y evita el error. En producción, con nueve de diez, no he visto
un 429; rozando el tope, sí.
"""
from __future__ import annotations

import asyncio
import time
from collections import deque

from .errores import HayCola

ESPERA_MAXIMA_POR_DEFECTO = 20.0
"""Más de esto esperando y se prefiere avisar. Veinte segundos es
mucho para una web y poco para perder la petición."""


class Turnero:
    """Reparte turnos para no pasarse de un límite por ventana.

        turnero = Turnero(cuantas=9, ventana=60)
        await turnero.turno()      # espera lo justo, o lanza HayCola
        ...tu petición...

    También vale como gestor de contexto:

        async with turnero:
            ...tu petición...
    """

    def __init__(self, cuantas: int = 9, ventana: float = 60.0,
                 espera_maxima: float = ESPERA_MAXIMA_POR_DEFECTO):
        if cuantas < 1:
            raise ValueError("cuantas tiene que ser 1 o más")
        if ventana <= 0:
            raise ValueError("ventana tiene que ser mayor que cero")
        self.cuantas = cuantas
        self.ventana = float(ventana)
        self.espera_maxima = float(espera_maxima)
        self._salidas: deque[float] = deque()
        self._cerrojo = asyncio.Lock()

    # ── por dentro ──────────────────────────────────────────────
    def _limpiar(self, ahora: float) -> None:
        """Olvida las salidas que ya no cuentan para la ventana."""
        while self._salidas and ahora - self._salidas[0] >= self.ventana:
            self._salidas.popleft()

    # ── por fuera ───────────────────────────────────────────────
    def espera_estimada(self) -> float:
        """Cuánto habría que esperar AHORA. No pide turno ni lo gasta.

        Sirve para decidir antes de llamar: si esto devuelve 12, puedes
        enseñar «hay cola» sin bloquear a nadie.
        """
        ahora = time.monotonic()
        self._limpiar(ahora)
        if len(self._salidas) < self.cuantas:
            return 0.0
        return max(0.0, self.ventana - (ahora - self._salidas[0]))

    @property
    def en_la_ventana(self) -> int:
        """Cuántas peticiones cuentan ahora mismo dentro de la ventana."""
        self._limpiar(time.monotonic())
        return len(self._salidas)

    async def turno(self) -> None:
        """Espera a que toque. Lanza HayCola si la espera es absurda.

        El cerrojo sólo cubre mirar y apuntar, nunca el sleep: si
        durmiera con el cerrojo cogido, el turnero dejaría de ser
        concurrente y se convertiría en una cola de uno en uno.
        """
        while True:
            async with self._cerrojo:
                ahora = time.monotonic()
                self._limpiar(ahora)
                if len(self._salidas) < self.cuantas:
                    self._salidas.append(ahora)
                    return
                falta = self.ventana - (ahora - self._salidas[0]) + 0.05
            if falta > self.espera_maxima:
                raise HayCola(falta, self.cuantas, self.ventana)
            await asyncio.sleep(min(falta, 1.0))

    async def __aenter__(self) -> "Turnero":
        await self.turno()
        return self

    async def __aexit__(self, *_) -> None:
        return None

    def __repr__(self) -> str:
        return (f"Turnero(cuantas={self.cuantas}, ventana={self.ventana:g}, "
                f"en_la_ventana={len(self._salidas)})")
