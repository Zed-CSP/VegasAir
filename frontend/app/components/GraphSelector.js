import React from 'react';

const GraphSelector = ({ selectedGraph, onSelectGraph }) => {
  const graphTypes = [
    { id: 'demand', label: 'Demand Forecast', icon: '📈' },
    { id: 'revenue', label: 'Revenue Distribution', icon: '🎯' },
    { id: 'price', label: 'Price Evolution', icon: '💰' },
    { id: 'occupancy', label: 'Occupancy Heat Map', icon: '📅' },
    { id: 'sensitivity', label: 'Price Sensitivity', icon: '📊' }
  ];

  return (
    <div className="graph-selector">
      {graphTypes.map((graph) => (
        <button
          key={graph.id}
          className={`graph-selector-button ${selectedGraph === graph.id ? 'selected' : ''}`}
          onClick={() => onSelectGraph(graph.id)}
        >
          <span className="graph-icon">{graph.icon}</span>
          {graph.label}
        </button>
      ))}
    </div>
  );
};

export default GraphSelector; 