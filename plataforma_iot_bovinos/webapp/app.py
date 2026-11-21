"""
app.py — Servidor Flask Modular con Autenticación RBAC, Multi-Ranchos, Métricas y Descarga de Reportes
     Valle del Mezquital, Hidalgo
     Puerto: 5000
"""
import sys
import os
import csv
import io
from functools import wraps

# Asegurar que database/ esté en el path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "database"))

from flask import (
    Flask, jsonify, request, render_template, redirect, url_for,
    session, abort, Response
)
import db_manager as db

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.secret_key = "mezquital_bovinos_iot_secret_key_2026_rbac"

# Inicializar DB al arrancar
db.init_db()
print("[OK] Base de datos con soporte RBAC inicializada:", db.DB_PATH)


# ============================================================
#  DECORADORES DE AUTENTICACIÓN Y ROLES
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("view_login"))
        return f(*args, **kwargs)
    return decorated_function


def roles_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user" not in session:
                return redirect(url_for("view_login"))
            user_role = session["user"].get("rol")
            if user_role not in allowed_roles:
                abort(403, "Acceso restringido para su rol.")
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================
#  RUTAS DE LOGIN / LOGOUT
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def view_login():
    if request.method == "POST":
        correo = request.form.get("correo")
        password = request.form.get("password")
        user = db.autenticar_usuario(correo, password)
        if user:
            session["user"] = {
                "id": user["id"],
                "nombre": user["nombre"],
                "correo": user["correo"],
                "rol": user["rol"]
            }
            return redirect(url_for("view_dashboard"))
        else:
            return render_template("login.html", error="Credenciales inválidas. Verifique correo o contraseña.")
    
    if "user" in session:
        return redirect(url_for("view_dashboard"))
    return render_template("login.html")


@app.route("/logout")
def view_logout():
    session.clear()
    return redirect(url_for("view_login"))


# ============================================================
#  VISTAS MODULARES CON CONTROL DE ACCESO
# ============================================================

@app.route("/")
@login_required
def view_dashboard():
    return render_template("dashboard.html", active_page="dashboard")


@app.route("/mapa")
@login_required
def view_mapa():
    return render_template("mapa.html", active_page="mapa")


@app.route("/ranchos")
@login_required
def view_ranchos():
    return render_template("ranchos.html", active_page="ranchos")


@app.route("/bovinos")
@login_required
def view_bovinos():
    return render_template("bovinos.html", active_page="bovinos")


@app.route("/alertas")
@login_required
def view_alertas():
    return render_template("alertas.html", active_page="alertas")


# VISTAS EXCLUSIVAS DE ADMINISTRADOR (Métricas y Reportes)
@app.route("/metricas")
@login_required
@roles_required("administrador")
def view_metricas():
    return render_template("metricas.html", active_page="metricas")


@app.route("/reportes")
@login_required
@roles_required("administrador")
def view_reportes():
    return render_template("reportes.html", active_page="reportes")


# VISTAS TÉCNICAS (Admin y Técnico)
@app.route("/dispositivos")
@login_required
@roles_required("administrador", "tecnico_mantenimiento")
def view_dispositivos():
    return render_template("dispositivos.html", active_page="dispositivos")


@app.route("/conexion")
@login_required
@roles_required("administrador", "tecnico_mantenimiento")
def view_conexion():
    return render_template("conexion.html", active_page="conexion")


@app.route("/simulador")
@login_required
@roles_required("administrador", "tecnico_mantenimiento")
def view_simulador():
    return render_template("simulador.html", active_page="simulador")


# ============================================================
#  API REST SEGURA (FILTRADA POR ROL Y MULTI-RANCHOS)
# ============================================================

@app.route("/api/dashboard")
@login_required
def api_dashboard():
    return jsonify(db.resumen_dashboard_rol(session["user"]))


@app.route("/api/ranchos")
@login_required
def api_ranchos():
    return jsonify(db.listar_ranchos_usuario(session["user"]))


@app.route("/api/bovinos")
@login_required
def api_bovinos():
    return jsonify(db.listar_bovinos_usuario(session["user"]))


@app.route("/api/historial/<int:animal_id>")
@login_required
def api_historial(animal_id):
    horas = int(request.args.get("horas", 24))
    datos = db.historial_animal(animal_id, horas)
    return jsonify(datos)


@app.route("/api/alertas")
@login_required
def api_alertas():
    solo = request.args.get("activas", "false").lower() == "true"
    return jsonify(db.listar_alertas_usuario(session["user"], solo_activas=solo))


@app.route("/api/alertas/atender/<int:alerta_id>", methods=["POST"])
@login_required
def api_atender_alerta(alerta_id):
    ok = db.atender_alerta(alerta_id, session["user"]["id"])
    return jsonify({"ok": ok, "id": alerta_id})


@app.route("/api/dispositivos")
@login_required
def api_dispositivos():
    return jsonify(db.listar_dispositivos())


@app.route("/api/potreros")
@login_required
def api_potreros():
    return jsonify(db.listar_potreros(session["user"]))


# ============================================================
#  ENDPOINTS DE ANALÍTICA Y DESCARGA DE REPORTES
# ============================================================

@app.route("/api/metricas")
@login_required
@roles_required("administrador")
def api_metricas():
    return jsonify(db.metricas_analiticas_admin())


@app.route("/api/reportes/actividad")
@login_required
@roles_required("administrador")
def api_reportes_actividad():
    rancho_id = request.args.get("rancho_id", type=int)
    datos = db.reporte_actividad_animales(rancho_id)
    return jsonify(datos)


@app.route("/api/reportes/descargar/csv")
@login_required
@roles_required("administrador")
def descargar_reporte_csv():
    rancho_id = request.args.get("rancho_id", type=int)
    datos = db.reporte_actividad_animales(rancho_id)

    output = io.StringIO()
    writer = csv.writer(output, delimiter=",")
    # Encabezados
    writer.writerow([
        "ID Animal", "Arete SAGARPA", "Nombre", "Raza", "Sexo", "Peso (kg)",
        "Rancho", "Potrero", "Collar LoRa", "Bateria (%)", "Total Reportes",
        "Distancia Estimada (km)", "Velocidad Max (km/h)", "Velocidad Promedio (km/h)",
        "Ultima Posicion GPS", "Ultima Conexion UTC", "Estado Vigencia"
    ])

    for fila in datos:
        writer.writerow([
            fila["animal_id"], fila["arete"], fila["nombre"], fila["raza"], fila["sexo"], fila["peso_kg"],
            fila["rancho"], fila["potrero"], fila["collar"], fila["bateria_pct"], fila["total_reportes"],
            fila["distancia_km"], fila["vel_max_kmh"], fila["vel_prom_kmh"],
            fila["ultima_posicion"], fila["ultima_conexion"], fila["estado_vigencia"]
        ])

    csv_data = output.getvalue()
    nombre_archivo = f"reporte_actividad_bovinos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={nombre_archivo}"}
    )


@app.route("/api/reportes/descargar/json")
@login_required
@roles_required("administrador")
def descargar_reporte_json():
    rancho_id = request.args.get("rancho_id", type=int)
    datos = db.reporte_actividad_animales(rancho_id)
    nombre_archivo = f"reporte_actividad_bovinos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    response = jsonify(datos)
    response.headers["Content-Disposition"] = f"attachment; filename={nombre_archivo}"
    return response


# ============================================================
#  INGESTA DE TELEMETRÍA (FIRMWARE / SIMULADOR)
# ============================================================

@app.route("/api/lectura", methods=["POST"])
def api_lectura():
    if not request.is_json:
        abort(400, "Se esperaba JSON")
    data = request.json
    required = ["animal_id", "lat", "lon"]
    for key in required:
        if key not in data:
            abort(400, f"Campo requerido: {key}")
    lat, lon = float(data["lat"]), float(data["lon"])
    if lat == 0.0 and lon == 0.0:
        return jsonify({"ok": False, "error": "Coordenadas 0,0 rechazadas (GPS sin fix)"}), 422
    new_id = db.insertar_lectura(
        animal_id      = int(data["animal_id"]),
        lat            = lat,
        lon            = lon,
        altitud        = float(data.get("altitud", 0)),
        velocidad      = float(data.get("velocidad", 0)),
        hdop           = float(data.get("hdop", 1.0)),
        satelites      = int(data.get("satelites", 0)),
        bateria        = int(data.get("bateria", 100)),
        rssi           = int(data.get("rssi", -100)),
        dispositivo_id = data.get("dispositivo_id")
    )
    return jsonify({"ok": True, "lectura_id": new_id}), 201


if __name__ == "__main__":
    print("=" * 60)
    print("  BOVINOS IoT RBAC + ANALYTICS — Valle del Mezquital")
    print("  Servidor en: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
