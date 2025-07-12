# Malaysian Business Integration Suite

A comprehensive Python integration suite for Malaysian businesses, combining **Ninja Van API** for shipping logistics and **LHDN MyInvois API** for e-Invoice compliance. This suite enables businesses to streamline their shipping operations and maintain compliance with Malaysia's e-Invoice requirements.

## Features

### Ninja Van Integration
- **OAuth 2.0 Authentication** - Secure token-based authentication with automatic refresh
- **Order Creation** - Create shipping orders with comprehensive validation
- **Label Generation** - Download shipping labels as PDF files
- **Error Handling** - Robust error handling with automatic retry mechanisms
- **Input Validation** - Comprehensive validation for all input parameters
- **Token Management** - Automatic token refresh before expiration

### LHDN e-Invoice Integration
- **MyInvois API Integration** - Full integration with Malaysia's official e-Invoice system
- **OAuth 2.0 Authentication** - Secure authentication with LHDN's MyInvois platform
- **Invoice Creation** - Create compliant e-Invoices according to LHDN specifications
- **Document Submission** - Submit invoices directly to LHDN for validation
- **Status Tracking** - Check submission status and document processing
- **PDF Generation** - Retrieve official PDF versions of submitted invoices
- **Digital Signatures** - HMAC-SHA256 signature generation for API security
- **Multi-environment Support** - Sandbox and production environment support

## Prerequisites

- Python 3.6 or higher
- **For Ninja Van:**
  - Ninja Van Postpaid Pro account
  - Access to Ninja Van Dashboard to obtain credentials
- **For LHDN e-Invoice:**
  - Registered business with SSM (Companies Commission of Malaysia)
  - MyInvois account with LHDN (Lembaga Hasil Dalam Negeri)
  - API credentials from MyInvois portal

## Installation

1. Clone this repository:
```bash
git clone https://github.com/TabariqAwabUllah/Malaysia-Ecommerce-Integrations.git
cd NinjaVanOrderCreation
```

2. Install required dependencies:
```bash
pip install requests
```

## Configuration

### Ninja Van Setup

1. **Get Your Credentials:**
   - Log in to your Ninja Van Dashboard
   - Navigate to API settings
   - Copy your `Client ID` and `Client Secret`

2. **Update the Configuration:**
   ```python
   CLIENT_ID = "YOUR_CLIENT_ID"        # Replace with your actual Client ID
   CLIENT_SECRET = "YOUR_CLIENT_SECRET" # Replace with your actual Client Secret
   COUNTRY_CODE = "sg"                 # Change according to your region
   ```

### LHDN e-Invoice Setup

1. **Register with MyInvois:**
   - Visit the MyInvois portal
   - Complete business registration
   - Obtain your API credentials

2. **Configure e-Invoice Handler:**
   ```python
   einvoice_handler = LHDNEInvoice(
       client_id="YOUR_MYINVOIS_CLIENT_ID",
       client_secret="YOUR_MYINVOIS_CLIENT_SECRET",
       environment="sandbox"  # Use "production" for live environment
   )
   ```

## Usage

### Ninja Van Integration

#### Basic Usage
```python
from ninjaVanCreatingOrder import create_ninja_van_order

# Create an order with default values
success = create_ninja_van_order()
```

#### Advanced Usage with Custom Details
```python
success = create_ninja_van_order(
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
```

### LHDN e-Invoice Integration

#### Basic e-Invoice Creation and Submission
```python
from lhdn_einvoice import LHDNEInvoice

# Initialize the e-Invoice handler
einvoice_handler = LHDNEInvoice(
    client_id="YOUR_MYINVOIS_CLIENT_ID",
    client_secret="YOUR_MYINVOIS_CLIENT_SECRET",
    environment="sandbox"
)

# Prepare invoice data
invoice_data = {
    "document_type": "INVOICE",
    "invoice_number": "INV-2025-001",
    "invoice_date": "2025-03-07",
    "currency": "MYR",
    
    # Seller information
    "seller_name": "ABC Sdn Bhd",
    "seller_id": "123456789",
    "seller_id_type": "Business Registration",
    "seller_address_line1": "123 Jalan Bukit Bintang",
    "seller_city": "Kuala Lumpur",
    "seller_postcode": "50200",
    "seller_state": "Wilayah Persekutuan",
    "seller_country": "MY",
    "seller_contact_person": "John Doe",
    "seller_email": "accounts@abccompany.com",
    "seller_phone": "+60312345678",
    
    # Buyer information
    "buyer_name": "XYZ Corporation",
    "buyer_id": "987654321",
    "buyer_id_type": "Business Registration",
    "buyer_address_line1": "456 Jalan Ampang",
    "buyer_city": "Kuala Lumpur",
    "buyer_postcode": "50450",
    "buyer_state": "Wilayah Persekutuan",
    "buyer_country": "MY",
    "buyer_contact_person": "Jane Smith",
    "buyer_email": "finance@xyzcorp.com",
    "buyer_phone": "+60323456789",
    
    # Payment information
    "payment_method": "BANK_TRANSFER",
    "payment_due_date": "2025-04-06",
    "payment_terms": "30 days",
    
    # Line items
    "items": [
        {
            "description": "Office Desk",
            "quantity": 2,
            "price": 1200.00,
            "tax_rate": 6
        },
        {
            "description": "Office Chair",
            "quantity": 4,
            "price": 450.00,
            "tax_rate": 6
        }
    ]
}

# Create and submit the invoice
invoice = einvoice_handler.create_invoice(invoice_data)
submission_result = einvoice_handler.submit_invoice(invoice)

if submission_result.get("success"):
    print(f"Invoice submitted successfully!")
    print(f"Transaction ID: {submission_result.get('submission_id')}")
    
    # Check status
    status = einvoice_handler.get_invoice_status(submission_result.get('submission_id'))
    print(f"Status: {status}")
    
    # Download PDF
    pdf_result = einvoice_handler.get_invoice_pdf(invoice['documentNumber'])
    if pdf_result.get("success"):
        with open(f"{invoice['documentNumber']}.pdf", "wb") as pdf_file:
            pdf_file.write(pdf_result.get("content"))
        print(f"PDF saved as {invoice['documentNumber']}.pdf")
```

#### Individual e-Invoice Functions
```python
# Get access token
access_token = einvoice_handler.get_access_token()

# Create invoice structure
invoice = einvoice_handler.create_invoice(invoice_data)

# Submit invoice to LHDN
submission_result = einvoice_handler.submit_invoice(invoice)

# Check submission status
status = einvoice_handler.get_invoice_status(transaction_id)

# Download PDF version
pdf_result = einvoice_handler.get_invoice_pdf(document_number)
```

## API Functions

### Ninja Van Functions

#### `get_access_token(force_refresh=False)`
- Obtains OAuth 2.0 access token
- Automatically refreshes token before expiration
- Returns: Access token string or None

#### `create_order(access_token, service_level, sender, recipient, parcel, cod_details, max_retries)`
- Creates a new shipping order
- Returns: Tracking number string or None

#### `download_shipping_label(tracking_number, access_token, file_path, max_retries)`
- Downloads shipping label as PDF
- Returns: Boolean indicating success

#### `create_ninja_van_order(...)`
- Main function that combines order creation and label download
- Returns: Boolean indicating overall success

### LHDN e-Invoice Functions

#### `LHDNEInvoice(client_id, client_secret, environment)`
- Initialize the e-Invoice handler
- Parameters: client credentials and environment ("sandbox" or "production")

#### `get_access_token()`
- Obtains OAuth 2.0 access token from LHDN
- Automatically manages token expiration
- Returns: Access token string or None

#### `create_invoice(invoice_data)`
- Creates properly formatted invoice payload
- Validates and structures data according to LHDN specifications
- Returns: Formatted invoice dictionary

#### `submit_invoice(invoice)`
- Submits e-Invoice to LHDN MyInvois system
- Includes digital signature generation
- Returns: Submission result with transaction ID

#### `get_invoice_status(transaction_id)`
- Checks the processing status of submitted invoice
- Returns: Status information and document details

#### `get_invoice_pdf(document_number)`
- Retrieves official PDF version of submitted invoice
- Returns: PDF content as bytes

#### `generate_signature(method, url_path, payload, timestamp)`
- Generates HMAC-SHA256 digital signature for API requests
- Returns: Headers with signature information

## Validation Features

### Ninja Van Validation
- **Phone Numbers**: Format validation with international support
- **Addresses**: Minimum length and content validation
- **Dimensions**: Weight and size limits (max 50kg, 200cm per dimension)
- **Service Types**: Standard, Express, Parcel, Same Day
- **Country Codes**: Supported Ninja Van regions
- **Tracking Numbers**: Format validation

### e-Invoice Validation
- **Business Registration**: Validates seller and buyer identification
- **Tax Calculations**: Automatic GST/SST calculation and validation
- **Currency Support**: MYR currency validation
- **Date Formats**: ISO date format validation
- **Digital Signatures**: HMAC-SHA256 signature validation
- **Document Structure**: LHDN specification compliance

## Error Handling

### Ninja Van
- **Automatic Retry**: Failed requests are automatically retried
- **Token Refresh**: Expired tokens are automatically refreshed
- **Comprehensive Logging**: Detailed error messages and status updates
- **Graceful Degradation**: Continues operation despite non-critical errors

### e-Invoice
- **OAuth Token Management**: Automatic token refresh and error handling
- **API Rate Limiting**: Handles rate limiting responses
- **Signature Validation**: Ensures request authenticity
- **Status Monitoring**: Tracks document processing status
- **Comprehensive Error Reporting**: Detailed error codes and messages

## Environment Support

### Ninja Van
#### Sandbox Testing
```python
BASE_URL_Sandbox = f"https://api-sandbox.ninjavan.co/{COUNTRY_CODE}"
```

#### Production
```python
BASE_URL = f"https://api.ninjavan.co/{COUNTRY_CODE}"
```

### LHDN e-Invoice
#### Sandbox Testing
```python
base_url = "https://sandbox-myinvois-api.hasil.gov.my"
token_url = "https://sandbox-myinvois-api.hasil.gov.my/connect/token"
```

#### Production
```python
base_url = "https://myinvois-api.hasil.gov.my"
token_url = "https://myinvois-api.hasil.gov.my/oauth/token"
```

## Supported Features

### Ninja Van
- **Service Levels**: Standard, Express, Parcel, Same Day
- **COD Support**: Cash on Delivery with multiple currencies
- **Country Support**: Singapore, Malaysia, Indonesia, Philippines, Thailand, Vietnam

### e-Invoice
- **Document Types**: INVOICE, CREDIT_NOTE, DEBIT_NOTE
- **Tax Types**: GST, SST, Service Tax
- **Payment Methods**: Bank Transfer, Cash, Credit Card, Cheque
- **Multi-language Support**: English, Bahasa Malaysia
- **Currency**: Malaysian Ringgit (MYR)

## File Structure

```
NinjaVanOrderCreation/
│
├── ninjaVanCreatingOrder.py    # Ninja Van API integration
├── lhdn_einvoice.py           # LHDN e-Invoice integration
├── README.md                  # This documentation file

```

## Complete Business Workflow Example

```python
# Complete workflow: Create order, generate invoice, submit to LHDN
from ninjaVanCreatingOrder import create_ninja_van_order
from lhdn_einvoice import LHDNEInvoice

# Step 1: Create shipping order
shipping_success = create_ninja_van_order(
    service_level="Standard",
    sender=sender_data,
    recipient=recipient_data,
    parcel=parcel_data,
    cod_details=cod_data
)

if shipping_success:
    print("✅ Shipping order created successfully!")
    
    # Step 2: Generate e-Invoice
    einvoice_handler = LHDNEInvoice(
        client_id="YOUR_MYINVOIS_CLIENT_ID",
        client_secret="YOUR_MYINVOIS_CLIENT_SECRET",
        environment="sandbox"
    )
    
    invoice = einvoice_handler.create_invoice(invoice_data)
    submission_result = einvoice_handler.submit_invoice(invoice)
    
    if submission_result.get("success"):
        print("✅ e-Invoice submitted successfully!")
        print(f"📋 Transaction ID: {submission_result.get('submission_id')}")
        
        # Step 3: Download invoice PDF
        pdf_result = einvoice_handler.get_invoice_pdf(invoice['documentNumber'])
        if pdf_result.get("success"):
            with open(f"invoice_{invoice['documentNumber']}.pdf", "wb") as pdf_file:
                pdf_file.write(pdf_result.get("content"))
            print(f"📄 Invoice PDF saved successfully!")
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues related to:
- **This Integration**: Create an issue on GitHub
- **Ninja Van API**: Contact Ninja Van support
- **LHDN e-Invoice**: Contact LHDN MyInvois support
- **API Documentation**: 
  - Ninja Van: [Developer Portal](https://api-docs.ninjavan.co/)
  - LHDN: [MyInvois API Documentation](https://sdk.myinvois.hasil.gov.my/einvoicingapi/)

## Changelog

### v2.0.0
- ✨ Added LHDN e-Invoice integration
- ✨ Added digital signature generation
- ✨ Added multi-environment support for e-Invoice
- ✨ Added PDF generation for invoices
- ✨ Added comprehensive invoice validation
- 🔧 Enhanced error handling across both integrations

### v1.0.0
- 🎉 Initial release
- ✅ Ninja Van OAuth 2.0 authentication
- ✅ Order creation and label download
- ✅ Comprehensive validation
- ✅ Error handling and retry mechanisms

## Compliance and Legal

### e-Invoice Compliance
- **LHDN Approved**: This integration follows LHDN's official MyInvois API specifications
- **Digital Signature**: Uses HMAC-SHA256 for secure API communication
- **Tax Compliance**: Supports Malaysian GST/SST tax calculations
- **Audit Trail**: Maintains complete transaction logs for compliance

### Data Security
- **OAuth 2.0**: Secure authentication protocols
- **Token Management**: Automatic token refresh and secure storage
- **API Rate Limiting**: Respects API rate limits and usage policies
- **Error Logging**: Comprehensive logging without exposing sensitive data

## Acknowledgments

- Ninja Van for providing the shipping API
- LHDN (Lembaga Hasil Dalam Negeri) for the MyInvois e-Invoice system
- Contributors and testers
- Malaysian business community for feedback and requirements

## Security Notes

- Never commit your actual credentials to version control
- Use environment variables for production deployments
- Regularly rotate your API credentials
- Monitor API usage and logs for suspicious activity
- Keep your integration updated with latest security patches

---

**Note**: This integration suite is designed for Malaysian businesses requiring both shipping logistics and e-Invoice compliance. Ensure your business is registered with the appropriate authorities before using the e-Invoice functionality.
