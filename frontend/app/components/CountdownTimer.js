'use client';

import { useState, useEffect } from 'react';

const CountdownTimer = ({ daysUntilDeparture, hours }) => {
  return (
    <div className="countdown-timer">
      <div className="countdown-item">
        <div className="countdown-value">{daysUntilDeparture}</div>
        <div className="countdown-label">Days</div>
      </div>
      <div className="countdown-item">
        <div className="countdown-value">{hours}</div>
        <div className="countdown-label">Hours</div>
      </div>
    </div>
  );
}

export default CountdownTimer; 