const SelectedSeatModal = ({ selectedSeat, onCancel, onPurchase }) => {
  if (!selectedSeat) return null;

  return (
    <div className="selected-seat-card">
      <h2>Selected Seat: {selectedSeat.row_number}{selectedSeat.seat_letter}</h2>
      <p>Class: {selectedSeat.class_type}</p>
      <p>Price: ${selectedSeat.base_price}</p>
      <div className="button-group">
        <button 
          className="purchase-button" 
          onClick={onPurchase}
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