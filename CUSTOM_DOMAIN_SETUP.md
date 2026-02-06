# Custom Domain Setup for campusouting.app

## Overview
Configure your custom domain `campusouting.app` for both frontend and backend services.

**Recommended DNS Setup:**
- **Frontend**: `campusouting.app` or `www.campusouting.app`
- **Backend API**: `api.campusouting.app`

---

## Part 1: Frontend Domain (Azure Static Web Apps)

### Step 1: Add Custom Domain in Azure Portal

1. Go to **Azure Portal** → Your Static Web App (`agreeable-sky-058124200`)
2. Click **Custom domains** (left sidebar)
3. Click **+ Add**
4. Select **Custom domain on other DNS**
5. Enter: `campusouting.app` (or `www.campusouting.app`)
6. Click **Next**

Azure will show you DNS records to add.

### Step 2: Configure DNS Records (Name.com)

1. Log in to **Name.com**.
2. Go to **My Domains** → Click `campusouting.app`.
3. Click **Manage DNS Records**.
4. **Delete** any existing A records or CNAME records for `www` or `@` if they conflict.

**Add these records:**

**1. Frontend (www):**
- **Type**: `CNAME`
- **Host**: `www`
- **Answer**: `agreeable-sky-058124200.4.azurestaticapps.net`
- **TTL**: `300`

**2. Frontend Validation (if asked by Azure):**
- **Type**: `TXT`
- **Host**: `_dnsauth`
- **Answer**: *(Paste the validation token from Azure Portal)*
- **TTL**: `300`

**3. Root Domain Redirection (Optional but recommended):**
Name.com supports URL Forwarding to redirect `campusouting.app` to `www.campusouting.app`.
- Go to **Web Forwarding** (on the left menu).
- **Domain**: `campusouting.app` (leave blank or use @)
- **DestinationURL**: `https://www.campusouting.app`
- **Type**: `Redirect (301)`

---

## Part 2: Backend API Domain (Azure App Service)

### Step 1: Add Custom Domain in Azure Portal

1. Go to **Azure Portal** → Your App Service (`outing-backend-api`)
2. Click **Custom domains** (left sidebar)
3. Click **+ Add custom domain**
4. Enter: `api.campusouting.app`
5. Click **Validate**

### Step 2: Configure DNS Records (Name.com)

In Name.com DNS management, add:

**1. Backend CNAME:**
- **Type**: `CNAME`
- **Host**: `api`
- **Answer**: `outing-backend-api.azurewebsites.net`
- **TTL**: `300`

**2. Backend Validation:**
- **Type**: `TXT`
- **Host**: `asuid.api`
- **Answer**: *(Paste the Custom Domain Verification ID from Azure)*
- **TTL**: `300`

### Step 3: Add SSL Certificate

After domain is validated:

1. In **Custom domains**, click on `api.campusouting.app`
2. Click **Add binding**
3. Select **TLS/SSL certificate**: **App Service Managed Certificate** (FREE)
4. Click **Add**

Azure will automatically provision and renew the SSL certificate.

---

## Part 3: Update Application Configuration

### Update Frontend Environment Variables

In **Azure Static Web Apps** → **Configuration**:

```
VITE_API_URL=https://api.campusouting.app
```

### Update CORS in Backend

If your backend has CORS configuration, update it to allow your custom domain:

```python
# In form_filler/api.py or wherever CORS is configured
CORS(app, origins=[
    "https://campusouting.app",
    "https://www.campusouting.app",
    "http://localhost:3000"  # For local development
])
```

---

## DNS Propagation Check

After adding DNS records, check propagation:
- **Online tool**: [whatsmydns.net](https://www.whatsmydns.net)
- **Command line**: `nslookup campusouting.app`

DNS can take 5 minutes to 48 hours to fully propagate globally.

---

## Final URLs

After setup:
- **Frontend**: https://campusouting.app
- **Backend API**: https://api.campusouting.app
- **Health Check**: https://api.campusouting.app/health

---

## Troubleshooting

### Domain validation fails
- Ensure DNS records are correct (no typos)
- Wait longer for DNS propagation
- Check TTL is not too high (use 3600 or lower)

### SSL certificate not provisioning
- Ensure domain is fully validated first
- Try removing and re-adding the domain
- Check that CNAME points to correct Azure endpoint

### CORS errors after domain change
- Update backend CORS configuration
- Clear browser cache
- Check frontend is using correct API URL
