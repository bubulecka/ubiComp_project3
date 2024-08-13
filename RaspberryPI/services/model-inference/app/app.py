import signal
from datetime import datetime, timezone
import time

import asyncio
import websockets
import numpy as np
import tflite_runtime.interpreter as tflite
from influxdb import InfluxDBClient

DB_HOST = "influxdb"
DB_PORT = 8086
DB_USERNAME = ''
DB_PASSWORD = ''
DB_NAME = 'sensor_data'

NANOSECONDS_DELAY = 5_000_000_000
SAMPLES = 125
FRAME_SIZE = SAMPLES*3
QUERY = f'SELECT "accX","accY","accZ" FROM sensor_data WHERE time > now() - 500ms LIMIT {SAMPLES}'

TAG_INDEX = 3
TAG_THRESHOLD = 0.7
MODEL_PATH = 'ei-my-arduino-motion-project-simple-classifier-tensorflow-lite-float32-model.lite'
TAGS = ["circle", "idle", "left-right", "up-down"]

WEBSOCKET_HOST = "server-websocket"
WEBSOCKET_PORT = 8765
WEBSOCKET_SERVER_URL = f'ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}'

def start_action_simulate():
    print("INFO: Here I start an action, like start blinking.", flush=True)

async def sendNotification():
    print(f"INFO: Sending notification.", flush=True)
    async with websockets.connect(WEBSOCKET_SERVER_URL) as websocket:
        await websocket.send("Move!")
        #response = await websocket.recv()
        await websocket.close()

def main():
    print()
    print(f"@{datetime.now(timezone.utc)} INFO: Starting up.", flush=True)

    # Load TFLite model and allocate tensors.
    interpreter = tflite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()

    # Get input and output tensors.
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    print(f"INFO: Input shape: {input_details[0]['shape']}", flush=True)
    print(f"INFO: Output shape tags: {TAGS}", flush=True)

    # open InfluxDB connection and prepare query
    print("INFO: Setting up the database connection.", flush=True)
    dbClient = InfluxDBClient(host=DB_HOST, port=DB_PORT, username=DB_USERNAME, password=DB_PASSWORD, database=DB_NAME)

    print("INFO: Starting inference...", flush=True)
    timestamp = time.time_ns()
    listener = SignalListener()
    while listener.keepRunning:

        # Read data from database
        features = []
        try:
            result = dbClient.query(QUERY)
        except Exception as e:
            print(f"@{datetime.now(timezone.utc)} ERROR: Error connecting to InfluxDB: {e}", flush=True)
            continue

        if (not result):
            continue

        # Extract & format only the data we need for inference
        for series in result.get_points():
                features.append(series['accX'])
                features.append(series['accY'])
                features.append(series['accZ'])

        # Size defined by the output_details = (accX, accY, accZ)x13
        if (len(features) < FRAME_SIZE):
            continue

        #print(features, flush=True)
        # Convert the feature list to a NumPy array of type float32
        np_features = np.array(features, dtype=np.float32)

        # Add dimension to input sample (TFLite model expects (# samples, data))
        np_features = np.expand_dims(np_features, axis=0)

        # Create input tensor out of raw features
        interpreter.set_tensor(input_details[0]['index'], np_features)

        # Run inference
        interpreter.invoke()

        # output_details[0]['index'] = the index which provides the input
        output_data = interpreter.get_tensor(output_details[0]['index'])

        # Print the results of inference
        max_index = np.argmax(output_data)
        max_value = np.max(output_data)
        if (max_index == TAG_INDEX and max_value > TAG_THRESHOLD):
            time_new = time.time_ns()
            if (time_new - timestamp > NANOSECONDS_DELAY):
                timestamp = time.time_ns()
                tag_with_highest_output = TAGS[max_index]
                print(f"@{datetime.now(timezone.utc)} INFO: Infered {tag_with_highest_output}", flush=True)
                start_action_simulate()
                asyncio.get_event_loop().run_until_complete(sendNotification())

    dbClient.close()


class SignalListener:
    keepRunning = True

    def __init__(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, signum, frame):
        print(f'@{datetime.now(timezone.utc)} INFO: Shutting down...', flush=True)
        self.keepRunning = False


if __name__ == '__main__':
    main()
