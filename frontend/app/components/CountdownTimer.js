'use client';

import { useState, useEffect } from 'react';

const CountdownTimer = ({ daysUntilDeparture }) => {
  const [timeLeft, setTimeLeft] = useState({
    days: 0,
    hours: 0
  });

  useEffect(() => {
    // Calculate the departure date based on days until departure
    const departureDate = new Date();
    departureDate.setDate(departureDate.getDate() + daysUntilDeparture);
    
    // Track the simulated time
    let simulatedHours = 0;
    
    // Update the countdown every 2.5 seconds (simulating 1 hour)
    const timer = setInterval(() => {
      // Increment simulated hours
      simulatedHours++;
      
      // Calculate remaining time based on simulated hours
      const totalHoursUntilDeparture = daysUntilDeparture * 24;
      const remainingHours = Math.max(0, totalHoursUntilDeparture - simulatedHours);
      
      // Convert to days and hours
      const days = Math.floor(remainingHours / 24);
      const hours = remainingHours % 24;
      
      setTimeLeft({ days, hours });
      
      // If we've reached the departure time, stop the timer
      if (remainingHours <= 0) {
        clearInterval(timer);
      }
    }, 2500); // 2.5 seconds = 1 simulated hour
    
    // Initial calculation
    setTimeLeft({ 
      days: daysUntilDeparture, 
      hours: 0 
    });
    
    return () => clearInterval(timer);
  }, [daysUntilDeparture]);

  return (
    <div className="countdown-timer">
      <div className="countdown-item">
        <div className="countdown-value">{timeLeft.days}</div>
        <div className="countdown-label">Days</div>
      </div>
      <div className="countdown-item">
        <div className="countdown-value">{timeLeft.hours}</div>
        <div className="countdown-label">Hours</div>
      </div>
    </div>
  );
};

export default CountdownTimer; 