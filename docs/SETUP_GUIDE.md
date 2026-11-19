# DesiReels Studio — Platform Setup & Credentials Guide
**Step-by-Step Instructions for YouTube Shorts, Instagram Reels, Facebook Reels & macOS Power Settings**

---

## 1. Security Philosophy & Manual Boundaries

**Why Manual Setup?**
In strict accordance with enterprise security practices, DesiReels Studio enforces an absolute boundary between local AI video generation and third-party account authentication:
- **No Stored Passwords:** The system never asks for or stores account passwords.
- **Strictly Git-Ignored:** All tokens, JSON keys, and credentials are saved in `credentials/` and `.env`, which are hard-blocked by `.gitignore`.
- **DRY_RUN Safety Default:** `DRY_RUN=true` is the default in `.env`. Even if you configure credentials, nothing is published live until you explicitly set `DRY_RUN=false`.

---

## 2. YouTube Shorts Setup (Google Data API v3)

YouTube Shorts uses standard Google OAuth 2.0 with a persistent offline refresh token.

### Step 2.1: Create a Google Cloud Project
1. Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click **Select a project** $\rightarrow$ **New Project**.
3. Name your project: `DesiReels Studio` $\rightarrow$ Click **Create**.

### Step 2.2: Enable YouTube Data API v3
1. In the Google Cloud Console, open the navigation menu and select **APIs & Services** $\rightarrow$ **Library**.
2. Search for `YouTube Data API v3`.
3. Select it and click **Enable**.

### Step 2.3: Configure OAuth Consent Screen
1. Go to **APIs & Services** $\rightarrow$ **OAuth consent screen**.
2. Select **External** user type $\rightarrow$ Click **Create**.
3. Fill in:
   - **App name:** `DesiReels Studio`
   - **User support email:** Your personal Gmail address
   - **Developer contact information:** Your personal Gmail address
4. Click **Save and Continue**.
5. Under **Scopes**, click **Add or Remove Scopes**, check:
   - `.../auth/youtube.upload` (Upload YouTube videos)
   - `.../auth/youtube` (Manage your YouTube account)
6. Under **Test users**, click **Add Users** and enter your personal Google email (the channel owner email).
7. Save and finish.

### Step 2.4: Create OAuth Client ID
1. Go to **APIs & Services** $\rightarrow$ **Credentials**.
2. Click **Create Credentials** $\rightarrow$ **OAuth client ID**.
3. Select **Application type:** `Desktop app`.
4. Name: `DesiReels Desktop Uploader` $\rightarrow$ Click **Create**.
5. Click **Download JSON** on the created credential.
6. Rename the downloaded file to `youtube_client_secret.json` and move it into:
   ```bash
   desi-reels-studio/credentials/youtube_client_secret.json
   ```

### Step 2.5: Generate Your Offline Refresh Token
Run the interactive authentication script once from your terminal:
```bash
cd /Users/amrit/.gemini/antigravity/scratch/desi-reels-studio
python3 scripts/auth_youtube.py
```
- Your default web browser will open asking you to sign in with your Google account.
- Select your channel, accept the upload permissions, and click **Continue**.
- The script automatically saves the persistent refresh token to `credentials/youtube_token.json`.

---

## 3. Instagram Reels Setup (Meta Graph API)

Instagram Reels publishing requires an **Instagram Professional (Creator or Business) Account** connected to a Facebook Page.

### Step 3.1: Switch to Professional Account & Link to Page
1. On your smartphone, open the Instagram app $\rightarrow$ Profile $\rightarrow$ **Settings** $\rightarrow$ **Account type and tools** $\rightarrow$ **Switch to professional account** (choose "Creator" or "Video Creator").
2. Connect your Instagram account to a Facebook Page you own (Profile $\rightarrow$ Edit profile $\rightarrow$ Public business information $\rightarrow$ Page).

### Step 3.2: Create a Meta for Developers App
1. Navigate to the [Meta for Developers Portal](https://developers.facebook.com/).
2. Click **My Apps** $\rightarrow$ **Create App**.
3. Select **Other** $\rightarrow$ Next $\rightarrow$ Select **Business** as the app type.
4. Name your app: `DesiReels Studio` $\rightarrow$ Click **Create App**.

### Step 3.3: Add Instagram Graph API
1. In the app dashboard, find **Instagram Graph API** and click **Set Up**.
2. In the left sidebar, navigate to **Tools** $\rightarrow$ **Graph API Explorer**.

### Step 3.4: Generate Long-Lived Access Token
1. In the **Graph API Explorer**, select your app (`DesiReels Studio`) from the dropdown.
2. Under **Permissions**, add:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
   - `pages_read_engagement`
3. Click **Generate Access Token** and log in to Facebook, granting permissions for your Page and Instagram account.
4. Convert this short-lived token to a **60-day Long-Lived Token**:
   - Make this GET request in the Graph API Explorer:
     ```text
     oauth/access_token?grant_type=fb_exchange_token&client_id={YOUR_APP_ID}&client_secret={YOUR_APP_SECRET}&fb_exchange_token={SHORT_LIVED_TOKEN}
     ```
   - Copy the resulting `access_token`.

### Step 3.5: Find your Instagram Business Account ID
In the Graph API Explorer, query:
```text
me/accounts?fields=instagram_business_account{id,username}
```
Copy the returned `instagram_business_account.id` (e.g., `17841400000000000`).

### Step 3.6: Update your `.env`
Add these two lines to your `desi-reels-studio/.env`:
```ini
INSTAGRAM_ACCOUNT_ID=17841400000000000
INSTAGRAM_ACCESS_TOKEN=EAA...your_long_lived_token...
```

---

## 4. Facebook Reels Setup (Meta Page Video Reels API)

Facebook Page Reels uses the same Meta Developer App and allows posting directly to your Facebook Page feed.

### Step 4.1: Retrieve Your Facebook Page ID
1. Open your Facebook Page in a browser.
2. Click **About** $\rightarrow$ **Page Transparency** (or scroll to Page ID), or query in Graph API Explorer:
   ```text
   me/accounts?fields=id,name,access_token
   ```
3. Copy the numeric `id` of your Page.

### Step 4.2: Retrieve a Permanent Page Access Token
From the `me/accounts` response above, copy the specific `access_token` for your Facebook Page. A Page Access Token obtained from a 60-day user token never expires as long as your user account maintains admin rights over the Page.

### Step 4.3: Update your `.env`
Add these two lines to your `desi-reels-studio/.env`:
```ini
FACEBOOK_PAGE_ID=your_page_numeric_id
FACEBOOK_PAGE_ACCESS_TOKEN=EAA...your_page_access_token...
```

---

## 5. macOS MacBook Air M5 Sleep & Power Settings

Because the MacBook Air M5 is fanless and highly energy-efficient, we recommend configuring macOS to ensure smooth once-daily runs without draining battery.

### 5.1 How macOS `launchd` Handles Sleep
- macOS `launchd` is calendar-aware.
- If your MacBook Air is asleep when the 18:00 IST trigger arrives, **macOS will automatically execute the daily task immediately upon system wake**. No daily video is ever lost.

### 5.2 Optional: Auto-Wake at 17:55 IST (Power Adapter Mode)
If you prefer your Mac to wake up automatically from sleep on weekdays:
```bash
# Wakes the system at 17:55:00 every day
sudo pmset repeat wake MTWRFSU 17:55:00
```
*(To cancel auto-wake later: `sudo pmset repeat cancel`).*

### 5.3 Battery Optimization
In macOS **System Settings** $\rightarrow$ **Battery** $\rightarrow$ **Options**:
- Enable **Wake for network access** (Only on Power Adapter).
- Keep **Low Power Mode** set to "Never" or "Only on Battery" to ensure fast hardware-accelerated video rendering.

---

## 6. Verifying Platform Connections Without Publishing

Before flipping `DRY_RUN=false`, test your configurations safely:

### 1. Test YouTube OAuth Token
```bash
python3 -c "
from src.config import config
print('Client Secret Exists:', config.YOUTUBE_CLIENT_SECRETS_FILE.is_file())
print('Token File Exists:', config.YOUTUBE_TOKEN_FILE.is_file())
"
```

### 2. Test Instagram Reels Token Validity
```bash
source .env
curl -s "https://graph.facebook.com/v20.0/${INSTAGRAM_ACCOUNT_ID}?fields=username,name&access_token=${INSTAGRAM_ACCESS_TOKEN}"
```
*(Expected response: `{"username": "your_handle", "id": "..."}`).*

### 3. Test Facebook Page Token Validity
```bash
source .env
curl -s "https://graph.facebook.com/v20.0/${FACEBOOK_PAGE_ID}?fields=name,category&access_token=${FACEBOOK_PAGE_ACCESS_TOKEN}"
```
*(Expected response: `{"name": "Your Page Name", "id": "..."}`).*

### 4. Test Dry-Run Publishing Stage
```bash
python3 -m src.orchestrator
```
*(Confirms that payload formatting, title checks, hashtag assembly, and SQLite logging succeed).*
