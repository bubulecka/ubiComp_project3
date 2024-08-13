# Simple MQTT-based endpoint metadata management client
# Receives data from Arduino sensors via serial port
# Sends them to Mosquitto server
from datetime import datetime, timezone
import json
import signal

import serial #pip install pyserial
import paho.mqtt.client as mqtt #pip install paho-mqtt

MY_MQTT_HOST = "mosquitto"
MY_MQTT_PORT = 1883
TOPIC = "/robot/sensors"

LOCAL_SERIAL_PORT = "/dev/ttyACM0"
LOCAL_BAUD = 115200

class DataCollectionClient:

    def __init__(self, client):
        self.client = client
        self.client.on_message = self.on_message
        self.data_collection_topic = TOPIC

    def connect_to_server(self):
        print(f'Connecting to MQTT server at {MY_MQTT_HOST}:{MY_MQTT_PORT}', flush=True)
        self.client.connect(MY_MQTT_HOST, MY_MQTT_PORT, 60)
        print(f'Successfully connected to MQTT server at {MY_MQTT_HOST}:{MY_MQTT_PORT}', flush=True)

    def disconnect_from_server(self):
        print(f'Disconnecting from MQTT server at {MY_MQTT_HOST}:{MY_MQTT_PORT}...', flush=True)
        self.client.loop_stop()
        self.client.disconnect()
        print(f'Successfully disconnected from MQTT server at {MY_MQTT_HOST}:{MY_MQTT_PORT}', flush=True)

    def on_message(client, userdata, message):
        print(f'<-- Message received from MQTT server: topic "{message.topic}":\n{str(message.payload.decode("utf-8"))}', flush=True)

def main():
    # Open serial port
    try:
        ser = serial.Serial(LOCAL_SERIAL_PORT, LOCAL_BAUD)
    except serial.SerialException:
        print(f"Error connecting to serial port {LOCAL_SERIAL_PORT} at {LOCAL_BAUD}.", flush=True)
        return

    # Initiate MQTT server connection
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    data_collection_client = DataCollectionClient(client)
    data_collection_client.connect_to_server()
    client.loop_start()

    # Send data samples in loop
    listener = SignalListener()
    print(f'@{datetime.now(timezone.utc)} Starting to listen...', flush=True)
    while listener.keepRunning:
        data = ser.readline().decode().strip()

        if data.startswith('{'):
            payload = json.dumps(data)
            result = data_collection_client.client.publish(topic=data_collection_client.data_collection_topic, payload=payload)
            if result.rc != 0:
                print('Server connection lost, attempting to reconnect', flush=True)
                data_collection_client.connect_to_server()
            #else:
                #print(f'--> Sent message on topic "{data_collection_client.data_collection_topic}":\n{payload}', flush=True)

    data_collection_client.disconnect_from_server()



class SignalListener:
    keepRunning = True

    def __init__(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, signum, frame):
        print(f'@{datetime.now(timezone.utc)} Shutting down...', flush=True)
        self.keepRunning = False


if __name__ == '__main__':
    main()
