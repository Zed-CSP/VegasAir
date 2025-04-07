'use client';

import { useState, useEffect } from 'react';
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
  const flightId = 1; // For now, we're only working with flight 1

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = (data) => {
    if (data.type === 'SEAT_UPDATE') {
      setSeats(prevSeats => 
        prevSeats.map(seat => 
          seat.id === data.seat.id ? { ...seat, ...data.seat } : seat
        )
      );
    } else if (data.type === 'TIME_UPDATE') {
      setDaysUntilDeparture(data.days_until_departure);
    }
  };

  // Initialize WebSocket connection
  const { sendMessage } = useWebSocket(flightId, handleWebSocketMessage);

  useEffect(() => {
    fetchFlightData();
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

  const handleSeatClick = (seat) => {
    if (!seat.is_occupied) {
      setSelectedSeat(seat);
    }
  };

  const handlePurchase = async () => {
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

      // Update local state
      setSeats(prevSeats =>
        prevSeats.map(seat =>
          seat.id === selectedSeat.id ? { ...seat, is_occupied: true, sale_price: selectedSeat.base_price } : seat
        )
      );

      setSelectedSeat(null);
    } catch (err) {
      console.error('Error purchasing seat:', err);
    }
  };

  if (loading) return <div className="container">Loading seats...</div>;
  if (error) return <div className="container">Error: {error}</div>;

  return (
    <div className="container">
      <h1 style={{ textAlign: 'center', marginBottom: '20px' }}>VegasAir Flight 001</h1>
      
      <CountdownTimer daysUntilDeparture={daysUntilDeparture} />
      
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
