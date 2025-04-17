'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import SeatGrid from './components/SeatGrid';
import Legend from './components/Legend';
import SelectedSeatModal from './components/SelectedSeatModal';
import CountdownTimer from './components/CountdownTimer';
import useWebSocket from './hooks/useWebSocket';
import FlightDepartureAnimation from './components/FlightDepartureAnimation';
import DemandForecast from './components/DemandForecast';
import RevenueStats from './components/RevenueStats';
import GraphLegend from './components/GraphLegend';
import RevenueDistribution from './components/RevenueDistribution';
import PriceEvolution from './components/PriceEvolution';
import OccupancyHeatMap from './components/OccupancyHeatMap';
import PriceSensitivity from './components/PriceSensitivity';

export default function Home() {
  const [seats, setSeats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSeat, setSelectedSeat] = useState(null);
  const [daysUntilDeparture, setDaysUntilDeparture] = useState(0);
  const [hours, setHours] = useState(0);
  const [showDepartureAnimation, setShowDepartureAnimation] = useState(false);
  const [currentFlightId, setCurrentFlightId] = useState(null);
  const [currentFlightNumber, setCurrentFlightNumber] = useState("");
  const [departureDate, setDepartureDate] = useState(null);
  const [selectedGraph, setSelectedGraph] = useState('demand');
  
  // Use refs to store pending updates
  const pendingSeatUpdates = useRef(new Map());
  const updateTimeout = useRef(null);

  // Function to fetch the current active flight
  const fetchCurrentFlight = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/v1/flights/active');
      const activeFlight = response.data;
      if (activeFlight) {
        setCurrentFlightId(activeFlight.id);
        setCurrentFlightNumber(activeFlight.flight_number);
        setDaysUntilDeparture(activeFlight.days_until_departure);
        setDepartureDate(activeFlight.departure_date);
      }
    } catch (err) {
      console.error('Error fetching current flight:', err);
      setError(err.message);
    }
  };

  // Fetch current flight on mount
  useEffect(() => {
    fetchCurrentFlight();
  }, []);

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
      
      // Update departure date from the WebSocket message
      if (data.departure_date) {
        setDepartureDate(data.departure_date);
      }
    } else if (data.type === "FLIGHT_DEPARTURE") {
      // Show departure animation and store new flight ID
      setShowDepartureAnimation(true);
      setCurrentFlightId(data.new_flight);
      // Fetch new flight details to get the new flight number
      axios.get(`http://localhost:8000/api/v1/flights/${data.new_flight}`)
        .then(response => {
          setCurrentFlightNumber(response.data.flight_number);
        })
        .catch(err => console.error('Error fetching new flight details:', err));
    }
  }, []);

  // Modify the handleAnimationComplete to also fetch flight details
  const handleAnimationComplete = useCallback(() => {
    setShowDepartureAnimation(false);
    
    // Fetch the new flight details to ensure we have the correct flight number
    if (currentFlightId) {
      const startNewFlight = async () => {
        try {
          console.log(`Starting timer and bots for flight ${currentFlightId}`);
          await axios.post(`http://localhost:8000/api/v1/flights/${currentFlightId}/start`);
          
          // Fetch updated flight details
          const flightResponse = await axios.get(`http://localhost:8000/api/v1/flights/${currentFlightId}`);
          setCurrentFlightNumber(flightResponse.data.flight_number);
          setDaysUntilDeparture(flightResponse.data.days_until_departure);
          setDepartureDate(flightResponse.data.departure_date);
          
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

  // Modify the existing useEffect to only fetch flight data when we have a currentFlightId
  useEffect(() => {
    if (currentFlightId) {
      fetchFlightData();
    }
    
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

  const handleGraphSelect = (graphId) => {
    setSelectedGraph(graphId);
  };

  const renderGraph = () => {
    switch(selectedGraph) {
      case 'demand':
        return <DemandForecast />;
      case 'revenue':
        return <RevenueDistribution />;
      case 'price':
        return <PriceEvolution />;
      case 'occupancy':
        return <OccupancyHeatMap />;
      case 'sensitivity':
        return <PriceSensitivity />;
      default:
        return <DemandForecast />;
    }
  };

  if (loading) return <div className="container">Loading seats...</div>;
  if (error) return <div className="container">Error: {error}</div>;

  return (
    <div className="container">
      <div className="countdown-timer">
        <div className="flight-info">
          <h2>VegasAir Flight {currentFlightNumber}</h2>
          <div className="departure-date">
            <span className="departure-label">Departure Date:</span><br />
            {departureDate ? new Date(departureDate).toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            }) : 'Loading...'}
          </div>
        </div>
        <div className="countdown-items">
          <div className="countdown-item">
            <div className="countdown-value">{daysUntilDeparture}</div>
            <div className="countdown-label">Days</div>
          </div>
          <div className="countdown-item">
            <div className="countdown-value">{hours}</div>
            <div className="countdown-label">Hours</div>
          </div>
        </div>
        <RevenueStats seats={seats} currentFlightId={currentFlightId} />
      </div>
      
      <SelectedSeatModal 
        selectedSeat={selectedSeat}
        onCancel={() => setSelectedSeat(null)}
        onPurchase={handlePurchase}
      />
      
      <div className="main-content">
        <div className="seating-section">
          <Legend />
          <SeatGrid 
            seats={seats}
            selectedSeat={selectedSeat}
            onSeatClick={handleSeatClick}
          />
        </div>
        <div className="analytics-section">
          <GraphLegend 
            selectedGraph={selectedGraph} 
            onSelectGraph={handleGraphSelect}
          />
          <div className="forecast-section">
            {renderGraph()}
          </div>
        </div>
      </div>

      {showDepartureAnimation && (
        <FlightDepartureAnimation 
          onComplete={handleAnimationComplete} 
          flightNumber={currentFlightNumber}
        />
      )}
    </div>
  );
}
