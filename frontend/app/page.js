'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import SeatGrid from './components/SeatGrid';
import Legend from './components/Legend';
import SelectedSeatModal from './components/SelectedSeatModal';
import useWebSocket from './hooks/useWebSocket';

export default function Home() {
  const [seats, setSeats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSeat, setSelectedSeat] = useState(null);
  const flightId = 1; // For now, we're only working with flight 1

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = (data) => {
    if (data.type === 'SEAT_UPDATE') {
      setSeats(prevSeats => 
        prevSeats.map(seat => 
          seat.id === data.seat.id ? { ...seat, ...data.seat } : seat
        )
      );
    }
  };

  // Initialize WebSocket connection
  const { sendMessage } = useWebSocket(flightId, handleWebSocketMessage);

  useEffect(() => {
    fetchSeats();
  }, []);

  const fetchSeats = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/v1/flights/${flightId}/seats`);
      setSeats(response.data);
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
      <h1 style={{ textAlign: 'center', marginBottom: '30px' }}>VegasAir Flight 001</h1>
      
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
