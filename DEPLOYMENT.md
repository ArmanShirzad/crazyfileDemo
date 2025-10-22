# Deployment Guide

## Frontend Deployment (GitHub Pages)

### Automatic Deployment
The frontend is automatically deployed to GitHub Pages using GitHub Actions.

**URL**: `https://armanshirzad.github.io/crazyfileDemo/`

### Manual Setup (if needed)
1. Go to repository Settings
2. Navigate to Pages section
3. Source: GitHub Actions
4. The workflow will automatically deploy on push to main branch

## Backend Deployment (Railway)

### Prerequisites
1. Railway account (free tier available)
2. GitHub repository connected to Railway

### Deployment Steps

#### Option 1: Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Deploy from project root
railway deploy
```

#### Option 2: Railway Dashboard
1. Go to [Railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will automatically detect Python and deploy

### Environment Variables
Set these in Railway dashboard:
- `BACKEND=mock`
- `LOG_LEVEL=info`
- `MAX_DRONES=10`
- `SIMULATION_SPEED=1.0`
- `BEARER_TOKEN=demo-token`

### Custom Domain (Optional)
1. In Railway dashboard, go to Settings
2. Add custom domain
3. Update frontend API URL accordingly

## Testing Deployment

### Frontend
- Visit: `https://armanshirzad.github.io/crazyfileDemo/`
- Should show connection status as "Connected"

### Backend
- Health check: `https://your-railway-url.up.railway.app/health`
- API docs: `https://your-railway-url.up.railway.app/docs`

## Troubleshooting

### Frontend Issues
- Check browser console for CORS errors
- Verify API URL in `frontend/js/api.js`
- Ensure Railway backend is running

### Backend Issues
- Check Railway logs for errors
- Verify environment variables
- Check Python version compatibility

### CORS Issues
- Backend has CORS configured for all origins
- If issues persist, check Railway environment variables
