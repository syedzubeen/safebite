# SafeBite 🛡️

> A silent Slack agent that privately protects people with celiac disease during team lunches by scanning live menus and alerting them before anyone else knows.

Built for the **Slack Agent Builder Challenge 2026**: Agent for Good track.

![SafeBite Banner](https://github.com/syedzubeen/safebite/blob/d89bf79f3541162b138af09658e46333e1f862a5/assets/5.banner_safebite.gif)



## The Problem

Every time someone posts "team lunch at Karim's, who's in?" in Slack, a person with celiac disease faces an impossible choice: stay quiet and gamble on finding something safe, or announce a medical condition they never wanted to share at work.

SafeBite eliminates that choice.

---

## What SafeBite Does

**Silent Guardian**: Monitors Slack channels for food mentions. When a colleague posts about lunch, SafeBite privately DMs at-risk users with a live menu scan, safe dishes, what to avoid, and nearby gluten-free alternatives if nothing is safe. Nobody in the channel knows.

**Food Query**: Ask SafeBite anything in the Chat panel. "Is biryani safe?" "Can I eat nihari?" SafeBite searches the workspace's Slack history for past team food discussions and returns a personalised verdict with a colored Block Kit response.

**Restaurant Scanner**: `/safebite scan Karim's Delhi` fetches the live menu and returns a full safety report with safe dishes, dishes to avoid, and cuisine-specific tips.

**Ingredient Label Scanner**: Upload a photo of any ingredient label. Gemini Vision reads every ingredient and flags hidden gluten sources like hing, maida, suji, barley malt, and modified starch.

**Food Photo Analysis**: Upload a photo of any dish. SafeBite identifies it and assesses safety with a confidence score.

**Nearby Gluten-Free Finder**: When nothing is safe, SafeBite searches Google Maps for gluten-friendly restaurants within 5km, correctly geocoded to the user's city.

**Weekly Digest via Gmail**: A personalised weekly email sent via a Gmail MCP server that SafeBite connects to as an MCP client.

**App Home Dashboard**: Profile, protection status, and quick action buttons in a dedicated Slack Home tab.

![SafeBite Arch](https://github.com/syedzubeen/safebite/blob/2ee00c307ebaa8449ee6f75a076370855420681a/assets/architecture-diagram.png)

---

## Hackathon Technologies Used

| Technology | How SafeBite uses it |
|---|---|
| **Slack AI Capabilities** | Native Assistant framework, App Home tab, suggested prompts, Chat/History UI |
| **Real-Time Search API** | `assistant.search.context` searches workspace history for past food discussions |
| **MCP Server Integration** | SafeBite connects to a Gmail MCP server as an MCP client to send weekly digests |

---

## Tech Stack

- **Bolt for Python**: Slack app framework, Socket Mode
- **Gemini 2.5 Flash**: Food safety reasoning, vision (labels and photos), structured JSON output
- **SerpAPI**: Dual restaurant menu search, Google Maps nearby discovery
- **Slack Block Kit**: Colored verdict banners (green/yellow/red) for all responses
- **FastMCP**: Gmail MCP server for email digest delivery
- **Python**: smtplib, httpx, asyncio

---

## Project Structure

```
safebite/
├── app.py                      # Bolt app entry point, event routing
├── manifest.json               # App scopes, slash commands, assistant config
├── handlers/
│   ├── app_home.py             # App Home tab and quick action modals
│   ├── assistant.py            # Slack AI Assistant framework handler
│   ├── food_query.py           # Direct food safety queries
│   ├── onboarding.py           # User profile setup with checkboxes
│   ├── photo_handler.py        # Label and food photo analysis
│   ├── restaurant_scan.py      # Live menu scanning via SerpAPI
│   ├── silent_guardian.py      # Channel monitor, menu scan, nearby finder
│   └── weekly_digest.py        # Weekly digest via Gmail MCP
├── mcp_server/
│   └── gmail_server.py         # FastMCP Gmail server (send_email tool)
├── utils/
│   ├── ai_client.py            # Gemini 2.5 Flash client
│   ├── block_builder.py        # Block Kit message builder
│   ├── food_detector.py        # NLP food mention detection
│   ├── nearby_restaurants.py   # Google Maps nearby search with AI geocoding
│   └── slack_search.py         # Slack RTS API wrapper
└── db/
    └── user_profiles.py        # User profile storage (private, local JSON)
```

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js (for pptxgenjs, optional)
- Slack CLI installed and authenticated
- Slack Developer Program account with sandbox provisioned

### 1. Clone and install

```bash
git clone https://github.com/syedzubeen/safebite.git
cd safebite
python -m venv .venv
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file:

```
GEMINI_API_KEY=your-gemini-api-key
SERPAPI_KEY=your-serpapi-key
GMAIL_ADDRESS=your-gmail@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password
DEMO_MODE=false
```

> Set `DEMO_MODE=true` to receive guardian alerts as the message sender (for testing).

### 3. Run

```bash
slack run
```

The Slack CLI injects `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` automatically.

---

## Indian Cuisine Depth

SafeBite has explicit knowledge of hidden gluten risks in Indian cuisine that most tools miss:

- **Hing (asafoetida)**: almost always contains wheat flour as anti-caking agent
- **Nihari**: uses maida as a standard thickening agent
- **Birista** (fried onions in biryani): often dusted with flour before frying
- **Shami and seekh kebab**: use flour-based binders as a standard recipe step
- **Korma**: gravies can use wheat flour alongside nut-paste base

---

## Privacy by Design

The user's dietary condition is never mentioned publicly. No channel replies, no public alerts, no announcements. SafeBite operates silently: a private DM is the only interaction the at-risk user sees.

---

## License

[MIT](LICENSE). Free to use, fork, and build on. If SafeBite helps someone with celiac disease eat safely at a team lunch, that is enough.

---

*Built for the Slack Agent Builder Challenge 2026: Agent for Good track.*
*For people with celiac disease navigating the same invisible challenge every day.*
