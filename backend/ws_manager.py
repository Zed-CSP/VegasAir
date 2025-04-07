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
            print(f"New connection added for flight {flight_id}. Total connections: {len(self.flight_connections[flight_id])}")

    def disconnect(self, websocket: WebSocket, flight_id: int = None):
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            
            if flight_id and flight_id in self.flight_connections:
                if websocket in self.flight_connections[flight_id]:
                    self.flight_connections[flight_id].remove(websocket)
                    print(f"Connection removed for flight {flight_id}. Remaining connections: {len(self.flight_connections[flight_id])}")
                
                if not self.flight_connections[flight_id]:
                    del self.flight_connections[flight_id]
                    print(f"No more connections for flight {flight_id}")
        except Exception as e:
            print(f"Error in disconnect: {e}")

    async def broadcast_to_flight(self, flight_id: int, message: dict):
        """Broadcast a message to all connections for a specific flight"""
        if flight_id in self.flight_connections:
            dead_connections = []
            for connection in self.flight_connections[flight_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting to connection: {e}")
                    dead_connections.append(connection)
            
            # Clean up dead connections
            for dead_conn in dead_connections:
                self.disconnect(dead_conn, flight_id)

    async def broadcast(self, message: dict):
        """Broadcast a message to all active connections"""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to connection: {e}")
                dead_connections.append(connection)
        
        # Clean up dead connections
        for dead_conn in dead_connections:
            self.disconnect(dead_conn)

# Create a global connection manager instance
manager = ConnectionManager() 