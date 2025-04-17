'use client';

import { useState, useEffect } from 'react';

const RevenueStats = ({ seats, currentFlightId }) => {
  const [stats, setStats] = useState({
    seatsSold: 0,
    totalSeats: 0,
    grossRevenue: 0,
    theoreticalRevenue: 0,
    dynamicPricingIncrease: 0
  });

  useEffect(() => {
    if (seats && seats.length > 0) {
      // Calculate seats sold and total seats
      const seatsSold = seats.filter(seat => seat.is_occupied).length;
      const totalSeats = seats.length;
      
      // Calculate gross revenue (actual revenue from dynamic pricing)
      const grossRevenue = seats
        .filter(seat => seat.is_occupied)
        .reduce((total, seat) => total + (seat.sale_price || seat.base_price), 0);
      
      // Calculate theoretical revenue (if all seats were sold at base price)
      const theoreticalRevenue = seats
        .filter(seat => seat.is_occupied)
        .reduce((total, seat) => total + seat.base_price, 0);
      
      // Calculate dynamic pricing increase
      const dynamicPricingIncrease = theoreticalRevenue > 0 
        ? ((grossRevenue - theoreticalRevenue) / theoreticalRevenue) * 100 
        : 0;
      
      setStats({
        seatsSold,
        totalSeats,
        grossRevenue,
        theoreticalRevenue,
        dynamicPricingIncrease
      });
    }
  }, [seats]);

  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  // Format percentage
  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`;
  };

  return (
    <div className="revenue-stats">
      <div className="stats-item">
        <div className="stats-value">{stats.seatsSold}/{stats.totalSeats}</div>
        <div className="stats-label">Seats Sold</div>
      </div>
      <div className="stats-item">
        <div className="stats-value">{formatCurrency(stats.theoreticalRevenue)}</div>
        <div className="stats-label">Fixed Price Revenue</div>
      </div>
      <div className="stats-item">
        <div className="stats-value">{formatCurrency(stats.grossRevenue)}</div>
        <div className="stats-label">Gross Revenue</div>
      </div>
      <div className="stats-item">
        <div className="stats-value">{formatPercentage(stats.dynamicPricingIncrease)}</div>
        <div className="stats-label">Dynamic Pricing Increase</div>
      </div>
    </div>
  );
};

export default RevenueStats; 