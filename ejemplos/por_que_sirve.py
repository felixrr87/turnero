# -*- coding: utf-8 -*-
"""Qué hace turnero, enseñándolo en vez de contándolo.

Se monta una API de mentira con la misma regla que football-data:
sólo deja pasar DIEZ peticiones cada ventana. La undécima no espera:
devuelve 429 y se pierde. Eso es lo que le pasa a un servicio pequeño
el día que entra más de una persona a la vez.

    python ejemplos/por_que_sirve.py                 # imprime la tabla
    python ejemplos/por_que_sirve.py salida.json     # y además la deja en JSON

El JSON existe para que los gráficos de las publicaciones lean las
cifras de aquí en vez de llevarlas tecleadas. Un número tecleado a
mano en un dibujo es un número que nadie vuelve a comprobar.
"""
import asyncio, json, sys, time
from turnero import Turnero, UnViaje

VENTANA = 5.0          # en football-data son 60 s; aquí 5 para no esperar
LIMITE = 10


class ApiDeMentira:
    """Cuenta lo que le llega y castiga pasarse, igual que la de verdad."""

    def __init__(self):
        self.salidas = []        # cuándo llegó cada petición
        self.servidas = 0
        self.rechazadas = 0

    async def pedir(self, que):
        ahora = time.monotonic()
        self.salidas = [t for t in self.salidas if ahora - t < VENTANA]
        if len(self.salidas) >= LIMITE:
            self.rechazadas += 1
            raise RuntimeError("429 demasiadas peticiones")
        self.salidas.append(ahora)
        self.servidas += 1
        await asyncio.sleep(0.05)        # la red tarda algo
        return f"datos de {que}"


async def _lanzar(n, hacer):
    ini = time.monotonic()
    await asyncio.gather(*(hacer(i) for i in range(n)))
    return time.monotonic() - ini


async def sin_turnero(n=15):
    api = ApiDeMentira()

    async def visitante(i):
        try:
            await api.pedir(f"equipo-{i}")
        except RuntimeError:
            pass

    return api, await _lanzar(n, visitante)


async def con_turnero(n=15):
    api = ApiDeMentira()
    # NUEVE de diez, a propósito: el reloj del proveedor no es el tuyo.
    turno = Turnero(cuantas=9, ventana=VENTANA, espera_maxima=30.0)

    async def visitante(i):
        async with turno:
            try:
                await api.pedir(f"equipo-{i}")
            except RuntimeError:
                pass

    return api, await _lanzar(n, visitante)


async def mismo_dato_sin_agrupar(n=20):
    api = ApiDeMentira()

    async def visitante(_):
        try:
            await api.pedir("clasificacion-LaLiga")
        except RuntimeError:
            pass

    return api, await _lanzar(n, visitante)


async def mismo_dato_agrupado(n=20):
    api = ApiDeMentira()
    viaje = UnViaje()

    async def visitante(_):
        try:
            await viaje.haz("clasificacion-LaLiga",
                            lambda: api.pedir("clasificacion-LaLiga"))
        except RuntimeError:
            pass

    return api, await _lanzar(n, visitante)


async def main():
    import turnero
    VISITANTES_A, VISITANTES_B = 15, 20

    a, ta = await sin_turnero(VISITANTES_A)
    b, tb = await con_turnero(VISITANTES_A)
    c, tc = await mismo_dato_sin_agrupar(VISITANTES_B)
    d, td = await mismo_dato_agrupado(VISITANTES_B)

    print(f"\nAPI de mentira: deja pasar {LIMITE} peticiones cada {VENTANA:.0f} s.\n")
    print(f"A) {VISITANTES_A} visitantes entran a la vez, "
          f"cada uno pide una cosa distinta")
    print(f"  sin turnero     atendidos {VISITANTES_A - a.rechazadas:>2} · "
          f"CON ERROR {a.rechazadas:>2}   en {ta:.1f} s")
    print(f"  CON turnero     atendidos {VISITANTES_A - b.rechazadas:>2} · "
          f"CON ERROR {b.rechazadas:>2}   en {tb:.1f} s")
    print(f"\nB) {VISITANTES_B} visitantes entran a la vez y piden TODOS LO MISMO")
    print(f"  sin UnViaje     atendidos {VISITANTES_B - c.rechazadas:>2} · "
          f"CON ERROR {c.rechazadas:>2}   · {c.servidas + c.rechazadas} "
          f"peticiones a la fuente")
    print(f"  CON UnViaje     atendidos {VISITANTES_B - d.rechazadas:>2} · "
          f"CON ERROR {d.rechazadas:>2}   · {d.servidas + d.rechazadas} "
          f"petición a la fuente\n")

    datos = {
        "version_turnero": turnero.__version__,
        "limite": LIMITE,
        "ventana": VENTANA,
        "A": {
            "visitantes": VISITANTES_A,
            "sin": {"con_error": a.rechazadas, "segundos": round(ta, 2),
                    "peticiones": a.servidas + a.rechazadas},
            "con": {"con_error": b.rechazadas, "segundos": round(tb, 2),
                    "peticiones": b.servidas + b.rechazadas},
        },
        "B": {
            "visitantes": VISITANTES_B,
            "sin": {"con_error": c.rechazadas, "segundos": round(tc, 2),
                    "peticiones": c.servidas + c.rechazadas},
            "con": {"con_error": d.rechazadas, "segundos": round(td, 2),
                    "peticiones": d.servidas + d.rechazadas},
        },
    }
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print(f"escrito {sys.argv[1]}")


asyncio.run(main())
