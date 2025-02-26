from influxdb_client import InfluxDBClient, Point
import time
from datetime import datetime, timezone

# Configuración de la conexión a InfluxDB
url = "https://eu-central-1-1.aws.cloud2.influxdata.com"  # Cambia esto según tu configuración
token = "L5nqlhoL1qbw3tWOt1nh_HjRlqwUZ8Neqt6kqyvjvDv4iRR02bESGzrvEZs3A3jado_WhvPZMtf71QtxTOk9Rw=="  # Reemplaza con tu token de acceso
org = "ParkingMonitoringTeam"      # Reemplaza con tu organización
database = "Parking1"       # Reemplaza con el bucket o base de datos


def registrar_evento_parking_con_puerta(matricula, tipo, puerta, client, org, database):
    """
    Registra un evento de entrada o salida con la puerta en InfluxDB.
    
    :param matricula: Matrícula del vehículo (str).
    :param tipo: Tipo de evento ("entrada" o "salida") (str).
    :param puerta: Número o identificador de la puerta (str).
    :param client: Cliente de InfluxDB (InfluxDBClient).
    :param org: Organización de InfluxDB (str).
    :param database: Base de datos o bucket en InfluxDB (str).
    :return: Mensaje de éxito o error.
    """
    try:
        # Validar tipo de evento
        if tipo not in ["entrada", "salida"]:
            return "El tipo de evento debe ser 'entrada' o 'salida'."
        
        # Inicializar el API para escritura
        write_api = client.write_api()
        
        # Crear un punto de datos
        point = Point("parking_events") \
            .field("matricula", matricula) \
            .tag("tipo", tipo) \
            .tag("puerta", puerta)
        
        # Escribir el punto en InfluxDB
        write_api.write(bucket=database, org=org, record=point)
        
        return f"Evento '{tipo}' para la matrícula {matricula} registrado con éxito en la puerta {puerta}."
    
    except Exception as e:
        return f"Error al registrar el evento: {e}"

def calcular_tiempo_en_parking(matricula, client, org, database):
    """
    Calcula el tiempo que un vehículo ha estado estacionado.

    :param matricula: Matrícula del vehículo (str).
    :param client: Cliente de InfluxDB (InfluxDBClient).
    :param org: Organización de InfluxDB (str).
    :param database: Base de datos o bucket en InfluxDB (str).
    :return: Tiempo en minutos o mensaje de error.
    """
    query_api = client.query_api()

    # Consulta para obtener la fecha del último valor con tipo=entrada
    query_entrada = f'''
        from(bucket: "{database}")
          |> range(start: 0)
          |> filter(fn: (r) => r["_measurement"] == "parking_events")
          |> filter(fn: (r) => r["tipo"] == "entrada")
          |> filter(fn: (r) => r["_field"] == "matricula" and r["_value"] == "{matricula}")
          |> group(columns: [])  // Agrupa todos los resultados en una sola tabla
          |> sort(columns: ["_time"], desc: true)
          |> limit(n: 1)
    '''

    try:
        # Obtener fecha de entrada
        result_entrada = query_api.query(org=org, query=query_entrada)
        fecha_entrada = None
        if result_entrada and len(result_entrada) > 0:
            record_entrada = result_entrada[0].records[0]
            fecha_entrada = record_entrada.get_time()
        
        # Obtener fecha actual del servidor como fecha de salida
        fecha_salida = datetime.now(timezone.utc)
        
        # Verificar si ambas fechas existen
        if fecha_entrada and fecha_salida:
            # Calcular diferencia en minutos
            diferencia_minutos = (fecha_salida - fecha_entrada).total_seconds() / 60
            return diferencia_minutos
        else:
            return "No se encontraron registros suficientes para calcular el tiempo."

    except Exception as e:
        return f"Error al calcular el tiempo en el parking: {e}"

# Inicializar cliente de InfluxDB
client = InfluxDBClient(url=url, token=token, org=org)

# Ejemplo de uso
matricula = "1234ABC"
tipo_evento = "entrada"  # Puede ser "entrada" o "salida"
puerta = "P1"  # Identificador de la puerta, por ejemplo, "P1" o "Puerta Norte"

resultado = registrar_evento_parking_con_puerta(matricula, tipo_evento, puerta, client, org, database)
print(resultado)

tiempo_estacionado = calcular_tiempo_en_parking(matricula, client, org, database)
if isinstance(tiempo_estacionado, float):
    print(f"Tiempo en el parking para la matrícula {matricula}: {tiempo_estacionado} minutos")
else:
    print(tiempo_estacionado)

# Cerrar cliente
client.close()