## Inspiration

I was diagnosed with celiac disease when I was 3 years old. What followed was two decades of learning the hard way — birthday parties with no cake, school canteens with no options, and restaurants where I had to quietly interrogate the staff before anyone else at the table noticed.

By the time I reached my professional life, I had made peace with most of it. But one thing never got easier: the Slack message that says _"team lunch at Karim's, who's in?"_ Every time, the same impossible choice — stay quiet and gamble, or announce a medical condition I never wanted to define me at work.

I built SafeBite because that choice shouldn't exist. And because I was the only person who could build it right — with 22 years of knowing that hing contains wheat, that nihari uses maida as a thickener, that biryani can be contaminated by birista. Knowledge most apps simply don't have.

---

## What it does

SafeBite is a silent food safety guardian for people with celiac disease, living inside Slack.

### Silent Guardian
Monitors Slack channels for food mentions. When a colleague posts _"team lunch at Koji's Ramen, who's in?"_ — SafeBite detects it, scans the live menu, and privately DMs the at-risk user with:
- Safe dishes at that restaurant
- What to avoid and why
- A practical tip for talking to staff
- If nothing is safe, 4-5 nearby gluten-friendly alternatives with ratings and Google Maps links

No one in the channel knows it happened. The user's condition stays private.

### Direct Food Query
Users ask SafeBite anything in the Chat panel — _"is biryani safe?"_, _"can I eat nihari?"_, _"what about rajma chawal?"_ SafeBite searches the Slack workspace for past team discussions about that food using the **Real-Time Search API**, then returns a personalised verdict with a colored Block Kit response.

### Restaurant Scanner
`/safebite scan Karim's Delhi` fetches the live menu via two complementary searches and returns a structured safety report — safe dishes, dishes to avoid, and cuisine-specific pro tips.

### Ingredient Label Scanner
Upload a photo of any packaged food label. Gemini Vision reads every ingredient, flags hidden gluten sources like **hing**, **maida**, **suji**, **barley malt**, and **modified starch**, and returns a verdict with a confidence score (High / Medium / Low).

### Food Photo Analysis
Upload a photo of any dish. SafeBite identifies it, assesses safety, and explains the specific risks — including Indian cuisine knowledge most tools miss entirely.

### Weekly Digest via Gmail
A personalised weekly digest sent to the user's email inbox via a **Gmail MCP server** that SafeBite connects to as an MCP client. Covers hidden gluten risks, an Indian cuisine spotlight, a safe swap of the week, and practical tips.

### App Home Dashboard
A dedicated Home tab showing the user's profile, protection status, and quick action buttons for every SafeBite feature.

---

## How we built it

**Slack AI capabilities**
Built on Slack's native `Assistant` framework using Bolt for Python. SafeBite appears as a first-class agent in the assistant panel with suggested prompts, Chat/History tabs, and a proper App Home dashboard.

**Real-Time Search API**
SafeBite calls `assistant.search.context` to search the workspace for past food discussions. The `action_token` is retrieved from `payload.get("assistant_thread", {}).get("action_token")` — a nested location not documented in the official docs.

**MCP server integration**
SafeBite connects to a Gmail MCP server as an MCP client to send weekly digests to users' email inboxes. SafeBite is the client. Gmail is the external tool. The Slack agent orchestrates an action outside Slack through the MCP protocol.

**Gemini 2.5 Flash**
Handles food safety reasoning, vision for label and photo analysis, AI-powered location extraction for geocoding, and structured JSON output that feeds directly into Block Kit responses.

**SerpAPI**
Powers two-search restaurant menu scanning (general menu + targeted gluten-safe items) and Google Maps nearby restaurant discovery with AI geocoding.

**Block Kit**
All responses use colored verdict banners via Slack's attachment API:
- `#2EB67D` for Safe
- `#ECB22E` for Use Caution
- `#E01E5A` for Unsafe

---

## Challenges we ran into

- **Windows + Slack CLI:** The CLI on Windows runs hooks through PowerShell, which treats single-quoted strings as literals. Fixed by defining all hooks with `cmd /c` prefix.

- **Gemini JSON wrapping:** Gemini wraps JSON in markdown code blocks even when explicitly told not to. Fixed by extracting JSON robustly using `re.search(r'\{.*\}', response, re.DOTALL)`.

- **RTS action_token location:** The token needed for `assistant.search.context` is nested inside `payload.get("assistant_thread", {}).get("action_token")` — not in the top-level payload. Took significant debugging to find.

- **Incomplete menu data:** A single search for "Karim's Delhi menu" returned only their roll section, causing a false "nothing safe" verdict. Fixed with a dual-search approach — general menu + targeted search for rice dishes and grilled meats.

- **SerpAPI geocoding:** Searching "Belgian Waffle restaurant" returned results from random US cities. Fixed with a Gemini-powered location extractor that converts the full message context into a clean geocoding query.

- **Assistant middleware:** Slack's Assistant framework intercepts all DM messages before the regular handler. Required consolidating all routing through the `user_message` handler.

---

## Accomplishments that we're proud of

- The **Silent Guardian** working end-to-end — channel message to live menu scan to private DM with safe dishes and nearby alternatives, completely invisible to the rest of the team.

- **Indian cuisine depth** that no other tool has — catching hing as a gluten risk, nihari's maida thickener, birista cross-contamination in biryani, and kebab binders.

- The **Gmail MCP integration** — SafeBite as a genuine MCP client calling an external MCP server to orchestrate an action outside Slack.

- Using all **three hackathon technologies** meaningfully, not as checkboxes.

---

## What we learned

The most important design decision wasn't technical — it was the **privacy-first constraint**. The user's condition is never mentioned publicly. This single constraint shaped every feature and every interaction.

Generic food safety tools fail Indian cuisine users not because of lack of data, but because nobody has explicitly encoded the hidden risks specific to Indian cooking. The gap isn't artificial intelligence — it's lived experience.

MCP's real value isn't replacing APIs. It's standardising how agents discover and use tools at runtime. The Gmail integration would have been a direct API call without MCP. With MCP, it becomes a composable tool any agent can call.

---

## What's next for SafeBite

- **ICMR-NIN Indian food database:** A curated dataset of 500+ Indian dishes with ground-truth gluten status, replacing inferred knowledge with verified nutritional science.

- **Zomato/Swiggy link detection:** When someone shares a food delivery link in a channel, SafeBite scans that specific restaurant's actual online menu rather than searching Google.

- **Expanding conditions:** The Silent Guardian architecture extends to nut allergies, diabetes, and lactose intolerance. The privacy-first model is condition-agnostic.

- **Slack Marketplace distribution:** SafeBite as an installable app for any workspace, with admin channel controls and anonymised aggregate safety statistics.

For the 3-year-old version of me who couldn't read ingredient labels yet, and for everyone else navigating the same invisible challenge every day — this one's for you.
