# Free Deployment Guide - Excel Mock Interviewer

This guide shows exactly how to deploy the entire system using only free services.

## Prerequisites

1. GitHub account (free)
2. Render.com account (free tier)
3. Streamlit Cloud account (free)
4. Optional: Groq account for API key (free tier)

## Step 1: Prepare Repository

1. Fork/clone the repository to your GitHub account
2. Ensure all files are committed and pushed
3. Copy .env.example to .env and configure (see Step 4)

## Step 2: Deploy Database & Redis (Render.com)

### PostgreSQL Database

1. Go to https://render.com and sign up/login
2. Click "New +" → "PostgreSQL"
3. Fill in:
   - Name: excel-interview-db
   - Database: interview_db  
   - User: interview_user
   - Plan: Free
4. Click "Create Database"
5. Copy the "Internal Database URL" for later

### Redis Instance

1. Click "New +" → "Redis"
2. Fill in:
   - Name: excel-interview-redis
   - Plan: Free (25MB)
3. Click "Create Redis"
4. Copy the "Internal Redis URL" for later

## Step 3: Deploy Backend API (Render.com)

1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Fill in:
   - Name: excel-interview-api
   - Runtime: Python 3
   - Build Command: pip install -r backend/requirements.txt
   - Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   - Root Directory: backend
   - Plan: Free

4. Set Environment Variables:
   - DATABASE_URL: [paste Internal Database URL from Step 2]
   - REDIS_URL: [paste Internal Redis URL from Step 2]  
   - MOCK_MODE: true (or false if you have API keys)
   - GROQ_API_KEY: [your key or leave empty]
   
5. Click "Create Web Service"
6. Wait for deployment (5-10 minutes)
7. Copy the service URL (e.g., https://excel-interview-api.onrender.com)

## Step 4: Deploy Frontend (Streamlit Cloud)

1. Go to https://share.streamlit.io
2. Click "New app"
3. Select your GitHub repository
4. Fill in:
   - Branch: main
   - Main file path: frontend/streamlit_app.py
   - App URL: excel-mock-interviewer (or your choice)

5. Click "Advanced settings" and add:

[build]
requirements = ["streamlit>=1.28.0", "requests>=2.31.0"]

[env]
API_BASE_URL = "https://excel-interview-api.onrender.com"


6. Click "Deploy"
7. Your app will be available at: https://excel-mock-interviewer.streamlit.app

## Step 5: Deploy Worker Service (Render.com)

1. Click "New +" → "Background Worker"  
2. Connect your GitHub repository
3. Fill in:
- Name: excel-interview-worker
- Runtime: Python 3
- Build Command: pip install -r backend/requirements.txt
- Start Command: python -m app.workers.evaluator_worker
- Root Directory: backend
- Plan: Free

4. Use same Environment Variables as Step 3
5. Click "Create Background Worker"

## Step 6: Get Groq API Key (Optional but Recommended)

1. Go to https://console.groq.com
2. Sign up for free account
3. Navigate to API Keys section
4. Create new API key
5. Update your Render services:
- Go to each service → Environment tab
- Set GROQ_API_KEY to your key
- Set MOCK_MODE to false
- Save changes (services will auto-redeploy)

## Step 7: Test Deployment

1. Visit your Streamlit app URL
2. Create a test interview
3. Answer a few questions  
4. Verify evaluation works
5. Generate a report

## Step 8: Monitor Free Tier Limits

### Render.com Limits (Free Tier):
- 750 hours/month per service (sleep after 15min idle)
- 100GB bandwidth/month
- PostgreSQL: 1GB storage, 97 connections
- Redis: 25MB memory

### Streamlit Cloud Limits:
- 1GB memory per app
- Unlimited public apps
- 3 private apps

## Troubleshooting

**Service won't start:**
- Check logs in Render dashboard
- Verify environment variables
- Ensure requirements.txt is correct

**Database connection fails:**
- Use Internal URLs (not External)
- Check DATABASE_URL format
- Verify service names match

**Frontend can't connect to API:**
- Ensure API_BASE_URL uses https://
- Check CORS settings in backend
- Verify API service is running

**Evaluation not working:**
- Check worker service logs
- Verify REDIS_URL is correct
- Test with MOCK_MODE=true first

## Cost Optimization

- Services sleep after 15min idle (free tier)
- Use MOCK_MODE=true to avoid API costs during development
- Monitor bandwidth usage in Render dashboard
- Consider upgrading to paid tiers only when needed

## Scaling Beyond Free Tier

When ready to scale:
1. Upgrade Render services to paid plans
2. Add horizontal scaling (multiple worker instances)
3. Use external Redis (Redis Cloud) for better performance
4. Consider AWS/GCP for larger storage needs

