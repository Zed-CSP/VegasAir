import { useEffect, useRef } from 'react';

const useWebSocket = (flightId, onMessage) => {
  const ws = useRef(null);

  useEffect(() => {
    // Create WebSocket connection
    ws.current = new WebSocket(`ws://localhost:8000/api/v1/ws/flight/${flightId}`);

    // Connection opened
    ws.current.onopen = () => {
      console.log('WebSocket Connected');
    };

    // Listen for messages
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    // Connection closed
    ws.current.onclose = () => {
      console.log('WebSocket Disconnected');
    };

    // Cleanup on unmount
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [flightId, onMessage]);

  // Function to send messages
  const sendMessage = (message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  };

  return { sendMessage };
};

export default useWebSocket; 