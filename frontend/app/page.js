'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import SeatGrid from './components/SeatGrid';
import Legend from './components/Legend';
import SelectedSeatModal from './components/SelectedSeatModal';
import CountdownTimer from './components/CountdownTimer';
import useWebSocket from './hooks/useWebSocket';

export default function Home() {
  const [seats, setSeats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSeat, setSelectedSeat] = useState(null);
  const [daysUntilDeparture, setDaysUntilDeparture] = useState(0);
  const [hours, setHours] = useState(0);
  const flightId = 1; // For now, we're only working with flight 1
  
  // Use refs to store pending updates
  const pendingSeatUpdates = useRef(new Map());
  const updateTimeout = useRef(null);

  // Debounced function to apply seat updates
  const applySeatUpdates = useCallback(() => {
    if (pendingSeatUpdates.current.size > 0) {
      setSeats(prevSeats => {
        const newSeats = [...prevSeats];
        pendingSeatUpdates.current.forEach((update, id) => {
          const index = newSeats.findIndex(seat => seat.id === id);
          if (index !== -1) {
            newSeats[index] = { ...newSeats[index], ...update };
          }
        });
        return newSeats;
      });
      pendingSeatUpdates.current.clear();
    }
  }, []);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((data) => {
    if (data.type === "SEAT_UPDATE") {
      // Add the update to pending updates
      pendingSeatUpdates.current.set(data.seat.id, data.seat);
      
      // Clear any existing timeout
      if (updateTimeout.current) {
        clearTimeout(updateTimeout.current);
      }
      
      // Set a new timeout to apply updates
      updateTimeout.current = setTimeout(applySeatUpdates, 100); // 100ms debounce
    } else if (data.type === "TIME_UPDATE") {
      // Update time immediately as it's less frequent
      setDaysUntilDeparture(data.days_until_departure);
      setHours(data.hours);
    }
  }, [applySeatUpdates]);

  // Initialize WebSocket connection
  const { sendMessage } = useWebSocket(flightId, handleWebSocketMessage);

  useEffect(() => {
    fetchFlightData();
    
    // Cleanup function
    return () => {
      if (updateTimeout.current) {
        clearTimeout(updateTimeout.current);
      }
    };
  }, []);

  const fetchFlightData = async () => {
    try {
      // Fetch seats
      const seatsResponse = await axios.get(`http://localhost:8000/api/v1/flights/${flightId}/seats`);
      setSeats(seatsResponse.data);
      
      // Fetch flight details including days until departure
      const flightResponse = await axios.get(`http://localhost:8000/api/v1/flights/${flightId}`);
      setDaysUntilDeparture(flightResponse.data.days_until_departure);
      
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleSeatClick = useCallback((seat) => {
    if (!seat.is_occupied) {
      setSelectedSeat(seat);
    }
  }, []);

  const handlePurchase = useCallback(async () => {
    if (!selectedSeat) return;

    try {
      // Send WebSocket message about the seat being purchased
      sendMessage({
        type: 'SEAT_UPDATE',
        seat: {
          id: selectedSeat.id,
          is_occupied: true,
          sale_price: selectedSeat.base_price // For now, we'll use the base price as the sale price
        }
      });

      // Update local state immediately for better UX
      setSeats(prevSeats =>
        prevSeats.map(seat =>
          seat.id === selectedSeat.id ? { ...seat, is_occupied: true, sale_price: selectedSeat.base_price } : seat
        )
      );

      setSelectedSeat(null);
    } catch (err) {
      console.error('Error purchasing seat:', err);
    }
  }, [selectedSeat, sendMessage]);

  if (loading) return <div className="container">Loading seats...</div>;
  if (error) return <div className="container">Error: {error}</div>;

  return (
    <div className="container">
      <h1 style={{ textAlign: 'center', marginBottom: '20px' }}>VegasAir Flight 001</h1>
      
      <CountdownTimer daysUntilDeparture={daysUntilDeparture} hours={hours} />
      
      <SelectedSeatModal 
        selectedSeat={selectedSeat}
        onCancel={() => setSelectedSeat(null)}
        onPurchase={handlePurchase}
      />
      
      <Legend />

      <SeatGrid 
        seats={seats}
        selectedSeat={selectedSeat}
        onSeatClick={handleSeatClick}
      />
    </div>
  );
}
