# Deployment Guide

## Backend → Railway

### 1. Push your code to GitHub
Make sure `flight-search/backend/` (the backend folder) is in a GitHub repository.

### 2. Create a Railway project
1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **New Project → Deploy from GitHub repo**
3. Select your repository
4. Set **Root Directory** to `backend`
5. Railway will auto-detect Python and build using `requirements.txt`

### 3. Add a persistent volume (for alerts.db)
1. In your Railway project, click **+ Add** → **Volume**
2. Mount path: `/data`
3. Railway sets `RAILWAY_VOLUME_MOUNT_PATH=/data` automatically

### 4. Set environment variables in Railway
Go to your service → **Variables** tab and add:
```
SERPAPI_KEY=your_serpapi_key
RESEND_API_KEY=your_resend_key
RESEND_FROM_EMAIL=alerts@yourdomain.com
ALLOWED_ORIGINS=https://your-app.vercel.app
```

### 5. Get your Railway URL
After deploy, Railway gives you a URL like `https://your-app.up.railway.app`.
Save this — you'll need it for Vercel.

---

## Frontend → Vercel

### 1. Push your frontend to GitHub
Make sure `flight-search/frontend/` is in your GitHub repository.

### 2. Create a Vercel project
1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click **Add New → Project**
3. Select your repository
4. Set **Root Directory** to `frontend`
5. Vercel auto-detects Vite — no build config needed

### 3. Set environment variable in Vercel
Go to your project → **Settings → Environment Variables** and add:
```
VITE_API_URL=https://your-app.up.railway.app
```
(Use your actual Railway URL from step 5 above)

### 4. Redeploy
After adding the env var, trigger a redeploy from the Vercel dashboard.

---

## Local development (unchanged)
```bash
# Terminal 1 — backend
cd flight-search/backend
python -m uvicorn main:app --reload

# Terminal 2 — frontend
cd flight-search/frontend
npm start
```

The Vite proxy handles routing locally so no env vars are needed.
