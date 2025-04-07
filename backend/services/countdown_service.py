import asyncio
from datetime import datetime, timedelta
from typing import Dict, Callable, Awaitable, List

class CountdownService:
    """Service to manage countdown timers for flights"""
    
    def __init__(self):
        self._timers: Dict[int, asyncio.Task] = {}
        self._callbacks: Dict[int, List[Callable[[int, int], Awaitable[None]]]] = {}
        self._hours_remaining: Dict[int, int] = {}
        self._initialized: Dict[int, bool] = {}
    
    def start_timer(self, flight_id: int, _: int):  # Ignore the days_until_departure parameter
        """Start a countdown timer for a flight"""
        # Only initialize the timer once per flight
        if flight_id not in self._initialized:
            # Initialize with 120 days worth of hours
            self._hours_remaining[flight_id] = 120 * 24
            
            # Create a new task for the timer
            self._timers[flight_id] = asyncio.create_task(
                self._run_timer(flight_id)
            )
            
            self._initialized[flight_id] = True
            print(f"Timer initialized for flight {flight_id} with {self._hours_remaining[flight_id]} hours remaining")
    
    def stop_timer(self, flight_id: int):
        """Stop a countdown timer for a flight"""
        if flight_id in self._timers:
            self._timers[flight_id].cancel()
            del self._timers[flight_id]
            if flight_id in self._hours_remaining:
                del self._hours_remaining[flight_id]
            if flight_id in self._initialized:
                del self._initialized[flight_id]
    
    def register_callback(self, flight_id: int, callback: Callable[[int, int], Awaitable[None]]):
        """Register a callback to be called when the timer updates"""
        if flight_id not in self._callbacks:
            self._callbacks[flight_id] = []
        self._callbacks[flight_id].append(callback)
        
        # Send current time to the new callback immediately
        if flight_id in self._hours_remaining:
            asyncio.create_task(self._notify_from_hours(flight_id))
    
    def unregister_callback(self, flight_id: int, callback: Callable[[int, int], Awaitable[None]]):
        """Unregister a callback"""
        if flight_id in self._callbacks and callback in self._callbacks[flight_id]:
            self._callbacks[flight_id].remove(callback)
    
    async def _run_timer(self, flight_id: int):
        """Run the countdown timer for a flight"""
        try:
            print(f"Timer started for flight {flight_id}")
            
            # Update every second (decrementing 1 hour)
            while self._hours_remaining[flight_id] > 0:
                await asyncio.sleep(1)  # 1 second = 1 simulated hour
                
                # Decrement one hour
                self._hours_remaining[flight_id] -= 1
                
                # Notify callbacks
                await self._notify_from_hours(flight_id)
                
                if self._hours_remaining[flight_id] % 24 == 0:
                    print(f"Flight {flight_id}: {self._hours_remaining[flight_id] // 24} days remaining")
        except asyncio.CancelledError:
            # Timer was cancelled
            print(f"Timer cancelled for flight {flight_id}")
        except Exception as e:
            print(f"Error in timer for flight {flight_id}: {e}")
    
    async def _notify_from_hours(self, flight_id: int):
        """Calculate days and hours from total hours and notify callbacks"""
        if flight_id not in self._hours_remaining:
            return
            
        total_hours = self._hours_remaining[flight_id]
        days = total_hours // 24
        hours = total_hours % 24
        
        if flight_id in self._callbacks:
            for callback in self._callbacks[flight_id]:
                try:
                    await callback(days, hours)
                except Exception as e:
                    print(f"Error in countdown callback: {e}")

# Global instance
countdown_service = CountdownService() 