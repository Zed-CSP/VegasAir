'use client';

import { useState, useEffect } from 'react';

const FlightDepartureAnimation = ({ onComplete }) => {
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
      setPosition(-100 + (progress * 200));

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
      <div 
        className="plane"
        style={{
          position: 'fixed',
          left: `${position}%`,
          top: '50%',
          transform: 'translateY(-50%)',
          opacity: opacity,
          fontSize: '4rem',
          zIndex: 1000,
          transition: 'opacity 0.3s ease-out'
        }}
      >
        ✈️
      </div>
    </div>
  );
};

export default FlightDepartureAnimation; 