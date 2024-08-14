# IoT Stack Project
## Overview
This project showcases an IoT solution with two main components: an Arduino-based keyword spotting system and a Raspberry Pi server setup. The system leverages a machine learning model for keyword recognition and motion detection, integrated with various technologies for data handling and analysis.

### Components
 - Arduino Code: Implements a keyword spotting ML model and provides sensor data to the Raspberry Pi.
 - Raspberry Pi Code: Acts as an IoT server, processing data received from the Arduino and interacting with various services.

## Arduino Code
The Arduino code performs keyword spotting using a machine learning model to recognize the keywords and react to them. The functionality is as follows:
- `"hello"`: Sends sensor data via serial port to the Raspberry Pi.
- `"stop"`: Stops sending data.

## Raspberry Pi Code
The Raspberry Pi setup consists of multiple components working together to process the data received from the Arduino. The custom Python scripts include:

1. `client-mqtt`
Function: Receives sensor data from the Arduino via the serial port and publishes it to an MQTT broker (Mosquitto).
Dependencies: paho-mqtt, pyserial
2. `model-inference`
Function: Reads data from the InfluxDB, processes it using a TensorFlow Lite model to recognize an "up-down" motion, and sends notifications to a WebSocket server if such motion is detected.
Dependencies: tensorflow, paho-mqtt, influxdb-client
3. `server-websocket`
Function: Handles WebSocket connections and broadcasts messages to connected clients based on notifications from the model-inference component.
Dependencies: websockets, asyncio

## Supporting Services
- IOTstack: Tool for setting up docker containers.
- Portainer: Container management software that includes UI.
- MQTT Broker: Mosquitto, used for message passing between components.
- Node-RED: Transfers data from MQTT to InfluxDB.
- InfluxDB: Database that stores time-series data.
- Grafana: Visualizes the data stored in InfluxDB.
