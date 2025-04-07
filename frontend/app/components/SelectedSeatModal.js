const SelectedSeatModal = ({ selectedSeat, onCancel }) => {
  if (!selectedSeat) return null;

  return (
    <div className="selected-seat-card">
      <h2>Selected Seat: {selectedSeat.row_number}{selectedSeat.seat_letter}</h2>
      <p>Class: {selectedSeat.class_type}</p>
      <p>Price: ${selectedSeat.base_price}</p>
      <div className="button-group">
        <button 
          className="purchase-button" 
          onClick={() => alert('Purchase functionality coming soon!')}
        >
          Purchase
        </button>
        <button 
          className="cancel-button" 
          onClick={onCancel}
        >
          Cancel
        </button>
      </div>
    </div>
  );
};

export default SelectedSeatModal; 