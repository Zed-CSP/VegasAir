const Legend = () => {
  return (
    <div className="legend">
      <div className="legend-item">
        <div className="legend-color first"></div>
        <span>First Class</span>
      </div>
      <div className="legend-item">
        <div className="legend-color business"></div>
        <span>Business</span>
      </div>
      <div className="legend-item">
        <div className="legend-color economy"></div>
        <span>Economy</span>
      </div>
    </div>
  );
};

export default Legend; 