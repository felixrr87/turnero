# -*- coding: utf-8 -*-
"""Los errores que este paquete puede lanzar.

Tienen clase propia a propósito. Quien usa la librería necesita poder
distinguir «hay cola, espera» de «esto se ha roto», porque son dos
mensajes distintos para el usuario final y dos decisiones distintas
para el programa.
"""
from __future__ import annotations


class HayCola(Exception):
    """La espera sería más larga de lo que se ha dicho que se tolera.

    No es un fallo: es el turnero diciendo que prefiere contestar a
    tener a alguien mirando una ruedecita. Trae el número para que
    arriba se pueda escribir «vuelve en N segundos» en vez de un
    error genérico.
    """

    def __init__(self, espera: float, cuantas: int, ventana: float):
        self.espera = espera
        self.cuantas = cuantas
        self.ventana = ventana
        super().__init__(
            f"hay cola: habría que esperar {espera:.0f} segundos. "
            f"El límite configurado es de {cuantas} peticiones "
            f"cada {ventana:.0f} segundos, compartidas por todo el mundo."
        )
