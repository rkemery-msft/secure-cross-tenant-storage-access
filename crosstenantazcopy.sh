#!/bin/bash
# ====== Fill these in ======
#### REFERENCE: https://github.com/rkemery-msft/secure-cross-tenant-storage-access?tab=readme-ov-file  
export CUSTOMER_TENANT_ID="00000000-0000-0000-0000-000000000000"   # Tenant B
export CUSTOMER_STORAGE_ACCOUNT_NAME="custstorageacct"
export CUSTOMER_CONTAINER_NAME="custcontainer"

export UAMI_CLIENT_ID="11111111-1111-1111-1111-111111111111"      # UAMI in Tenant A (assigned to this VM/ACI/Func/etc.)
export APP_REG_CLIENT_ID="22222222-2222-2222-2222-222222222222"    # Multi-tenant App Reg in Tenant A (federation configured)

# Storage REST API version (keep your current, or bump to a newer supported version)
export STORAGE_REST_API_VERSION="2023-11-03"
# ===========================
# AzCopy does not currently accept a --federated-token parameter itself; the recommended workaround is to log in with Azure CLI
# using the federated token and let AzCopy reuse that token.

# 1) Get the Federated Identity Token from IMDS
# Requires 'jq' (sudo apt-get install -y jq)
FIC_TOKEN=$(curl -sS -H "Metadata:true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=api://AzureADTokenExchange" \
  | jq -r .access_token)
echo "Got Federated Identity Token"

# 2) Log in to Azure CLI as the app in Tenant B using the federated token
echo "Try login with federated token"
az login --service-principal \
  --username "${APP_REG_CLIENT_ID}" \
  --tenant "${CUSTOMER_TENANT_ID}" \
  --federated-token "${FIC_TOKEN}" \
  --allow-no-subscriptions

# Sanity check: token now comes from Tenant B
echo "Sanity check: token = $(az account show --query tenantId -o tsv)"


# 3) Use AzCopy to list and sync blobs in the container
export AZCOPY_AUTO_LOGIN_TYPE="AZCLI"   # point AzCopy at the active Azure CLI session
echo "Use AZCOPY to list the blob container"
azcopy ls "https://${CUSTOMER_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/${CUSTOMER_CONTAINER_NAME}/"
echo "Syncing blobs from the container to local storage"
azcopy sync "https://${CUSTOMER_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/${CUSTOMER_CONTAINER_NAME}/" "${HOME}/data/" --recursive=true
echo "ls -lah ${HOME}/data/"
ls -lah "${HOME}/data/"
