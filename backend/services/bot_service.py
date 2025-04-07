import asyncio
import random
from typing import Dict, List, Set, Optional
from datetime import datetime, timedelta

from backend.database import SessionLocal
from backend.models.seat import Seat
from backend.ws_manager import manager
from backend.services.countdown_service import countdown_service

class BotService:
    """Service to manage bots that simulate seat purchases"""
    
    def __init__(self):
        self._bot_tasks: Dict[int, asyncio.Task] = {}
        self._active_bots: Dict[int, Set[int]] = {}  # flight_id -> set of seat_ids
        self._preferences = {
            'window_preference': 0.4,  # 40% of bots prefer window seats
            'aisle_preference': 0.4,   # 40% of bots prefer aisle seats
            'class_preference': {
                'First Class': 0.4,    # 10% prefer first class
                'Business Class': 0.3,  # 20% prefer business class
                'Economy Class': 0.3    # 70% prefer economy class
            },
            'price_sensitivity': 0.5,  # 0-1 scale, higher means more sensitive to price
            'extra_legroom_preference': 0.3  # 30% of bots prefer extra legroom
        }
    
    def start_bots(self, flight_id: int, available_seats: List[dict]):
        """Start bots for a flight"""
        if flight_id in self._bot_tasks:
            # Bots already running for this flight
            return
        
        # Initialize active bots for this flight
        self._active_bots[flight_id] = set()
        
        # Create a task for the bots
        self._bot_tasks[flight_id] = asyncio.create_task(
            self._run_bots(flight_id, available_seats)
        )
        
        print(f"Bots started for flight {flight_id}")
    
    def stop_bots(self, flight_id: int):
        """Stop bots for a flight"""
        if flight_id in self._bot_tasks:
            self._bot_tasks[flight_id].cancel()
            del self._bot_tasks[flight_id]
            if flight_id in self._active_bots:
                del self._active_bots[flight_id]
            print(f"Bots stopped for flight {flight_id}")
    
    async def _run_bots(self, flight_id: int, available_seats: List[dict]):
        """Run bots for a flight"""
        try:
            # Wait for the countdown service to be ready
            while flight_id not in countdown_service._hours_remaining:
                await asyncio.sleep(1)
            
            # Get the initial hours remaining
            hours_remaining = countdown_service._hours_remaining[flight_id]
            days_remaining = hours_remaining // 24
            
            # Calculate the base purchase rate (purchases per day)
            base_rate = 1
            
            # Run until the flight departs
            while hours_remaining > 0:
                # Calculate the current demand multiplier based on days remaining
                demand_multiplier = self._calculate_demand_multiplier(days_remaining)
                
                # Calculate the probability of a purchase in this hour
                purchase_prob = (base_rate / 24) * demand_multiplier
                
                # Randomly decide if a bot should make a purchase
                if random.random() < purchase_prob:
                    # Select a seat based on preferences
                    seat = self._select_seat(available_seats, flight_id)
                    if seat:
                        # Make the purchase
                        await self._make_purchase(flight_id, seat)
                
                # Wait for the next hour (0.5 seconds in our simulation)
                await asyncio.sleep(0.25)
                
                # Update hours remaining
                hours_remaining = countdown_service._hours_remaining.get(flight_id, 0)
                days_remaining = hours_remaining // 24
                
                # If we've reached the end of the flight, stop
                if hours_remaining <= 0:
                    break
                
                # Periodically update available seats (every 24 hours)
                if hours_remaining % 24 == 0:
                    # In a real implementation, you would fetch updated seats from the database
                    # For now, we'll just use the existing list
                    pass
                
        except asyncio.CancelledError:
            # Bots were cancelled
            print(f"Bots cancelled for flight {flight_id}")
        except Exception as e:
            print(f"Error in bots for flight {flight_id}: {e}")
    
    def _calculate_demand_multiplier(self, days_remaining: int) -> float:
        """Calculate the demand multiplier based on days remaining"""
        # Peak at 60 days before departure
        peak1_days = 60
        
        # Peak in the last 10 days
        peak2_days = 10
        
        # Calculate distance from peaks
        dist_from_peak1 = abs(days_remaining - peak1_days)
        dist_from_peak2 = abs(days_remaining - peak2_days)
        
        # Calculate multipliers for each peak
        # Use a bell curve shape (normal distribution approximation)
        multiplier1 = 2.5 * (1 / (1 + dist_from_peak1 / 10))
        multiplier2 = 3.0 * (1 / (1 + dist_from_peak2 / 5))
        
        # Combine the multipliers
        # For days between peaks, use a weighted average
        if days_remaining > peak1_days and days_remaining < (peak1_days + peak2_days) / 2:
            # Between peak1 and midpoint
            weight = (days_remaining - peak1_days) / ((peak1_days + peak2_days) / 2 - peak1_days)
            return multiplier1 * (1 - weight) + multiplier2 * weight
        elif days_remaining >= (peak1_days + peak2_days) / 2 and days_remaining < peak2_days:
            # Between midpoint and peak2
            weight = (days_remaining - (peak1_days + peak2_days) / 2) / (peak2_days - (peak1_days + peak2_days) / 2)
            return multiplier1 * weight + multiplier2 * (1 - weight)
        else:
            # Outside the peaks, use the higher multiplier
            return max(multiplier1, multiplier2)
    
    def _select_seat(self, available_seats: List[dict], flight_id: int) -> Optional[dict]:
        """Select a seat based on bot preferences"""
        # Filter out seats that are already occupied by bots
        available_seats = [seat for seat in available_seats 
                          if seat['id'] not in self._active_bots.get(flight_id, set())]
        
        if not available_seats:
            return None
        
        # Apply preferences to score each seat
        scored_seats = []
        for seat in available_seats:
            score = 0
            
            # Window preference
            if seat['is_window'] and random.random() < self._preferences['window_preference']:
                score += 3
            
            # Aisle preference
            if seat['is_aisle'] and random.random() < self._preferences['aisle_preference']:
                score += 2
            
            # Class preference
            class_pref = self._preferences['class_preference'].get(seat['class_type'], 0)
            score += class_pref * 5
            
            # Extra legroom preference
            if seat['is_extra_legroom'] and random.random() < self._preferences['extra_legroom_preference']:
                score += 2
            
            # Price sensitivity (lower price = higher score)
            price_sensitivity = self._preferences['price_sensitivity']
            max_price = max(s['base_price'] for s in available_seats)
            min_price = min(s['base_price'] for s in available_seats)
            if max_price > min_price:
                price_score = 1 - ((seat['base_price'] - min_price) / (max_price - min_price))
                score += price_score * price_sensitivity * 3
            
            # Add some randomness
            score += random.random() * 2
            
            scored_seats.append((seat, score))
        
        # Sort by score (highest first)
        scored_seats.sort(key=lambda x: x[1], reverse=True)
        
        # Select from the top 3 seats with probability weighted by score
        top_seats = scored_seats[:3]
        total_score = sum(score for _, score in top_seats)
        
        if total_score == 0:
            # Fallback to random selection
            return random.choice(available_seats)
        
        # Select based on score
        r = random.random() * total_score
        cumulative_score = 0
        for seat, score in top_seats:
            cumulative_score += score
            if r <= cumulative_score:
                return seat
        
        # Fallback
        return top_seats[0][0]
    
    async def _make_purchase(self, flight_id: int, seat: dict):
        """Make a purchase for a seat"""
        # Mark the seat as purchased by a bot
        self._active_bots[flight_id].add(seat['id'])
        
        # Get the current hours remaining
        hours_remaining = countdown_service._hours_remaining.get(flight_id, 0)
        days_remaining = hours_remaining // 24
        
        # Calculate a price based on days remaining and seat class
        base_price = seat['base_price']
        
        # Apply pricing based on days remaining
        if days_remaining <= 10:  # Last 10 days - higher prices
            price_multiplier = 1.5
        elif days_remaining <= 30:  # Last month - medium prices
            price_multiplier = 1.2
        elif days_remaining <= 60:  # Peak booking period - standard prices
            price_multiplier = 1.0
        else:  # Early booking - slightly lower prices
            price_multiplier = 0.9
        
        # Apply class-based pricing
        if seat['class_type'] == 'First Class':
            class_multiplier = 1.3
        elif seat['class_type'] == 'Business Class':
            class_multiplier = 1.2
        else:  # Economy Class
            class_multiplier = 1.0
        
        # Calculate final price
        sale_price = base_price * price_multiplier * class_multiplier
        
        # Round to nearest dollar
        sale_price = round(sale_price)
        
        # Enhanced console logging
        print("\n" + "="*50)
        print(f"🤖 BOT PURCHASE MADE")
        print(f"Flight ID: {flight_id}")
        print(f"Seat: Row {seat['row_number']}{seat['seat_letter']} (ID: {seat['id']})")
        print(f"Class: {seat['class_type']}")
        print(f"Features: {'Window ' if seat['is_window'] else ''}{'Aisle ' if seat['is_aisle'] else ''}{'Extra Legroom' if seat['is_extra_legroom'] else ''}")
        print(f"Days until departure: {days_remaining}")
        print(f"Pricing: Base ${base_price} × {price_multiplier:.1f} (time) × {class_multiplier:.1f} (class) = ${sale_price}")
        print("="*50 + "\n")
        
        # Update the database
        db = SessionLocal()
        try:
            # Get the seat from the database
            db_seat = db.query(Seat).filter(Seat.id == seat['id']).first()
            if db_seat:
                # Update the seat
                db_seat.is_occupied = True
                db_seat.sale_price = sale_price
                db_seat.days_until_departure = days_remaining
                db.commit()
                
                # Broadcast the update to all clients
                try:
                    # Send a complete seat update that matches what the frontend expects
                    await manager.broadcast_to_flight(flight_id, {
                        "type": "SEAT_UPDATE",
                        "seat": {
                            "id": db_seat.id,
                            "row_number": db_seat.row_number,
                            "seat_letter": db_seat.seat_letter,
                            "is_occupied": db_seat.is_occupied,
                            "class_type": db_seat.class_type,
                            "is_window": db_seat.is_window,
                            "is_aisle": db_seat.is_aisle,
                            "is_middle": db_seat.is_middle,
                            "is_extra_legroom": db_seat.is_extra_legroom,
                            "base_price": db_seat.base_price,
                            "sale_price": db_seat.sale_price,
                            "days_until_departure": db_seat.days_until_departure
                        }
                    })
                    print(f"WebSocket update sent for seat {db_seat.id}")
                except Exception as e:
                    print(f"Error broadcasting seat update: {e}")
        except Exception as e:
            print(f"Error updating seat in database: {e}")
            db.rollback()
        finally:
            db.close()

# Global instance
bot_service = BotService() 