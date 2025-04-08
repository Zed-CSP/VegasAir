'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import SeatGrid from './components/SeatGrid';
import Legend from './components/Legend';
import SelectedSeatModal from './components/SelectedSeatModal';
import CountdownTimer from './components/CountdownTimer';
import useWebSocket from './hooks/useWebSocket';
import FlightDepartureAnimation from './components/FlightDepartureAnimation';

export default function Home() {
  const [seats, setSeats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSeat, setSelectedSeat] = useState(null);
  const [daysUntilDeparture, setDaysUntilDeparture] = useState(0);
  const [hours, setHours] = useState(0);
  const [showDepartureAnimation, setShowDepartureAnimation] = useState(false);
  const [currentFlightId, setCurrentFlightId] = useState(1); // Start with flight 1
  const [currentFlightNumber, setCurrentFlightNumber] = useState("001");
  
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
    console.log('WebSocket message received:', data);
    
    if (data.type === "SEAT_UPDATE") {
      // Update seats immediately when a seat update is received
      setSeats(prevSeats => {
        return prevSeats.map(seat => {
          if (seat.id === data.seat.id) {
            // Log the update for debugging
            console.log(`Updating seat ${seat.id} (${seat.row_number}${seat.seat_letter}) to occupied: ${data.seat.is_occupied}`);
            // Return the updated seat with all properties from the WebSocket message
            return { ...seat, ...data.seat };
          }
          return seat;
        });
      });
    } else if (data.type === "TIME_UPDATE") {
      // Update time immediately as it's less frequent
      setDaysUntilDeparture(data.days_until_departure);
      setHours(data.hours);
    } else if (data.type === "FLIGHT_DEPARTURE") {
      // Show departure animation and store new flight ID
      setShowDepartureAnimation(true);
      setCurrentFlightId(data.new_flight);
    }
  }, []);

  // Handle animation completion
  const handleAnimationComplete = useCallback(() => {
    setShowDepartureAnimation(false);
    
    // The WebSocket connection will automatically reconnect to the new flight
    // because we're updating currentFlightId, which triggers the useEffect
    // that calls fetchFlightData
    
    // Start the timer and bots for the new flight
    if (currentFlightId) {
      const startNewFlight = async () => {
        try {
          console.log(`Starting timer and bots for flight ${currentFlightId}`);
          await axios.post(`http://localhost:8000/api/v1/flights/${currentFlightId}/start`);
          console.log(`Successfully started timer and bots for flight ${currentFlightId}`);
        } catch (err) {
          console.error(`Error starting timer and bots for flight ${currentFlightId}:`, err);
        }
      };
      
      startNewFlight();
    }
  }, [currentFlightId]);

  // Initialize WebSocket connection with the current flight ID
  const { sendMessage } = useWebSocket(currentFlightId, handleWebSocketMessage);

  useEffect(() => {
    fetchFlightData();
    
    // Cleanup function
    return () => {
      if (updateTimeout.current) {
        clearTimeout(updateTimeout.current);
      }
    };
  }, [currentFlightId]); // Re-fetch when flight ID changes

  const fetchFlightData = async () => {
    try {
      // Fetch seats
      const seatsResponse = await axios.get(`http://localhost:8000/api/v1/flights/${currentFlightId}/seats`);
      setSeats(seatsResponse.data);
      
      // Fetch flight details including days until departure
      const flightResponse = await axios.get(`http://localhost:8000/api/v1/flights/${currentFlightId}`);
      setDaysUntilDeparture(flightResponse.data.days_until_departure);
      setCurrentFlightNumber(flightResponse.data.flight_number);
      
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
      <h1 style={{ textAlign: 'center', marginBottom: '20px' }}>
        VegasAir Flight {currentFlightNumber}
      </h1>
      
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

      {showDepartureAnimation && (
        <FlightDepartureAnimation onComplete={handleAnimationComplete} />
      )}
    </div>
  );
}
