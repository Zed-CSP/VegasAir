import { useEffect, useRef, useCallback, useState } from 'react';

const useWebSocket = (flightId, onMessage) => {
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);
  const reconnectAttempts = useRef(0);
  const [isConnected, setIsConnected] = useState(false);
  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_DELAY = 3000; // 3 seconds

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    if (ws.current?.readyState === WebSocket.CONNECTING) {
      console.log('WebSocket connection in progress');
      return;
    }

    console.log(`Attempting to connect to WebSocket for flight ${flightId}...`);
    
    // Create WebSocket connection
    try {
      ws.current = new WebSocket(`ws://localhost:8000/api/v1/ws/flight/${flightId}`);

      // Connection opened
      ws.current.onopen = () => {
        console.log(`WebSocket Connected for flight ${flightId}`);
        setIsConnected(true);
        reconnectAttempts.current = 0; // Reset reconnect attempts on successful connection
      };

      // Listen for messages
      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log(`WebSocket message received for flight ${flightId}:`, data);
          onMessage(data);
        } catch (error) {
          console.error(`Error parsing WebSocket message for flight ${flightId}:`, error, 'Raw message:', event.data);
        }
      };

      // Connection closed
      ws.current.onclose = (event) => {
        console.log(`WebSocket Disconnected for flight ${flightId}. Code: ${event.code}, Reason: ${event.reason}`);
        setIsConnected(false);
        
        // Attempt to reconnect if we haven't exceeded max attempts
        if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttempts.current += 1;
          console.log(`Attempting to reconnect for flight ${flightId} (${reconnectAttempts.current}/${MAX_RECONNECT_ATTEMPTS})...`);
          
          // Clear any existing timeout
          if (reconnectTimeout.current) {
            clearTimeout(reconnectTimeout.current);
          }
          
          // Set new timeout for reconnection
          reconnectTimeout.current = setTimeout(() => {
            connect();
          }, RECONNECT_DELAY);
        } else {
          console.log(`Max reconnection attempts reached for flight ${flightId}`);
        }
      };

      // Connection error
      ws.current.onerror = (error) => {
        console.error(`WebSocket error for flight ${flightId}:`, error);
        setIsConnected(false);
      };
    } catch (error) {
      console.error(`Error creating WebSocket connection for flight ${flightId}:`, error);
      setIsConnected(false);
    }
  }, [flightId, onMessage]);

  useEffect(() => {
    if (flightId) {
      connect();
    } else {
      console.warn('No flightId provided to useWebSocket hook');
    }

    // Cleanup on unmount
    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        console.log(`Closing WebSocket connection for flight ${flightId}`);
        ws.current.close();
      }
    };
  }, [connect, flightId]);

  // Function to send messages
  const sendMessage = useCallback((message) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      try {
        const messageString = JSON.stringify(message);
        console.log(`Sending WebSocket message for flight ${flightId}:`, message);
        ws.current.send(messageString);
      } catch (error) {
        console.error(`Error sending WebSocket message for flight ${flightId}:`, error);
      }
    } else {
      console.warn(`Cannot send message - WebSocket is not connected for flight ${flightId}`);
    }
  }, [flightId]);

  return { sendMessage, isConnected };
};

export default useWebSocket; 