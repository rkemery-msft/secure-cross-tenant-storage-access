# Azure Cross-Tenant Storage Account Access via Private Endpoint using Private Link

This document outlines two scenarios for securely accessing an Azure Storage Account in a customer tenant (Tenant B) from a provider tenant (Tenant A) using Private Endpoints, without exposing secrets.

1.  **Federated Managed Identity (Scenario A):** Uses Azure's workload identity federation to allow a User-Assigned Managed Identity (UAMI) in Tenant A to access storage in Tenant B.
2.  **Client Credentials (Scenario B):** Uses a Service Principal created and managed by Tenant B, with credentials provided to Tenant A.

> **Note:** Replace placeholder values (like `{PROVIDER_TENANT_ID}`, `{UAMI_CLIENT_ID}`, etc.) with your actual values throughout this guide.

#### Important Context: Cross-Tenant Federation with Managed Identity (Scenario A)

* **Limited Documentation & Recency:** This specific method (cross-tenant Managed Identity federation) is relatively new, with examples emerging around late 2024. Documentation focused on this end-to-end flow can be less comprehensive than for other established methods.

* **Manual Token Exchange Required:** Unlike simpler authentication flows within `azure-identity`, this scenario currently requires manually implementing the token exchange process in your code:
    1.  Acquire the initial token from the Managed Identity (scoped for `api://AzureADTokenExchange`).
    2.  POST this token (as a `client_assertion`) via an HTTP request to the *customer* tenant's token endpoint to receive the final, federated token scoped for the target resource (e.g., `https://storage.azure.com/.default`).

* **Python SDK Usage:** While the *final* federated token obtained from the exchange **can** be used effectively with standard Azure SDK clients (like `BlobServiceClient`) by wrapping it in `BearerTokenCredential` (although I never personally found BearerTokenCredential was implemented in import), the token exchange step *itself* is not fully abstracted into a simple credential call within the `azure-identity` library for this specific flow at this time. The REST API example provided earlier bypasses the Storage SDK client entirely.

* **Simpler Alternative (Client Credentials):** Using the Client Credentials flow (Scenario B), where Tenant B creates a dedicated Service Principal and provides its credentials (Client ID/Secret) to Tenant A, is often more straightforward and benefits from more extensive documentation and examples for cross-tenant access, *if* this credential management approach is acceptable for your requirements.

---

## Table of Contents

- [Architecture Diagrams](#architecture-diagrams)
  - [Scenario A: Federated Managed Identity](#scenario-a-federated-managed-identity)
  - [Scenario B: Client Credentials](#scenario-b-client-credentials)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
  - [Scenario A: Federated Managed Identity Setup](#scenario-a-federated-managed-identity-setup)
  - [Scenario B: Client Credentials Setup](#scenario-b-client-credentials-setup)
  - [Common: Private Endpoint & DNS Setup](#common-private-endpoint--dns-setup)
- [Testing Access](#testing-access)
  - [Testing Scenario A (Federation - Python Example)](#testing-scenario-a-federation---python-example)
  - [Testing Scenario B (Client Credentials - CLI Example)](#testing-scenario-b-client-credentials---cli-example)
  - [Partial Verification with CLI (Federation Scenario)](#partial-verification-with-cli-federation-scenario)
- [Troubleshooting](#troubleshooting)
- [References](#references)
- [License](#license)

---

## Architecture Diagrams

### Scenario A: Federated Managed Identity

![Scenario A Architecture Diagram](https://uml.planttext.com/plantuml/png/ZLPTRo8t57r7uZzSKQaRL05gjazHWtQ0f49AqXIoMQdQ5pFZW9l1djeUicpP_zvx_J4Vm5QD5CKPdtjzVUxniJyOoxGjjtctymu-6WuvVx43gmPQh3SMShPNfUrsw2jO1Vvh9ZHFhL2osw6mfTtd75H1NmnS-07BOG1BiIroyI9u1ikzjEnBlzinhq8MJBCj52nzPMlkmoaZa-kSDn5cmpBr9kGQNbXkMbEfsXPAScbzEExWiZMTgpARA9rnFLMvqh3AItuAm0hMMfKoyw2SjdUCb2hZpKnhpVOdy-SI7GCpPjcAcQDadCkpeFCPZz0ijKetyzshD6L6d04TvQk1rC8PVn6IG_Arr1m8ka9kWUTyYmm3Ii28Z8FbaabhkXr77lJQyC_oub6B7RCSxeHyXINNEv7oVW-OWLK0-UMkh-79vO84C4ZjCBlkes3kI6TBMklwkji90e7U6N0F_kbs07-8VkWztuy-AVsQAvQvzNRRn4zNEe7Un-H-ZaKM8SMWP5lXgwFHAJuf2bZmjJ1MCv8qngPQ6JFmF0nOKVXm720k9l3St4YCWlaCBcBn7ilfUz8g_O5RgAlQIMuzb4P9t6P4HuflP5Oe8IqMPR2zIDEW25mNFEJ_rbmc1iuUbl2dRrVXF-NOhU4gLwlXSEWpPD8ar2cAVWU3mG3cqd9DXxfgXUQvOyLiH648u-58F0o7OqyfN45YZ5XBD81vXbiNTkzXWR8Mz9RZ_h6U33u9ky7wbkNgBxI5QseS_Ex6yrc_NWVhyXnTmQ94wvbB6C5KIOb0pFAaF9HsqyIIEe-dgGxaZJ9ne_8TDsXhZbQu_MFsW60OZBkTRyVwdS35jCG6RBr-5yuVlolW9heIS3pnq8ih9ccA1vLQco8wj9UbQT15-33vRxrD6dgRd6ZxXlg9_STbKUQuqe8NGuYdYxvLuJWEySv86fj9igsG_WJGQDAMp9BRia0MESf3o9gmIYe-2FyVnsMG_WiVzdCVVjDaDjHFWzCd8P65EkQo7zHcO359fh1GEQaSMzVURL1GN7FOofMKTgEq-8e2UHRC9VeVIx_lKs9a3tNpU1Crw6x8MZ9JPnw1XnfYu4UupTMRSP8XBB67fl26XWQFp6vWXvLKhkpu8wtY08k9peh5jEotMSEg4TigFu0CtUt1h_4KuPj0fhokXJYXmvkw0--AfSiznPreeSYMmz75sRwlpntFSN0xueboK5SN_E-I6mjuef_KAzrc0KELKLJ4NXBMbbeseCsiamg9vDzyIJVuUk0nFROzHf4ck7Q5__HPDXME1WJEJqA-umf-gIgedScbzCT5SzAb8N45LKM-PdYYwH1pOm9P3KgStT0IVXuf8KU-K-grB0A82l5c5558HcYLqq9izFpHNRgXaACgNK51UdTypMNc19RxeNl9aR8FiDomWkFV6JUf5kxr1WStzIi9v-g7wbaq3cvpWCfkHiUFXjD8UWUD_Irqg7HDDbjgbDi8dk-_6rGxrg6wG6Z90f-LGOtJ6d8c2RwNnhN37k38OjinyKqq3avty0v7xs8TaDWRz-kPIxJ6xXxWQL_4ZLEB3vNAHxJFWXpC2o5Y7AXrn4UD0rl3pW1RNX20T7iTK4Dh92NtgLx4slj0X8nTmS7TF7Lk_e8ihdzsU-wbYEQExHLvNlftqCwjYXBoGYA9VS2_-03_5m00)

* **Key Components:** UAMI, multi-tenant App Registration with Federated Credential (Tenant A); Enterprise Application, Storage Account, RBAC assignment (Tenant B).
* **Flow:** UAMI token (Tenant A) -> Exchanged for Federated Token (Tenant B) -> Access Storage (Tenant B) via PE.

### Scenario B: Client Credentials

![Scenario B Architecture Diagram](https://uml.planttext.com/plantuml/png/VLTjRo8t4FwEn7yOvQG6L2sq-LITBkXuoKb8IOx2DPMgIfNP7S35s5lRIygL_lVEsBkmI-X5IbYypupdvPd7paVdXVN5JhLRj_2BGr2uyeatYPNhZGSb3gRmxHQlWZSGLpDfCVNIw7QBpHR-e11CpYiEEl51A4XW8NUvaYk96ImEsek_k-sMsqgT2ojsa8jqAzOOpTcZq6k5TOJRYCoyIhs6bL2kyIerkzner3wQKmPtZTVA5Dd8s0pjs2XZOQaAV0kW2DRM53gB8CNfNIAroR3kQMt5uStxQuukWPdmOYdSXJD4VHLqtUC5MgJUsBg_9vEcmiahe0j_ru2d7jGzJeJTVhQqZDUX5tuZ56xX4ttvWbfe3oDOp9WeSzoPFN71KUUvgITt3eG3ly43x0B1fFPeLsWHNgNVG8OhKQWp6s-XMNs7EVpqGtETmjXMwv6c4rn9ZJ3yMf1V3dj9_05Kk2CM0JbsCaFm8MJNRWM2m4qJ_hlkpApS2u_mAFKM5cZtCiNk3IUmB45nk_lxAlqXa97PatVRfQ5uv5bQy5xtz-rMEGHmSmLy0_-qMq0_d2JSl3prVpLsgup8mdxxtR3n-XazTFBIEDbhz34kVceWgnGUT9ORgZLbvOWY54QIbxdaUDLYyho0ts8TyhYag0ozfJBBNgyNJJFjXbm2jhw594bW_l3q-ULX0XkPPQY1JHoiY1-vSPB5Wib0mARLb4d0EdAgZ4KbWiXiPEwY0SEf3X3rAXd4PE4zp0lIegc6FeoDriHMujqN4mqeEKYAl8QUOAxCWI1J7I6Sn0M66rvp4X2zGN16sw4pQe-En30K4ZxzF7acB2I3TklVIqQCe3CkgEIxo8Xv8Ft_KgAEFb6YqWcugNOSfYcD8JSp9NJPK96c9GlAXL4qBzdzeBqLC9r0fzehWf7NI-Xfr6chI7SWEkXKvaBHPcEBWekxF43JXyj7yAvI3dOKTAYMrJ3RIHsWWfz6pVOlKi9PQLWzq1VvkTyHJTy7OO_tq1ab4V9Z5s8ur8SPVCzVY71Uqk7nrhIiHzt-hWj3v-IQg3CV3SSmDugfJcrSpFuOTQCFthFNi1yMVcEi_4fLU94Yc3Pp6PlTpkXlvL4BfWwcU7AUQ4fezb0nEHoyPqwDhN4kAQjwXZZu3Zufy-e2fnZBaP16l9A6m4oGhkufs9CGXh32P2GSKILc5553yUenB6ksZHnAaEChGyMPgQQhXaxn70kNZRkJXg4EmKAZxvsnagpDjJPso_8rPZwoDJQIdJ8FvlXNWSxJ26vHCqsZg-caly3KabAo_bHTBHqauV8pOETdNtVionTMdrpDCRTqvj0fKJceCfhGKF8SedDbEXniY9NkCPfS1zKWvoM80cL9VJHcM-Gbiieg2ak5f33AgeQsLJsPpiAHL8OJ8ZndHkmRPd-I610nXRNcjJeAYJMFk4QT1Mwe-1ZsPMOUOR4HETBd15rgPRZFmJ6y-i0zV__kT54Qb4foX9EKz2-FsBUMV3CQnAFbUA8aIsXXYIbzU7cYFqJuVgZEaVAWeLZIwPt1CnjbvxYk-AOxqk2iZqUu4CXcFDKzQ53Aqp7A4j-5RHCPfMnGqyDZxO9pgOobBH4W_CQw3ha9R7R8gxBG0K5fVaZegQ9idqj1briAFf2e0XBos1pWVcqSkLZX50lNcKRDQg3BofNJVlo6C9JRzteCUpHhcbSLTrx9THI5VZp_YaYK-jQgnB_PbxnnGKhbZ0eGV7LOFhjNonTkc7HQ4BcaKiHhItRx424HEDAO2VwHFkaVWly0)

* **Key Components:** Tenant B creates and manages a **Service Principal** with credentials (secret/cert). This SP is granted RBAC roles on the Storage Account. Tenant A application uses these provided credentials directly.
* **Flow:** Application in Tenant A -> Authenticates directly to Tenant B Entra ID using provided Client ID/Secret -> Access Storage (Tenant B) via PE using the obtained token.

---

## Prerequisites

-   **Azure CLI (`az`)** installed and authenticated.
-   **Python 3.8+** installed.
-   **Required Python packages:**
    ```bash
    pip install requests azure-identity azure-storage-blob
    ```
-   **Permissions:** Appropriate permissions in both Tenant A and Tenant B to manage identities, applications, network resources (VNets, Private Endpoints, DNS Zones), and storage accounts (including IAM/RBAC and PE connection approval).

---

## Setup Instructions

Follow the relevant setup steps based on the chosen scenario. The Private Endpoint setup is common to both.

### Scenario A: Federated Managed Identity Setup

#### Tenant A (Provider) Configuration

1.  **Identify/Create UAMI:** Ensure a UAMI exists in Tenant A. Note its **Client ID** (`{UAMI_CLIENT_ID}`) and **Object ID** (`{UAMI_OBJECT_ID}`). Note the **Tenant A ID** (`{PROVIDER_TENANT_ID}`).
2.  **Identify/Create App Registration:** Ensure a multi-tenant App Registration exists in Tenant A. Note its **Client ID** (`{APP_REG_CLIENT_ID}`).
3.  **Add Federated Credential:** On the App Registration (`{APP_REG_CLIENT_ID}`), add a Federated Credential via **Certificates & secrets** -> **Federated credentials**:
    * **Issuer:** `https://login.microsoftonline.com/{PROVIDER_TENANT_ID}/v2.0`
    * **Subject:** `{UAMI_OBJECT_ID}` (UAMI's Object ID)
    * **Audience:** `api://AzureADTokenExchange`

#### Generate Admin Consent URL

Construct this URL for the Tenant B admin (replace placeholders):

`https://login.microsoftonline.com/{CUSTOMER_TENANT_ID}/adminconsent?client_id={APP_REG_CLIENT_ID}&redirect_uri=https://localhost`

#### Tenant B (Customer) Configuration

1.  **Grant Admin Consent:** The Tenant B admin uses the URL above to consent. This creates an **Enterprise Application** (`ENTERPRISE_APP_IN_TENANT_B`) in Tenant B.
2.  **Assign RBAC Role:** On the target Storage Account (`{CUSTOMER_STORAGE_ACCOUNT_NAME}`) -> **Access control (IAM)**, assign the required role (e.g., `Storage Blob Data Contributor`) to the `ENTERPRISE_APP_IN_TENANT_B`.
3.  **Provide Storage Account Resource ID:** Give the full Resource ID of the storage account to Tenant A.

### Scenario B: Client Credentials Setup

#### Tenant B (Customer) Configuration

1.  **Create Service Principal:** Create a new App Registration and corresponding Service Principal (`TENANT_B_SP`) *within Tenant B*. Note its **Client ID** (`{TENANT_B_SP_CLIENT_ID}`).
2.  **Generate Credentials:** Create a **client secret** (or certificate) for `TENANT_B_SP`. Securely record the **secret value** (`{TENANT_B_SP_CLIENT_SECRET}`).
3.  **Assign RBAC Role:** On the target Storage Account (`{CUSTOMER_STORAGE_ACCOUNT_NAME}`) -> **Access control (IAM)**, assign the required role (e.g., `Storage Blob Data Contributor`) directly to the `TENANT_B_SP`.
4.  **Provide Credentials:** Securely share the Tenant B ID (`{CUSTOMER_TENANT_ID}`), SP Client ID (`{TENANT_B_SP_CLIENT_ID}`), and the Client Secret value with Tenant A.
5.  **Provide Storage Account Resource ID:** Give the full Resource ID of the storage account to Tenant A.

#### Tenant A (Provider) Configuration

1.  **Store Credentials:** The application in Tenant A must securely access the credentials provided by Tenant B (e.g., via environment variables, configuration files, Azure Key Vault).

### Common: Private Endpoint & DNS Setup

1.  **Tenant A: Create Private Endpoint:**
    * In Tenant A's VNet (`provider-vnet`), initiate **Create a private endpoint**.
    * On the **Resource** tab, select **Connect to an Azure resource by resource ID or alias**.
    * Paste the **Storage Account Resource ID** provided by Tenant B.
    * The **Target sub-resource** should automatically populate (e.g., `blob`). Verify it's correct.
    * On the **Virtual network** tab, select the VNet (`provider-vnet`) and subnet for the endpoint.
    * On the **DNS** tab, select **Yes** for **Integrate with private DNS zone**. Choose or create the zone `privatelink.blob.core.windows.net` and ensure it's linked to `provider-vnet`.
    * Review and create. A connection request is sent to Tenant B.

2.  **Tenant B: Approve Private Endpoint Connection:**
    The owner of the Storage Account (or a user with appropriate permissions like `Microsoft.Storage/storageAccounts/privateEndpointConnections/write`) in Tenant B must approve the connection request.

    * **Using the Azure Portal:**
        1.  Navigate to the target **Storage Account** in the Azure Portal for Tenant B.
        2.  In the left-hand menu under **Security + networking**, select **Networking**.
        3.  Click the **Private endpoint connections** tab.
        4.  Locate the connection request from Tenant A; its status will be "Pending".
        5.  Select the pending connection by checking the box next to it.
        6.  Click the **Approve** button at the top of the list.
        7.  (Optional) Add a description in the approval dialog.
        8.  Click **Yes** to confirm the approval.

    *(CLI/PowerShell methods can also be used - see References for documentation)*

---

## Testing Access

Ensure tests are run from a location within Tenant A's VNet that can resolve the Private DNS Zone and reach the Private Endpoint's IP address (e.g., the VM in `provider-vnet`).

### Testing Scenario A (Federation - Python Example)

* Use the accompanying Python script (e.g., `federated_storage_access.py`).
* Configure placeholders in the script (`UAMI_CLIENT_ID`, `APP_REG_CLIENT_ID`, tenant IDs, storage details).
* **Script Logic:**
    1.  Acquire initial token using `ManagedIdentityCredential`.
    2.  Exchange token via POST request to Tenant B token endpoint.
    3.  Wrap federated token using `BearerTokenCredential`.
    4.  Create `BlobServiceClient` using the `BearerTokenCredential`.
    5.  Perform storage operation (e.g., list blobs).

### Testing Scenario B (Client Credentials - CLI Example)

* Use credentials (`{TENANT_B_SP_CLIENT_ID}`, `{TENANT_B_SP_CLIENT_SECRET}`) provided by Tenant B.

    ```bash
    # 1. Login using Tenant B SP credentials
    az login --service-principal \
        -u {TENANT_B_SP_CLIENT_ID} \
        -p {TENANT_B_SP_CLIENT_SECRET} \
        --tenant {CUSTOMER_TENANT_ID}

    # 2. Access storage via PE (ensure network path allows)
    az storage blob list \
        --account-name {CUSTOMER_STORAGE_ACCOUNT_NAME} \
        --container-name {CUSTOMER_CONTAINER_NAME} \
        --auth-mode login \
        --output table
    ```

### Partial Verification with CLI (Federation Scenario)

* Use these commands on the VM assigned the UAMI in Tenant A:

    ```bash
    # 1. Login as UAMI (Should SUCCEED)
    az login --identity -u {UAMI_CLIENT_ID}

    # 2. Get initial token for assertion (Should SUCCEED)
    az account get-access-token --resource api://AzureADTokenExchange --output json

    # 3. Attempt direct storage access (Should FAIL - 403)
    az storage blob list \
        --account-name {CUSTOMER_STORAGE_ACCOUNT_NAME} \
        --container-name {CUSTOMER_CONTAINER_NAME} \
        --auth-mode login
    ```

---

## Troubleshooting

* **ImportError (Python):** Ensure `azure-identity>=1.5.0` is installed in the *active* Python environment. Check for conflicting `azure.py` files. Verify script execution within the activated virtual environment.
* **Authorization Errors (403 Forbidden):**
    * Verify correct IAM role is assigned to the correct identity (`ENTERPRISE_APP_IN_TENANT_B` for Scen. A, `{TENANT_B_SP_CLIENT_ID}` for Scen. B) on the Storage Account in Tenant B.
    * Allow time for IAM propagation (minutes).
    * Ensure final token scope is `https://storage.azure.com/.default`.
    * Confirm network connectivity via PE (`nslookup`, `curl -kv`, `Test-NetConnection`). Check NSGs.
* **Token Exchange Errors (4xx - Scenario A):**
    * Verify Federated Credential (Issuer, Subject=UAMI Object ID, Audience) on Tenant A App Reg.
    * Ensure `client_id` in exchange request is Provider App Reg Client ID (`{APP_REG_CLIENT_ID}`).
    * Ensure MI token (`client_assertion`) is valid (not expired).
* **Client Credential Errors (4xx - Scenario B):**
    * Verify correct Tenant B ID, SP Client ID, and SP Client Secret.
    * Ensure SP exists and secret is valid.
* **Private Endpoint / DNS Issues:**
    * Confirm Tenant B approved the PE connection.
    * Verify correct Storage Account Resource ID used for PE creation.
    * Ensure Private DNS Zone in Tenant A resolves FQDN to the PE private IP from within the VNet. Check VNet link. Check for conflicting DNS settings.

---

## References

* [Workload identity federation](https://learn.microsoft.com/entra/workload-id/workload-identity-federation)
* [Azure Identity client library for Python](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=azure-python)
* [Azure Storage authentication with Microsoft Entra ID](https://learn.microsoft.com/azure/storage/common/storage-auth-aad)
* [What is Azure Private Endpoint?](https://learn.microsoft.com/azure/private-link/private-endpoint-overview)
* [Azure Private Endpoint DNS configuration](https://learn.microsoft.com/azure/private-link/private-endpoint-dns)
* [Effortlessly access cloud resources across Azure tenants without using secrets](https://devblogs.microsoft.com/identity/access-cloud-resources-across-tenants-without-secrets/)
* [Azure Private Link](https://learn.microsoft.com/en-us/azure/private-link/private-link-overview)

---

## License

MIT License