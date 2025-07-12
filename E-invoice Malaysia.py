import requests
import json
import datetime
import uuid
import base64
import logging
import hmac
import hashlib

class LHDNEInvoice:
    """
    A class to handle integration with LHDN's MyInvois e-Invoicing API.
    Based on the documentation at https://sdk.myinvois.hasil.gov.my/einvoicingapi/
    """
    
    def __init__(self, client_id, client_secret, environment="sandbox"):
        """
        Initialize the LHDN e-Invoice handler.
        
        Args:
            client_id (str): OAuth client ID provided by LHDN
            client_secret (str): OAuth client secret provided by LHDN
            environment (str): "sandbox" or "production"
        """
        self.client_id = client_id
        self.client_secret = client_secret
        
        # Set the appropriate base URLs based on environment
        if environment.lower() == "production":
            self.base_url = "https://myinvois-api.hasil.gov.my"
            self.token_url = "https://myinvois-api.hasil.gov.my/oauth/token"
        else:
            self.base_url = "https://sandbox-myinvois-api.hasil.gov.my"
            self.token_url = "https://sandbox-myinvois-api.hasil.gov.my/connect/token"
            
        self.access_token = None
        self.token_expiry = None
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('LHDNEInvoice')
    
    def get_access_token(self):
        """
        Obtain an OAuth access token from LHDN.
        
        Returns:
            str: The access token if successful, None otherwise
        """
        # Check if we already have a valid token
        if self.access_token and self.token_expiry and datetime.datetime.now() < self.token_expiry:
            return self.access_token
            
        # Prepare token request
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        try:
            response = requests.post(self.token_url, data=payload, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            
            # Calculate token expiry time (usually 1 hour)
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
            
            self.logger.info("Successfully obtained access token")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to obtain access token: {str(e)}")
            if response:
                self.logger.error(f"Response: {response.text}")
            return None
    
    def create_invoice(self, invoice_data):
        """
        Create a properly formatted invoice payload according to MyInvois API specifications.
        
        Args:
            invoice_data (dict): Basic invoice information
            
        Returns:
            dict: Properly formatted document payload for the API
        """
        # Generate a document ID if not provided
        document_number = invoice_data.get("invoice_number", f"INV-{uuid.uuid4().hex[:8].upper()}")
        
        # Format the date correctly (YYYY-MM-DD)
        if "invoice_date" in invoice_data:
            document_date = invoice_data["invoice_date"]
        else:
            document_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Calculate total amounts
        items = invoice_data.get("items", [])
        total_amount_excluding_tax = sum(item.get("price", 0) * item.get("quantity", 0) for item in items)
        total_tax_amount = sum((item.get("price", 0) * item.get("quantity", 0) * item.get("tax_rate", 0) / 100) for item in items)
        total_amount_including_tax = total_amount_excluding_tax + total_tax_amount
        
        # Create document payload
        # Structure the invoice according to LHDN's e-Invoice format
        einvoice = {
            "documentType": invoice_data.get("document_type", "INVOICE"),
            "documentNumber": document_number,
            "documentDate": document_date,
            "currency": invoice_data.get("currency", "MYR"),
            "seller": {
                "name": invoice_data.get("seller_name", ""),
                "identificationNumber": invoice_data.get("seller_id", ""),
                "identificationType": invoice_data.get("seller_id_type", "Business Registration"),
                "address": {
                    "line1": invoice_data.get("seller_address_line1", ""),
                    "line2": invoice_data.get("seller_address_line2", ""),
                    "city": invoice_data.get("seller_city", ""),
                    "postcode": invoice_data.get("seller_postcode", ""),
                    "state": invoice_data.get("seller_state", ""),
                    "country": invoice_data.get("seller_country", "MY")
                },
                "contactPerson": invoice_data.get("seller_contact_person", ""),
                "email": invoice_data.get("seller_email", ""),
                "phoneNumber": invoice_data.get("seller_phone", "")
            },
            "buyer": {
                "name": invoice_data.get("buyer_name", ""),
                "identificationNumber": invoice_data.get("buyer_id", ""),
                "identificationType": invoice_data.get("buyer_id_type", "Business Registration"),
                "address": {
                    "line1": invoice_data.get("buyer_address_line1", ""),
                    "line2": invoice_data.get("buyer_address_line2", ""),
                    "city": invoice_data.get("buyer_city", ""),
                    "postcode": invoice_data.get("buyer_postcode", ""),
                    "state": invoice_data.get("buyer_state", ""),
                    "country": invoice_data.get("buyer_country", "MY")
                },
                "contactPerson": invoice_data.get("buyer_contact_person", ""),
                "email": invoice_data.get("buyer_email", ""),
                "phoneNumber": invoice_data.get("buyer_phone", "")
            },
            "items": [],
            "paymentInfo": {
                "method": invoice_data.get("payment_method", ""),
                "dueDate": invoice_data.get("payment_due_date", ""),
                "terms": invoice_data.get("payment_terms", "")
            },
            "totalAmountExcludingTax": total_amount_excluding_tax,
            "totalTaxAmount": total_tax_amount,
            "totalAmountIncludingTax": total_amount_including_tax
        }
        
        # Add line items
        
        for idx, item in enumerate(items, 1):
            line_amount = item.get("price", 0) * item.get("quantity", 0)
            tax_amount = line_amount * (item.get("tax_rate", 0) / 100)
            
            line_item = {
                "itemNumber": idx,
                "description": item.get("description", ""),
                "quantity": item.get("quantity", 0),
                "unitPrice": item.get("price", 0),
                "taxRate": item.get("tax_rate", 0),
                "taxAmount": tax_amount,
                "totalAmount": line_amount + tax_amount
            }
            einvoice["items"].append(line_item)
        
        return einvoice
    
    def generate_signature(self, method, url_path, payload=None, timestamp=None):
        """
        Generate the required signature for API requests.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            url_path (str): The URL path (without base URL)
            payload (dict, optional): Request payload for POST requests
            timestamp (str, optional): Timestamp in ISO format, defaults to current time
            
        Returns:
            dict: Headers with signature information
        """ 
        # Use provided timestamp or generate current timestamp
        if not timestamp:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Create the string to sign
        string_to_sign = method.upper() + "\n"
        string_to_sign += url_path + "\n"
        string_to_sign += timestamp + "\n"
        
        # If payload exists, add it to the string to sign (for POST requests)
        if payload and isinstance(payload, dict):
            payload_json = json.dumps(payload, separators=(',', ':'))
            string_to_sign += payload_json
        
        # Generate HMAC signature using client secret as the key
        signature = hmac.new(
            self.client_secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Create headers with the signature
        headers = {
            "X-Timestamp": timestamp,
            "X-Signature": signature,
            "X-Client-ID": self.client_id
        }
        
        return headers

    def submit_invoice(self, invoice):
        """
        Submit an e-Invoice document to LHDN's MyInvois API.
        
        Args:
            invoice (dict): The invoice data to submit
            
        Returns:
            dict: Response from the MyInvois API
        """
        # Get a valid access token
        token = self.get_access_token()
        if not token:
            return {
                "success": False,
                "error_message": "Failed to obtain access token"
            }
        
        # API endpoint path (without base URL)
        endpoint_path = "/einvoice/document/submit"
        
        # Full URL
        submit_url = f"{self.base_url}{endpoint_path}"
        
        # Generate signature headers
        signature_headers = self.generate_signature(
            method="POST",
            url_path=endpoint_path,
            payload=invoice
        )
        
        # Combine signature headers with other required headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Correlation-ID": str(uuid.uuid4())
        }
        headers.update(signature_headers)
        
        try:
            response = requests.post(
                submit_url,
                headers=headers,
                data=json.dumps(invoice)
            )
            
            # Process the response
            if response.status_code in [200, 201, 202]:
                response_data = response.json()
                self.logger.info(f"Invoice submitted successfully: {response_data}")
                return {
                    "success": True,
                    "invoice_id": invoice.get("documentNumber"),
                    "submission_id": response_data.get("transactionId"),
                    "status": response_data.get("status"),
                    "message": response_data.get("message", ""),
                    "details": response_data
                }
            else:
                error_message = "Unknown error"
                error_details = {}
                try:
                    error_details = response.json()
                    error_message = error_details.get("message", "Unknown error")
                except:
                    error_message = response.text
                
                self.logger.error(f"Invoice submission failed: {error_message}")
                return {
                    "success": False,
                    "error_code": response.status_code,
                    "error_message": error_message,
                    "error_details": error_details
                }
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Exception during invoice submission: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            }
        
    def get_invoice_status(self, transaction_id):
        """
        Check the status of a previously submitted invoice.
        
        Args:
            transaction_id (str): The transaction ID returned from submit_invoice
            
        Returns:
            dict: Status information from the MyInvois API
        """
        # Get a valid access token
        token = self.get_access_token()
        if not token:
            return {
                "success": False,
                "error_message": "Failed to obtain access token"
            }
        
        # API endpoint path (without base URL)
        endpoint_path = f"/einvoice/submission/{transaction_id}"
        
        # Full URL
        status_url = f"{self.base_url}{endpoint_path}"
        
        # Generate signature headers
        signature_headers = self.generate_signature(
            method="GET",
            url_path=endpoint_path
        )
        
        # Combine signature headers with other required headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "X-Correlation-ID": str(uuid.uuid4())
        }
        headers.update(signature_headers)
        
        try:
            response = requests.get(status_url, headers=headers)
            
            if response.status_code == 200:
                status_data = response.json()
                self.logger.info(f"Status check successful: {status_data}")
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "status": status_data.get("status"),
                    "document_number": status_data.get("documentNumber", ""),
                    "submission_date": status_data.get("submissionDate", ""),
                    "document_status": status_data.get("documentStatus", ""),
                    "message": status_data.get("message", ""),
                    "details": status_data
                }
            else:
                error_message = "Unknown error"
                try:
                    error_details = response.json()
                    error_message = error_details.get("message", "Unknown error")
                except:
                    error_message = response.text
                
                self.logger.error(f"Status check failed: {error_message}")
                return {
                    "success": False,
                    "transaction_id": transaction_id,
                    "error_code": response.status_code,
                    "error_message": error_message
                }
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Exception during status check: {str(e)}")
            return {
                "success": False,
                "transaction_id": transaction_id,
                "error_message": str(e)
            }
    
    def get_invoice_pdf(self, document_number):
        """
        Retrieve a PDF version of the submitted invoice based on document number.
        First gets the document details, then retrieves the PDF if available.
        
        Args:
            document_number (str): The document number of the invoice
            
        Returns:
            dict: PDF content if successful, error details if not
        """
        # Get a valid access token
        token = self.get_access_token()
        if not token:
            return {
                "success": False,
                "error_message": "Failed to obtain access token"
            }
        
        # API endpoint path for document details (without base URL)
        details_endpoint_path = f"/einvoice/document/{document_number}"
        
        # Full URL for document details
        details_url = f"{self.base_url}{details_endpoint_path}"
        
        # Generate signature headers for document details request
        details_signature_headers = self.generate_signature(
            method="GET",
            url_path=details_endpoint_path
        )
        
        # Combine signature headers with other required headers for document details
        details_headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "X-Correlation-ID": str(uuid.uuid4())
        }
        details_headers.update(details_signature_headers)
        
        try:
            # Get document details first
            details_response = requests.get(details_url, headers=details_headers)
            
            if details_response.status_code != 200:
                error_message = "Unknown error"
                try:
                    error_details = details_response.json()
                    error_message = error_details.get("message", "Unknown error")
                except:
                    error_message = details_response.text
                
                self.logger.error(f"Document details retrieval failed: {error_message}")
                return {
                    "success": False,
                    "document_number": document_number,
                    "error_code": details_response.status_code,
                    "error_message": error_message
                }
            
            # Document details retrieved, now get PDF
            details_data = details_response.json()
            
            # API endpoint path for PDF retrieval (without base URL)
            pdf_endpoint_path = f"/einvoice/document/{document_number}/pdf"
            
            # Full URL for PDF retrieval
            pdf_url = f"{self.base_url}{pdf_endpoint_path}"
            
            # Generate signature headers for PDF request
            pdf_signature_headers = self.generate_signature(
                method="GET",
                url_path=pdf_endpoint_path
            )
            
            # Combine signature headers with other required headers for PDF request
            pdf_headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/pdf",
                "X-Correlation-ID": str(uuid.uuid4())
            }
            pdf_headers.update(pdf_signature_headers)
            
            pdf_response = requests.get(pdf_url, headers=pdf_headers)
            
            if pdf_response.status_code == 200:
                return {
                    "success": True,
                    "document_number": document_number,
                    "document_type": details_data.get("documentType", ""),
                    "document_date": details_data.get("documentDate", ""),
                    "content": pdf_response.content,
                    "content_type": pdf_response.headers.get("Content-Type", "application/pdf")
                }
            else:
                error_message = "Unknown error"
                try:
                    error_details = pdf_response.json()
                    error_message = error_details.get("message", "Unknown error")
                except:
                    error_message = pdf_response.text
                
                self.logger.error(f"PDF retrieval failed: {error_message}")
                return {
                    "success": False,
                    "document_number": document_number,
                    "error_code": pdf_response.status_code,
                    "error_message": error_message
                }
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Exception during document retrieval: {str(e)}")
            return {
                "success": False,
                "document_number": document_number,
                "error_message": str(e)
            }

            
    # def cancel_invoice(self, invoice_id, reason):
    #     """
    #     Cancel a previously issued invoice.
        
    #     Args:
    #         invoice_id (str): The ID of the invoice to cancel
    #         reason (str): Reason for cancellation
            
    #     Returns:
    #         dict: Cancellation result
    #     """
    #     # Get a valid access token
    #     token = self.get_access_token()
    #     if not token:
    #         return {
    #             "success": False,
    #             "error_message": "Failed to obtain access token"
    #         }
        
    #     # Prepare headers
    #     headers = {
    #         "Authorization": f"Bearer {token}",
    #         "Content-Type": "application/json",
    #         "Accept": "application/json",
    #         "X-Correlation-ID": str(uuid.uuid4())
    #     }
        
    #     # Payload for cancellation
    #     payload = {
    #         "documentNumber": invoice_id,
    #         "reason": reason,
    #         "cancellationDate": datetime.datetime.now().strftime("%Y-%m-%d")
    #     }
        
    #     # Endpoint for cancellation
    #     cancel_url = f"{self.base_url}/einvoice/document/cancel"
        
    #     try:
    #         response = requests.post(
    #             cancel_url,
    #             headers=headers,
    #             data=json.dumps(payload)
    #         )
            
    #         if response.status_code == 200:
    #             response_data = response.json()
    #             self.logger.info(f"Invoice cancelled successfully: {response_data}")
    #             return {
    #                 "success": True,
    #                 "invoice_id": invoice_id,
    #                 "status": "Cancelled",
    #                 "message": response_data.get("message", "Invoice successfully cancelled"),
    #                 "details": response_data
    #             }
    #         else:
    #             error_message = "Unknown error"
    #             try:
    #                 error_details = response.json()
    #                 error_message = error_details.get("message", "Unknown error")
    #             except:
    #                 error_message = response.text
                
    #             self.logger.error(f"Invoice cancellation failed: {error_message}")
    #             return {
    #                 "success": False,
    #                 "invoice_id": invoice_id,
    #                 "error_code": response.status_code,
    #                 "error_message": error_message
    #             }
                
    #     except requests.exceptions.RequestException as e:
    #         self.logger.error(f"Exception during invoice cancellation: {str(e)}")
    #         return {
    #             "success": False,
    #             "invoice_id": invoice_id,
    #             "error_message": str(e)
    #         }


# Example usage
if __name__ == "__main__":
    # Initialize the LHDN e-Invoice handler
    einvoice_handler = LHDNEInvoice(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        environment="sandbox"  # Use "production" for live environment
    )
    
    # Sample invoice data
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
        "seller_address_line2": "",
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
        "buyer_address_line2": "",
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
    
    # Create the invoice
    invoice = einvoice_handler.create_invoice(invoice_data)
    print(f"Invoice created with ID: {invoice['documentNumber']}")
    
    # Submit the invoice
    submission_result = einvoice_handler.submit_invoice(invoice)
    print(f"Submission result: {submission_result}")
    
    # Check status (in a real implementation, this would typically be done later)
    if submission_result.get("success"):
        transaction_id = submission_result.get("submission_id")
        status = einvoice_handler.get_invoice_status(transaction_id)
        print(f"Invoice status: {status}")
        
        # Get PDF version
        invoice_id = invoice["documentNumber"]
        pdf_result = einvoice_handler.get_invoice_pdf(invoice_id)
        if pdf_result.get("success"):
            # Save the PDF
            with open(f"{invoice_id}.pdf", "wb") as pdf_file:
                pdf_file.write(pdf_result.get("content"))
            print(f"PDF saved as {invoice_id}.pdf")