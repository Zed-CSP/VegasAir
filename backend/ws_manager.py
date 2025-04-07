from fastapi import WebSocket
from typing import List, Dict
import json

class ConnectionManager:
    def __init__(self):
        # Store active connections
        self.active_connections: List[WebSocket] = []
        # Store flight-specific connections
        self.flight_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, flight_id: int = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if flight_id:
            if flight_id not in self.flight_connections:
                self.flight_connections[flight_id] = []
            self.flight_connections[flight_id].append(websocket)

    def disconnect(self, websocket: WebSocket, flight_id: int = None):
        self.active_connections.remove(websocket)
        if flight_id and flight_id in self.flight_connections:
            self.flight_connections[flight_id].remove(websocket)
            if not self.flight_connections[flight_id]:
                del self.flight_connections[flight_id]

    async def broadcast_to_flight(self, flight_id: int, message: dict):
        """Broadcast a message to all connections for a specific flight"""
        if flight_id in self.flight_connections:
            for connection in self.flight_connections[flight_id]:
                try:
                    await connection.send_json(message)
                except:
                    # Remove dead connections
                    self.disconnect(connection, flight_id)

    async def broadcast(self, message: dict):
        """Broadcast a message to all active connections"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Remove dead connections
                self.disconnect(connection)

# Create a global connection manager instance
manager = ConnectionManager() 