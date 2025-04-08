'use client';

import { useState, useEffect } from 'react';

const FlightDepartureAnimation = ({ onComplete, flightNumber }) => {
  const [position, setPosition] = useState(-100);
  const [opacity, setOpacity] = useState(1);

  useEffect(() => {
    // Start the animation
    const startTime = Date.now();
    const duration = 3000; // 3 seconds

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Move the plane from left to right
      setPosition(-100 + (progress * 300));

      // Fade out at the end
      if (progress > 0.7) {
        setOpacity(1 - ((progress - 0.7) / 0.3));
      }

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        // Animation complete
        if (onComplete) {
          onComplete();
        }
      }
    };

    requestAnimationFrame(animate);
  }, [onComplete]);

  return (
    <div className="flight-departure-animation">
      <h2 
        className="departure-headline"
        style={{
          position: 'fixed',
          left: '50%',
          top: '30%',
          transform: 'translate(-50%, -50%)',
          fontSize: '3.5rem',
          textAlign: 'center',
          opacity: opacity,
          zIndex: 1000,
          fontFamily: "'Orbitron', 'Arial Black', sans-serif",
          fontWeight: '900',
          letterSpacing: '4px',
          textTransform: 'uppercase',
          background: 'linear-gradient(to right, #ff0000, #ff8800, #ffff00, #00ff00, #00ffff, #0000ff, #ff00ff)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          textShadow: '0 0 10px rgba(255, 255, 255, 0.8)',
          whiteSpace: 'nowrap'
        }}
      >
        VegasAir Flight {flightNumber} Departing
      </h2>
      <div 
        className="plane"
        style={{
          position: 'fixed',
          left: `${position}%`,
          top: '50%',
          transform: 'translate(-50%, -50%) rotate(45deg)',
          opacity: opacity,
          fontSize: '16rem',
          zIndex: 1000,
          display: 'inline-block',
          filter: 'drop-shadow(0 0 10px rgba(255, 255, 255, 0.5))'
        }}
      >
        ✈️
      </div>
    </div>
  );
};

export default FlightDepartureAnimation; 