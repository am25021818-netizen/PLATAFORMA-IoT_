# Guía Paso a Paso: Despliegue en Docker y Publicación Web con Subdominio

**Materia:** Internet de las Cosas (IoT) — Maestría en Mecatrónica ITESHU  
**Docente:** DTI. Carlos Arturo Espinoza Galicia  
**Estudiante:** Iván Rodríguez Hernández  
**Proyecto:** Plataforma IoT para Monitoreo GPS de Bovinos en el Valle del Mezquital  

---

## 1. Requisitos Previos en el Servidor / PC Anfitrión
- Tener instalado **Docker** y **Docker Compose** (o Docker Desktop en Windows/Linux).
- Conexión a Internet.
- Un broker MQTT activo (incluido automáticamente en el `docker-compose.yml` con Mosquitto).

---

## 2. Construcción y Ejecución con Docker Compose

1. Abre una terminal y dirígete a la carpeta `plataforma/`:
   ```bash
   cd plataforma
   ```

2. (Opcional) Copia el archivo de variables de entorno:
   ```bash
   cp .env.example .env
   ```

3. Construye y levanta los contenedores en segundo plano (`daemon`):
   ```bash
   docker compose up -d --build
   ```

4. Verifica que los servicios estén activos y saludables:
   ```bash
   docker compose ps
   ```
   Deberás ver activos:
   - `iteshu_mosquitto_broker` (Puertos 1883, 9001)
   - `iteshu_plataforma_iot` (Puerto 8501)

5. Inspecciona los registros para verificar la conexión de la ingesta y Streamlit:
   ```bash
   docker compose logs -f
   ```

6. Comprobación local: Abre tu navegador web en:
   ```
   http://localhost:8501
   ```

---

## 3. Publicación en Internet con Subdominio (Evidencia de Entrega)

La instrucción solicita:
> *"debe ser funcional y estar publicada en tu servidor web con un subdominio referente a tu proyecto, p.e. `bovinos.midominio.com` o similar"*

A continuación se presentan las 3 alternativas más eficientes y profesionales para lograrlo:

### Método A: Cloudflare Tunnel (Recomendado: 100% Gratuito, HTTPS automático, Sin abrir puertos)
Cloudflare Tunnel conecta de forma cifrada tu contenedor local con la nube pública bajo tu subdominio sin que necesites abrir puertos en el módem de tu casa o rancho.

1. Si ya tienes un dominio propio gestionado en Cloudflare:
   - Ve al panel de **Cloudflare Zero Trust** -> **Networks** -> **Tunnels**.
   - Haz clic en **Create a Tunnel** y nómbralo `bovinos-iot`.
   - Copia el comando de instalación para tu sistema o ejecuta el conector de Cloudflare en Docker:
     ```bash
     docker run -d --name cloudflared --restart unless-stopped cloudflare/cloudflared:latest tunnel --no-autoupdate run --token TU_TOKEN_DE_CLOUDFLARE
     ```
   - En la sección **Public Hostname**, configura:
     - **Subdominio:** `bovinos`
     - **Dominio:** `tudominio.com`
     - **Tipo:** `HTTP`
     - **URL:** `host.docker.internal:8501` (o la IP local del contenedor `plataforma-iot:8501`).
   - ¡Listo! Tu plataforma estará publicada en `https://bovinos.tudominio.com` con certificado SSL válido.

2. **Si NO tienes dominio propio comprado (Opción Express Gratuita con Quick Tunnels):**
   Descarga `cloudflared` y ejecuta en terminal:
   ```bash
   cloudflared tunnel --url http://localhost:8501
   ```
   Te entregará un subdominio HTTPS público inmediato (ej. `https://bovinos-mezquital-iteshu.trycloudflare.com`).

---

### Método B: Servidor VPS con Nginx y Certbot (DigitalOcean / AWS / Linode / Oracle Cloud)
Si desplegaste en un servidor virtual privado en la nube:

1. Configura un registro DNS tipo **A** o **CNAME** en tu registrador:
   - **Host / Nombre:** `bovinos`
   - **Valor / Destino:** `IP_PUBLICA_DE_TU_SERVIDOR`

2. Crea la configuración de Nginx en `/etc/nginx/sites-available/bovinos.conf`:
   ```nginx
   server {
       server_name bovinos.tudominio.com;

       location / {
           proxy_pass http://127.0.0.1:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 86400;
       }
   }
   ```

3. Habilita el sitio y emite el certificado SSL gratis con Let's Encrypt:
   ```bash
   sudo ln -s /etc/nginx/sites-available/bovinos.conf /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   sudo certbot --nginx -d bovinos.tudominio.com
   ```

---

### Método C: DuckDNS (DNS Dinámico 100% Gratuito con subdominio personalizado)
1. Entra a [https://www.duckdns.org](https://www.duckdns.org).
2. Crea una cuenta gratuita y da de alta un subdominio referente a tu proyecto:
   - Ejemplo: `bovinos-iteshu.duckdns.org`
3. Asigna la IP pública de tu conexión.
4. Mapea el puerto del router al puerto 8501 de tu PC o utiliza Nginx Proxy Manager.
