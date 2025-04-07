from services.bot_service import bot_service

async def handle_start_bots(websocket, data):
    """Handle request to start bots for a flight"""
    flight_id = data.get('flight_id')
    if not flight_id:
        await websocket.send_json({
            'type': 'error',
            'message': 'Missing flight_id'
        })
        return
    
    # Get available seats for the flight
    available_seats = await get_available_seats(flight_id)
    
    # Start the bots
    bot_service.start_bots(flight_id, available_seats)
    
    await websocket.send_json({
        'type': 'bots_started',
        'flight_id': flight_id
    })

async def handle_stop_bots(websocket, data):
    """Handle request to stop bots for a flight"""
    flight_id = data.get('flight_id')
    if not flight_id:
        await websocket.send_json({
            'type': 'error',
            'message': 'Missing flight_id'
        })
        return
    
    # Stop the bots
    bot_service.stop_bots(flight_id)
    
    await websocket.send_json({
        'type': 'bots_stopped',
        'flight_id': flight_id
    })

# Add the new handlers to the message handlers dictionary
message_handlers = {
    'start_bots': handle_start_bots,
    'stop_bots': handle_stop_bots,
} 