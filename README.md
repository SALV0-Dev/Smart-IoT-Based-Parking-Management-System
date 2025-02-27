# Smart-IoT-Based-Parking-Management-System

## Overview
The **Smart Parking System** is an IoT-based solution designed to optimize parking management. It enables automated vehicle detection, real-time data collection, and predictive analytics using machine learning. The system integrates an **ESP32** microcontroller with various sensors and a **Flask-based server** connected to an **InfluxDB** database for data storage and analysis.

## Features
- **Automated vehicle detection** using ultrasonic sensors
- **User interaction** via an LCD display and a keypad for license plate input
- **Barrier control** using servo motors
- **Real-time data storage** with InfluxDB
- **REST API** implemented with Flask for communication
- **Web interface** displaying parking status and occupancy predictions
- **Machine learning-based prediction** of parking availability using Holt-Winters model

## System Architecture
### 1. ESP32 Module
- Detects vehicles via ultrasonic sensors
- Collects and processes license plate input
- Sends data to the server via Wi-Fi
- Controls entry and exit barriers

### 2. Flask Server
- Receives data from ESP32 and updates database
- Computes parking costs and processes payments
- Provides REST API endpoints
- Hosts a web interface for real-time monitoring

### 3. Database (InfluxDB)
- Stores parking events (entries/exits)
- Allows historical and real-time queries

### 4. Machine Learning (River)
- Uses Holt-Winters model for predictive analytics
- Forecasts occupancy trends to optimize parking management

## Installation & Setup
### Prerequisites
- Python 3.x
- Flask
- InfluxDB
- ESP32 board with necessary sensors

### Steps
1. **Clone the repository:**
   ```sh
   git clone https://github.com/your-repo/smart-parking-iot.git
   cd smart-parking-iot
   ```
2. **Set up the server:**
   ```sh
   pip install -r requirements.txt
   python server.py
   ```
3. **Flash ESP32 with the Arduino code** (located in the `ESP32/` folder).
4. **Run the web interface** by accessing `http://localhost:5000`.

## API Endpoints
| Endpoint        | Method | Description |
|---------------|--------|------------|
| `/submit`     | POST   | Register vehicle entry/exit |
| `/status`     | GET    | Get current parking status |
| `/`           | GET    | Load web dashboard |

## Future Improvements
- Mobile app integration for reservations and notifications
- Dynamic pricing based on demand
- Energy-efficient solar-powered ESP32 deployment
- AI-based license plate recognition

## Contributors
- **Alejandro Sánchez Bardera**
- **Salvatore Pernice**
- **Jorge Ruíz García**

## License
This project is licensed under the MIT License - see the LICENSE file for details.

