# Lista de Tareas: fix-failsafe-gps-y-resiliencia

- [x] Redactar propuesta, diseño, tareas y delta de especificación en `openspec/changes/fix-failsafe-gps-y-resiliencia/`.
- [x] Corregir el collar para transmitir `0,0` con `fix_valido=0` cuando no haya fix.
- [x] Retener la última coordenada válida en el gateway y publicarla con `fix_valido=false`.
- [x] Sustituir `delay(3000)` del gateway por reconexión no bloqueante con `millis()`.
- [x] Configurar `LORA_TX_POWER=20` en el gateway.
- [x] Modificar la ingesta para persistir y alertar coordenadas fuera de rango en lugar de descartarlas.
- [x] Modificar `database.py` para conservar la última posición válida y marcarla como desactualizada.
- [x] Corregir el import de `datetime` y el modo debug en la webapp Flask.
- [x] Añadir `webapp/requirements.txt` y actualizar el script de arranque.
- [x] Ampliar `README.md` con documentación completa del repositorio.
- [x] Reforzar `.gitignore` y alinear el pin de `paho-mqtt`.
- [x] Ejecutar pruebas unitarias, simulador, Streamlit y endpoints Flask con bases temporales.
- [x] Publicar el repositorio en GitHub conservando el historial remoto y sin archivos prohibidos.
