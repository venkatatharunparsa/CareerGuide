# Complete Setup Guide

From zero to a fully running Job Agent in under 30 minutes.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Get Your API Keys](#get-your-api-keys)
3. [Local Setup](#local-setup)
4. [Test It Works](#test-it-works)
5. [AWS Free Tier Deployment](#aws-free-tier-deployment)
6. [Make It Run 24/7](#make-it-run-247)
7. [Set Up Auto-Deploy](#set-up-auto-deploy)
8. [Email Notifications](#email-notifications)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you start, make sure you have:

| Tool | Version | Download |
|---|---|---|
| Git | Any | https://git-scm.com |
| Docker Desktop | Latest | https://docker.com/products/docker-desktop |
| Python | 3.9+ | https://python.org (only for running tests) |
| A browser | Any | You have this |

Check Docker is running:
```bash
docker --version
docker compose version
```

---

## Get Your API Keys

You need 2 services. Both are completely free.

### Gemini API Keys (get 3 from 3 Google accounts)

1. Go to https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the key (starts with AIzaSy...)
5. Repeat with 2 more Google accounts

Why 3 keys? Free tier allows 1500 requests/day per key.
3 keys = 4500 requests/day. The agent rotates automatically.

### Tavily Search API Key

1. Go to https://tavily.com
2. Sign up free
3. Go to dashboard → copy your API key (starts with tvly-)

Free tier: 1000 searches/month. Enough for 1 user running every 6 hours.

---

## Local Setup

### Step 1 — Fork and clone

First fork the repo on GitHub (click Fork button top right).
Then clone your fork:

```bash
git clone https://github.com/YOUR_USERNAME/CareerGuide.git
cd CareerGuide/job-agent
```

### Step 2 — Create environment file

```bash
cp .env.example .env
```

Open .env in any text editor and fill in:

```env
# Your 3 Gemini API keys
GEMINI_API_KEY_1=AIzaSy_your_first_key_here
GEMINI_API_KEY_2=AIzaSy_your_second_key_here
GEMINI_API_KEY_3=AIzaSy_your_third_key_here

# Your Tavily key
TAVILY_API_KEY=tvly-your_key_here

# Generate a random secret key
# Run: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=paste_generated_key_here

# Leave these as default for local
APP_ENV=development
FRONTEND_URL=http://localhost:3000
CHROMA_PERSIST_PATH=/chroma_db
SQLITE_DB_PATH=/chroma_db/jobagent.db
```

Generate your SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste it as SECRET_KEY in .env

### Step 3 — Build and run

```bash
docker compose up --build -d
```

First build takes 5-10 minutes (downloads Python, Node, dependencies).
Subsequent builds take under 2 minutes.

Watch the build:
```bash
docker compose logs -f backend
```

Wait until you see:
job_agent_backend | INFO: Application startup complete.

Then press Ctrl+C to stop watching logs.
The containers keep running in the background.

### Step 4 — Open the app

Open your browser and go to:
http://localhost:3000

You should see the Job Agent login page.

---

## Test It Works

### Quick smoke test

Install httpx first:
```bash
pip install httpx
```

Run the test:
```bash
python tests/test_smoke.py
```

Expected output:
=== Job Agent Smoke Test ===
[OK] Health check: 200
[OK] Register user: 201
[OK] Login: 200
[OK] Auth /me: 200
[OK] Update profile: 200
[OK] Get profile: 200
Running agent (180s timeout)...
[OK] Run agent: 200
-> X jobs found, avg score X%
[OK] Get jobs: 200
=== ALL TESTS PASSED ===

### Full manual test

1. Open http://localhost:3000
2. Click Register — create an account
3. Go to Profile page
4. Upload your resume PDF (skills auto-extracted)
5. Add your projects with tech stacks
6. Add target roles (Backend Developer, ML Engineer etc)
7. Click Save Profile
8. Go to Dashboard
9. Click Run Job Agent
10. Wait 60-90 seconds
11. Go to Jobs page
12. You should see real jobs with match scores
13. Click any job to expand — see matched/missing skills
14. Click Tailor Resume PDF — download your custom resume

### Stop and start

```bash
# Stop
docker compose down

# Start again (fast, uses existing image)
docker compose up -d

# Rebuild after code changes
docker compose up --build -d
```

---

## AWS Free Tier Deployment

Deploy once. Runs forever. Costs $0/month.

### AWS Free Tier limits we use
- EC2 t3.micro: 750 hours/month free (enough for 24/7)
- EBS storage: 30GB free
- Data transfer: 15GB/month free

### Step 1 — Create AWS account

Go to https://aws.amazon.com/free and create an account.
You need a credit card but will NOT be charged if you
stay within free tier limits.

### Step 2 — Launch EC2 instance

1. Go to AWS Console → EC2 → Launch Instance
2. Fill in these settings:

**Name:** job-agent

**OS:** Amazon Linux 2023 (free tier eligible)

**Instance type:** t3.micro (free tier eligible)

**Key pair:**
- Click Create new key pair
- Name: job-agent-key
- Type: RSA
- Format: .pem
- Click Create and download
- SAVE THIS FILE — you cannot download it again

**Security group — add these inbound rules:**
- SSH | TCP | Port 22 | Source: Anywhere
- HTTP | TCP | Port 80 | Source: Anywhere
- Custom TCP | Port 8000 | Source: Anywhere
- Custom TCP | Port 3000 | Source: Anywhere

**Storage:** 20GB gp3 (within free tier)

3. Click Launch Instance
4. Wait 2 minutes for status to show Running
5. Click on the instance and copy the Public IPv4 address
   It looks like: 3.xx.xx.xx

### Step 3 — Connect to EC2

**On Windows (PowerShell):**
```powershell
# Fix key permissions first
icacls "C:\path\to\job-agent-key.pem" /inheritance:r /grant:r "$($env:USERNAME):(R)"

# Connect
ssh -i "C:\path\to\job-agent-key.pem" ec2-user@YOUR_EC2_IP
```

**On Mac/Linux:**
```bash
chmod 400 ~/Downloads/job-agent-key.pem
ssh -i ~/Downloads/job-agent-key.pem ec2-user@YOUR_EC2_IP
```

You should see the Amazon Linux welcome screen.

### Step 4 — Install Docker on EC2

Run these commands inside the EC2 terminal:

```bash
# Update and install Docker + Git
sudo yum update -y
sudo yum install -y docker git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Docker Buildx (required for build)
mkdir -p ~/.docker/cli-plugins
curl -SL "https://github.com/docker/buildx/releases/download/v0.17.1/buildx-v0.17.1.linux-amd64" -o ~/.docker/cli-plugins/docker-buildx
chmod +x ~/.docker/cli-plugins/docker-buildx

# Verify
docker --version
docker-compose --version
docker buildx version
```

Expected output:
Docker version 25.x.x
Docker Compose version v2.24.x
github.com/docker/buildx v0.17.1

### Step 5 — Clone and configure

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/CareerGuide.git
cd CareerGuide/job-agent

# Create .env file
nano .env
```

In the nano editor, paste your .env content
(same as local but update FRONTEND_URL):

```env
GEMINI_API_KEY_1=AIzaSy_your_first_key
GEMINI_API_KEY_2=AIzaSy_your_second_key
GEMINI_API_KEY_3=AIzaSy_your_third_key
TAVILY_API_KEY=tvly-your_key
SECRET_KEY=your_generated_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CHROMA_PERSIST_PATH=/chroma_db
SQLITE_DB_PATH=/chroma_db/jobagent.db
APP_ENV=production
FRONTEND_URL=http://YOUR_EC2_IP:3000
GMAIL_SENDER=
GMAIL_APP_PASSWORD=
NOTIFICATION_EMAIL=
```

Replace YOUR_EC2_IP with your actual EC2 public IP.

Save: Ctrl+X → Y → Enter

### Step 6 — Update API URL for frontend

```bash
sed -i 's|VITE_API_URL=http://localhost:8000|VITE_API_URL=http://YOUR_EC2_IP:8000|g' docker-compose.yml
```

Replace YOUR_EC2_IP with your actual EC2 public IP.

### Step 7 — Build and deploy

```bash
docker-compose up --build -d
```

This takes 5-15 minutes on first run.
Watch progress:
```bash
docker-compose logs -f backend
```

Wait for:
job_agent_backend | INFO: Application startup complete.

### Step 8 — Verify it is running

Test the API:
```bash
curl http://localhost:8000/health
```

Expected: {"status":"ok","env":"production"}

Open in browser:
http://YOUR_EC2_IP:3000

You should see the login page.

---

## Make It Run 24/7

Currently if the EC2 reboots, containers stop.
Fix this with systemd:

```bash
sudo nano /etc/systemd/system/job-agent.service
```

Paste this:
```ini
[Unit]
Description=Job Agent Application
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ec2-user/CareerGuide/job-agent
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=300
User=ec2-user

[Install]
WantedBy=multi-user.target
```

Save: Ctrl+X → Y → Enter

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable job-agent
sudo systemctl start job-agent
sudo systemctl status job-agent
```

You should see: Active: active (exited)

Now containers automatically start when EC2 reboots.

The APScheduler inside the backend container runs the
job search agent every 6 hours automatically.
No cron jobs needed. No manual intervention ever.

---

## Set Up Auto-Deploy

Every time you push code to GitHub, it automatically
deploys to your EC2 instance.

### Step 1 — Add GitHub Secrets

Go to your GitHub repo →
Settings → Secrets and variables → Actions → New repository secret

Add these 3 secrets:

| Name | Value |
|---|---|
| EC2_HOST | Your EC2 public IP (3.xx.xx.xx) |
| EC2_USER | ec2-user |
| EC2_SSH_KEY | Full contents of job-agent-key.pem file |

To get EC2_SSH_KEY contents:

**Windows:**
```powershell
Get-Content "C:\path\to\job-agent-key.pem"
```

**Mac/Linux:**
```bash
cat ~/Downloads/job-agent-key.pem
```

Copy everything including the
-----BEGIN RSA PRIVATE KEY----- and
-----END RSA PRIVATE KEY----- lines.

### Step 2 — Push any change to trigger deploy

```bash
git add .
git commit -m "test: trigger auto deploy"
git push origin main
```

Go to GitHub → Actions tab → watch the deployment run.

After 2-3 minutes your EC2 will have the latest code running.

---

## Email Notifications

Get job digest emails automatically every 6 hours.

### Step 1 — Get Gmail App Password

1. Go to https://myaccount.google.com
2. Click Security
3. Click 2-Step Verification (enable if not already)
4. Scroll down to App Passwords
5. Click App Passwords
6. Select app: Mail
7. Select device: Other → type "Job Agent"
8. Click Generate
9. Copy the 16-character password shown

### Step 2 — Add to .env

On EC2:
```bash
nano ~/CareerGuide/job-agent/.env
```

Fill in these lines:
```env
GMAIL_SENDER=youremail@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
NOTIFICATION_EMAIL=youremail@gmail.com
```

Save and restart backend:
```bash
cd ~/CareerGuide/job-agent
docker-compose restart backend
```

Next agent run (within 6 hours) will send you an email
with job matches and direct apply links.

---

## Troubleshooting

### Docker build fails with playwright error
Error: playwright install-deps failed
Fix: This is expected. Playwright is not used in basic mode.
The build should still succeed. If it fails completely:
```bash
docker compose down
docker compose up --build -d
```

### Backend returns 500 on agent run
Error: 500 Internal Server Error
Fix: Your profile has no skills saved.
Go to Profile page → add skills + target roles → Save → try again.

### CORS error in browser console
Error: Access-Control-Allow-Origin header missing
Fix:
```bash
# Check FRONTEND_URL in .env
grep FRONTEND_URL .env
# Should show: FRONTEND_URL=http://YOUR_EC2_IP:3000

# If wrong, fix it
nano .env
# Update FRONTEND_URL

docker-compose restart backend
```

### Frontend calls localhost instead of EC2 IP
Error: net::ERR_CONNECTION_REFUSED localhost:8000
Fix:
```bash
grep VITE_API_URL docker-compose.yml
# Should show your EC2 IP

# If wrong:
sed -i 's|localhost:8000|YOUR_EC2_IP:8000|g' docker-compose.yml
docker-compose up --build -d
```

### Gemini returns 429 quota exceeded
WARNING: Rate limit hit, rotating key
This is normal on free tier. The system automatically:
1. Rotates to next API key
2. Falls back to keyword matching if all keys exhausted
3. Resets the next day

Fix: Add more Gemini keys or wait 24 hours for reset.

### Jobs found but match score is very low (under 50%)
Fix: Your profile needs more data.
- Upload your resume PDF (auto-extracts skills)
- Add projects with tech stacks
- Add work experience
- Set specific target roles
More profile data = much better matching.

### PDF shows LaTeX code instead of resume
Fix: Upload your resume PDF from Profile page first.
The system needs real resume content to tailor from.
Without it, it uses a basic fallback template.

### EC2 containers stopped after reboot
Fix: Set up systemd service (see Make It Run 24/7 section above).

### Cannot connect to EC2 via SSH
Error: Permission denied (publickey)
Fix on Windows:
```powershell
icacls "path\to\job-agent-key.pem" /inheritance:r /grant:r "$($env:USERNAME):(R)"
```
Fix on Mac/Linux:
```bash
chmod 400 path/to/job-agent-key.pem
```

### Port 3000 not accessible in browser
Fix: Add inbound rule in EC2 Security Group:
AWS Console → EC2 → Security Groups →
Edit inbound rules → Add rule:
Custom TCP | Port 3000 | Anywhere (0.0.0.0/0)

### Check container status
```bash
docker-compose ps
docker-compose logs backend --tail=50
docker-compose logs frontend --tail=20
```

### Restart everything fresh
```bash
docker-compose down
docker-compose up -d
```

### Nuclear option — full rebuild
```bash
docker-compose down
docker system prune -f
docker-compose up --build -d
```

---

## Useful Commands Reference

```bash
# Check if running
docker-compose ps

# Watch backend logs live
docker-compose logs -f backend

# Restart backend only
docker-compose restart backend

# Rebuild after code change
docker-compose up --build -d

# Stop everything
docker-compose down

# Check API health
curl http://localhost:8000/health

# Run smoke test
python tests/test_smoke.py

# Check EC2 disk space
df -h

# Check memory usage
free -m

# Check container resource usage
docker stats
```

---

## Cost Monitoring

Stay within AWS Free Tier:

1. Go to AWS Console → Billing → Free Tier
2. Check your usage monthly
3. Set a billing alert:
   - AWS Console → Billing → Budgets
   - Create budget → $1/month threshold
   - Add your email
   - You will be notified before any charges

Things that could accidentally cost money:
- Running more than 1 EC2 instance
- EBS volume over 30GB
- Data transfer over 15GB/month
- Leaving snapshots or AMIs lying around

---

## Getting Help

- Open a GitHub Issue for bugs
- Start a GitHub Discussion for questions
- Check existing issues before opening new ones
- Include docker-compose logs output with bug reports

---

## What to do after setup

1. Upload your resume PDF from Profile page
2. Add your real skills and target roles
3. Add your projects with tech stacks
4. Run the agent once manually from Dashboard
5. Check your email for the job digest
6. Come back in 6 hours — new jobs will be there automatically

That is it. The agent runs forever from here.
