import React from 'react';
import GraphSelector from './GraphSelector';

const GraphLegend = ({ selectedGraph, onSelectGraph }) => {
  return (
    <div className="graph-legend">
      <GraphSelector selectedGraph={selectedGraph} onSelectGraph={onSelectGraph} />
    </div>
  );
};

export default GraphLegend; 