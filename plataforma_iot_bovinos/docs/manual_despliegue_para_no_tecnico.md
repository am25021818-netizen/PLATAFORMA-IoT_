# Manual para subir el sitio web al servidor del ITESHU
## Explicado para una persona que no trabaja en programación

**Servidor:** `sti.itsoeh.edu.mx`  
**Proyecto:** Plataforma IoT para monitoreo GPS de bovinos  
**Tiempo estimado:** 45 a 60 minutos  
**Antes de empezar:** necesitas autorización del área de STI del ITESHU.

---

## 1. Primero, entiende qué es cada cosa

Imagina que vas a mudar una tienda de un local a otro.

| Término | En palabras sencillos | Analogía |
|---|---|---|
| **Servidor** | Una computadora del instituto que está encendida 24/7 y guarda páginas web. | El local donde estará tu tienda. |
| **Dominio** `sti.itsoeh.edu.mx` | La dirección que la gente escribe para llegar. | El número y nombre de la calle del local. |
| **DNS** | La guía telefónica que traduce el nombre del dominio en la dirección real del servidor. | La lista que dice "ese nombre corresponde a esa IP". |
| **ThingsBoard** | Un programa que hoy ocupa esa dirección y muestra otra plataforma. | El negocio anterior que está en el local. |
| **SSH** | Una forma de conectarte al servidor escribiendo comandos desde tu computadora. | Un control remoto para trabajar dentro del local sin estar ahí. |
| **Terminal / consola** | La ventana donde escribes esos comandos. | El tablero de control. |
| **Docker** | Una herramienta que guarda tu aplicación dentro de "cajas" ya configuradas. | Cajas de mudanza: dentro va tu programa listo para funcionar. |
| **Contenedor** | Cada una de esas cajas ejecutándose. | Cada caja trabajando. |
| **Nginx** | El recepcionista que decide a qué caja enviar a cada visitante. | El empleado que recibe a la gente y la dirige. |
| **HTTPS / certificado** | El candado que hace que la comunicación sea segura. | Sobre cerrado y con sello. |
| **MQTT / Mosquitto** | El "radiotelefono" por el que los collares envían la ubicación. | La radio de los sensores. |
| **Base de datos** | El archivero donde se guardan los datos de los bovinos. | El archivo de la tienda. |
| **GitHub** | El lugar donde está guardado tu proyecto con su historial. | Un Google Drive con control de versiones. |
| **`.env` (archivo secreto)** | Un archivo con la clave privada de tu sitio. No se comparte ni se sube a internet. | La llave de la caja fuerte. |
| **`sudo`** | Palabra que se pone delante de un comando para pedir permiso de administrador. | Pedir autorización al encargado del edificio. |

---

## 2. Qué vamos a lograr

**Antes:**

```text
Visitante → sti.itsoeh.edu.mx → ThingsBoard
```

**Después:**

```text
Visitante → sti.itsoeh.edu.mx → Tu sitio web
                                 ├── Página principal con login (Flask)
                                 └── Mapa y dashboard (Streamlit)
```

No vamos a borrar tu proyecto de tu computadora. Solamente vamos a copiarlo al servidor y a cambiar qué programa atiende esa dirección.

---

## 3. Lo que necesitas tener listo

Marca cada una:

- [ ] Permiso de STI/ITESHU para cambiar el servidor.
- [ ] Un **usuario** y **contraseña** para entrar por SSH.
- [ ] Saber si ese usuario tiene permisos de administrador (`sudo`). Si no, pide a TI que ejecute los pasos 3, 5, 9, 10 y 11.
- [ ] Tu computadora con internet.
- [ ] Un bloc de notas para anotar contraseñas (no las pegues en chat ni correos).
- [ ] 45–60 minutos sin interrupciones.
- [ ] Avisar a los compañeros que usan ThingsBoard que habrá un cambio.

---

## 4. Reglas de oro (léelas antes de tocar nada)

1. **No ejecutes comandos que no entiendas** sin preguntar a alguien de tecnología.
2. **No compartas contraseñas** por WhatsApp, correo ni chat.
3. **Haz el respaldo del paso 3 antes de apagar ThingsBoard.**
4. **Prueba primero en un nombre de prueba** si es posible: `bovinos.sti.itsoeh.edu.mx`.
5. **Si algo falla, detente.** No sigas probando cosas al azar; usa el paso 12 para volver atrás.
6. **No apagues la ventana de comandos** mientras se esté descargando o instalando algo.

---

## 5. Paso a paso, con explicación

### Paso 1 — Conectarte al servidor (tomar el control remoto)

En tu computadora con Windows, abre **PowerShell** y escribe:

```powershell
ssh usuario@sti.itsoeh.edu.mx
```

Te pedirá la contraseña. **No verás los caracteres mientras escribes**; es normal. Escribe la contraseña y da Enter.

**Qué deberías ver:** un mensaje de bienvenida y algo como:

```text
usuario@servidor:~$
```

**Interpretación:** ya estás "dentro" de la computadora del instituto. Todo lo que escribas de ahora en adelante se ejecuta allá, no en tu PC.

---

### Paso 2 — Confirmar que estás en el sitio correcto

Escribe:

```bash
whoami
dig sti.itsoeh.edu.mx +short
curl ifconfig.me
```

**Interpretación:**

- `whoami` dice con qué usuario entraste.
- `dig ... +short` muestra la dirección IP real de `sti.itsoeh.edu.mx`.
- `curl ifconfig.me` muestra la IP del servidor donde estás.

**Ambas IP deben coincidir.** Si no coinciden, el dominio apunta a otra máquina: llama a STI antes de continuar.

---

### Paso 3 — Hacer una copia de seguridad de ThingsBoard

Aunque vamos a quitar ThingsBoard, guardamos una copia por si alguien la necesita después. Es como fotocopiar un expediente antes de mover el archivo.

```bash
sudo mkdir -p /opt/respaldos/thingsboard-$(date +%F)
sudo cp -a /etc/thingsboard /opt/respaldos/thingsboard-$(date +%F)/ 2>/dev/null
sudo cp -a /var/lib/thingsboard /opt/respaldos/thingsboard-$(date +%F)/ 2>/dev/null
```

Si ThingsBoard estaba en Docker (lo más probable), además ejecuta:

```bash
sudo docker ps -a | grep -i thingsboard
sudo docker volume ls | grep -i thingsboard
```

Si ves un volumen con nombre parecido a `thingsboard_data`, guarda su contenido:

```bash
docker run --rm \
  -v thingsboard_data:/data \
  -v /opt/respaldos:/backup \
  alpine tar czf /backup/thingsboard_data_$(date +%F).tgz -C /data .
```

**Qué significa `sudo`:** estás pidiendo permiso de administrador. Si te pide contraseña, escribe la misma del SSH.

---

### Paso 4 — Apagar ThingsBoard (cerrar el negocio anterior)

Primero averigua cómo estaba encendido:

```bash
sudo ss -tlnp | grep -E ':80|:443|:8080'
systemctl list-units --type=service | grep -i things
sudo docker ps -a | grep -i things
```

Dependiendo de lo que aparezca, elige **una** de estas opciones:

**Si aparece como servicio:**

```bash
sudo systemctl stop thingsboard
sudo systemctl disable thingsboard
```

> `stop` = apagarlo ahora. `disable` = evitar que se encienda solo cuando el servidor se reinicie.

**Si aparece como contenedor Docker:**

```bash
sudo docker stop thingsboard
sudo docker rm thingsboard
```

Si el nombre no es exactamente `thingsboard`, copia el nombre que apareció en `sudo docker ps -a`.

**Si Nginx lo redirigía:**

```bash
sudo rm /etc/nginx/sites-enabled/thingsboard
sudo nginx -t && sudo systemctl reload nginx
```

Comprueba que los puertos quedaron libres:

```bash
sudo ss -tlnp | grep -E ':80|:443'
```

**Si no sale nada, bien:** significa que ya no hay nadie ocupando la entrada.

---

### Paso 5 — Preparar las herramientas

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin nginx certbot python3-certbot-nginx
sudo systemctl enable --now docker nginx
```

**Interpretación sencilla:**

- `apt update` = actualizar la lista de programas disponibles.
- `apt install` = instalar Git (descargar el proyecto), Docker (las cajas), Nginx (el recepcionista) y Certbot (el candado HTTPS).
- `enable --now` = encender Docker y Nginx y que sigan encendidos después de reiniciar.

Puede tardar varios minutos. **No cierres la ventana.**

---

### Paso 6 — Traer tu proyecto desde GitHub

```bash
sudo git clone https://github.com/am25021818-netizen/PLATAFORMA-IoT_.git /opt/plataforma_iot
cd /opt/plataforma_iot/plataforma_iot_bovinos
ls -l docker-compose.prod.yml webapp/Dockerfile.prod plataforma/mosquitto.conf
```

**Interpretación:** estás descargando una copia de tu proyecto a una carpeta del servidor llamada `/opt/plataforma_iot`. El comando `ls` confirma que los archivos de despliegue llegaron.

---

### Paso 7 — Crear el archivo secreto

```bash
sudo tee .env >/dev/null <<'EOF'
FLASK_SECRET_KEY=cambia-esta-clave-por-una-larga-y-aleatoria
EOF
sudo chmod 600 .env
```

**Si el prompt cambió a `>` y no sabes cómo salir:** presiona **Ctrl+C** y pega el bloque completo otra vez. No escribas comillas adicionales; esta versión con `sudo tee` es más segura.

**Interpretación:** creas una "llave" para que nadie pueda falsificar el inicio de sesión de tu sitio. Sustituye el texto `cambia-esta-clave...` por una frase larga y aleatoria, por ejemplo:

```text
Mezquital-Bovinos-ITESHU-2026-Clave-Unica-X7k9
```

Ese archivo **no se ve desde internet** y por eso no está en GitHub.

---

### Paso 8 — Encender las tres cajas de tu aplicación

```bash
sudo docker compose -f docker-compose.prod.yml up -d --build
sudo docker compose -f docker-compose.prod.yml ps
```

**Qué son las tres cajas:**

| Caja | Qué hace | Dirección interna |
|---|---|---|
| `iteshu_mosquitto` | Recibe los datos de los collares | `127.0.0.1:1883` |
| `iteshu_streamlit` | Muestra el mapa y el dashboard | `127.0.0.1:8501` |
| `iteshu_flask` | Muestra el sitio con login y reportes | `127.0.0.1:5000` |

`up -d` = "enciende todo y déjalo corriendo en segundo plano". `--build` = "prepara las cajas antes".

Comprueba que responden:

```bash
curl -I http://127.0.0.1:5000
curl -I http://127.0.0.1:8501
```

**Qué deberías ver:** líneas que empiezan con `HTTP/1.1 200 OK`. Si sale `Connection refused`, la caja aún no terminó de encender; espera 20 segundos y repite.

Si quieres ver mensajes de error:

```bash
sudo docker compose -f docker-compose.prod.yml logs -f
```

Para salir de los registros, presiona **Ctrl + C**.

---

### Paso 9 — Configurar al recepcionista (Nginx)

Esto le dice al servidor: *"si alguien entra a la página principal, mándalo al sitio con login; si entra a `/dashboard/`, mándalo al mapa"*.

```bash
sudo cat > /etc/nginx/sites-available/sti <<'EOF'
server {
    listen 80;
    server_name sti.itsoeh.edu.mx bovinos.sti.itsoeh.edu.mx;

    client_max_body_size 20M;

    location /dashboard/ {
        proxy_pass http://127.0.0.1:8501/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_buffering off;
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/sti /etc/nginx/sites-enabled/sti
sudo nginx -t
sudo systemctl reload nginx
```

**Interpretación de `nginx -t`:** es un "test" que revisa que el texto esté bien escrito. Si dice `syntax is ok` y `test is successful`, todo bien.

---

### Paso 10 — Poner el candado (HTTPS)

```bash
sudo certbot --nginx -d sti.itsoeh.edu.mx -d bovinos.sti.itsoeh.edu.mx
sudo systemctl reload nginx
```

Te pedirá un correo para avisos y aceptar términos (escribe `Y` cuando pregunte). Al terminar, la dirección será `https://...` y el navegador mostrará un candado.

Si el instituto ya tiene su propio certificado, **no ejecutes este paso**: pide a TI que aplique el suyo.

---

### Paso 11 — Abrir solo las puertas necesarias

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

**Interpretación:** permitimos entrar por SSH (para administrar), por el puerto 80 (web normal) y por el 443 (web segura). **No** abrimos los puertos internos 1883, 5000 ni 8501 al público; Nginx ya se encarga de ellos.

---

### Paso 12 — Probar como si fueras un visitante

Desde tu propia computadora abre el navegador y entra a:

```text
https://sti.itsoeh.edu.mx/login
https://sti.itsoeh.edu.mx/dashboard/
```

También puedes verificar desde el servidor:

```bash
curl -I https://sti.itsoeh.edu.mx
curl -I https://sti.itsoeh.edu.mx/dashboard/
sudo docker compose -f /opt/plataforma_iot/plataforma_iot_bovinos/docker-compose.prod.yml ps
```

**Qué deberías ver:**

- En `/login`: el formulario de acceso de tu plataforma.
- En `/dashboard/`: el mapa con los bovinos del Valle del Mezquital.
- En `curl`: `HTTP/1.1 200 OK` o `HTTP/2 200`.
- En `docker compose ps`: los tres servicios con estado `Up`.

Prueba iniciar sesión con:

```text
Correo: admin@mezquital.mx
Contraseña: admin123
```

**Cámbiala antes de dejar el sitio público.**

---

### Paso 13 — Si estás probando en el subdominio

Si decidiste probar primero en `bovinos.sti.itsoeh.edu.mx`, pide a STI que apunte también el nombre principal `sti.itsoeh.edu.mx` a la misma IP del servidor. No necesitas volver a instalar nada: Nginx ya acepta ambos nombres.

---

## 6. Lista de verificación final

| Pregunta | Cómo comprobarlo | Si no |
|---|---|---|
| ¿Ya no aparece ThingsBoard? | Abre `https://sti.itsoeh.edu.mx` | Repite el paso 4 |
| ¿Aparece el login de tu proyecto? | Abre `/login` | Revisa paso 8 y 9 |
| ¿Funciona el mapa? | Abre `/dashboard/` | Revisa WebSocket en paso 9 |
| ¿Tiene candado HTTPS? | Mira la barra del navegador | Repite paso 10 |
| ¿Siguen corriendo los servicios tras reiniciar? | `docker compose ... ps` | `restart: unless-stopped` ya está configurado |
| ¿Quedó el respaldo de ThingsBoard? | `ls /opt/respaldos` | No borres esa carpeta |

---

## 7. Si algo sale mal (solución en lenguaje sencillo)

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| La página sigue mostrando ThingsBoard | No se apagó del todo | Repite el paso 4 y recarga con Ctrl+F5 |
| Sale error `502 Bad Gateway` | La caja Flask o Streamlit está apagada | `sudo docker compose -f docker-compose.prod.yml restart` |
| Sale error `404` | Nginx no apunta bien | Repite el paso 9 y haz `sudo nginx -t` |
| No aparece el candado | Falta certificado | Repite el paso 10 |
| No conecta desde fuera, sí desde el servidor | Firewall cerrado | Repite el paso 11 |
| No recuerdas la contraseña del login | Usuario de demostración | Mira `webapp/database/seed.sql` y cámbiala |
| Quieres volver a ThingsBoard | Necesitas revertir | Ejecuta el paso 8 de la sección siguiente |

### Volver atrás (reversa)

```bash
cd /opt/plataforma_iot/plataforma_iot_bovinos
sudo docker compose -f docker-compose.prod.yml down

sudo rm /etc/nginx/sites-enabled/sti
sudo ln -s /etc/nginx/sites-available/thingsboard /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

sudo systemctl enable --now thingsboard
```

Esto no borra tu proyecto ni el respaldo; solo devuelve el sitio anterior.

---

## 8. Qué NO hacer

- No borres carpetas del servidor que no reconozcas (`/etc`, `/var`, `/opt/thingsboard` sin respaldo).
- No subas el archivo `.env` a GitHub.
- No dejes las contraseñas de demostración en producción.
- No expongas el puerto 1883 (MQTT) sin usuario y contraseña.
- No cierres la sesión SSH mientras se esté instalando o descargando.
- No hagas cambios directamente en el sitio web hasta terminar la prueba completa.

---

## 9. Quién hace qué

| Tarea | La puedes hacer tú | Lo debe hacer STI |
|---|---|---|
| Pedir permiso y datos de acceso | ✅ | |
| Conectarte por SSH | ✅ | |
| Descargar el proyecto desde GitHub | ✅ | |
| Crear el archivo `.env` | ✅ | |
| Encender los contenedores | ✅ si tienes Docker | ✅ si no tienes permisos |
| Detener ThingsBoard | Solo con autorización | ✅ |
| Instalar Docker/Nginx/certbot | Solo con `sudo` | ✅ |
| Cambiar DNS del dominio principal | | ✅ |
| Dar soporte si algo falla | | ✅ |

---

## 10. Actualizar el sitio en el futuro

Cuando hagas cambios en tu proyecto y los subas a GitHub:

```bash
cd /opt/plataforma_iot/plataforma_iot_bovinos
sudo git pull origin main
sudo docker compose -f docker-compose.prod.yml up -d --build
```

Tus datos no se pierden: las bases de datos están en `plataforma/data` y `webapp/database`, fuera de las imágenes.

---

## 11. Llenar el sitio con datos de prueba de bovinos

Cuando quieras mostrar la plataforma con ejemplos completos —no vacía ni en rojo— ejecuta esto en el servidor:

```bash
cd /opt/plataforma_iot/plataforma_iot_bovinos
sudo git pull origin main
sudo python3 simular_datos_integrales.py
```

**Interpretación sencilla:** estás pidiendo al sistema que invente un hato de demostración con 12 vacas y toros, sus collares, sus movimientos de dos días y varias alertas. Es como poner ejemplos en una libreta antes de enseñarla. La palabra `sudo` es necesaria porque esas libretas pertenecen al administrador del servidor.

Al terminar debe decir:

```text
RESULTADO: TODO OK
```

Si no hay `python3` en el servidor, usa esta otra forma:

```bash
sudo docker exec -i iteshu_flask python3 - --solo-webapp --webapp-db /app/database/bovinos_iot.db < simular_datos_integrales.py
sudo docker exec -i iteshu_streamlit python3 - --solo-plataforma --plataforma-db /app/data/datos_iot.db < simular_datos_integrales.py
```

Después recarga la página con `Ctrl + F5`. Ya no necesitas reiniciar nada.

**Qué verás:**

- En el sitio principal: 12 animales, 12 collares, 3 ranchos, gráficas de razas y baterías, y un reporte con distancias recorridas.
- En el mapa: animales verdes, amarillos y rojos, según qué tan reciente sea su último aviso.
- En el dashboard: alertas de batería baja, desconexión, salida del potrero y velocidad anómala.
- Dos animales tendrán una posición "desactualizada" a propósito, para demostrar que el sistema no inventa coordenadas cuando el GPS falla.

**Importante:** esto es solo para prueba o demostración. Si algún día entran datos reales de collares, **no vuelvas a ejecutar este comando**, porque sustituiría la libreta de datos de ejemplo. ANTES de ejecutarlo se guardan copias de seguridad con extensión `.bak`.

---

**En resumen:** tú no estás "programando" el servidor; estás **cerrando un local anterior (ThingsBoard), mudando tres cajas con tu aplicación, poniendo un recepcionista (Nginx) y un candado (HTTPS)**. Si sigues los pasos en orden y haces el respaldo, el proceso es seguro y reversible.
