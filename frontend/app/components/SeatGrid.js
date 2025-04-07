'use client';

export default function SeatGrid({ seats, selectedSeat, onSeatClick }) {
  const renderSeatGrid = () => {
    const rows = {};
    seats.forEach(seat => {
      if (!rows[seat.row_number]) {
        rows[seat.row_number] = [];
      }
      rows[seat.row_number].push(seat);
    });

    return Object.entries(rows).map(([rowNum, rowSeats]) => {
      // Sort seats by letter to ensure correct order
      rowSeats.sort((a, b) => a.seat_letter.localeCompare(b.seat_letter));
      
      return rowSeats.map((seat, index) => {
        // Add aisle space after seat C (index 2)
        const seatElement = (
          <div
            key={`${seat.row_number}${seat.seat_letter}`}
            className={`seat ${seat.class_type.replace(' ', '-')} ${seat.is_occupied ? 'occupied' : ''} ${selectedSeat?.row_number === seat.row_number && selectedSeat?.seat_letter === seat.seat_letter ? 'selected' : ''}`}
            onClick={() => onSeatClick(seat)}
          >
            <div style={{ fontWeight: 'bold' }}>{seat.row_number}{seat.seat_letter}</div>
            <div className="seat-price">
              ${seat.is_occupied && seat.sale_price ? seat.sale_price : seat.base_price}
            </div>
          </div>
        );

        if (index === 2) { // After seat C
          return [
            seatElement,
            <div key={`aisle-${rowNum}-${index}`} className="aisle" />
          ];
        }
        return seatElement;
      });
    });
  };

  return (
    <div className="seat-grid">
      {renderSeatGrid()}
    </div>
  );
} 