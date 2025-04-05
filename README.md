# Azure Cross-Tenant Private Endpoint Access using Federated Identity and Managed Identity

## Architecture Overview (List Format)

This describes the components and their relationships across the two tenants.
![Scenario A Architecture Diagram](https://uml.planttext.com/plantuml/png/ZLPTRo8t57r7uZzSKQaRL05gjazHWtQ0f49AqXIoMQdQ5pFZW9l1djeUicpP_zvx_J4Vm5QD5CKPdtjzVUxniJyOoxGjjtctymu-6WuvVx43gmPQh3SMShPNfUrsw2jO1Vvh9ZHFhL2osw6mfTtd75H1NmnS-07BOG1BiIroyI9u1ikzjEnBlzinhq8MJBCj52nzPMlkmoaZa-kSDn5cmpBr9kGQNbXkMbEfsXPAScbzEExWiZMTgpARA9rnFLMvqh3AItuAm0hMMfKoyw2SjdUCb2hZpKnhpVOdy-SI7GCpPjcAcQDadCkpeFCPZz0ijKetyzshD6L6d04TvQk1rC8PVn6IG_Arr1m8ka9kWUTyYmm3Ii28Z8FbaabhkXr77lJQyC_oub6B7RCSxeHyXINNEv7oVW-OWLK0-UMkh-79vO84C4ZjCBlkes3kI6TBMklwkji90e7U6N0F_kbs07-8VkWztuy-AVsQAvQvzNRRn4zNEe7Un-H-ZaKM8SMWP5lXgwFHAJuf2bZmjJ1MCv8qngPQ6JFmF0nOKVXm720k9l3St4YCWlaCBcBn7ilfUz8g_O5RgAlQIMuzb4P9t6P4HuflP5Oe8IqMPR2zIDEW25mNFEJ_rbmc1iuUbl2dRrVXF-NOhU4gLwlXSEWpPD8ar2cAVWU3mG3cqd9DXxfgXUQvOyLiH648u-58F0o7OqyfN45YZ5XBD81vXbiNTkzXWR8Mz9RZ_h6U33u9ky7wbkNgBxI5QseS_Ex6yrc_NWVhyXnTmQ94wvbB6C5KIOb0pFAaF9HsqyIIEe-dgGxaZJ9ne_8TDsXhZbQu_MFsW60OZBkTRyVwdS35jCG6RBr-5yuVlolW9heIS3pnq8ih9ccA1vLQco8wj9UbQT15-33vRxrD6dgRd6ZxXlg9_STbKUQuqe8NGuYdYxvLuJWEySv86fj9igsG_WJGQDAMp9BRia0MESf3o9gmIYe-2FyVnsMG_WiVzdCVVjDaDjHFWzCd8P65EkQo7zHcO359fh1GEQaSMzVURL1GN7FOofMKTgEq-8e2UHRC9VeVIx_lKs9a3tNpU1Crw6x8MZ9JPnw1XnfYu4UupTMRSP8XBB67fl26XWQFp6vWXvLKhkpu8wtY08k9peh5jEotMSEg4TigFu0CtUt1h_4KuPj0fhokXJYXmvkw0--AfSiznPreeSYMmz75sRwlpntFSN0xueboK5SN_E-I6mjuef_KAzrc0KELKLJ4NXBMbbeseCsiamg9vDzyIJVuUk0nFROzHf4ck7Q5__HPDXME1WJEJqA-umf-gIgedScbzCT5SzAb8N45LKM-PdYYwH1pOm9P3KgStT0IVXuf8KU-K-grB0A82l5c5558HcYLqq9izFpHNRgXaACgNK51UdTypMNc19RxeNl9aR8FiDomWkFV6JUf5kxr1WStzIi9v-g7wbaq3cvpWCfkHiUFXjD8UWUD_Irqg7HDDbjgbDi8dk-_6rGxrg6wG6Z90f-LGOtJ6d8c2RwNnhN37k38OjinyKqq3avty0v7xs8TaDWRz-kPIxJ6xXxWQL_4ZLEB3vNAHxJFWXpC2o5Y7AXrn4UD0rl3pW1RNX20T7iTK4Dh92NtgLx4slj0X8nTmS7TF7Lk_e8ihdzsU-wbYEQExHLvNlftqCwjYXBoGYA9VS2_-03_5m00)

**I. Tenant A (Provider Tenant - `{PROVIDER_TENANT_ID}`)**

* **Virtual Network (`provider-vnet`)**
    * Hosts the application workload (e.g., on a VM).
    * Contains the network interface for the Private Endpoint connecting to Tenant B's storage.
    * Is linked to the Private DNS Zone for resolving the storage account's private IP.
* **Compute Resource (e.g., Virtual Machine)**
    * Runs the application code (e.g., the Python script).
    * Has the User-Assigned Managed Identity (`provider-uami`) assigned to it.
    * Initiates the authentication flow and storage access requests.
* **User-Assigned Managed Identity (UAMI - `provider-uami`)**
    * Identity for the workload in Tenant A (`{UAMI_CLIENT_ID}`, `{UAMI_OBJECT_ID}`).
    * Used to acquire the initial token from Tenant A's Microsoft Entra ID.
    * Is the identity trusted by the Federated Credential configured on the App Registration.
* **App Registration (`cross-tenant-federation-app`)**
    * Registered in Tenant A (`{APP_REG_CLIENT_ID}`).
    * Configured as **Multi-tenant**.
    * Holds the **Federated Credential** configuration.
* **Federated Credential (on App Registration)**
    * Establishes trust between the App Registration and the UAMI.
    * Configuration:
        * **Issuer:** `https://login.microsoftonline.com/{PROVIDER_TENANT_ID}/v2.0`
        * **Subject:** `{UAMI_OBJECT_ID}` (Object ID of the UAMI)
        * **Audience:** `api://AzureADTokenExchange`
* **Private Endpoint (`storage-pe`)**
    * Created within `provider-vnet`.
    * Targets the Storage Account in Tenant B using its **Resource ID**.
    * Requires approval from the Storage Account owner in Tenant B.
    * Provides a private IP address within `provider-vnet` for accessing the storage account.
* **Private DNS Zone (`privatelink.blob.core.windows.net`)**
    * Linked to `provider-vnet`.
    * Contains an 'A' record mapping the storage account's FQDN (`{CUSTOMER_STORAGE_ACCOUNT_NAME}.blob.core.windows.net`) to the private IP address of the `storage-pe`.
* **Microsoft Entra ID (Tenant A)**
    * Authenticates the UAMI.
    * Issues the initial Managed Identity token (Audience: `api://AzureADTokenExchange`).

**II. Tenant B (Customer Tenant - `{CUSTOMER_TENANT_ID}`)**

* **Storage Account (`CUSTOMER_STORAGE_ACCOUNT_NAME`)**
    * The target resource containing the data (e.g., blobs).
    * **Public Network Access** should be **Disabled** for Private Endpoint security.
    * Owner provides its **Resource ID** to Tenant A for PE creation.
    * Owner approves the incoming **Private Endpoint Connection** request from Tenant A.
* **Private Endpoint Connection**
    * A sub-resource within the Storage Account's networking settings representing the approved connection from Tenant A's Private Endpoint.
* **Enterprise Application (`ENTERPRISE_APP_IN_TENANT_B`)**
    * Represents the Provider's App Registration (`{APP_REG_CLIENT_ID}`) within Tenant B.
    * Created automatically when a Tenant B administrator **grants Admin Consent** via the specially constructed URL.
* **RBAC Role Assignment**
    * Configured on the **Storage Account** -> Access Control (IAM).
    * Grants necessary permissions (e.g., `Storage Blob Data Contributor`) **to** the `ENTERPRISE_APP_IN_TENANT_B`. This is how the federated identity gets authorization.
* **Microsoft Entra ID (Tenant B)**
    * Receives the token exchange request from the application in Tenant A.
    * Validates the `client_assertion` (the MI token from Tenant A) against the federated credential configured on the `client_id` (the Provider's App Reg ID).
    * Issues the final **federated access token** (Audience: `https://storage.azure.com/`) valid for the storage account, based on the identity of the `ENTERPRISE_APP_IN_TENANT_B`.
* **Tenant B Administrator**
    * Performs the one-time Admin Consent action using the URL.
    * Assigns the RBAC role to the Enterprise Application on the Storage Account.
    * Approves the Private Endpoint connection request.

**III. Key Interactions / Flow**

1.  **Setup:** Configuration involves creating identities, apps, federation, PE, DNS, consent, and RBAC roles as described above.
2.  **Runtime Authentication & Access:**
    * The application on the VM in Tenant A uses its assigned UAMI (`{UAMI_CLIENT_ID}`) to request a token from Tenant A Entra ID for audience `api://AzureADTokenExchange`.
    * The application then makes a POST request to the Tenant B Entra ID token endpoint (`https://login.microsoftonline.com/{CUSTOMER_TENANT_ID}/oauth2/v2.0/token`). This request includes:
        * `client_id`: `{APP_REG_CLIENT_ID}` (Provider's App Reg)
        * `client_assertion`: The token obtained from the UAMI in the previous step.
        * `client_assertion_type`: `urn:ietf:params:oauth:client-assertion-type:jwt-bearer`
        * `scope`: `https://storage.azure.com/.default`
        * `grant_type`: `client_credentials`
    * Tenant B Entra ID validates the assertion based on the federated credential configured on the `{APP_REG_CLIENT_ID}` App Reg (which trusts the UAMI `{UAMI_OBJECT_ID}`).
    * If valid, Tenant B Entra ID issues an access token scoped for Azure Storage. This token represents the identity of the `ENTERPRISE_APP_IN_TENANT_B`.
    * The application in Tenant A performs a DNS lookup for `{CUSTOMER_STORAGE_ACCOUNT_NAME}.blob.core.windows.net`. The Private DNS Zone in Tenant A resolves this to the Private IP of the `storage-pe`.
    * The application connects to the Storage Account via the Private IP address.
    * It presents the **federated access token** (obtained from Tenant B) in the `Authorization: Bearer <token>` header.
    * Azure Storage validates the token and authorizes the request based on the RBAC roles assigned to the `ENTERPRISE_APP_IN_TENANT_B` in Tenant B.

This document outlines an end-to-end scenario for securely accessing an Azure Storage Account in a customer tenant (Tenant B) from a provider tenant (Tenant A) using Private Endpoints and workload identity federation with a User-Assigned Managed Identity (UAMI)—without using secrets.

In this solution:
- **Tenant A (Provider)** hosts the application workload running as a UAMI, deploys the Private Endpoint (and associated VNet), and uses its UAMI along with a multi-tenant App Registration (configured with federated credentials) to initiate access.
- **Tenant B (Customer)** owns the Storage Account, which is secured via the Private Endpoint connection originating from Tenant A. Tenant B grants admin consent to the Provider’s app and assigns RBAC roles on the Storage Account to authorize access.
- Tenant B also provides the Storage Account Resource ID so that the Private Endpoint connection request initiated from Tenant A can be linked and approved.

> **Note:** This solution leverages workload identity federation to securely exchange tokens across tenants based on a trust relationship configured via federated credentials. For background, see [Workload identity federation](https://learn.microsoft.com/entra/workload-id/workload-identity-federation).

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
  - [Tenant A (Provider) Setup](#tenant-a-provider-setup)
  - [Generate Admin Consent URL (For Tenant B Admin)](#generate-admin-consent-url-for-tenant-b-admin)
  - [Tenant B (Customer) Setup](#tenant-b-customer-setup)
  - [Private Endpoint & DNS Setup](#private-endpoint--dns-setup)
- [Testing the Federation Flow](#testing-the-federation-flow)
  - [Testing with Azure CLI (Partial Verification)](#testing-with-azure-cli-partial-verification)
  - [Testing End-to-End (Python Example)](#testing-end-to-end-python-example)
- [Alternative: Client Credentials Provided by Tenant B](#alternative-client-credentials-provided-by-tenant-b)
- [Troubleshooting](#troubleshooting)
- [References](#references)
- [License](#license)

---

## Overview

This solution enables a service running under a UAMI in **Tenant A (Provider)** to securely access a Storage Account in **Tenant B (Customer)** by:
- Restricting network access using a **Private Endpoint** established from Tenant A's VNet to Tenant B's Storage Account.
- Configuring **Private DNS** in Tenant A so that the Storage Account’s FQDN resolves to its private IP address within Tenant A's VNet.
- Setting up a **multi-tenant App Registration** in Tenant A with **federated credentials** trusting the UAMI in Tenant A.
- Having a Tenant B admin grant **admin consent** to the Provider's App Registration, creating a corresponding Enterprise Application (Service Principal) in Tenant B.
- Assigning Azure **RBAC roles** (e.g., Storage Blob Data Contributor) on the Storage Account in Tenant B to the Enterprise Application.
- Performing a **token exchange**: The UAMI in Tenant A acquires a token, which is then presented (as an assertion) to Tenant B's Microsoft Entra ID endpoint. Based on the federation trust, Tenant B issues a new token valid for accessing the Storage Account via the Enterprise Application's permissions.

---

## Architecture

**Tenant A (Provider):**
- **Virtual Network (`provider-vnet`):** Hosts the application workload and the Private Endpoint NIC.
- **Private DNS Zone (`privatelink.blob.core.windows.net`):** Linked to `provider-vnet`. Contains A record for the Storage Account's private IP.
- **User Assigned Managed Identity (UAMI):**
  - Example Name: `provider-uami`
  - **Tenant A ID:** `PROVIDER_TENANT_ID` (e.g., `00000000-0000-0000-0000-000000000001`)
  - **Client ID:** `UAMI_CLIENT_ID` (e.g., `11111111-1111-1111-1111-111111111111`)
  - **Object ID:** `UAMI_OBJECT_ID` (e.g., `22222222-2222-2222-2222-222222222222`) *(used as federated credential subject)*
- **App Registration:**
  - Example Name: `cross-tenant-federation-app`
  - **Supported Account Types:** Multi-tenant (Accounts in any organizational directory)
  - **Client ID:** `APP_REG_CLIENT_ID` (e.g., `33333333-3333-3333-3333-333333333333`)
- **Federated Credential (on App Registration):**
  - **Issuer:** `https://login.microsoftonline.com/{PROVIDER_TENANT_ID}/v2.0`
  - **Subject:** `UAMI_OBJECT_ID` (Object ID of the UAMI)
  - **Audience:** `api://AzureADTokenExchange`

**Tenant B (Customer):**
- **Storage Account:**
  - Name: `CUSTOMER_STORAGE_ACCOUNT_NAME` (e.g., `custstorageacct`)
  - **Public Network Access:** Disabled
  - **Resource ID:** `/subscriptions/{CUSTOMER_SUBSCRIPTION_ID}/resourceGroups/{CUSTOMER_RESOURCE_GROUP}/providers/Microsoft.Storage/storageAccounts/{CUSTOMER_STORAGE_ACCOUNT_NAME}` (Provided to Tenant A for PE creation)
- **Private Endpoint Connection:**
  - Connection initiated from Tenant A's Private Endpoint, approved by Tenant B Storage Account owner.
- **Enterprise Application:**
  - Created automatically when Tenant B admin grants consent to `APP_REG_CLIENT_ID`. Represents the provider's app within Tenant B. Name often matches `cross-tenant-federation-app`. Let's call its representation `ENTERPRISE_APP_IN_TENANT_B`.
- **RBAC Role Assignment:**
  - `ENTERPRISE_APP_IN_TENANT_B` is assigned an IAM role (e.g., Storage Blob Data Contributor) on the `CUSTOMER_STORAGE_ACCOUNT_NAME`.
- **Tenant B ID:** `CUSTOMER_TENANT_ID` (e.g., `44444444-4444-4444-4444-444444444444`)

---

## Prerequisites

- **Tenant A (Provider):**
  - An existing UAMI with known Client ID, Object ID.
  - An existing multi-tenant App Registration.
  - Permissions to configure Federated Credentials on the App Registration.
  - A Virtual Network and subnet for the Private Endpoint.
  - Permissions to create Private Endpoints and Private DNS Zones.
- **Tenant B (Customer):**
  - An existing Storage Account intended for private access. Note its Resource ID.
  - Permissions to approve Private Endpoint connections on the Storage Account.
  - Permissions to grant admin consent for applications.
  - Permissions to assign IAM roles on the Storage Account.
- **Tools & Libraries:**
  - Azure CLI (`az`) installed and authenticated.
  - Python 3.8+ installed.
  * Required Python packages:
      ```bash
      pip install requests azure-identity azure-storage-blob
      ```

---

## Setup Instructions

### Tenant A (Provider) Setup

1.  **Identify/Create User Assigned Managed Identity (UAMI):**
    * Ensure you have a UAMI in Tenant A. Record its details:
        * **Tenant A ID:** `{PROVIDER_TENANT_ID}`
        * **UAMI Client ID:** `{UAMI_CLIENT_ID}`
        * **UAMI Object ID:** `{UAMI_OBJECT_ID}`

2.  **Identify/Create Multi-Tenant App Registration:**
    * Ensure you have an App Registration in Tenant A.
    * Verify **Supported Account Types** is set to "Accounts in any organizational directory (Any Microsoft Entra ID tenant - Multitenant)".
    * Record its **Client ID:** `{APP_REG_CLIENT_ID}`

3.  **Add Federated Credential to App Registration:**
    * In the App Registration (`{APP_REG_CLIENT_ID}`), navigate to **Certificates & secrets → Federated credentials** (tab).
    * Click **Add credential**.
    * Configure the fields:
        * **Federated credential scenario:** Other issuer
        * **Issuer:** `https://login.microsoftonline.com/{PROVIDER_TENANT_ID}/v2.0`
        * **Subject:** `{UAMI_OBJECT_ID}` (Object ID of the UAMI)
        * **Audience:** `api://AzureADTokenExchange`
        * **Name:** (Provide a descriptive name, e.g., `uami-federation`)
    * Click **Add**.

### Generate Admin Consent URL (For Tenant B Admin)

Construct the following URL manually, replacing the placeholders:

`https://login.microsoftonline.com/{CUSTOMER_TENANT_ID}/adminconsent?client_id={APP_REG_CLIENT_ID}&redirect_uri=https://localhost`

* `{CUSTOMER_TENANT_ID}`: Tenant ID for Tenant B.
* `{APP_REG_CLIENT_ID}`: Client ID of the App Registration from Tenant A.

Provide this URL to an administrator in Tenant B.

### Tenant B (Customer) Setup

1.  **Grant Admin Consent:**
    * The Tenant B administrator opens the Admin Consent URL in a browser.
    * They sign in with Tenant B admin credentials.
    * Review the (likely minimal) permissions requested and click **Accept**.
    * This creates the corresponding Enterprise Application (Service Principal) for the provider's app in Tenant B.

2.  **Verify Enterprise Application:**
    * Confirm the Enterprise Application now exists in **Tenant B → Microsoft Entra ID → Enterprise Applications**. Note its name (usually matches the App Reg name). Let's call this `ENTERPRISE_APP_IN_TENANT_B`.

3.  **Assign RBAC Role on Storage Account:**
    * Navigate to the **Storage Account** in Tenant B.
    * Go to **Access Control (IAM)**.
    * Click **Add** → **Add role assignment**.
    * Select a suitable role (e.g., `Storage Blob Data Contributor`, `Storage Blob Data Reader`).
    * Click **Next**.
    * Assign access to: **User, group, or service principal**.
    * Click **+ Select members**. Search for and select `ENTERPRISE_APP_IN_TENANT_B`.
    * Click **Select**.
    * Click **Review + assign**.

4.  **Provide Storage Account Resource ID:**
    * Provide the full **Resource ID** of the Storage Account to the team/person setting up the Private Endpoint in Tenant A. Format: `/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.Storage/storageAccounts/{STORAGE_ACCOUNT_NAME}`

### Private Endpoint & DNS Setup

*This can happen in parallel or after the Entra ID/RBAC setup.*

1.  **Tenant A: Create Private Endpoint:**
    * Initiate the creation of a Private Endpoint within a VNet (`provider-vnet`) in Tenant A.
    * During creation:
        * Select **Connect to an Azure resource by resource ID or alias**.
        * Paste the **Storage Account Resource ID** provided by Tenant B.
        * Target sub-resource should typically be `blob`.
        * Select the appropriate VNet and subnet in Tenant A.
        * Choose **Integrate with private DNS zone** and select or create the zone `privatelink.blob.core.windows.net`, ensuring it's linked to `provider-vnet`.
    * A connection request is sent to the Storage Account in Tenant B.

2.  **Tenant B: Approve Private Endpoint Connection:**
    * Navigate to the **Storage Account** in Tenant B.
    * Go to **Networking** → **Private endpoint connections**.
    * Find the pending connection request initiated from Tenant A.
    * Select it and click **Approve**.

---

## Testing the Federation Flow

### Testing with Azure CLI (Partial Verification)

You can use the Azure CLI *on a machine associated with the UAMI in Tenant A* (e.g., a VM with the UAMI assigned) to verify the initial steps.

1.  **Login as UAMI:**
    ```bash
    # Ensure you are on the VM/resource with the UAMI assigned
    # Use -u or --username for the UAMI client ID
    az login --identity -u {UAMI_CLIENT_ID}
    ```
    *(Verify the output shows login succeeded for the correct UAMI and Tenant A)*

2.  **Get Initial MI Token (for assertion):**
    ```bash
    # Use the audience configured in the federated credential as the resource
    az account get-access-token --resource api://AzureADTokenExchange --output json
    ```
    *(This should succeed and return a token if the UAMI is configured correctly. Save this token if needed for manual `curl` tests.)*

3.  **Attempt Direct Storage Access (Will Fail):**
    ```bash
    az storage blob list \
        --account-name {CUSTOMER_STORAGE_ACCOUNT_NAME} \
        --container-name {CUSTOMER_CONTAINER_NAME} \
        --auth-mode login \
        --output table
    ```
    * This command is **expected to fail** with an authorization error (403) because `az storage` doesn't perform the required cross-tenant token exchange. It demonstrates that the Tenant A token isn't directly valid in Tenant B for this flow.

### Testing End-to-End (Python Example)

Use the accompanying Python script (`federated_storage_access.py`) after configuring the placeholder variables. This script performs the full flow: MI token acquisition, token exchange, and storage access using the federated token via the SDK.

**Key Python Logic (See `federated_storage_access.py` for full code):**

1.  **Configuration:** Set variables like `{CUSTOMER_TENANT_ID}`, `{UAMI_CLIENT_ID}`, `{APP_REG_CLIENT_ID}`, `{CUSTOMER_STORAGE_ACCOUNT_NAME}`, etc.
2.  **Get MI Token:** Use `ManagedIdentityCredential(client_id=UAMI_CLIENT_ID)` to represent the UAMI. Get the initial token: `mi_token = mi_credential.get_token("api://AzureADTokenExchange")` (or use `get_bearer_token_provider`).
3.  **Exchange Token:** POST to `https://login.microsoftonline.com/{CUSTOMER_TENANT_ID}/oauth2/v2.0/token` with:
    * `client_id={APP_REG_CLIENT_ID}` (**Provider's** App Reg ID)
    * `client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer`
    * `client_assertion=<MI_TOKEN_STRING>`
    * `scope=https://storage.azure.com/.default`
    * `grant_type=client_credentials`
4.  **Parse Federated Token:** Extract the `access_token` (federated token) from the JSON response.
5.  **Wrap Token:** Create the SDK credential: `federated_credential = BearerTokenCredential(<FEDERATED_TOKEN_STRING>)`. (Requires `from azure.identity import BearerTokenCredential`).
6.  **Use with SDK:** Initialize the client: `client = BlobServiceClient(account_url=..., credential=federated_credential)`. Then perform storage operations.

---

## Alternative: Client Credentials Provided by Tenant B

If Tenant B prefers to provide credentials for an identity *within their own tenant* that has access to the storage account (instead of consenting to the Tenant A app), they can create a separate Service Principal in Tenant B, grant it IAM roles on the storage, and provide Tenant A with its Client ID and a Client Secret (or Certificate).

Tenant A's application would then authenticate directly using these client credentials against Tenant B.

**Example using Azure CLI (run from anywhere):**

```bash
# Login using SP details provided by Tenant B
az login --service-principal \
    -u {TENANT_B_SP_CLIENT_ID} \
    -p {TENANT_B_SP_CLIENT_SECRET} \
    --tenant {CUSTOMER_TENANT_ID}

# Access storage (assuming network path via PE exists if PE is enforced)
az storage blob list \
    --account-name {CUSTOMER_STORAGE_ACCOUNT_NAME} \
    --container-name {CUSTOMER_CONTAINER_NAME} \
    --auth-mode login \
    --output table
Note: Network connectivity via the Private Endpoint from Tenant A must still be functional if public access is disabled.

---

## Troubleshooting

* **ImportError (Python):** Ensure `azure-identity>=1.5.0` is installed in the *active* Python environment. Check for conflicting `azure.py` files. Verify the script runs within the activated virtual environment.
* **Authorization Errors (403 Forbidden) during Storage Access:**
    * Verify correct IAM role is assigned to `ENTERPRISE_APP_IN_TENANT_B` on the Storage Account in Tenant B.
    * Allow time for IAM propagation (can take several minutes).
    * Ensure the token used has the correct scope (`https://storage.azure.com/.default`).
    * Confirm network connectivity via the Private Endpoint. Perform `nslookup {CUSTOMER_STORAGE_ACCOUNT_NAME}.blob.core.windows.net` from the VM in Tenant A - it should resolve to a private IP. Test connectivity (e.g., `curl -kv https://{CUSTOMER_STORAGE_ACCOUNT_NAME}.blob.core.windows.net`, `Test-NetConnection` on Windows, or similar tools).
* **Token Exchange Errors (4xx from `login.microsoftonline.com`):**
    * Verify the Federated Credential details (Issuer, Subject=UAMI Object ID, Audience) on the App Registration in Tenant A are exactly correct.
    * Ensure the `client_id` used in the exchange request is the Provider App Reg Client ID (`{APP_REG_CLIENT_ID}`).
    * Ensure the `client_assertion` token (from MI) is valid and not expired.
* **Private Endpoint Connection Issues:**
    * Confirm Tenant B approved the connection request.
    * Verify Tenant B provided the correct Storage Account Resource ID for PE creation.
    * Check Network Security Groups (NSGs) associated with the Private Endpoint subnet in Tenant A are not blocking traffic to the storage private IP on port 443 (HTTPS).
    * Ensure Private DNS Zone in Tenant A is correctly linked to the VNet and contains the A record for the storage account FQDN.