from river import time_series
import threading
from InlfuxDB import comprobar_estado_parking
import time
from datetime import datetime, timedelta

# Inicializar modelo Holt-Winters
model = time_series.HoltWinters(alpha=0.3, beta=0.1, gamma=0.1, seasonality=24, multiplicative=False)

# Almacenar ocupaciones por franja horaria
hourly_data = []

# Inicializar hourly_data con datos simulados
def initialize_hourly_data():
    """Inicializar hourly_data con datos simulados de las últimas 24 horas."""
    now = datetime.now()
    hourly_data.clear()

    for i in range(24):
        hour = now - timedelta(hours=i)
        hour = hour.replace(minute=0, second=0, microsecond=0)
        occupancy = 10 + (i % 5)  # Ejemplo de ocupación: 10 + (variación cíclica)
        hourly_data.append((hour, occupancy))

def train_model_with_initial_data():
    """Entrenar el modelo con los datos inicializados."""
    for _, vehicles in hourly_data:
        model.learn_one(vehicles)

def collect_data():
    """Recolectar datos de ocupación cada 10 minutos."""
    while True:
        try:
            _, numero_vehiculos = comprobar_estado_parking()

            # Obtener la hora actual redondeada hacia abajo
            now = datetime.now()
            current_hour = now.replace(minute=0, second=0, microsecond=0)

            # Guardar ocupación con la marca de tiempo
            hourly_data.append((current_hour, numero_vehiculos))

            # Limitar el tamaño de los datos para evitar que crezca indefinidamente
            if len(hourly_data) > 24 * 7:  # Máximo de una semana de datos
                hourly_data.pop(0)

        except Exception as e:
            return(f"Error al recolectar datos: {e}")

        # Esperar 10 minutos (600 segundos)
        time.sleep(600)

def update_model():
    """Actualizar el modelo cada hora con el promedio de la última franja horaria."""
    while True:
        try:
            # Obtener la última hora completa
            now = datetime.now()
            last_hour = now - timedelta(hours=1)
            last_hour = last_hour.replace(minute=0, second=0, microsecond=0)

            # Filtrar datos de la última hora
            last_hour_data = [v for t, v in hourly_data if t == last_hour]
            if last_hour_data:
                average_occupancy = sum(last_hour_data) / len(last_hour_data)

                # Entrenar el modelo con el promedio
                model.learn_one(average_occupancy)
                return(f"Modelo actualizado con ocupación promedio {average_occupancy:.2f} para la hora {last_hour}")

        except Exception as e:
            return(f"Error al actualizar el modelo: {e}")

        # Esperar 1 hora (3600 segundos)
        time.sleep(3600)

def predict_next_hour():
    """Predecir la ocupación promedio en la próxima franja horaria."""
    try:
        prediction = model.forecast(1)[0]
        return round(prediction)
    
    except Exception as e:
        return f"Error al predecir el número de vehículos: {e}"

# Llamar a la función de inicialización
initialize_hourly_data()

# Entrenar el modelo con los datos iniciales
train_model_with_initial_data()

# Iniciar hilos
data_thread = threading.Thread(target=collect_data, daemon=True)
model_thread = threading.Thread(target=update_model, daemon=True)

data_thread.start()
model_thread.start()