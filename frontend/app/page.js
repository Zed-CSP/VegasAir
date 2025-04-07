'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import SeatGrid from './components/SeatGrid';
import Legend from './components/Legend';
import SelectedSeatModal from './components/SelectedSeatModal';

export default function Home() {
  const [seats, setSeats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSeat, setSelectedSeat] = useState(null);

  useEffect(() => {
    fetchSeats();
  }, []);

  const fetchSeats = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/v1/flights/1/seats');
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

  if (loading) return <div className="container">Loading seats...</div>;
  if (error) return <div className="container">Error: {error}</div>;

  return (
    <div className="container">
      <h1 style={{ textAlign: 'center', marginBottom: '30px' }}>VegasAir Flight 001</h1>
      
      <SelectedSeatModal 
        selectedSeat={selectedSeat}
        onCancel={() => setSelectedSeat(null)}
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
