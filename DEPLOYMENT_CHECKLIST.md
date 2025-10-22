# Deployment Checklist - Crazyflie Swarm Demo

## ✅ Frontend Configuration (GitHub Pages)
- **Repository**: https://github.com/ArmanShirzad/crazyfileDemo
- **Frontend Path**: `/frontend` (will be deployed to root)
- **API URL**: `https://crazyfileswarmdemoimrclab-production.up.railway.app`
- **GitHub Actions**: Automatic deployment on push to main
- **Expected URL**: `https://armanshirzad.github.io/crazyfileDemo/`

## ✅ Backend Configuration (Railway)
- **Project**: `crazyfileswarmdemoimrclab`
- **Domain**: `https://crazyfileswarmdemoimrclab-production.up.railway.app`
- **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**:
  - `BACKEND=mock`
  - `LOG_LEVEL=info`
  - `MAX_DRONES=10`
  - `SIMULATION_SPEED=1.0`
  - `BEARER_TOKEN=demo-token`

## 🔧 Deployment Files Status
- ✅ `Procfile`: `web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- ✅ `nixpacks.toml`: Properly configured for Python backend
- ✅ `railway.toml`: Start command synchronized
- ✅ `runtime.txt`: Python 3.11 specified
- ✅ `.github/workflows/deploy-frontend.yml`: GitHub Pages deployment
- ✅ `frontend/js/api.js`: Correct Railway URL configured

## 🚀 Manual Deployment Steps

### Backend (Railway):
1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select `ArmanShirzad/crazyfileDemo`
4. Railway will auto-detect Python and deploy
5. Set environment variables in Railway dashboard
6. Get the deployment URL

### Frontend (GitHub Pages):
1. Go to repository Settings → Pages
2. Source: GitHub Actions
3. Push to main branch triggers automatic deployment
4. Frontend will be available at GitHub Pages URL

## 🔗 Connection Verification
- Frontend will connect to Railway backend automatically
- API calls will go to `https://crazyfileswarmdemoimrclab-production.up.railway.app`
- CORS is configured to allow all origins
- Bearer token: `demo-token`

## 📋 Testing Checklist
- [ ] Railway backend responds to `/health`
- [ ] Frontend loads from GitHub Pages
- [ ] Frontend shows "Connected" status
- [ ] API calls work between frontend and backend
- [ ] Drone simulation functions properly
