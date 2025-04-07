import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from ws_manager import manager

class CountdownService:
    """Service to manage countdown timers for flights"""
    
    def __init__(self):
        self._hours_remaining: Dict[int, int] = {}
        self._tasks: Dict[int, asyncio.Task] = {}
    
    def start_timer(self, flight_id: int, hours_until_departure: int):
        """Start a countdown timer for a flight"""
        if flight_id in self._tasks:
            # Timer already running for this flight
            return
        
        self._hours_remaining[flight_id] = hours_until_departure
        
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
            if flight_id in self._hours_remaining:
                del self._hours_remaining[flight_id]
            print(f"Timer stopped for flight {flight_id}")
    
    async def _run_timer(self, flight_id: int):
        """Run the countdown timer for a flight"""
        try:
            while self._hours_remaining.get(flight_id, 0) > 0:
                # Get current hours remaining
                hours = self._hours_remaining[flight_id]
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
                
                # Wait for a second (2 hours in our simulation)
                await asyncio.sleep(1)
                
                # Update hours remaining (decrement by 2 hours)
                if flight_id in self._hours_remaining:
                    self._hours_remaining[flight_id] -= 2
                
                # If we've reached zero, stop
                if self._hours_remaining.get(flight_id, 0) <= 0:
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
            if flight_id in self._hours_remaining:
                del self._hours_remaining[flight_id]

# Global instance
countdown_service = CountdownService() 