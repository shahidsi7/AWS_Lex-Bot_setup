import json
import uuid
from datetime import datetime, timedelta
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('HotelBookings')  <---------------- DynamoDB Table name

# Base Room pricing per night
ROOM_PRICES = {
    "Classic": 100,
    "Deluxe": 150,
    "Suite": 200,
    "Duplex": 250,
    "Penthouse": 300
}

# Additional pricing for extra guests and specific bed types (per night)
ADDON_PRICES = {
    "extra_adult": 25,  # Surcharge per adult if exceeding standard room capacity (e.g., 2 adults)
    "child": 15,        # Surcharge per child
    "bed_type": {       # Surcharge for specific bed types
        "King": 10,
        "Queen": 5,
        "Twin": 0,      # No extra charge for Twin
        "Double": 0     # No extra extra charge for Double
        # Add more bed types as needed
    }
}

# Helper function to calculate the dynamic price based on all relevant slots
def calculate_dynamic_price(room_type, num_adults, num_children, bed_type, num_nights):
    """
    Calculates the total booking price based on room type, number of guests, bed type, and nights.
    """
    # Make room_type case-insensitive for lookup
    normalized_room_type = room_type.capitalize() if room_type else ""
    base_price_per_night = ROOM_PRICES.get(normalized_room_type, 0)
    
    daily_surcharge = 0

    # Apply surcharge for extra adults. Assuming standard rooms include 2 adults.
    # Adjust this logic based on your hotel's specific capacity rules per room type.
    if num_adults > 2:
        daily_surcharge += (num_adults - 2) * ADDON_PRICES.get("extra_adult", 0)
    
    # Apply surcharge for children
    daily_surcharge += num_children * ADDON_PRICES.get("child", 0)

    # Apply surcharge for specific bed types (case-insensitive lookup)
    normalized_bed_type = bed_type.capitalize() if bed_type else ""
    daily_surcharge += ADDON_PRICES["bed_type"].get(normalized_bed_type, 0)

    # Calculate total price
    total_price = (base_price_per_night + daily_surcharge) * num_nights

    print(f"DEBUG: base_price_per_night: {base_price_per_night}")
    print(f"DEBUG: daily_surcharge: {daily_surcharge}")
    print(f"DEBUG: num_nights: {num_nights}")
    print(f"DEBUG: Calculated total_price: {total_price}")

    return total_price

def lambda_handler(event, context):
    print(f"DEBUG: Event received by Lambda: {json.dumps(event, indent=2)}")

    slots = event['sessionState']['intent']['slots']
    
    # Extract all specified slots, safely handling if they are not provided by Lex
    user_name = slots.get('UserName', {}).get('value', {}).get('interpretedValue')
    room_type = slots.get('RoomType', {}).get('value', {}).get('interpretedValue')
    check_in_date_str = slots.get('CheckInDate', {}).get('value', {}).get('interpretedValue')
    num_nights_str = slots.get('NumNights', {}).get('value', {}).get('interpretedValue')
    num_adults_str = slots.get('NumAdults', {}).get('value', {}).get('interpretedValue')
    num_children_str = slots.get('NumChildren', {}).get('value', {}).get('interpretedValue')
    # ChildrenAges slot is intentionally not extracted as per previous request
    bed_type = slots.get('BedType', {}).get('value', {}).get('interpretedValue')
    accessibility_needs = slots.get('AccessibilityNeeds', {}).get('value', {}).get('interpretedValue')
    smoking_preference = slots.get('SmokingPreference', {}).get('value', {}).get('interpretedValue')
    city = slots.get('City', {}).get('value', {}).get('interpretedValue')
    hotel_name = slots.get('HotelName', {}).get('value', {}).get('interpretedValue')
    price_range = slots.get('PriceRange', {}).get('value', {}).get('interpretedValue')
    contact_email = slots.get('ContactEmail', {}).get('value', {}).get('interpretedValue')
    contact_phone = slots.get('ContactPhone', {}).get('value', {}).get('interpretedValue')
    preferred_payment_method = slots.get('PreferredPaymentMethod', {}).get('value', {}).get('interpretedValue')
    special_requests = slots.get('SpecialRequests', {}).get('value', {}).get('interpretedValue')
    
    # Convert numerical slots to integers, with default 0 if not provided or invalid
    num_nights = int(num_nights_str) if num_nights_str and num_nights_str.isdigit() else 0
    num_adults = int(num_adults_str) if num_adults_str and num_adults_str.isdigit() else 0
    num_children = int(num_children_str) if num_children_str and num_children_str.isdigit() else 0
    
    print(f"DEBUG: Extracted Slots - room_type: {room_type}, num_adults: {num_adults}, num_children: {num_children}, bed_type: {bed_type}, num_nights: {num_nights}")

    # Date calculations
    check_in_datetime = None
    check_out_date_formatted = None
    if check_in_date_str:
        try:
            check_in_datetime = datetime.strptime(check_in_date_str, "%Y-%m-%d")
            if num_nights > 0:
                check_out_datetime = check_in_datetime + timedelta(days=num_nights)
                check_out_date_formatted = check_out_datetime.strftime("%Y-%m-%d")
        except ValueError:
            pass # Lex should ideally prevent invalid dates, but this is a safeguard

    # Calculate total price using the new dynamic function
    total_price = calculate_dynamic_price(
        room_type, num_adults, num_children, bed_type, num_nights
    )
    
    booking_id = str(uuid.uuid4())

    # Prepare item for DynamoDB, including all slots only if they have a value
    item = {
        'bookingId': booking_id,
        'timestamp': datetime.now().isoformat()
    }

    if user_name: item['userName'] = user_name
    if room_type: item['roomType'] = room_type
    if check_in_date_str: item['checkInDate'] = check_in_date_str
    if num_nights > 0: item['numNights'] = num_nights
    if check_out_date_formatted: item['checkOutDate'] = check_out_date_formatted
    if total_price > 0: item['totalPrice'] = total_price

    if num_adults > 0: item['numAdults'] = num_adults
    if num_children > 0: item['numChildren'] = num_children
    if bed_type: item['bedType'] = bed_type
    if accessibility_needs: item['accessibilityNeeds'] = accessibility_needs
    if smoking_preference: item['smokingPreference'] = smoking_preference
    if city: item['city'] = city
    if hotel_name: item['hotelName'] = hotel_name
    if price_range: item['priceRange'] = price_range
    if contact_email: item['contactEmail'] = contact_email
    if contact_phone: item['contactPhone'] = contact_phone
    if preferred_payment_method: item['preferredPaymentMethod'] = preferred_payment_method
    if special_requests: item['specialRequests'] = special_requests

    # Save to DynamoDB
    table.put_item(Item=item)

    # Construct a confirmation message for the final response
    confirmation_message = (
        f"Thank you {user_name if user_name else 'guest'}, "
        f"your booking for a {room_type if room_type else 'room'} "
        f"from {check_in_date_str if check_in_date_str else 'an unspecified date'} "
        f"for {num_nights} nights "
    )
    
    # Conditionally add hotel name and city
    if hotel_name:
        confirmation_message += f"at {hotel_name} "
    if city:
        confirmation_message += f"in {city} "

    confirmation_message += f"is confirmed. The total estimated cost is ${total_price}. "

    if contact_email:
        confirmation_message += f"A confirmation email will be sent to {contact_email}."
    elif contact_phone:
        confirmation_message += f"We will contact you at {contact_phone} if needed."

    return {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                "name": "BookHotel",
                "state": "Fulfilled"
            },
            "sessionAttributes": {
                "totalPrice": str(total_price) # Pass total_price as a session attribute
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": confirmation_message
            }
        ]
    }
