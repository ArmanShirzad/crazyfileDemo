# Deployment Guide

This guide covers deploying the Crazyflie Swarm Demo to production environments.

## Overview

The demo uses a two-tier deployment:
- **Backend**: Railway (containerized FastAPI)
- **Frontend**: GitHub Pages (static files)

## Backend Deployment (Railway)

### Prerequisites
- Railway account (free tier available)
- GitHub repository with the code
- Docker installed locally (for testing)

### Step 1: Prepare for Deployment

1. **Create Railway Project**:
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login to Railway
   railway login
   
   # Create new project
   railway init
   ```

2. **Configure Environment Variables**:
   ```bash
   railway variables set BACKEND=mock
   railway variables set LOG_LEVEL=info
   railway variables set MAX_DRONES=10
   railway variables set SIMULATION_SPEED=1.0
   railway variables set BEARER_TOKEN=your-secure-token-here
   ```

3. **Test Docker Build Locally**:
   ```bash
   # Build Docker image
   docker build -t crazyflie-demo .
   
   # Test locally
   docker run -p 8000:8000 -e BACKEND=mock crazyflie-demo
   ```

### Step 2: Deploy to Railway

1. **Connect Repository**:
   - Go to Railway dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

2. **Configure Build Settings**:
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `/` (project root)

3. **Set Environment Variables**:
   ```bash
   BACKEND=mock
   LOG_LEVEL=info
   MAX_DRONES=10
   SIMULATION_SPEED=1.0
   BEARER_TOKEN=your-secure-token-here
   PORT=8000
   ```

4. **Deploy**:
   - Railway will automatically build and deploy
   - Monitor logs in the Railway dashboard
   - Test the health endpoint: `https://your-app.railway.app/health`

### Step 3: Configure Custom Domain (Optional)

1. **Add Custom Domain**:
   - Go to Railway project settings
   - Add custom domain
   - Update DNS records as instructed

2. **Update Frontend Configuration**:
   - Update `frontend/js/api.js` with your domain
   - Update CORS settings in `backend/main.py`

## Frontend Deployment (GitHub Pages)

### Step 1: Prepare Frontend

1. **Update API Configuration**:
   ```javascript
   // In frontend/js/api.js
   getBaseURL() {
       if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
           return 'http://localhost:8000';
       } else {
           return 'https://your-app.railway.app';  // Update this
       }
   }
   ```

2. **Test Locally**:
   ```bash
   cd frontend
   python -m http.server 3000
   # Open http://localhost:3000
   ```

### Step 2: Deploy to GitHub Pages

1. **Enable GitHub Pages**:
   - Go to repository Settings
   - Scroll to "Pages" section
   - Select "Deploy from a branch"
   - Choose "main" branch and "/ (root)" folder

2. **Create gh-pages Branch** (Alternative method):
   ```bash
   # Create and switch to gh-pages branch
   git checkout -b gh-pages
   
   # Copy frontend files to root
   cp -r frontend/* .
   
   # Commit and push
   git add .
   git commit -m "Deploy frontend to GitHub Pages"
   git push origin gh-pages
   ```

3. **Configure Pages Source**:
   - Go to repository Settings > Pages
   - Select "Deploy from a branch"
   - Choose "gh-pages" branch
   - Save

### Step 3: Update CORS Settings

1. **Update Backend CORS**:
   ```python
   # In backend/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "https://your-username.github.io",
           "https://your-username.github.io/crazyflie-demo",
           "http://localhost:3000"  # For local development
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Redeploy Backend**:
   - Push changes to trigger Railway rebuild
   - Or manually redeploy from Railway dashboard

## Alternative Deployment Options

### Backend Alternatives

#### Heroku
```bash
# Install Heroku CLI
npm install -g heroku

# Login and create app
heroku login
heroku create your-app-name

# Set environment variables
heroku config:set BACKEND=mock
heroku config:set BEARER_TOKEN=your-token

# Deploy
git push heroku main
```

#### DigitalOcean App Platform
1. Connect GitHub repository
2. Configure build settings
3. Set environment variables
4. Deploy

#### AWS Elastic Beanstalk
```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init

# Create environment
eb create production

# Deploy
eb deploy
```

### Frontend Alternatives

#### Netlify
1. Connect GitHub repository
2. Set build command: `echo "No build needed"`
3. Set publish directory: `frontend`
4. Deploy

#### Vercel
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel --prod
```

#### Firebase Hosting
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Initialize
firebase init hosting

# Deploy
firebase deploy
```

## Production Configuration

### Security Considerations

1. **Environment Variables**:
   ```bash
   # Use strong, unique tokens
   BEARER_TOKEN=$(openssl rand -hex 32)
   
   # Enable HTTPS only
   FORCE_HTTPS=true
   ```

2. **Rate Limiting**:
   ```python
   # Add to backend/main.py
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   from slowapi.errors import RateLimitExceeded
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
   
   # Apply to endpoints
   @app.post("/drones/create")
   @limiter.limit("5/minute")
   async def create_swarm(request: Request, ...):
   ```

3. **Input Validation**:
   ```python
   # Add Pydantic validators
   from pydantic import validator
   
   class CreateSwarmRequest(BaseModel):
       count: int
       
       @validator('count')
       def validate_count(cls, v):
           if v < 1 or v > 10:
               raise ValueError('Count must be between 1 and 10')
           return v
   ```

### Monitoring and Logging

1. **Health Checks**:
   ```python
   @app.get("/health")
   async def health_check():
       return {
           "status": "healthy",
           "backend": BACKEND,
           "timestamp": datetime.now().isoformat(),
           "uptime": time.time() - start_time
       }
   ```

2. **Metrics Endpoint**:
   ```python
   @app.get("/metrics")
   async def get_metrics():
       return {
           "active_drones": len(simulator.drones),
           "total_runs": get_total_runs(),
           "memory_usage": get_memory_usage()
       }
   ```

3. **Error Tracking**:
   ```python
   # Add Sentry for error tracking
   import sentry_sdk
   from sentry_sdk.integrations.fastapi import FastApiIntegration
   
   sentry_sdk.init(
       dsn="your-sentry-dsn",
       integrations=[FastApiIntegration()]
   )
   ```

### Performance Optimization

1. **Database Optimization**:
   ```python
   # Use connection pooling
   import sqlite3
   from contextlib import contextmanager
   
   @contextmanager
   def get_db_connection():
       conn = sqlite3.connect('swarm_logs.db', timeout=30)
       conn.execute('PRAGMA journal_mode=WAL')
       conn.execute('PRAGMA synchronous=NORMAL')
       try:
           yield conn
       finally:
           conn.close()
   ```

2. **Caching**:
   ```python
   # Add Redis caching
   import redis
   
   redis_client = redis.Redis(host='localhost', port=6379, db=0)
   
   @app.get("/drones")
   async def get_drones():
       cache_key = "drones_state"
       cached = redis_client.get(cache_key)
       if cached:
           return json.loads(cached)
       
       states = await simulator.get_all_states()
       redis_client.setex(cache_key, 1, json.dumps(states))
       return states
   ```

## Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Check allowed origins in backend
   - Verify frontend URL matches backend configuration

2. **Authentication Errors**:
   - Verify BEARER_TOKEN is set correctly
   - Check token in frontend API calls

3. **Database Errors**:
   - Ensure SQLite file is writable
   - Check disk space on deployment platform

4. **Memory Issues**:
   - Monitor memory usage in Railway dashboard
   - Consider reducing MAX_DRONES limit
   - Implement periodic cleanup of old data

### Debug Commands

```bash
# Check Railway logs
railway logs

# Test API endpoints
curl -H "Authorization: Bearer your-token" https://your-app.railway.app/health

# Check frontend deployment
curl https://your-username.github.io/crazyflie-demo/

# Test CORS
curl -H "Origin: https://your-username.github.io" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: authorization" \
     -X OPTIONS \
     https://your-app.railway.app/drones/create
```

## Maintenance

### Regular Tasks

1. **Monitor Performance**:
   - Check Railway metrics dashboard
   - Monitor response times
   - Watch for memory leaks

2. **Update Dependencies**:
   ```bash
   # Update Python packages
   pip-compile --upgrade requirements.in
   
   # Update frontend libraries
   npm update
   ```

3. **Backup Data**:
   ```bash
   # Export SQLite data
   sqlite3 swarm_logs.db ".dump" > backup.sql
   ```

4. **Security Updates**:
   - Regularly update dependencies
   - Rotate bearer tokens
   - Monitor for security advisories

### Scaling Considerations

1. **Horizontal Scaling**:
   - Use load balancer for multiple backend instances
   - Implement shared database (PostgreSQL)
   - Use Redis for session management

2. **Vertical Scaling**:
   - Upgrade Railway plan for more resources
   - Optimize database queries
   - Implement connection pooling

3. **CDN Integration**:
   - Use CloudFlare for frontend assets
   - Cache static resources
   - Implement edge computing for global users

This deployment guide provides a solid foundation for production deployment while maintaining the flexibility to scale and adapt as needed.
