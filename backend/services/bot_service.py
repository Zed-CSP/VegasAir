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
                'First Class': 0.6,    # 60% prefer first class
                'Business Class': 0.4,  # 40% prefer business class
                'Economy Class': 0.1    # 10% prefer economy class
            },
            'price_sensitivity': 0.2,  # 0-1 scale, higher means more sensitive to price
            'extra_legroom_preference': 0.3,  # 30% of bots prefer extra legroom
            'adjacent_seat_chance': 0.5  # 50% chance to buy an adjacent seat
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
            base_rate = 1.5
            
            # Run until the flight departs
            while hours_remaining > 0:
                # Filter out seats that are already occupied by bots
                current_available_seats = [seat for seat in available_seats 
                                         if seat['id'] not in self._active_bots.get(flight_id, set())]
                
                # Calculate the current demand multiplier based on days remaining and available seats
                demand_multiplier = self._calculate_demand_multiplier(days_remaining, current_available_seats)
                
                # Calculate the probability of a purchase in this hour
                purchase_prob = (base_rate / 24) * demand_multiplier
                
                # Randomly decide if a bot should make a purchase
                if random.random() < purchase_prob:
                    # Select a seat based on preferences
                    seat = self._select_seat(current_available_seats, flight_id)
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
    
    def _calculate_demand_multiplier(self, days_remaining: int, available_seats: List[dict] = None) -> float:
        """Calculate the demand multiplier based on days remaining and available seats"""
        # Peak at 60 days before departure
        peak1_days = 60
        
        # Peak in the last 10 days
        peak2_days = 10
        
        # Calculate distance from peaks
        dist_from_peak1 = abs(days_remaining - peak1_days)
        dist_from_peak2 = abs(days_remaining - peak2_days)
        
        # Calculate multipliers for each peak
        # Use a bell curve shape (normal distribution approximation)
        multiplier1 = 3 * (1 / (1 + dist_from_peak1 / 10))
        multiplier2 = 5 * (1 / (1 + dist_from_peak2 / 5))
        
        # Combine the multipliers
        # For days between peaks, use a weighted average
        if days_remaining > peak1_days and days_remaining < (peak1_days + peak2_days) / 2:
            # Between peak1 and midpoint
            weight = (days_remaining - peak1_days) / ((peak1_days + peak2_days) / 2 - peak1_days)
            time_multiplier = multiplier1 * (1 - weight) + multiplier2 * weight
        elif days_remaining >= (peak1_days + peak2_days) / 2 and days_remaining < peak2_days:
            # Between midpoint and peak2
            weight = (days_remaining - (peak1_days + peak2_days) / 2) / (peak2_days - (peak1_days + peak2_days) / 2)
            time_multiplier = multiplier1 * weight + multiplier2 * (1 - weight)
        else:
            # Outside the peaks, use the higher multiplier
            time_multiplier = max(multiplier1, multiplier2)
        
        # Add scarcity factor based on available seats if provided
        if available_seats:
            # Count seats by class
            first_class_seats = sum(1 for s in available_seats if s['class_type'] == 'First Class')
            business_class_seats = sum(1 for s in available_seats if s['class_type'] == 'Business Class')
            economy_class_seats = sum(1 for s in available_seats if s['class_type'] == 'Economy Class')
            
            # Calculate scarcity multiplier (fewer seats = higher demand)
            # We'll use a simple formula: 1 + (1 / (1 + count/10))
            # This gives a multiplier between 1.0 and 2.0, with higher values for fewer seats
            
            # Default values if no seats of a class are available
            first_scarcity = 2.0 if first_class_seats == 0 else 1 + (1 / (1 + first_class_seats/10))
            business_scarcity = 2.0 if business_class_seats == 0 else 1 + (1 / (1 + business_class_seats/10))
            economy_scarcity = 2.0 if economy_class_seats == 0 else 1 + (1 / (1 + economy_class_seats/10))
            
            # Calculate weighted average scarcity based on class preferences
            class_prefs = self._preferences['class_preference']
            weighted_scarcity = (
                first_scarcity * class_prefs.get('First Class', 0.4) +
                business_scarcity * class_prefs.get('Business Class', 0.3) +
                economy_scarcity * class_prefs.get('Economy Class', 0.3)
            )
            
            # Apply scarcity factor to time multiplier
            # We'll use a weighted average: 70% time factor, 30% scarcity factor
            return 0.7 * time_multiplier + 0.3 * weighted_scarcity
        
        # If no available seats provided, just return the time multiplier
        return time_multiplier
    
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
            score += class_pref * 15
            
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
    
    def _find_adjacent_seat(self, seat: dict, available_seats: List[dict], flight_id: int) -> Optional[dict]:
        """Find an adjacent seat within the same side of the plane"""
        # Get the row and seat letter of the current seat
        row = seat['row_number']
        seat_letter = seat['seat_letter']
        
        # Determine which side of the plane the seat is on
        # Left side: A, B, C
        # Right side: D, E, F
        is_left_side = seat_letter in ['A', 'B', 'C']
        
        # Find potential adjacent seats based on the side
        potential_adjacent_letters = []
        if is_left_side:
            if seat_letter == 'A':
                potential_adjacent_letters = ['B']
            elif seat_letter == 'B':
                potential_adjacent_letters = ['A', 'C']
            elif seat_letter == 'C':
                potential_adjacent_letters = ['B']
        else:  # Right side
            if seat_letter == 'D':
                potential_adjacent_letters = ['E']
            elif seat_letter == 'E':
                potential_adjacent_letters = ['D', 'F']
            elif seat_letter == 'F':
                potential_adjacent_letters = ['E']
        
        # Find available adjacent seats
        adjacent_seats = []
        for letter in potential_adjacent_letters:
            for available_seat in available_seats:
                if (available_seat['row_number'] == row and 
                    available_seat['seat_letter'] == letter and
                    available_seat['id'] not in self._active_bots.get(flight_id, set())):
                    adjacent_seats.append(available_seat)
        
        # Return a random adjacent seat if any are available
        if adjacent_seats:
            return random.choice(adjacent_seats)
        
        return None
    
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
            class_multiplier = 3.33  # First class is 3.33x base price
        elif seat['class_type'] == 'Business Class':
            class_multiplier = 2.0   # Business class is 2x base price
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
                
                # 50% chance to buy an adjacent seat
                if random.random() < self._preferences['adjacent_seat_chance']:
                    # Get all available seats from the database
                    available_seats = db.query(Seat).filter(
                        Seat.flight_id == flight_id,
                        Seat.is_occupied == False
                    ).all()
                    
                    # Convert to dictionary format
                    available_seats_dict = [
                        {
                            "id": s.id,
                            "row_number": s.row_number,
                            "seat_letter": s.seat_letter,
                            "is_occupied": s.is_occupied,
                            "class_type": s.class_type,
                            "is_window": s.is_window,
                            "is_aisle": s.is_aisle,
                            "is_middle": s.is_middle,
                            "is_extra_legroom": s.is_extra_legroom,
                            "base_price": s.base_price,
                            "sale_price": s.sale_price,
                            "days_until_departure": s.days_until_departure
                        }
                        for s in available_seats
                    ]
                    
                    # Find an adjacent seat
                    adjacent_seat = self._find_adjacent_seat(seat, available_seats_dict, flight_id)
                    
                    if adjacent_seat:
                        print(f"🤖 BOT ALSO PURCHASING ADJACENT SEAT: Row {adjacent_seat['row_number']}{adjacent_seat['seat_letter']}")
                        # Recursively call _make_purchase for the adjacent seat
                        await self._make_purchase(flight_id, adjacent_seat)
        except Exception as e:
            print(f"Error updating seat in database: {e}")
            db.rollback()
        finally:
            db.close()

# Global instance
bot_service = BotService() 