# turnero

**Límite de peticiones por ventana y agrupación de llamadas idénticas, para `asyncio`.**
Sin dependencias. Veinte pruebas. En castellano.

```bash
pip install turnero
```

---

## El problema

Tu proveedor te deja **diez peticiones por minuto**. No diez por visitante: diez en total.

En tu portátil, probando tú solo, nunca lo tocas. El día que compartes el enlace y entran
cinco personas a la vez, se las comen y todas reciben un error.

Un semáforo no sirve: limita cuántas cosas pasan **a la vez**, no cuántas pasan **por minuto**.
Puedes tener una sola petición en vuelo y aun así pasarte, si haces sesenta seguidas y rápidas.

## Las dos piezas

```python
import asyncio
from turnero import Turnero, UnViaje, HayCola

turnero = Turnero(cuantas=9, ventana=60)   # nueve de diez: ver abajo
viajes  = UnViaje()

async def traer_equipo(id_equipo):
    return await viajes.haz(f"equipo:{id_equipo}", lambda: _traer(id_equipo))

async def _traer(id_equipo):
    await turnero.turno()                  # espera lo justo, o lanza HayCola
    ...tu petición de verdad...
```

**`Turnero`** — ventana deslizante. Recuerda cuándo salió cada petición y no deja salir la
siguiente hasta que la más vieja caduca. Si la espera supera `espera_maxima` (20 s por defecto),
lanza `HayCola` con el número de segundos, para que puedas escribir *«vuelve en 12 segundos»*
en vez de un error genérico.

**`UnViaje`** — si cinco llamadas con la misma clave coinciden en el tiempo, sale **una** y las
otras cuatro se cuelgan de ella. En producción esto ahorró más peticiones que el propio
limitador, de largo: en una web abierta todo el mundo mira las mismas cosas.

También vale como gestor de contexto:

```python
async with turnero:
    ...tu petición...
```

## Por qué nueve y no diez

El contador de tu proveedor va por su ventana y su reloj; el tuyo va por el tuyo. Dos peticiones
separadas por un cuarto de segundo pueden caer en el mismo minuto suyo aunque no caigan en el
tuyo.

Dejar uno de margen cuesta un turno y evita el error. Con nueve de diez no he visto un 429
nunca; rozando el tope, sí.

---

## Lo que NO resuelve

Esto es tan importante como lo anterior, así que va en el README y no en una nota al pie.

**Vive en la memoria de UN proceso.** Con dos procesos, dos *workers* o dos máquinas, cada uno
lleva su cuenta y entre los dos se pasan del límite. Para eso hace falta un contador compartido
(Redis o similar) y esto no lo es. Si despliegas con más de un *worker*, `turnero` no te está
protegiendo.

**`UnViaje` no es una caché.** Agrupa sólo lo **simultáneo**. En cuanto la petición termina, la
siguiente vuelve a salir. Si quieres recordar la respuesta, pon una caché delante; son cosas
distintas y hacen falta las dos.

**No reintenta ni respeta `Retry-After`.** Si el proveedor te dice que no, eso lo decides tú
arriba.

## Lo que no está probado

En `tests/test_turnero.py` había una prueba que decía comprobar que el `sleep` está fuera del
cerrojo. Al romper el código a propósito, **siguió en verde**: no comprobaba nada. La he
borrado y he dejado escrito el motivo en su sitio.

La razón de tener el `sleep` fuera del cerrojo sigue siendo buena —si durmiera dentro, el
turnero dejaría de ser concurrente y se convertiría en una cola de uno en uno— pero es un
argumento de diseño que **no he sabido fijar con una prueba**. Prefiero decirlo a dejar una
prueba verde que miente.

---

## Pruebas

```bash
pip install -e ".[dev]"
pytest -q
```

Veinte pruebas, sin red. Cada una se escribió rompiendo el código a propósito y comprobando
que se ponía roja; lo que rompió cada una está anotado en su propio docstring.

De los tres sabotajes probados al publicar, dos pusieron la suite en rojo y uno no — ese está
contado arriba.

## Licencia

MIT. Félix Ramírez Ramírez, 2026.
