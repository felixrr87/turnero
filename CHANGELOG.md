# Registro de cambios

## 0.1.0 — primera versión

Primera publicación. Sale de un servicio en producción, no de un ejemplo:
el limitador que hacía falta para abrir [Sportalyze](https://sportalyze.onrender.com)
a la gente con una clave de diez peticiones por minuto.

- `Turnero`: ventana deslizante, `espera_maxima` configurable, `HayCola`
  con los segundos dentro, gestor de contexto y `espera_estimada()` que
  no gasta turno.
- `UnViaje`: agrupación de llamadas idénticas simultáneas, con `shield`
  para que cancelar a uno no deje tirados a los demás.
- Veinte pruebas, sin red. Una prueba retirada por no poder fallar; el
  motivo está en el código y en el README.
