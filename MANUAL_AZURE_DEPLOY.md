# Manual Azure Deployment Guide

Since Azure Container Registry was blocked by your student subscription, here's an alternative approach using **Azure App Service** with direct GitHub deployment.

---

## Option 1: Azure App Service (Recommended for Students)

### Step 1: Push Code to GitHub
1. Go to [GitHub](https://github.com) and create a new repository
2. In your terminal, run:
   ```powershell
   cd "c:\Users\admin\Documents\outing\agent 4.0"
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

### Step 2: Deploy Backend (form_filler) to Azure App Service

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **"Create a resource"** → Search **"Web App"** → Click **Create**
3. Fill in:
   - **Subscription**: Azure for Students
   - **Resource Group**: Create new → `rg-outing-agent`
   - **Name**: `outing-backend` (must be unique, try `outing-backend-YOUR_NAME`)
   - **Publish**: Docker Container
   - **Operating System**: Linux
   - **Region**: Central India (or any available)
   - **Pricing Plan**: Free F1 or Basic B1
4. Click **Next: Docker**
   - **Options**: Single Container
   - **Image Source**: Docker Hub
   - **Image and tag**: `python:3.11-slim` (placeholder, we'll configure later)
5. Click **Review + Create** → **Create**

### Step 3: Configure Backend with Deployment Center

1. After creation, go to your Web App
2. Click **Deployment Center** (left sidebar)
3. **Source**: GitHub
4. Authorize GitHub access
5. Select your repository and branch
6. **Build provider**: GitHub Actions (recommended)
7. Save

### Step 4: Add Environment Variables

1. In your Web App, go to **Configuration** → **Application settings**
2. Click **+ New application setting** for each:
   ```
   DB_HOST=your-mysql-server.mysql.database.azure.com
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_NAME=outing_db
   PORT=8080
   ```
3. Click **Save**

---

## Option 2: Deploy Frontend (doc_handle) to Azure Static Web Apps

This is perfect for React/Vite apps and is **FREE** for students!

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **"Create a resource"** → Search **"Static Web App"** → Click **Create**
3. Fill in:
   - **Subscription**: Azure for Students
   - **Resource Group**: `rg-outing-agent`
   - **Name**: `outing-frontend`
   - **Plan type**: Free
   - **Region**: Central US (or any available)
   - **Source**: GitHub
4. Link your GitHub repo and select:
   - **Branch**: main
   - **Build Presets**: React
   - **App location**: `/doc_handle`
   - **Output location**: `dist`
5. Click **Review + Create** → **Create**

After creation, Azure will automatically build and deploy your frontend whenever you push to GitHub!

---

## Option 3: Use Free Alternatives (Easiest)

If Azure continues to block resources, try these free platforms:

### Frontend (doc_handle)
- **Vercel**: [vercel.com](https://vercel.com) - Connect GitHub, auto-deploy
- **Netlify**: [netlify.com](https://netlify.com) - Similar to Vercel

### Backend (form_filler)
- **Railway**: [railway.app](https://railway.app) - Great for Python backends
- **Render**: [render.com](https://render.com) - Free tier available

### Database
- **Supabase**: [supabase.com](https://supabase.com) - Free PostgreSQL
- **PlanetScale**: [planetscale.com](https://planetscale.com) - Free MySQL

---

## Quick Commands Reference

```powershell
# Login to Azure CLI
az login

# Create Resource Group
az group create --name rg-outing-agent --location centralindia

# List available regions
az account list-locations -o table

# Check your subscription limits
az vm list-usage --location centralindia -o table
```

---

## Need Help?

If you encounter policy restrictions:
1. Contact your university IT department
2. Check "Usage + quotas" in Azure Portal → Subscriptions
3. Try different resource types (App Service vs Container Apps)
