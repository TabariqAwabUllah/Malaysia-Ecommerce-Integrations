import requests
import json
import re
import time
import threading
from datetime import datetime, timedelta

# ====================================================================================
# imp notes

# Prerequisites
# Ninja Van Postpaid Pro account.
# Access to Ninja Dashboard. through which we can get {Client_ID} and {Client_Secret}.

# As Documentation says for request access token
# Five minutes before the token expires, or if a request to a Ninja Van API returns an HTTP 401 status code, generate a new token.
# So uncomment everything related to 401

# Replace with your actual Ninja Van credentials
CLIENT_ID = "YOUR_CLIENT_ID"  # Replace with your actual Client ID
CLIENT_SECRET = "YOUR_CLIENT_SECRET"  # Replace
COUNTRY_CODE = "sg"  # Change according to your region (e.g., "my" for Malaysia)

# for testing on sandbox
# Note: All sandbox requests must be sent to the Singapore sandbox API:
BASE_URL_Sandbox = f"https://api-sandbox.ninjavan.co/{COUNTRY_CODE}"


# for production
# BASE_URL = f"https://api.ninjavan.co/{COUNTRY_CODE}"

# Token management
# 401
TOKEN_INFO = {
    "access_token": None,
    "expires_at": None,
    "refresh_timer": None
}

# Validation functions
def validate_phone_number(phone):
    """Validate phone number format."""
    # This pattern can be adjusted based on specific country requirements
    pattern = r'^\+?[0-9]{8,15}$'
    if not re.match(pattern, phone):
        raise ValueError(f"Invalid phone number format: {phone}")
    print("validate_phone_number")        
    return True

def validate_address(address):
    """Validate address is not empty and has minimum length."""
    if not address or len(address.strip()) < 5:
        raise ValueError("Address is too short or empty")
    print("validate_address")
    return True

def validate_dimensions(width, height, depth):
    """Validate parcel dimensions are within reasonable ranges."""
    if not (0 < width <= 200 and 0 < height <= 200 and 0 < depth <= 200):
        raise ValueError(f"Invalid dimensions: width={width}, height={height}, depth={depth}")
    print("validate_dimensions")
    return True

def validate_weight(weight):
    """Validate weight is within reasonable range."""
    if not (0 < weight <= 50):
        raise ValueError(f"Invalid weight: {weight}kg")
    print("validate_weight")
    return True

def validate_tracking_number(tracking_number):
    """Validate tracking number format."""
    if not tracking_number or not re.match(r'^[A-Za-z0-9-]{5,30}$', tracking_number):
        raise ValueError(f"Invalid tracking number format: {tracking_number}")
    print("validate_tracking_number")
    return True

def validate_service_type(service_type):
    """Validate service type is one of the allowed values."""
    allowed_types = ["Standard", "Express", "Parcel", "Same Day"]
    if service_type not in allowed_types:
        raise ValueError(f"Invalid service type: {service_type}. Must be one of {allowed_types}")
    print("validate_service_type")
    return True

def validate_country_code(country_code):
    """Validate country code is supported by Ninja Van."""
    supported_countries = ["sg", "my", "id", "ph", "th", "vn"]
    if country_code.lower() not in supported_countries:
        raise ValueError(f"Unsupported country code: {country_code}. Must be one of {supported_countries}")
    print("validate_country_code")
    return True

# Token management functions
# 401
def schedule_token_refresh():
    """Schedule a token refresh 5 minutes before expiration."""
    if TOKEN_INFO["refresh_timer"] is not None:
        # Cancel any existing timer
        TOKEN_INFO["refresh_timer"].cancel()
    
    # Calculate time until 5 minutes before expiration
    now = datetime.now()
    expires_at = TOKEN_INFO["expires_at"]
    
    if expires_at is None:
        return
    
    refresh_time = expires_at - timedelta(minutes=5)
    seconds_until_refresh = max(0, (refresh_time - now).total_seconds())
    
    # Schedule the refresh
    TOKEN_INFO["refresh_timer"] = threading.Timer(seconds_until_refresh, get_access_token)
    TOKEN_INFO["refresh_timer"].daemon = True
    TOKEN_INFO["refresh_timer"].start()
    print(f"Token refresh scheduled in {seconds_until_refresh:.1f} seconds")

# Step 1: Get Access Token
def get_access_token(force_refresh=False):
    """Get OAuth access token from Ninja Van API."""

    # 401
    # Check if we already have a valid token that's not about to expire    
    if not force_refresh and TOKEN_INFO["access_token"] and TOKEN_INFO["expires_at"]:
        now = datetime.now()
        # If token is still valid and not within 5 minutes of expiration
        if now < TOKEN_INFO["expires_at"] - timedelta(minutes=5):
            return TOKEN_INFO["access_token"]
    
    try:
        # Validate country code before making request
        # validate_country_code(COUNTRY_CODE)

        # for sandbox testing
        TOKEN_URL_Sandbox = f"{BASE_URL_Sandbox}/2.0/oauth/access_token"

        # TOKEN_URL = f"{BASE_URL}/2.0/oauth/access_token"
        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials"
        }

        # Validate credentials are not empty
        if not CLIENT_ID or not CLIENT_SECRET:
            raise ValueError("Client ID and Client Secret cannot be empty")

        # response = requests.post(TOKEN_URL, json=payload)
        response = requests.post(TOKEN_URL_Sandbox, json=payload)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)

        token_data = response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            
            raise ValueError("No access token received in response")
        
        # Get expiration time (default to 1 hour if not provided) 
        # 401
        expires_in = token_data.get("expires_in", 3600)  # Default to 1 hour
        TOKEN_INFO["access_token"] = access_token
        TOKEN_INFO["expires_at"] = datetime.now() + timedelta(seconds=expires_in)
        
        # Schedule a refresh 5 minutes before it expires
        schedule_token_refresh()
        
        print(f"New access token obtained, expires in {expires_in} seconds")
        print("Print 1, access_token",access_token)
        return access_token

    except requests.exceptions.RequestException as e:
        print("Error getting access token:", e)
        return None
    except ValueError as e:
        print("Validation error:", e)
        return None

access_token = get_access_token()

print("access_token universal",access_token)

# Step 2: Create an Order
def create_order(access_token=access_token, service_level="Standard", sender=None, recipient=None, parcel=None, cod_details=None, max_retries=1):
    """Create a new order with validated inputs."""
    # Get a token if not provided
    if access_token is None:
        access_token = get_access_token()

    print("Print 2 createOrder accessToken", access_token)
        
    if not access_token:
        print("Access token is not available in create_order")
        raise ValueError("Access token is required")
    
    # 401, 
    retry_count = 0   
    while retry_count <= max_retries:
        try:
            # for sandbox tesing 
            ORDER_URL_Sandbox = f"{BASE_URL_Sandbox}/4.2/orders"
            print("Print 3 ORDER_URL_Sandbox",ORDER_URL_Sandbox)
            # ORDER_URL = f"{BASE_URL}/4.2/orders"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            
            # Set default values if not provided
            if sender is None:
                sender = {
                    "name": "John Doe",
                    "phone_number": "123456789",
                    "email": "john.doe@gmail.com",
                    "address": {
                    "address1": "17 Lorong Jambu 3",
                    "address2": "",
                    "area": "Taman Sri Delima",
                    "city": "Simpang Ampat",
                    "state": "Pulau Pinang",
                    "address_type": "office",
                    "country": "MY",
                    "postcode": "51200",
                    }
                }
                
            if recipient is None:
                recipient = {
                    "name": "Jane Doe",
                    "phone_number": "987654321",
                    "email": "jane.doe@gmail.com",
                    "address": {
                    "address1": "Jalan PJU 8/8",
                    "address2": "",
                    "area": "Damansara Perdana",
                    "city": "Petaling Jaya",
                    "state": "Selangor",
                    "address_type": "home",
                    "country": "MY",
                    "postcode": "47820"
                    }
                }
                
            if parcel is None:
                parcel={
            "weight": 2.5,
            "dimensions": {
                "width": 30,
                "height": 20,
                "depth": 10
            },
            "item_description": "Electronics",
            "is_pickup_required": False,
            "delivery_start_date": "2021-12-15",
            "delivery_timeslot": {
                "start_time": "09:00",
                "end_time": "12:00",
                "timezone": "Asia/Kuala_Lumpur"
            }
        },
            
            # Validate sender and recipient information
            # validate_phone_number(sender["phone_number"])
            
            # validate_address(sender["address"])
            # validate_phone_number(recipient["phone_number"])
            # validate_address(recipient["address"])
            
            # # Validate service type
            # validate_service_type(service_level)
            
            # # Validate parcel information
            # validate_weight(parcel["weight"])
            # validate_dimensions(
            #     parcel["dimensions"]["width"],
            #     parcel["dimensions"]["height"],
            #     parcel["dimensions"]["depth"]
            # )
            
            # Prepare order payload
            order_payload = {
                "service_type": "Parcel",
                "service_level": service_level,
                "from": sender,
                "to": recipient,
                "parcel_job": parcel,
                
            }

            # print("Print 4 Order Payload:", json.dumps(order_payload, indent=4))
            
            # Add COD details if provided
            if cod_details:
                if "amount" not in cod_details or "currency" not in cod_details:
                    raise ValueError("COD details must include amount and currency")
                
                if not isinstance(cod_details["amount"], (int, float)) or cod_details["amount"] <= 0:
                    raise ValueError(f"Invalid COD amount: {cod_details['amount']}")
                    
                order_payload["parcel_job"]["cash_on_delivery"] = cod_details["amount"]
                order_payload["parcel_job"]["cash_on_delivery_currency"] = cod_details["currency"]

            # response = requests.post(ORDER_URL, json=order_payload, headers=headers)
            print("print 5")
            
            response = requests.post(ORDER_URL_Sandbox, json=order_payload, headers=headers)
            print("before 6 Response .text:", response.text)

            print("Print 6 responce",response)
            
            # Check for 401 unauthorized - token may have expired
            if response.status_code == 401:
                if retry_count < max_retries:
                    print("Received 401 Unauthorized, refreshing token and retrying...")
                    access_token = get_access_token(force_refresh=True)
                    if not access_token:
                        raise ValueError("Failed to refresh access token")
                    retry_count += 1
                    continue
                else:
                    raise ValueError("Maximum retries reached with unauthorized access")
            
            # For other errors, raise normally
            response.raise_for_status()

            print("print 7 response.raise_for_status()", response.raise_for_status())

            order_data = response.json()
            # print("Print 6 order_data",order_data)
            tracking_number = order_data.get("tracking_number")
            
            if not tracking_number:
                raise ValueError("No tracking number received in response")

            print("Order Created Successfully!")
            print("Tracking Number:", tracking_number)
            return tracking_number

        except requests.exceptions.RequestException as e:
            # Check if we should retry for other types of errors
            # 401
            if retry_count < max_retries:
                print(f"Request error (attempt {retry_count+1}/{max_retries+1}): {e}")
                retry_count += 1
                # Small delay before retry
                time.sleep(1)
                continue
            print("Error creating order:", e)
            return None
        except ValueError as e:
            print("Validation error:", e)
            return None

# Step 3: Download Shipping Label
def download_shipping_label(tracking_number, access_token=access_token, file_path="shipping_label.pdf", max_retries=1):
    """Download shipping label for a given tracking number."""
    # Get a token if not provided
    # if access_token is None:
        # access_token = get_access_token()

    print("Print 8 download_shipping_label access_token", access_token)

        
    if not access_token:
        print("Access token is not available in download_shipping_label")
        raise ValueError("Access token is required")
    
    # 401
    retry_count = 0    
    while retry_count <= max_retries:
        try:
            print("Print 9, in download_shipping_label")
            # Validate tracking number
            # validate_tracking_number(tracking_number)

            # for sandbox tesing 
            LABEL_URL_Sandbox = f"{BASE_URL_Sandbox}/2.0/reports/waybill?tid={tracking_number}"

            # LABEL_URL = f"{BASE_URL}/2.0/reports/waybill"

            headers = {
                "Authorization": f"Bearer {access_token}"
            }

            print("Print 10, in download_shipping_label tracking number", tracking_number)
            response = requests.get(LABEL_URL_Sandbox, headers=headers)

            print("after 10, in download_shipping_label response", response.text)
            
            #Check for 401 unauthorized - token may have expired
            if response.status_code == 401:
                if retry_count < max_retries:
                    print("Received 401 Unauthorized, refreshing token and retrying...")
                    access_token = get_access_token(force_refresh=True)
                    if not access_token:
                        print("Failed to refresh access token in download_shipping_label")
                        raise ValueError("Failed to refresh access token")
                    retry_count += 1
                    continue
                else:
                    raise ValueError("Maximum retries reached with unauthorized access")
                    
            # For other errors, raise normally
            print("Print 11, response.raise_for_status() in download_shipping_label", response.raise_for_status())
            response.raise_for_status()
            
            
            # Check if response content is empty
            if not response.content:
                raise ValueError("Empty response received when downloading label")

            with open(file_path, "wb") as file:
                file.write(response.content)

            print(f"Shipping label downloaded: {file_path}")
            return True

        except requests.exceptions.RequestException as e:
            # Check if we should retry for other types of errors
            # 401
            if retry_count < max_retries:
                print(f"⚠️ Request error (attempt {retry_count+1}/{max_retries+1}): {e}")
                retry_count += 1
                # Small delay before retry
                time.sleep(1)
                continue
            print("Error downloading shipping label:", e)
            return False
        except ValueError as e:
            print("Validation error:", e)
            return False

# Run the process
def create_ninja_van_order(
    access_token=access_token,
    service_level="Standard",
    sender=None,
    recipient=None,
    parcel=None,
    cod_details=None,
    label_file_path="shipping_label.pdf",
    max_retries=1
):
    """Main function to create order and download label with validation."""
    try:
        print("print 1 in create_ninja_van_order")
        # Validate country code
        # validate_country_code(COUNTRY_CODE)
        
        # Get access token (will be reused across API calls)
        # access_token = get_access_token()
        if not access_token:
            print("Access token not available in create_ninja_van_order")
            return False
            
        # Create order with provided details
        tracking_number = create_order(
            access_token,
            service_level=service_level,
            sender=sender,
            recipient=recipient,
            parcel=parcel,
            cod_details=cod_details,
            max_retries=max_retries
        )
        
        if not tracking_number:
            return False
            
        # Download shipping label
        success = download_shipping_label(
            tracking_number,
            access_token,
            file_path=label_file_path,
            max_retries=max_retries,
            
        )
        
        return success
        
    except Exception as e:
        print("Unexpected Error:", e)
        return False
# 401
# # Cleanup function for application shutdown
# def cleanup():
#     """Clean up resources when shutting down."""
#     if TOKEN_INFO["refresh_timer"]:
#         TOKEN_INFO["refresh_timer"].cancel()
#         print("🧹 Cancelled token refresh timer")

# # Register cleanup function to run at exit if possible
# try:
#     import atexit
#     atexit.register(cleanup)
# except ImportError:
#     pass

# Example usage
if __name__ == "__main__":
    # Example with all details specified
    create_ninja_van_order(
        service_level="Standard",
        sender={
            "name": "John Doe",
            "phone_number": "81234567",
            "email": "john.doe@gmail.com",
            "address": {
            "address1": "17 Lorong Jambu 3",
            "address2": "",
            "area": "Taman Sri Delima",
            "city": "Simpang Ampat",
            "state": "Pulau Pinang",
            "address_type": "office",
            "country": "MY",
            "postcode": "51200",
            }
        },
        recipient={
            "name": "Jane Doe",
            "phone_number": "98765432",
            "email": "jane.doe@gmail.com",
            "address": {
            "address1": "Jalan PJU 8/8",
            "address2": "",
            "area": "Damansara Perdana",
            "city": "Petaling Jaya",
            "state": "Selangor",
            "address_type": "home",
            "country": "MY",
            "postcode": "47820"
            }
        },
        parcel={
            "dimensions": {
                "weight": 2.5,
                "width": 30,
                "height": 20,
                "depth": 10,
                "size": "L"
            },
            "items": [
                {
                    "item_description": "Electronics",
                    "quantity": 1,
                }
            ],          
            "is_pickup_required": False,
            "delivery_start_date": "2025-03-07",
            "delivery_timeslot": {
                "start_time": "09:00",
                "end_time": "12:00",
                "timezone": "Asia/Kuala_Lumpur"
            }
        },

        
        cod_details={
            "amount": 100.00,
            "currency": "MYR"
        },
        label_file_path="ninja_van_label.pdf"
    )