#include <UltrasonicSensor.h>
#include <LiquidCrystal_I2C.h>
#include <Keypad.h>
#include <WiFi.h>
#include <WiFiManager.h>          // https://github.com/tzapu/WiFiManager WiFi Configuration Magic
#include <HTTPClient.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

// Define para el identificador único de la puerta
#define PUERTA_ID 1 // Cambia este número según la puerta

// Barreras
Servo servo_entrada;
Servo servo_salida;
int servoPinEntrada = 14;
int servoPinSalida = 27;

// Sensor de proximidad
UltrasonicSensor ultrasonicEntrada(13, 12); // Sensor de entrada
UltrasonicSensor ultrasonicSalida(33, 32);  // Sensor de salida
const int thresholdDistance = 4; // Distancia límite en cm

// Servidor HTTP
const char* serverURL = "http://172.20.10.4:5000/submit"; // Reemplazar con tu ordenador mobile hotspot ip

// Panel LCD
int lcdColumns = 16;
int lcdRows = 2;
LiquidCrystal_I2C lcd(0x27, lcdColumns, lcdRows);

// Teclado
const byte ROWS = 4;
const byte COLS = 4;
char hexaKeys[ROWS][COLS] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};

byte rowPins[ROWS] = {23, 19, 18, 5}; 
byte colPins[COLS] = {4, 0, 2, 15};   
Keypad customKeypad = Keypad(makeKeymap(hexaKeys), rowPins, colPins, ROWS, COLS);

// Matrícula
String matriculaEntrada = "";
String matriculaSalida = "";

// Estado del sistema
enum SystemState { SYS_IDLE, ENTRADA, SALIDA };
SystemState currentState = SYS_IDLE;

// Tiempo de estacionamiento y coste total
String tiempoEstacionado = "";
String costeTotal = "";

void setup() {
  Serial.begin(115200);

  // WiFi
  WiFiManager wifiManager;
  if (!wifiManager.autoConnect("AutoConnectAP", "password")) {
    Serial.println("No se pudo conectar a Wi-Fi y no se proporcionaron credenciales.");
    delay(3000);
    ESP.restart(); // Reinicia el dispositivo si no se conecta
  }

  Serial.println("Wi-Fi conectado!");

  // Configurar servos
  servo_entrada.setPeriodHertz(50);
  servo_entrada.attach(servoPinEntrada, 500, 2400);
  servo_salida.setPeriodHertz(50);
  servo_salida.attach(servoPinSalida, 500, 2400);

  // Inicializar LCD
  lcd.init();
  lcd.backlight();
  lcd.clear();
}

void loop() {
  // Medir distancia con ambos sensores de proximidad
  int distanciaEntrada = ultrasonicEntrada.distanceInCentimeters();
  int distanciaSalida = ultrasonicSalida.distanceInCentimeters();
  delay(200);

  switch (currentState) {
    case SYS_IDLE:
      checkSensorEntrada(distanciaEntrada);
      checkSensorSalida(distanciaSalida);
      break;

    case ENTRADA:
      handleKeypadEntrada(distanciaEntrada);
      break;

    case SALIDA:
      handleKeypadSalida(distanciaSalida);
      break;
  }
}

// Verificar si un vehículo está en el sensor de entrada
void checkSensorEntrada(int distanciaEntrada) {
  if (distanciaEntrada <= thresholdDistance) {
    currentState = ENTRADA;
  }
}


// Verificar si un vehículo está en el sensor de salida
void checkSensorSalida(int distanciaSalida) {
  if (distanciaSalida <= thresholdDistance) {
    currentState = SALIDA;
  }
}

// Manejar la entrada con el teclado
void handleKeypadEntrada(int distanciaEntrada) {
  handleKeypad(true, distanciaEntrada, servo_entrada, matriculaEntrada);
  if (distanciaEntrada > thresholdDistance && matriculaEntrada.length() == 0) {
    currentState = SYS_IDLE; // Volver al estado inactivo cuando se libera la entrada
  }
}

// Manejar la salida con el teclado
void handleKeypadSalida(int distanciaSalida) {
  handleKeypad(false, distanciaSalida, servo_salida, matriculaSalida);
  if (distanciaSalida > thresholdDistance && matriculaSalida.length() == 0) {
    currentState = SYS_IDLE; // Volver al estado inactivo cuando se libera la salida
  }
}

void handleKeypad(bool isEntrada, int distancia, Servo& servo, String& matricula) {
  static bool isLCDOn = false;

  if (!isLCDOn) {
    isLCDOn = true;
    lcd.backlight();
    lcd.clear();
    lcd.setCursor(3, 0);
    lcd.print("Matricula:");
  }

  char customKey = customKeypad.getKey();
  if (customKey) {
    if (customKey == '*') { // Borrar último caracter en la matrícula
      if (matricula.length() > 0) {
        matricula.remove(matricula.length() - 1);
        updateLCDWithMatricula(matricula);
      }
    } else if (customKey == '#') { // Validar y enviar matrícula
      if (matricula.length() == 6) {
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Enviando...");
        delay(200);
        enviarMatricula(matricula, isEntrada, servo);
      } else {
        showError("Matricula 6 dig.");
      }
    } else { // Añadir carácter a la matrícula
      matricula += customKey;
      updateLCDWithMatricula(matricula);
    }
  }

  // Restablecer LCD y servo si no hay matrícula activa y el vehículo se aleja
  if (distancia > thresholdDistance && matricula.isEmpty()) {
    resetLCDAndServo(isLCDOn, matricula, servo);
  }
}

void showError(const char* message) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Error");
  lcd.setCursor(0, 1);
  lcd.print(message);
  delay(2000);
  lcd.clear();
  lcd.setCursor(3, 0);
  lcd.print("Matricula:");
}

void updateLCDWithMatricula(const String& matricula) {
  lcd.setCursor(0, 1);
  lcd.print("                "); // Limpiar línea
  lcd.setCursor(0, 1);
  lcd.print(matricula);
}

void resetLCDAndServo(bool& isLCDOn, String& matricula, Servo& servo) {
  isLCDOn = false;
  lcd.clear();
  lcd.noBacklight();
  matricula = "";
  servo.write(0); // Cerrar barrera
}

void enviarMatricula(String& matricula, bool isEntrada, Servo& servo) {
    if (enviarSolicitudAlServidor(matricula, isEntrada, tiempoEstacionado, costeTotal)) {
        // Procesar éxito
        handleSuccessfulEntryOrExit(isEntrada, servo, matricula, tiempoEstacionado, costeTotal);
    }
}

bool enviarSolicitudAlServidor(String& matricula, bool isEntrada, String& tiempoEstacionado, String& costeTotal) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi no conectado.");
        showError("Sin WiFi");
        return false;
    }

    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");

    // Construir el payload
    String payload = "puerta=" + String(PUERTA_ID) + "&matricula=" + matricula + "&tipo=" + (isEntrada ? "entrada" : "salida");

    // Enviar la solicitud POST
    int httpResponseCode = http.POST(payload);
    DynamicJsonDocument doc(1024);
    String response = http.getString();
    deserializeJson(doc, response);

    if (httpResponseCode == 200) {
        Serial.println("Respuesta del servidor: " + response);

        // Procesar respuesta en caso de salida
        if (!isEntrada) {
            tiempoEstacionado = doc["tiempo_estacionado"].as<String>();
            costeTotal = doc["coste_total"].as<String>();
        }

        http.end();
        return true;

    } else if (isEntrada && httpResponseCode == 400 && doc["message"].as<String>() == "Parking lleno") {
        showError("Parking lleno");
        Serial.println("Respuesta del servidor: " + response);
        matricula = "";
        http.end();
        return false;

    } else {
        showError("Servidor");
        Serial.printf("Error: Código HTTP %d\n", httpResponseCode);
        matricula = "";
        http.end();
        return false;
    }
}

void handleSuccessfulEntryOrExit(bool isEntrada, Servo& servo, String& matricula, String& tiempoEstacionado, String& costeTotal) {
    if (isEntrada) {
        lcd.clear();
        lcd.setCursor(3, 0);
        lcd.print("Bienvenido");
        delay(1000);
        servo.write(90); // Abrir barrera
        delay(3000);
    } else {
        // Mostrar tiempo y coste
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Tiempo:");
        lcd.setCursor(0, 1);
        lcd.print(tiempoEstacionado + " min");
        delay(2000);

        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Coste:");
        lcd.setCursor(0, 1);
        lcd.print(costeTotal + " EUR");
        delay(2000);

        // Esperar al pago (pulsación de tecla A)
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Para pagar:");
        lcd.setCursor(0, 1);
        lcd.print("Pulse A");
        while (true) {
            char customKey = customKeypad.getKey();
            if (customKey == 'A') {
                lcd.clear();
                lcd.setCursor(4, 0);
                lcd.print("Gracias");
                delay(1000);
                break;
            }
        }

        servo.write(90); // Abrir barrera
        delay(3000);
    }

    matricula = ""; // Reiniciar matrícula
    lcd.clear();
    lcd.setCursor(3, 0);
    servo.write(0); // Cerrar barrera
}