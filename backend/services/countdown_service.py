import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from backend.websocket.ws_manager import manager
from backend.utils.constants import flight_state_manager, create_next_flight
from backend.services.purchase_history_service import purchase_history_service
from backend.db.database import SessionLocal
from backend.models.flight import Flight
from backend.models.seat import Seat

class CountdownService:
    """Service to manage countdown timers for flights"""
    
    def __init__(self):
        self._tasks: Dict[int, asyncio.Task] = {}
    
    def start_timer(self, flight_id: int, hours_until_departure: int):
        """Start a countdown timer for a flight"""
        if flight_id in self._tasks:
            # Timer already running for this flight
            return
        
        flight_state_manager.update_hours_remaining(flight_id, hours_until_departure)
        
        # Create a task for the timer
        self._tasks[flight_id] = asyncio.create_task(
            self._run_timer(flight_id)
        )
        
        print(f"Timer started for flight {flight_id}")
    
    def stop_timer(self, flight_id: int):
        """Stop a countdown timer for a flight"""
        if flight_id in self._tasks:
            self._tasks[flight_id].cancel()
            del self._tasks[flight_id]
            flight_state_manager.set_flight_inactive(flight_id)
            print(f"Timer stopped for flight {flight_id}")
    
    async def _run_timer(self, flight_id: int):
        """Run the countdown timer for a flight"""
        try:
            while flight_state_manager.get_hours_remaining(flight_id) > 0:
                # Get current hours remaining
                hours = flight_state_manager.get_hours_remaining(flight_id)
                days = hours // 24
                remaining_hours = hours % 24
                
                # Broadcast the update to all clients
                try:
                    await manager.broadcast_to_flight(flight_id, {
                        "type": "TIME_UPDATE",
                        "days_until_departure": days,
                        "hours": remaining_hours
                    })
                except Exception as e:
                    print(f"Error sending time update: {e}")
                
                # Wait for 0.5 seconds (4 hours in our simulation)
                await asyncio.sleep(0.25)
                
                # Update hours remaining (decrement by 4 hours)
                current_hours = flight_state_manager.get_hours_remaining(flight_id)
                if current_hours > 0:
                    flight_state_manager.update_hours_remaining(flight_id, current_hours - 4)
                
                # If we've reached zero, collect purchase history and stop
                if flight_state_manager.get_hours_remaining(flight_id) <= 0:
                    # Collect purchase history before stopping
                    purchase_history_service.collect_and_store_purchase_data(flight_id)
                    
                    # Create the next flight
                    try:
                        # Get the current flight number
                        db = SessionLocal()
                        current_flight = db.query(Flight).filter(Flight.id == flight_id).first()
                        if current_flight:
                            # Create the next flight with the incremented flight number
                            new_flight_id = create_next_flight(current_flight.flight_number)
                            if new_flight_id:
                                # Start the timer and bots for the new flight
                                try:
                                    # Get seats for the new flight
                                    new_seats = db.query(Seat).filter(Seat.flight_id == new_flight_id).all()
                                    if new_seats:
                                        # Get days until departure from the first seat
                                        days_until_departure = new_seats[0].days_until_departure
                                        
                                        # Start the countdown timer
                                        self.start_timer(new_flight_id, days_until_departure * 24)  # Convert days to hours
                                        
                                        # Convert seats to dictionary format for bot service
                                        seat_dicts = [{
                                            'id': seat.id,
                                            'row_number': seat.row_number,
                                            'seat_letter': seat.seat_letter,
                                            'is_occupied': seat.is_occupied,
                                            'class_type': seat.class_type,
                                            'is_window': seat.is_window,
                                            'is_aisle': seat.is_aisle,
                                            'is_middle': seat.is_middle,
                                            'is_extra_legroom': seat.is_extra_legroom,
                                            'base_price': seat.base_price,
                                            'sale_price': seat.sale_price,
                                            'days_until_departure': seat.days_until_departure
                                        } for seat in new_seats]
                                        
                                        # Start bots for the flight
                                        from backend.services.bot_service import bot_service
                                        bot_service.start_bots(new_flight_id, seat_dicts)
                                        
                                        print(f"Started timer and bots for new flight {new_flight_id}")
                                except Exception as e:
                                    print(f"Error starting timer and bots for new flight: {e}")
                                
                                # Broadcast flight departure and new flight creation
                                await manager.broadcast_to_flight(flight_id, {
                                    "type": "FLIGHT_DEPARTURE",
                                    "departed_flight": current_flight.flight_number,
                                    "new_flight": new_flight_id
                                })
                                print(f"Created new flight {new_flight_id} after flight {current_flight.flight_number} departed")
                    except Exception as e:
                        print(f"Error creating next flight: {e}")
                    finally:
                        if 'db' in locals():
                            db.close()
                    break
                
        except asyncio.CancelledError:
            # Timer was cancelled
            print(f"Timer cancelled for flight {flight_id}")
        except Exception as e:
            print(f"Error in timer for flight {flight_id}: {e}")
        finally:
            # Clean up
            if flight_id in self._tasks:
                del self._tasks[flight_id]
            flight_state_manager.set_flight_inactive(flight_id)

# Global instance
countdown_service = CountdownService() 