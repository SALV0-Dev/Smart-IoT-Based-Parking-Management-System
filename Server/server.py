from flask import Flask, request, jsonify, render_template
from InlfuxDB import comprobar_estado_parking, entrada_parking, salida_parking
from influxdb_client import InfluxDBClient
from prediction import predict_next_hour

# Configuración de la conexión a InfluxDB
url = "https://eu-central-1-1.aws.cloud2.influxdata.com"  # Cambia esto según tu configuración
token = "oQH0mexrvpwEuqmz3Mll9w9U_clVYT7j2AAHwl1WcfxbKGsLJLNVv2Un8E74r73wxKm4UdGuN-5xZlXsClAkAQ=="  # Reemplaza con tu token de acceso
org = "ParkingMonitoringTeam"  # Reemplaza con tu organización
database = "Parking2"  # Reemplaza con el bucket o base de datos

# Inicializar cliente de InfluxDB
client = InfluxDBClient(url=url, token=token, org=org)

# Servidor
app = Flask(__name__)

@app.route('/')
def index():
    """Mostrar la página web del parking."""
    try:
        # Obtener estado del parking y número de vehículos dentro
        _, numero_vehiculos = comprobar_estado_parking()

        # Obtener la predicción de la próxima hora
        prediccion = predict_next_hour()

        return render_template(
            'index.html', 
            numero_vehiculos=numero_vehiculos, 
            prediccion=prediccion
        )
    
    except Exception as e:
        return f"Error al cargar la página principal: {e}"

@app.route('/submit', methods=['POST'])
def procesar_matricula():
    """Procesar una nueva matrícula recibida del ESP32."""
    try:
        # Leer datos del microcontrolador
        data = request.form
        if not data:
            return jsonify({"status": "error", "message": "Datos no enviados en el cuerpo de la solicitud."}), 400

        matricula = data.get('matricula')
        tipo = data.get('tipo')  # "entrada" o "salida"
        puerta = data.get('puerta')  # Puerta por donde entra/sale

        if not matricula or not tipo or not puerta:
            return jsonify({"status": "error", "message": "Faltan datos obligatorios: matrícula, tipo o puerta."}), 400
        
        if tipo not in ["entrada", "salida"]:
            return jsonify({"status": "error", "message": "El tipo debe ser 'entrada' o 'salida'."}), 400

        # Obtener estado del parking y número de vehículos dentro
        vehiculos_dentro, numero_vehiculos = comprobar_estado_parking()
        max_plazas = 20

        if tipo == "entrada":
            if numero_vehiculos >= max_plazas:
                return jsonify({"status": "error", "message": "Parking lleno"}), 400

            if matricula in vehiculos_dentro:
                return jsonify({"status": "error", "message": f"La matrícula {matricula} ya está dentro del parking."}), 400

            entrada_parking(matricula, tipo, puerta)
            return jsonify({
                "status": "success",
                "message": f"La matrícula {matricula} ha entrado por la puerta {puerta}",
                "vehiculos_dentro": numero_vehiculos + 1
            })
        
        elif tipo == "salida":
            if matricula not in vehiculos_dentro:
                return jsonify({"status": "error", "message": f"La matrícula {matricula} no está dentro del parking."}), 400
            
            tiempo_estacionado, coste_total = salida_parking(matricula, tipo, puerta)
            
            return jsonify({
                "status": "success",
                "tiempo_estacionado": tiempo_estacionado,
                "coste_total": coste_total,
                "message": f"La matrícula {matricula} ha salido por la puerta {puerta}",
                "vehiculos_dentro": numero_vehiculos - 1
            })
    
    except Exception as e:
        return jsonify({"status": "error", "message": f"No se pudo procesar la solicitud: {e}"}), 500

@app.route('/status', methods=['GET'])
def obtener_estado_parking():
    """Obtener el estado del parking como JSON."""
    try:
        # Consultar el estado del parking
        vehiculos_dentro, numero_vehiculos = comprobar_estado_parking()
        prediccion = predict_next_hour()

        return jsonify({
            "vehiculos_dentro": vehiculos_dentro, 
            "numero_vehiculos": numero_vehiculos, 
            "prediccion": prediccion
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al obtener el estado del parking: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)