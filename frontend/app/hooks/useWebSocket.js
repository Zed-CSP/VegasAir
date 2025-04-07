import { useEffect, useRef, useCallback } from 'react';

const useWebSocket = (flightId, onMessage) => {
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);
  const reconnectAttempts = useRef(0);
  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_DELAY = 3000; // 3 seconds

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Create WebSocket connection
    ws.current = new WebSocket(`ws://localhost:8000/api/v1/ws/flight/${flightId}`);

    // Connection opened
    ws.current.onopen = () => {
      console.log('WebSocket Connected');
      reconnectAttempts.current = 0; // Reset reconnect attempts on successful connection
    };

    // Listen for messages
    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);
        onMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    // Connection closed
    ws.current.onclose = () => {
      console.log('WebSocket Disconnected');
      
      // Attempt to reconnect if we haven't exceeded max attempts
      if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts.current += 1;
        console.log(`Attempting to reconnect (${reconnectAttempts.current}/${MAX_RECONNECT_ATTEMPTS})...`);
        
        // Clear any existing timeout
        if (reconnectTimeout.current) {
          clearTimeout(reconnectTimeout.current);
        }
        
        // Set new timeout for reconnection
        reconnectTimeout.current = setTimeout(() => {
          connect();
        }, RECONNECT_DELAY);
      } else {
        console.log('Max reconnection attempts reached');
      }
    };

    // Connection error
    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }, [flightId, onMessage]);

  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  // Function to send messages
  const sendMessage = useCallback((message) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      try {
        ws.current.send(JSON.stringify(message));
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
      }
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
    }
  }, []);

  return { sendMessage };
};

export default useWebSocket; 