# Trader Storefront Generator

A FastAPI web application that lets Indian hardware traders create a professional digital storefront page showing their products — with a one-tap WhatsApp order button on every product. Built for traders who sell pipe fittings, electrical hardware, plumbing supplies, and more.

## What This Does

Traders get a store page (like a digital business card + product catalogue) that they can share via WhatsApp, Instagram, or any messaging app. Customers browse products and tap "Order on WhatsApp" — the button opens WhatsApp with a pre-filled message including the product name and price. No app install, no login, no friction.

There are two ways to create a store:

1. **Web form** — fill in a form at `/create-store`, upload photos, and get your store instantly.
2. **WhatsApp** — send voice notes and photos via WhatsApp, and the system builds the store for you. This requires n8n, Twilio, and Groq (see the WhatsApp section below).

## Who It's For

Hardware traders running small businesses in India — pipe fittings shops, electrical suppliers, plumbing material dealers, sanitary ware shops, paint dealers, and similar businesses who currently share products only via WhatsApp forwards or catalogue screenshots.

---

## Environment Variables

The system uses two groups of environment variables: **FastAPI variables** (set locally in `.env` or on Railway) and **n8n variables** (set inside n8n's settings). Do not mix them up.

### FastAPI Variables (local `.env` file or Railway dashboard)

| Variable | What It Does | Where to Get It | Required? |
|----------|-------------|-----------------|-----------|
| `CLOUDINARY_CLOUD_NAME` | Identifies your Cloudinary account | Sign up at [cloudinary.com](https://cloudinary.com) → Dashboard | No — photos save to local `uploads/` folder if not set |
| `CLOUDINARY_API_KEY` | Authenticates uploads to Cloudinary | Cloudinary Dashboard → API Keys | No (same as above) |
| `CLOUDINARY_API_SECRET` | Authenticates uploads to Cloudinary | Cloudinary Dashboard → API Keys | No (same as above) |
| `DATABASE_URL` | Database connection string | Leave blank to use SQLite | No — defaults to `sqlite:///trader_storefront.db` |

**No other variables are needed for the FastAPI app.** The app works immediately without any API keys — photos are saved locally, and the database is SQLite.

### n8n Variables (set in n8n → Settings → Variables)

| Variable | What It Does | Where to Get It |
|----------|-------------|-----------------|
| `GROQ_API_KEY` | Used by Groq Whisper (speech-to-text) and Groq LLM (data extraction) | Sign up at [console.groq.com](https://console.groq.com) → API Keys |
| `TWILIO_ACCOUNT_SID` | Identifies your Twilio account; used to send WhatsApp messages and download media | Sign up at [twilio.com](https://www.twilio.com) → Console → Dashboard |
| `TWILIO_AUTH_TOKEN` | Password for Twilio API calls | Twilio Console → Dashboard (click "Show") |
| `TWILIO_WHATSAPP_NUMBER` | Your Twilio WhatsApp sender number | Twilio Console → WhatsApp Sandbox (e.g., `whatsapp:+14155238886`) |
| `STORE_API_URL` | The URL of your deployed FastAPI app | Your Railway URL (e.g., `https://trader-app.up.railway.app`) |
| `CLOUDINARY_CLOUD_NAME` | Used by n8n to upload trader/product photos to Cloudinary | Same Cloudinary account as above |
| `CLOUDINARY_API_KEY` | Used by n8n for Cloudinary upload auth | Cloudinary Dashboard → API Keys |
| `CLOUDINARY_API_SECRET` | Used by n8n for Cloudinary upload auth | Cloudinary Dashboard → API Keys |

---

## Project Structure

```
trader-storefront/
├── main.py              # FastAPI app, logging, static file serving, startup
├── database.py           # SQLAlchemy engine, session, DB URL validation
├── models.py            # SQLModel tables (Trader, Product)
├── routes/
│   ├── __init__.py
│   ├── store.py         # All /api/store/* endpoints (6 endpoints)
│   └── pages.py         # HTML page routes (4 routes)
├── services/
│   ├── __init__.py
│   ├── cloudinary.py    # Image upload (Cloudinary with local fallback)
│   ├── slug.py          # Unique slug generator with counter-based dedup
│   └── graphic_trigger.py  # Fire-and-forget webhook to n8n
├── templates/
│   ├── index.html       # Landing page (dark theme, hero, features)
│   ├── create.html      # Store creation form (validation, animations)
│   ├── store.html       # Public storefront page (product grid, WhatsApp buttons)
│   └── success.html     # Post-creation success page (copy link, share)
├── static/
│   └── styles.css       # Base CSS overrides (Tailwind via CDN)
├── n8n/
│   └── whatsapp-store-flow.json  # Import into n8n (33-node Twilio + Groq session flow)
├── prompts/
│   ├── trader-extraction.md      # Groq prompt for extracting trader info
│   └── product-extraction.md     # Groq prompt for extracting product info
├── requirements.txt
├── railway.toml
├── .env.example         # Template — copy to .env and fill in your values
├── .gitignore           # Excludes .env, venv, __pycache__, .db, uploads/
└── SETUP.txt            # Quick-start command reference
```

---

## Local Setup — Step by Step

### 1. Extract and Enter the Folder

```bash
cd trader-storefront
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

You will see `(venv)` at the start of your command prompt.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. (Optional) Set Up Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in your Cloudinary credentials if you want cloud photo storage. If you skip this, photos are saved to a local `uploads/` folder and everything still works.

**No API keys are required to run the app locally.**

### 5. Run the Server

```bash
uvicorn main:app --reload --port 8000
```

You will see: `INFO: Uvicorn running on http://127.0.0.1:8000`

### 6. Test the Web Form

1. Open **http://localhost:8000/create-store** in your browser
2. Fill in:
   - Business Name: `Rajesh Hardware`
   - WhatsApp Number: `9876543210`
   - Business Category: `Pipe Fittings`
   - Profile Photo: pick any image
   - Product 1 Name: `CPVC Ball Valve`
   - Product 1 Price: `350`
   - Product 1 Photo: pick any image
3. Click **Create Store**
4. The success page appears with your store link
5. Click the link — your live store page opens with WhatsApp order buttons
6. Click any "Order on WhatsApp" button — WhatsApp opens with a pre-filled message

### Stopping the Server

Press `Ctrl + C` in the terminal.

---

## Railway Deployment — Step by Step

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Trader Storefront Generator"
git remote add origin https://github.com/YOUR_USERNAME/trader-storefront.git
git push -u origin main
```

### 2. Deploy on Railway

1. Go to [railway.app](https://railway.app) and log in with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your `trader-storefront` repository
4. Railway auto-detects `railway.toml` and builds with nixpacks
5. Once deployed, go to the **Variables** tab and add:
   - `CLOUDINARY_CLOUD_NAME` = your cloud name
   - `CLOUDINARY_API_KEY` = your API key
   - `CLOUDINARY_API_SECRET` = your API secret
   - `DATABASE_URL` = (optional, only if you want PostgreSQL instead of SQLite)
6. **Do NOT** add `GROQ_API_KEY`, `TWILIO_*`, or `STORE_API_URL` to Railway — those go in n8n only
7. Railway sets `PORT` automatically — no need to add it
8. Go to **Settings** → **Networking** → set up a custom domain if desired

### 3. Verify Deployment

- Open your Railway URL — the landing page should load
- Test the create-store flow to confirm Cloudinary uploads work in production

---

## Connecting the n8n WhatsApp Flow

This section explains how to set up the WhatsApp conversation flow that lets traders create stores by sending voice notes and photos via WhatsApp.

### Overview

```
Trader's WhatsApp → Twilio → n8n Webhook → Groq (transcribe + extract) → Cloudinary (upload photos) → FastAPI Store API
```

### Prerequisites

Before starting, you need:

- A deployed FastAPI app (Railway URL or `http://localhost:8000` for local testing)
- A [Twilio account](https://www.twilio.com/try-twilio) with WhatsApp Sandbox activated
- A [Groq account](https://console.groq.com) with an API key
- A [Cloudinary account](https://cloudinary.com) (free tier works)
- An n8n instance (self-hosted or [n8n.cloud](https://n8n.cloud))

### Step 1: Set Up Twilio

1. Sign up at [twilio.com](https://www.twilio.com/try-twilio)
2. Go to the **WhatsApp Sandbox** in the Twilio Console
3. Follow the on-screen instructions to activate the sandbox — you will send a join code to the Twilio WhatsApp number
4. Once activated, your phone can send and receive WhatsApp messages through Twilio
5. Note your **Account SID** and **Auth Token** from the Twilio Console dashboard
6. Note the **Twilio WhatsApp Number** (e.g., `whatsapp:+14155238886`)

For production use, you will need to apply for a WhatsApp Business Sender through Twilio.

### Step 2: Set Up n8n Credentials

You need to create two credentials in n8n:

**Credential A — Twilio API (for sending WhatsApp messages):**
1. In n8n, go to **Credentials** → **Add Credential**
2. Search for **Twilio API**
3. Enter your **Account SID** and **Auth Token**
4. Save it (name it "Twilio API" for clarity)

### Step 3: Configure n8n Environment Variables

In n8n, go to **Settings** → **Variables** and add all seven variables listed in the "n8n Variables" table above. These are used by the workflow via `$env.VARIABLE_NAME` expressions.

### Step 4: Import the Workflow

1. In n8n, click **...** (three dots) in the top-left of the editor
2. Select **Import from File**
3. Upload `n8n/whatsapp-store-flow.json`
4. The workflow appears on the canvas with **33 nodes** including:

### Step 5: Attach Twilio Credential to Message Nodes

After importing, the seven Twilio message nodes need their credential set. Click each of these nodes one by one, and in the **Credential** dropdown, select the "Twilio API" credential you created in Step 2:

- **Send Welcome Message** (sends the initial greeting)
- **Ask for Profile Photo** (asks the trader to send a photo)
- **Ask for Products** (instructs the trader to add products)
- **Acknowledge Product Photo** (confirms a product photo was received)
- **Confirm Product Added** (confirms a product was extracted and saved)
- **Send Building Message** (sends "Building your store...")
- **Send Store Ready Message** (sends the final store URL)

### Step 6: Connect Twilio Webhook to n8n

1. Click on the **Twilio Webhook** node in n8n
2. Copy the **Webhook URL** shown at the bottom of the node (e.g., `https://your-n8n.com/webhook/whatsapp-incoming`)
3. Go to **Twilio Console** → **WhatsApp Sandbox** → **"When a message comes in"**
4. Paste the n8n webhook URL and set the method to **HTTP POST**
5. Click **Save**

### Step 7: Activate and Test

1. In n8n, toggle the workflow **Active** (switch in the top-right corner)
2. Send `STORE` to your Twilio WhatsApp number
3. The bot should reply with a welcome message asking for a voice note
4. Follow the full test sequence in the "How to Test the WhatsApp Flow" section below

---

## How to Test the WhatsApp Flow

Make sure your FastAPI app is running and the n8n workflow is Active before testing.

### Step-by-Step Test

| Step | Action | Expected Bot Reply |
|------|--------|-------------------|
| 1 | Send `STORE` to your Twilio WhatsApp number | "Let's build your store! Send a voice note with your business name, WhatsApp number, and business category..." |
| 2 | Send a voice note: *"My name is Rajesh Kumar, my number is 9876543210, I sell pipe fittings and plumbing supplies in Pune"* | Bot transcribes via Groq Whisper, extracts details via Groq LLM, then replies: "Great! Now send a profile photo for your store." |
| 3 | Send any photo | "Looking good! Now add your products. Send a product photo and a voice note with its name and price..." |
| 4 | Send a product photo | "Photo received! Now send a voice note with the product name and price." |
| 5 | Send a voice note: *"This is a CPVC ball valve, price is 350 rupees"* | "Product 1 added. Send your next product photo and voice note, or type DONE to finish." |
| 6 | (Optional) Repeat steps 4–5 for more products | "Product 2 added. ..." |
| 7 | Send `DONE` | "Building your store..." followed by "Your store is live!" with the store URL |
| 8 | Open the store URL in your browser | Store page loads with trader profile, product cards, and working "Order on WhatsApp" buttons |

### Testing the Web Form

1. Open `http://localhost:8000/create-store`
2. Fill in all fields and add at least one product with a photo
3. Click **Create Store**
4. On the success page, click the store link
5. Verify the store page shows the correct products, photos, and WhatsApp buttons
6. Click an "Order on WhatsApp" button — confirm WhatsApp opens with a pre-filled message

---

## Troubleshooting

### Bug 1: "model does not exist" error from Groq

**Symptom:** The Extract Trader Details or Extract Product Details node fails with a 404 error mentioning the model.

**Cause:** The Groq model `llama-3.3-70b-versatile` was discontinued.

**Fix:** Both extract nodes now use `openai/gpt-oss-20b`. If you see this error, open the node in n8n and verify the model name in the JSON Body expression is `openai/gpt-oss-20b`.

### Bug 2: LLM returns raw transcript instead of extracted data

**Symptom:** The extraction node sends the transcript straight through without extracting name/price/category.

**Cause:** The user message content was wrapped in extra single quotes, making n8n treat the entire expression as a literal string instead of evaluating the concatenation.

**Fix:** The content field in both extract nodes now uses clean concatenation: `"Extract trader details from this transcript: " + $json.transcript`. If you see this issue, open the node, click into the JSON Body field, and verify there are no extra single quotes around the `content` value.

### Bug 3: Groq Whisper fails with "no audio data" or empty response

**Symptom:** The Whisper node fails because it receives no audio file.

**Cause:** Twilio webhook sends a media URL, not the actual audio file. The Whisper node needs a downloaded binary file, not a URL string.

**Fix:** Two new nodes — **Download Trader Audio** and **Download Product Audio** — were added before the Whisper nodes. These download the audio from Twilio using Basic Auth (Account SID + Auth Token) and pass it as binary data. If you imported an older version of the flow, re-import the latest `whatsapp-store-flow.json`.

### General Issues

- **No reply after sending STORE:** Check that the n8n workflow is Active, the Twilio webhook URL is correct, and you have joined the WhatsApp Sandbox.
- **Voice note not transcribed:** Verify `GROQ_API_KEY` is set in n8n Settings → Variables. Check the n8n execution log for the Download Audio and Groq Whisper nodes — look for 401 (bad key) or timeout errors.
- **Profile photo upload fails:** Verify all three `CLOUDINARY_*` variables are set in n8n Settings → Variables.
- **Store API call fails:** Verify `STORE_API_URL` in n8n points to your running FastAPI app. Check that the `/api/store/create-whatsapp` endpoint is reachable from n8n.
- **Product photo not showing on store page:** Check the n8n execution log for the "Upload Product Photo" and "Save Product to Session" nodes. Verify the Cloudinary URL is returned and saved correctly.

---

## How Session Management Works

The WhatsApp workflow uses n8n's `$getWorkflowStaticData('global')` to persist session state across multiple webhook calls. Each sender's phone number is a key. The session tracks:

- `state` — current step: `idle`, `waiting_voice_note`, `waiting_profile_photo`, `collecting_products`
- `trader_name`, `whatsapp_number`, `business_category`, `language` — extracted trader data
- `profile_photo_url` — Cloudinary URL of the trader's profile photo
- `products[]` — array of collected products with name, price, description, photo URL, language
- `last_product_photo_url` — temporarily stores a product photo URL while waiting for the voice note
- `product_count` — number of products collected so far

Session data persists in n8n's database as long as the n8n instance is running. It resets if n8n is restarted. For production with strict persistence requirements, replace staticData with a database table or Redis.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/store/create` | Web form store creation (multipart form data) |
| POST | `/api/store/create-whatsapp` | n8n WhatsApp flow store creation (JSON body) |
| GET | `/api/store/{slug}` | Store data as JSON (trader + products) |
| POST | `/api/store/{slug}/add-product` | Add a product to an existing store (multipart) |
| PUT | `/api/store/{slug}/update` | Update trader profile fields (JSON body, partial updates supported) |
| GET | `/` | Landing page (HTML) |
| GET | `/create-store` | Store creation form (HTML) |
| GET | `/store/{slug}` | Public storefront page (HTML) |
| GET | `/store/{slug}/success` | Post-creation success page (HTML) |

### PUT Update Example

```bash
curl -X PUT http://localhost:8000/api/store/rajesh-hardware/update \
  -H "Content-Type: application/json" \
  -d '{"name": "Rajesh Hardware New", "bio": "Best prices in Pune"}'
```

Only the fields you include in the JSON body will be updated. Omitting a field leaves it unchanged.

---

## Graphic Generator Webhook

The create endpoints fire a fire-and-forget HTTP request to `N8N_GRAPHIC_WEBHOOK_URL` for every product created. To use this feature:

1. Set `N8N_GRAPHIC_WEBHOOK_URL` in your `.env` or Railway variables to point to an n8n webhook
2. Create a separate n8n workflow that listens on that webhook URL
3. That workflow receives product data (name, price, photo URL, language) and generates a WhatsApp status graphic
4. It then sends the graphic back to the trader via Twilio

If this variable is not set, the fire-and-forget request silently fails and does not affect store creation.

---

## Sample Stores

1. [Rajesh Hardware - Pipe Fittings Store](https://your-railway-app.up.railway.app/store/rajesh-hardware)
2. [Amit Electrical Supplies](https://your-railway-app.up.railway.app/store/amit-electrical)
3. [Suresh Plumbing Centre](https://your-railway-app.up.railway.app/store/suresh-plumbing)

## Demo Video

[Watch the full demo — web form store creation, WhatsApp flow, and live store page on phone](https://www.loom.com/share/PLACEHOLDER-LOOM-VIDEO-LINK)

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web Framework | FastAPI |
| Database | SQLModel + SQLite (PostgreSQL via DATABASE_URL) |
| Templates | Jinja2 — server-rendered HTML |
| Styling | Tailwind CSS (CDN, no build step) |
| Image Hosting | Cloudinary (with local filesystem fallback) |
| Async HTTP | httpx (fire-and-forget webhook triggers) |
| Slug Generation | python-slugify with counter-based deduplication |
| Deployment | Railway (nixpacks builder) |
| AI (n8n flow) | Groq Whisper + openai/gpt-oss-20b |
| WhatsApp | Twilio WhatsApp API |

## License

MIT
