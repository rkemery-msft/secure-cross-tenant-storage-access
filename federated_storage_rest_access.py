# -----------------------------------------------------------------------------
# Script Name: federated_storage_rest_access.py
# Description: Demonstrates accessing Azure Storage in a Customer Tenant (Tenant B)
#              from a Provider Tenant (Tenant A) using:
#              1. A User-Assigned Managed Identity (UAMI) in Tenant A.
#              2. Workload Identity Federation configured on an App Registration
#                 in Tenant A, trusting the UAMI.
#              3. Consent granted to the App Registration in Tenant B.
#              4. RBAC roles assigned to the resulting Enterprise App in Tenant B
#                 on the Storage Account.
#              5. Direct REST API calls to Azure Storage, authenticated with the
#                 federated token obtained via token exchange.
#              NOTE: This script avoids using azure.storage.blob.BlobServiceClient
#                    and uses requests/xml libraries for storage interaction.
# -----------------------------------------------------------------------------

import requests # Library for making HTTP requests (token exchange, REST API)
import os # Used here primarily for path manipulation if needed, not essential
import traceback # Library for printing detailed error stack traces
import xml.etree.ElementTree as ET # Library for parsing the XML response from Storage REST API
from azure.identity import ManagedIdentityCredential, get_bearer_token_provider # For UAMI auth & token fetching

# --- Configuration ---
# IMPORTANT: Replace ALL placeholder values below with your actual resource details.

# == Tenant B (Customer - where Storage Account resides) ==
CUSTOMER_TENANT_ID = "{CUSTOMER_TENANT_ID}" # Example: "00000000-0000-0000-0000-000000000001"
CUSTOMER_STORAGE_ACCOUNT_NAME = "{CUSTOMER_STORAGE_ACCOUNT_NAME}" # Example: "custstorageacct"
CUSTOMER_CONTAINER_NAME = "{CUSTOMER_CONTAINER_NAME}" # Example: "custcontainer"

# == Tenant A (Provider - where Managed Identity and App Registration reside) ==
PROVIDER_TENANT_ID = "{PROVIDER_TENANT_ID}" # Example: "00000000-0000-0000-0000-000000000001" - Needed for Fed Cred Issuer verification conceptually, not directly in this script's calls
UAMI_CLIENT_ID = "{UAMI_CLIENT_ID}" # Client ID of the User-Assigned Managed Identity assigned to the VM/resource running this script
APP_REG_CLIENT_ID = "{APP_REG_CLIENT_ID}" # Client ID of the multi-tenant App Registration in Tenant A that has the Federated Credential configured

# == Federation & Scopes ==
# Audience value configured in the Federated Credential on the App Registration in Tenant A
FEDERATION_AUDIENCE = "api://AzureADTokenExchange"
# Scope required for the final token to access Azure Storage
STORAGE_SCOPE = "https://storage.azure.com/.default"
# Scope/Resource identifier used to get the initial MI token for the exchange process
# Must match the audience the Federated Credential expects. Appending /.default is standard for requesting OAuth scopes.
MI_EXCHANGE_SCOPE = f"{FEDERATION_AUDIENCE}/.default"

# == Azure Storage REST API Configuration ==
# Use a recent, valid version. Check Azure Storage documentation for current versions.
# Ref: https://learn.microsoft.com/en-us/rest/api/storageservices/versioning-for-the-azure-storage-services
STORAGE_REST_API_VERSION = "2023-11-03"


# --- Step 1: Prepare Managed Identity Authentication ---
# Get a credential object representing the specified User-Assigned Managed Identity.
# Then, create a helper function (provider) that can be called later to get
# a token specifically for the 'MI_EXCHANGE_SCOPE'.
print("-" * 60)
print(f"[Step 1] Preparing Managed Identity credential (Client ID: {UAMI_CLIENT_ID})")
print(f"         Target scope for initial token: {MI_EXCHANGE_SCOPE}")
print("-" * 60)
mi_token_provider = None
try:
    # Create the credential object for the specific UAMI
    mi_credential = ManagedIdentityCredential(client_id=UAMI_CLIENT_ID)

    # Create the provider function using the credential and the required scope/audience
    # This doesn't fetch the token yet, it just prepares the function.
    mi_token_provider = get_bearer_token_provider(mi_credential, MI_EXCHANGE_SCOPE)

    print("[Step 1] Managed Identity credential and token provider created successfully.")

except Exception as e:
    print(f"[Step 1] FATAL ERROR: Could not create Managed Identity credential or token provider.")
    print(f"         Error: {e}")
    print("-" * 60)
    traceback.print_exc()
    print("-" * 60)
    exit(1) # Cannot proceed without the initial credential


# --- Step 2: Exchange MI Token for Federated Token (in Customer Tenant B) ---
# Call the provider function created in Step 1 to get the actual MI token string.
# Send this token (as a client_assertion) to the Customer Tenant's token endpoint.
# The client_id identifies the Provider's App Reg which has the federation configured.
# Tenant B's Entra ID validates the assertion against the federation config and issues
# a new token if valid, scoped for Azure Storage.
print("\n" + "-" * 60)
print(f"[Step 2] Exchanging MI token for a federated token from Customer Tenant: {CUSTOMER_TENANT_ID}")
print(f"         Using Provider App Reg Client ID: {APP_REG_CLIENT_ID}")
print(f"         Requesting scope for Storage: {STORAGE_SCOPE}")
print("-" * 60)
federated_token_string = None
try:
    # Define the Customer Tenant's token endpoint URL
    token_url = f"https://login.microsoftonline.com/{CUSTOMER_TENANT_ID}/oauth2/v2.0/token"

    # Prepare headers for the POST request
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # Call the provider function NOW to get the actual token string from the UAMI
    print("[Step 2] Calling MI token provider function to get assertion token...")
    mi_token_string = mi_token_provider()
    print("[Step 2] Assertion token acquired from Managed Identity.")

    # Prepare the data payload for the token exchange request
    data = {
        "client_id": APP_REG_CLIENT_ID, # Client ID of the Provider's App Reg (links to federation config)
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer", # Indicates assertion type
        "client_assertion": mi_token_string, # The actual token obtained from the UAMI
        "scope": STORAGE_SCOPE, # The scope needed for the final token (Storage access)
        "grant_type": "client_credentials" # Standard grant type for this flow
    }

    # Make the POST request to exchange the token
    print(f"[Step 2] Posting request to token endpoint: {token_url}")
    response = requests.post(token_url, headers=headers, data=data)
    response.raise_for_status() # Raise an HTTPError if the status code is 4xx or 5xx

    # Extract the final access token (federated token) from the JSON response
    federated_token_string = response.json()["access_token"]
    print("[Step 2] Federated token acquired successfully from customer tenant.")

except Exception as e:
    # Catch potential errors from mi_token_provider() or requests.post()
    print(f"[Step 2] FATAL ERROR: Could not exchange token.")
    print(f"         Error: {e}")
    # If it was an HTTP error from requests, print response details
    if isinstance(e, requests.exceptions.RequestException) and e.response is not None:
        print(f"         Response Status Code: {e.response.status_code}")
        print(f"         Response Body:\n{e.response.text}")
    print("-" * 60)
    traceback.print_exc()
    print("-" * 60)
    exit(1) # Cannot proceed without the federated token


# --- Step 3: Use Federated Token with Azure Storage REST API ---
# Use the federated token obtained in Step 2 to make direct REST API calls
# to the Azure Storage service in the Customer Tenant.
print("\n" + "-" * 60)
print(f"[Step 3] Accessing Storage Account '{CUSTOMER_STORAGE_ACCOUNT_NAME}' via REST API")
print(f"         Listing blobs in container: '{CUSTOMER_CONTAINER_NAME}'")
print(f"         Using REST API Version: {STORAGE_REST_API_VERSION}")
print("-" * 60)
try:
    # Construct the URL for the List Blobs operation
    # Ref: https://learn.microsoft.com/en-us/rest/api/storageservices/list-blobs
    list_blobs_url = f"https://{CUSTOMER_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{CUSTOMER_CONTAINER_NAME}"
    list_blobs_params = {
        "restype": "container", # Required parameter for container operations
        "comp": "list"          # Specifies the 'list blobs' component/operation
    }

    # Prepare the necessary HTTP headers for the authenticated REST API call
    rest_headers = {
        # Use the federated token obtained in Step 2 for Authorization
        "Authorization": f"Bearer {federated_token_string}",
        # Azure Storage REST APIs require the version to be specified
        "x-ms-version": STORAGE_REST_API_VERSION,
        # Specify that we expect an XML response (List Blobs returns XML)
        "Accept": "application/xml"
        # Optionally add 'x-ms-date' header if needed:
        # "x-ms-date": datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'),
    }

    # Make the GET request to the List Blobs endpoint
    print(f"[Step 3] Making GET request to: {list_blobs_url} with specified params")
    rest_response = requests.get(list_blobs_url, headers=rest_headers, params=list_blobs_params)
    rest_response.raise_for_status() # Check for HTTP errors (like 403 Forbidden, 404 Not Found, etc.)

    print("[Step 3] REST API call successful (Status Code: {}).".format(rest_response.status_code))

    # --- Parse the XML Response ---
    print("[Step 3] Parsing XML response...")
    # Ensure correct encoding; requests usually detects it, but explicitly setting can help if needed
    # rest_response.encoding = 'utf-8'
    xml_root = ET.fromstring(rest_response.text)

    # Find all 'Name' elements within 'Blob' elements under the 'Blobs' container
    # Basic XPath-like query. Might need namespace handling {namespace}Blob/{namespace}Name
    # if the XML response explicitly uses namespaces.
    blob_name_elements = xml_root.findall('.//Blobs/Blob/Name')

    print("\n--- Blobs in Container (from REST API) ---")
    if not blob_name_elements:
         print("Successfully connected, but the container is empty or no blobs were found.")
    else:
        for blob_name_element in blob_name_elements:
            print(f"- {blob_name_element.text}")
        print("\n[Step 3] Successfully listed blobs via REST API.")

except requests.exceptions.RequestException as e:
     # Handle errors specifically from the REST API HTTP request
     print(f"\n[Step 3] FATAL ERROR during Storage REST API request.")
     print(f"         Error: {e}")
     if e.response is not None:
        print(f"         Response Status Code: {e.response.status_code}")
        print(f"         Response Body:\n{e.response.text}") # Crucial for debugging Storage errors (Auth, Not Found, etc.)
     print("-" * 60)
     traceback.print_exc()
     print("-" * 60)
     exit(1)
except ET.ParseError as e:
    # Handle errors during XML parsing
    print(f"\n[Step 3] FATAL ERROR: Could not parse the XML response from storage.")
    print(f"         Error: {e}")
    print("-" * 60)
    print("Response Text Received:\n" + rest_response.text)
    print("-" * 60)
    traceback.print_exc()
    print("-" * 60)
    exit(1)
except Exception as e:
    # Catch any other unexpected errors during Step 3
    print(f"\n[Step 3] An unexpected error occurred during REST API interaction.")
    print(f"         Error: {e}")
    print("-" * 60)
    traceback.print_exc()
    print("-" * 60)
    exit(1)

print("\nScript finished successfully.")