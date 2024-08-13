import asyncio
import websockets
import json
from datetime import datetime, timezone

HOST = "0.0.0.0"
PORT = 8765

# Store connected clients
clients = set()

# Function to send notifications to all connected clients
async def send_notification(message):
    if clients:  # Check if there are connected clients
        await asyncio.wait([client.send(message) for client in clients])

# WebSocket handler
async def websocket_handler(websocket, path):
    # Register client
    clients.add(websocket)
    try:
        # Wait for incoming messages indefinitely
        async for message in websocket:
            print(f"@{datetime.now(timezone.utc)} INFO Received message: {message}", flush=True)
            # await websocket.send(json.dumps("Message Received!"))
            # Process the message if needed

    finally:
        # Unregister client on disconnect
        clients.remove(websocket)

print(f"INFO: Starting up websocket server on {HOST}:{PORT}.", flush=True)

# Start WebSocket server
start_server = websockets.serve(websocket_handler, HOST, PORT)

# Start event loop
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
