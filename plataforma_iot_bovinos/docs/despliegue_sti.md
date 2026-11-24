# Guía: Reemplazar ThingsBoard por el sitio web en `sti.itsoeh.edu.mx`

**Servidor:** `sti.itsoeh.edu.mx` (actualmente ThingsBoard)  
**Proyecto:** Plataforma IoT para Monitoreo GPS de Bovinos — ITESHU  
**Resultado esperado:** Flask en `/` y Streamlit en `/dashboard/`, con HTTPS.

> ⚠️ **No ejecutes esto sin autorización de STI/ITESHU.** ThingsBoard puede estar en uso por otras personas. Haz un respaldo y trabaja en ventana de mantenimiento.

---

## 0. Estrategia recomendada

Publica primero en `bovinos.sti.itsoeh.edu.mx` y valida. Después, con autorización, apunta también `sti.itsoeh.edu.mx` al mismo servidor y retira ThingsBoard.

---

## 1. Verifica acceso y DNS

Desde tu PC:

```powershell
ssh usuario@sti.itsoeh.edu.mx
```

Dentro del servidor:

```bash
whoami
sudo -v
dig sti.itsoeh.edu.mx +short
curl ifconfig.me
```

La IP de `dig` debe coincidir con la del servidor. Si no, el DNS lo administra otra máquina o TI.

---

## 2. Respalda ThingsBoard

```bash
sudo mkdir -p /opt/respaldos/thingsboard-$(date +%F)
sudo cp -a /etc/thingsboard /opt/respaldos/thingsboard-$(date +%F)/ 2>/dev/null
sudo cp -a /var/lib/thingsboard /opt/respaldos/thingsboard-$(date +%F)/ 2>/dev/null
```

Si corre en Docker:

```bash
docker ps -a | grep -i thingsboard
docker volume ls | grep -i thingsboard

docker run --rm \
  -v thingsboard_data:/data \
  -v /opt/respaldos:/backup \
  alpine tar czf /backup/thingsboard_data_$(date +%F).tgz -C /data .
```

---

## 3. Detecta y detén ThingsBoard

```bash
sudo ss -tlnp | grep -E ':80|:443|:8080'
systemctl list-units --type=service | grep -i things
docker ps -a | grep -i things
```

### Servicio systemd

```bash
sudo systemctl stop thingsboard
sudo systemctl disable thingsboard
```

### Contenedor Docker

```bash
docker stop thingsboard
docker rm thingsboard
# o:
docker compose -f /opt/thingsboard/docker-compose.yml down
```

### Configuración de Nginx

```bash
ls -l /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/thingsboard
sudo nginx -t && sudo systemctl reload nginx
```

Confirma que 80/443 quedaron libres:

```bash
sudo ss -tlnp | grep -E ':80|:443'
```

---

## 4. Instala requisitos

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin nginx certbot python3-certbot-nginx
sudo systemctl enable --now docker nginx
```

---

## 5. Clona el repositorio

El repo trae los archivos de producción listos:

```bash
sudo git clone https://github.com/am25021818-netizen/PLATAFORMA-IoT_.git /opt/plataforma_iot
cd /opt/plataforma_iot/plataforma_iot_bovinos
ls -l docker-compose.prod.yml webapp/Dockerfile.prod plataforma/mosquitto.conf
```

---

## 6. Crea el archivo de entorno

`.env` no se versiona por seguridad:

```bash
sudo bash -c 'cat > .env <<EOF
FLASK_SECRET_KEY=cambia-esta-clave-por-una-larga-y-aleatoria
EOF'
sudo chmod 600 .env
```

Cambia también las contraseñas de demostración en `webapp/database/seed.sql` antes de publicar.

---

## 7. Arranca los servicios

```bash
sudo docker compose -f docker-compose.prod.yml up -d --build
sudo docker compose -f docker-compose.prod.yml ps
sudo docker compose -f docker-compose.prod.yml logs -f
```

Deben aparecer activos:

- `iteshu_mosquitto` → `127.0.0.1:1883`
- `iteshu_streamlit` → `127.0.0.1:8501`
- `iteshu_flask` → `127.0.0.1:5000`

Prueba local:

```bash
curl -I http://127.0.0.1:5000
curl -I http://127.0.0.1:8501
```

---

## 8. Configura Nginx

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

- `/` → webapp Flask (login, mapa, reportes).
- `/dashboard/` → dashboard Streamlit.

Si solo quieres Streamlit como raíz, cambia `proxy_pass` del bloque `location /` a `http://127.0.0.1:8501`.

---

## 9. HTTPS

```bash
sudo certbot --nginx -d sti.itsoeh.edu.mx -d bovinos.sti.itsoeh.edu.mx
sudo systemctl reload nginx
```

Si el certificado lo administra TI, omite este paso y usa el certificado institucional.

---

## 10. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

**No** abras 1883, 5000 ni 8501 al público.

---

## 11. Verificación final

```bash
curl -I https://sti.itsoeh.edu.mx
curl -I https://sti.itsoeh.edu.mx/dashboard/
sudo ss -tlnp | grep -E ':80|:443'
sudo docker compose -f /opt/plataforma_iot/plataforma_iot_bovinos/docker-compose.prod.yml ps
```

En navegador:

```text
https://sti.itsoeh.edu.mx/login
https://sti.itsoeh.edu.mx/dashboard/
```

---

## 12. Reversa

```bash
cd /opt/plataforma_iot/plataforma_iot_bovinos
sudo docker compose -f docker-compose.prod.yml down

sudo rm /etc/nginx/sites-enabled/sti
sudo ln -s /etc/nginx/sites-available/thingsboard /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

sudo systemctl enable --now thingsboard
```

El respaldo de ThingsBoard de `/opt/respaldos` no se toca.

---

## 13. Actualizaciones futuras

```bash
cd /opt/plataforma_iot/plataforma_iot_bovinos
sudo git pull origin main
sudo docker compose -f docker-compose.prod.yml up -d --build
```

Las bases de datos viven en `./plataforma/data` y `./webapp/database`, por lo que sobreviven a reconstrucciones de imagen.
