# Azure Chatbot Setup Guide

This guide will walk you through setting up and deploying a chatbot application on Azure using Terraform, Docker, and Kubernetes.

## Prerequisites

### 1. Install Required Tools

#### Azure CLI
```bash
# macOS
brew install azure-cli

# Or download from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
```

#### Terraform
```bash
# macOS
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Verify installation
terraform -version
```

#### Docker
```bash
# macOS
brew install --cask docker

# Start Docker Desktop and verify
docker --version
```

#### kubectl
```bash
# macOS
brew install kubectl

# Verify installation
kubectl version --client
```

#### uv (Python package manager)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

#### Node.js and npm
```bash
# macOS
brew install node

# Verify installation
node --version
npm --version
```

---

## Azure Setup

### Step 1: Login to Azure
```bash
az login
```

This will open a browser window for authentication.

### Step 2: List and Select Your Subscription
```bash
# List all subscriptions
az account list --output table

# Set the subscription you want to use
az account set --subscription "<YOUR_SUBSCRIPTION_ID>"

# Verify current subscription
az account show --output table
```

### Step 3: Apply for Azure OpenAI Access

**IMPORTANT:** You must have Azure OpenAI access approved before deploying infrastructure.

1. Go to: https://aka.ms/oai/access
2. Fill out the form with your use case
3. Wait for approval (usually 24-48 hours)

**Alternative:** Create through Azure AI Foundry:
- Visit: https://ai.azure.com
- Sign in and follow prompts to request access

---

## Terraform Authentication

### Step 4: Create Service Principal for Terraform

```bash
# Create a service principal
az ad sp create-for-rbac --name "terraform-sp" --role="Contributor" --scopes="/subscriptions/<YOUR_SUBSCRIPTION_ID>"
```

**Save the output** - you'll need these values:
```json
{
  "appId": "xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx",
  "displayName": "terraform-sp",
  "password": "xxxxxx~xxxx~xxxxxxxxxx",
  "tenant": "xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"
}
```

### Step 5: Export Terraform Environment Variables

Create a file `terraform.env` (do NOT commit this):

```bash
export ARM_CLIENT_ID="<appId from above>"
export ARM_CLIENT_SECRET="<password from above>"
export ARM_SUBSCRIPTION_ID="<your subscription id>"
export ARM_TENANT_ID="<tenant from above>"
```

Load the environment variables:
```bash
source terraform.env
```

---

## Verify Azure OpenAI Access

Before running Terraform, verify you have Azure OpenAI access:

```bash
# Try to list available locations for Azure OpenAI
az cognitiveservices account list-kinds | grep OpenAI

# Try to list available models (this will work if you have access)
az cognitiveservices account list-models --kind OpenAI
```

If you get errors, you don't have access yet. Wait for approval before proceeding.

---

## Next Steps

Once all prerequisites are installed and Azure is configured:

1. Navigate to `cloud_infra/` directory
2. Run `terraform init`
3. Run `terraform plan` to preview changes
4. Run `terraform apply` to create infrastructure

See `DEPLOYMENT.md` for detailed deployment instructions.

---

## Troubleshooting

### "Subscription not registered for Azure OpenAI"
- You need to apply for and receive Azure OpenAI access approval
- Cannot be automated - must wait for Microsoft approval

### "Authentication failed for terraform"
- Verify environment variables are set: `echo $ARM_CLIENT_ID`
- Re-source the terraform.env file: `source terraform.env`
- Verify service principal has Contributor role

### Docker commands fail
- Ensure Docker Desktop is running
- Check Docker status: `docker ps`

---

## Cost Considerations

With Azure free tier ($200 credit for 30 days):

| Service | Estimated Cost/Month |
|---------|---------------------|
| AKS (2 B2s nodes) | ~$70-100 |
| ACR (Basic) | ~$5 |
| Azure OpenAI | ~$0.002-0.03 per 1K tokens (usage-based) |
| Networking | ~$5-10 |
| **Total** | **~$80-120/month** |

Your $200 credit should last 2-3 months with moderate usage.

**Set up budget alerts:**
```bash
# Create a budget alert
az consumption budget create \
  --budget-name "chatbot-budget" \
  --amount 200 \
  --time-grain Monthly \
  --category Cost
```
