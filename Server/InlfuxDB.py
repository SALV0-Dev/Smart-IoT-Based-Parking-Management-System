from influxdb_client import InfluxDBClient, Point
from datetime import datetime
import pytz
import math

# Configuración de la conexión a InfluxDB
url = "https://eu-central-1-1.aws.cloud2.influxdata.com"  # Cambia esto según tu configuración
token = "oQH0mexrvpwEuqmz3Mll9w9U_clVYT7j2AAHwl1WcfxbKGsLJLNVv2Un8E74r73wxKm4UdGuN-5xZlXsClAkAQ=="  # Reemplaza con tu token de acceso
org = "ParkingMonitoringTeam"  # Reemplaza con tu organización
bucket = "Parking2"  # Reemplaza con el bucket o base de datos

client = InfluxDBClient(url=url, token=token, org=org)
query_api = client.query_api()
write_api = client.write_api()

def comprobar_estado_parking():
    """Comprueba el estado actual del parking"""
    # Consulta para obtener vehículos dentro
    query = f'''
    from(bucket: "{bucket}")
    |> range(start: 0)
    |> filter(fn: (r) => r["_measurement"] == "parking_events")
    |> filter(fn: (r) => r["_field"] == "matricula")
    '''
    try:
        result = query_api.query(org=org, query=query)
        
        # Procesar registros en un diccionario
        parking_status = {}
        for table in result:
            for record in table.records:
                matricula = record["_value"]
                tipo = record["tipo"]

                if matricula not in parking_status:
                    parking_status[matricula] = {"entrada": 0, "salida": 0}
                
                # Incrementar contador de entrada o salida
                if tipo == "entrada":
                    parking_status[matricula]["entrada"] += 1
                elif tipo == "salida":
                    parking_status[matricula]["salida"] += 1

        # Filtrar matrículas que están dentro
        vehiculos_dentro = [
            matricula for matricula, conteo in parking_status.items()
            if conteo["entrada"] > conteo["salida"]
        ]
        numero_vehiculos = len(vehiculos_dentro)

        return vehiculos_dentro, numero_vehiculos

    except Exception as e:
        return f"Error al ejecutar la consulta: {e}"
    
def registrar_evento(matricula, tipo, puerta):
    """Registra un evento en el parking."""
    try:
        point = Point("parking_events") \
            .field("matricula", matricula) \
            .tag("tipo", tipo) \
            .tag("puerta", puerta)
        write_api.write(bucket=bucket, org=org, record=point)

        return f"Evento '{tipo}' registrado para la matrícula {matricula}."
    
    except Exception as e:
        return f"Error al registrar el evento para {matricula}: {e}"
    
def entrada_parking(matricula, tipo, puerta):
    """Registra la entrada de un vehículo."""
    return registrar_evento(matricula, tipo, puerta)

def salida_parking(matricula, tipo, puerta):
    """Registra la salida de un vehículo y calcula el coste."""
    registrar_evento(matricula, tipo, puerta)
    tiempo_estacionado, coste_total = calcular_coste(matricula)
    return tiempo_estacionado, coste_total

def calcular_coste(matricula):
    """Calcula el tiempo y coste de estacionamiento."""
    try:
        # Obtener la última entrada
        query_entrada = f'''
            from(bucket: "{bucket}")
            |> range(start: 0)
            |> filter(fn: (r) => r["_measurement"] == "parking_events")
            |> filter(fn: (r) => r["tipo"] == "entrada")
            |> filter(fn: (r) => r["_field"] == "matricula" and r["_value"] == "{matricula}")
            |> sort(columns: ["_time"], desc: true)
            |> limit(n: 1)
        '''

        result_entrada = query_api.query(org=org, query=query_entrada)
        if not result_entrada:
            return f"No se encontró la última entrada para la matrícula {matricula}."
        fecha_entrada = result_entrada[0].records[0].get_time()

        # Obtener la hora actual como salida
        fecha_salida = datetime.now(pytz.utc)
        tiempo_estacionado = math.floor((fecha_salida - fecha_entrada).total_seconds() / 60)
        coste_minuto = 0.05
        coste_total = round(tiempo_estacionado * coste_minuto, 2)

        return tiempo_estacionado, coste_total

    except Exception as e:
        return f"Error al calcular el coste para {matricula}: {e}"