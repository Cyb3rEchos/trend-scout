# 🚀 GitHub Actions Setup Guide

## 🔐 Required Secrets

You need to add 3 secrets to your GitHub repository:

**Go to: Settings → Secrets and variables → Actions**

| Secret Name | Description |
|-------------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Your Supabase service role key |
| `HUGGING_FACE_API_KEY` | Your Hugging Face API token |

## 🧪 Testing

1. Go to **Actions** tab
2. Click **🧪 Test Automation (Manual)**
3. Click **Run workflow**
4. Watch it collect test data

## 🏭 Production

The workflow runs automatically at **9:00 AM UTC** daily.

Manual run:
1. Go to **Actions** tab
2. Click **📱 Daily Trend Scout Automation**
3. Click **Run workflow**

## 📊 What It Does

- ✅ Collects top apps from 10 categories
- ✅ Scrapes app details with caching  
- ✅ Generates AI recommendations
- ✅ Stores in Supabase database
- ✅ Creates detailed logs

## 💰 Cost: FREE

Runs within GitHub's 2,000 min/month free tier.