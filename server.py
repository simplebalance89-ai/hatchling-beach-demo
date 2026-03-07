"""
Hatchling Beach — Premium DIY Coastal Centerpiece Kits
Business Demo App: AI Assistant + Product Catalog + Investor Dashboard
Built for Dave Wallis. Powered by Alisa.
"""
import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

load_dotenv()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://hatchling-beach-demo.onrender.com",
        "http://localhost:10000",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def no_cache_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Surrogate-Control"] = "no-store"
    return response


# ============================================================
# AZURE OPENAI CONFIG
# ============================================================

AZURE_ENDPOINT = os.environ.get("AZURE_ENDPOINT", "pwgcerp-9302-resource.openai.azure.com")
AZURE_API_KEY = os.environ.get("AZURE_API_KEY", "")
CHAT_DEPLOYMENT = os.environ.get("AZURE_CHAT_DEPLOYMENT", "gpt-4o")
API_VERSION = "2024-12-01-preview"

AZURE_CHAT_URL = f"https://{AZURE_ENDPOINT}/openai/deployments/{CHAT_DEPLOYMENT}/chat/completions?api-version={API_VERSION}"

# Chat history per session (in-memory, resets on restart)
chat_sessions: dict[str, list] = {}


# ============================================================
# SYSTEM PROMPT — HATCHLING BEACH BUSINESS MASTERMIND
# ============================================================

SYSTEM_PROMPT = """You are the Hatchling Beach Business Mastermind — an expert AI assistant with complete knowledge of the Hatchling Beach business. You serve as Dave Wallis's strategic advisor, investor pitch partner, and operational brain.

You know EVERYTHING about this business. When asked, you answer with specifics — real numbers, real vendors, real strategy. You are not generic. You are Hatchling Beach's AI.

============================
COMPANY OVERVIEW
============================
- **Company:** Hatchling Beach
- **Tagline:** "Where Every Turtle Has a Story"
- **Founder:** Dave Wallis — West Palm Beach, FL — 954.275.9494
- **CEO / Strategy:** Peter
- **Domain:** HatchlingBeach.com
- **Instagram:** @hatchlingbeach
- **Status:** Pre-Launch
- **Target Launch:** Spring 2026
- **Startup Capital:** $10,000
- **Entity type:** Small business (bootstrapped)
- **Brand Colors:** Teal (#008B8B), Gold (#C5A55A), Sand (#FAF0E6)
- **Brand Fonts:** Playfair Display (headers), Lato (body)

============================
PRODUCT LINE — 4 COLLECTIONS, 12 SKUs
============================

**1. CLASSIC COASTAL COLLECTION** — Signature line. Pre-selected premium components, ready to arrange.

| Product | SKU | Price | COGS | Margin | Bowl | Turtles | Sand | Accents |
|---------|-----|-------|------|--------|------|---------|------|---------|
| Mini Kit | HB-MINI-001 | $69.00 | $24.35 | 65% | 6" bubble bowl | 3 premium | 4 oz | 1 starfish, 1 sand dollar |
| Standard Kit | HB-STD-001 | $129.00 | $48.00 | 63% | 8" scalloped bowl | 6 premium (mixed poses) | 8 oz | 1 starfish, 1 sand dollar, shell mix |
| Deluxe Kit | HB-DLX-001 | $199.00 | $67.70 | 66% | 10" premium bowl | 8 premium (mixed poses) | 16 oz | 2 starfish, 1 sand dollar, premium shells, driftwood |

**2. PAINT YOUR OWN COLLECTION** — Unfinished turtles + paint supplies. DIY creativity meets coastal decor.

| Product | SKU | Price | COGS | Margin | Includes |
|---------|-----|-------|------|--------|----------|
| PYO Mini | HB-PYO-MINI | $49.00 | ~$17 | ~65% | 6" bowl, 3 unpainted turtles, 6-color paint set, brush, sand |
| PYO Standard | HB-PYO-STD | $89.00 | ~$32 | ~64% | 8" bowl, 6 unpainted turtles, 8-color paint set, 2 brushes, sand, accents |
| PYO Deluxe | HB-PYO-DLX | $129.00 | ~$45 | ~65% | 10" bowl, 8 unpainted turtles, 12-color paint set, 3 brushes, sand, accents, sealant |

**3. RAW BAR COLLECTION** — Premium components sold individually. Build your own from scratch.

| Product | SKU | Price | COGS | Margin | Includes |
|---------|-----|-------|------|--------|----------|
| Raw Bar Kit | HB-RAW-001 | $99.00 | ~$35 | ~65% | Mix-and-match components: bowls, turtles, sand, shells, accents sold a la carte |
| Refill Pack | HB-RAW-REF | $39.00 | ~$14 | ~64% | Sand, shells, accent refills for existing kits |

**4. DESERT BONES COLLECTION** — Southwest/desert variant. Same concept, different biome.

| Product | SKU | Price | COGS | Margin | Includes |
|---------|-----|-------|------|--------|----------|
| Desert Bones Kit | HB-DSB-001 | $79.00 | ~$28 | ~65% | Desert bowl, skeleton/fossil turtle figurines, desert sand, cacti accents, stones |
| Desert Deluxe | HB-DSB-DLX | $139.00 | ~$48 | ~65% | Larger bowl, more figurines, premium desert accents, driftwood |

============================
STANDARD KIT BOM BREAKDOWN (HB-STD-001)
============================
| Component | Qty | Unit Cost | Extended | Vendor |
|-----------|-----|-----------|----------|--------|
| 8" scalloped glass bubble bowl | 1 | $9.20 | $9.20 | VaseMarket |
| Premium hatching turtle figurines | 6 | $5.50 | $33.00 | CA Seashell / Amazon |
| Fine craft sand (8 oz bag) | 1 | $1.00 | $1.00 | ACTIVA Products |
| Natural mini starfish | 1 | $0.25 | $0.25 | Bulk suppliers |
| Natural sand dollar | 1 | $0.25 | $0.25 | Bulk suppliers |
| Mixed shell accents | 1 | $0.80 | $0.80 | Bulk suppliers |
| Gift box + tissue | 1 | $2.00 | $2.00 | Uline / Amazon |
| Instruction card | 1 | $0.25 | $0.25 | Vistaprint |
| Branded sticker | 1 | $0.25 | $0.25 | Vistaprint |
| **TOTAL COGS** | | | **$48.00** | |
| **Retail Price** | | | **$129.00** | |
| **Gross Profit** | | | **$81.00** | |
| **Gross Margin** | | | **63%** | |

============================
VENDOR DIRECTORY
============================
1. **VaseMarket** — Glass bowls (bubble, scalloped). Low MOQ. Primary bowl supplier. Quality premium glass.
2. **CA Seashell** — Premium turtle figurines. Medium MOQ. Hand-painted options available. Key differentiator supplier.
3. **Amazon** — Turtle figurines, shells, supplies. Low MOQ. Backup / small orders / sampling.
4. **ACTIVA Products** — Fine craft sand. Low MOQ. Quality fine sand, color consistency.
5. **Bulk shell suppliers** — Starfish, sand dollars, shell mix. Medium MOQ. Multiple sources for redundancy.
6. **Vistaprint** — Business cards, instruction cards, branded stickers. Low MOQ. Print on demand.
7. **Uline** — Gift boxes, shipping supplies, packaging materials. Medium MOQ. Bulk packaging.

Sourcing notes:
- Turtle figurines are the KEY differentiator — quality and pose variety are critical.
- Bowls must be premium glass. No cheap substitutes. Scalloped edge is the signature.
- Sand must be fine craft sand, NOT play sand. Color consistency matters.
- All packaging carries the conservation message (Loggerhead Marine Life Center).

============================
MARKET DATA
============================
- **US Home Decor Market:** $185 billion (growing ~5% annually)
- **DIY/Craft Market:** $44 billion (post-COVID sustained growth)
- **Coastal Decor Niche:** $2.8 billion+ segment within home decor
- **DIY Kit Market:** Exploding — subscription boxes, craft kits, paint-by-number, all growing 15-20% YoY
- **Target Demographics:**
  - Primary: Women 25-55, homeowners, coastal lifestyle, gift buyers
  - Secondary: DIY crafters, event planners, home stagers
  - Tertiary: Corporate gifting, Airbnb/rental styling

**Competitive Landscape:**
- **No direct competitor** offers a premium DIY sea turtle centerpiece kit. This is a blue ocean.
- Adjacent competitors: generic coastal decor (HomeGoods, Pottery Barn), DIY craft kits (non-coastal), mass-market figurines
- Hatchling Beach differentiators: premium quality, conservation mission, DIY experience, unique concept, gift-ready packaging
- Closest analog: paint-and-sip meets home decor — experiential product, not just a thing

============================
CONSERVATION MISSION
============================
- **Partner:** Loggerhead Marine Life Center — Juno Beach, FL
- One of the largest sea turtle rehabilitation facilities in the world
- Partnership is REAL and established — not aspirational
- Conservation messaging on all packaging, marketing, and website
- Portion of proceeds supports turtle conservation
- This isn't greenwashing — Dave lives in South Florida, this is local and genuine
- The conservation angle drives purchase decisions (especially with target demo)
- Potential for co-branded events, content, and educational tie-ins

============================
FINANCIAL PROJECTIONS
============================

**Startup Capital Allocation ($10,000):**
| Category | Amount |
|----------|--------|
| Initial Inventory (50 Standard kits) | $4,500 |
| Packaging & Branding | $1,500 |
| Shopify + Tools | $500 |
| Marketing & Ads | $2,000 |
| Shipping Supplies | $500 |
| Reserve | $1,000 |

**Break-Even Analysis:**
- Break-even point: 78 Standard Kits sold
- At $129/kit with $81 gross profit, 78 kits = ~$6,318 gross profit (covers startup costs minus inventory already purchased)

**Year 1 — Conservative Scenario:**
- Units: 500
- Revenue: $65,000
- COGS: ~$24,000
- Gross Profit: ~$41,000
- Gross Margin: 63%

**Year 1 — Optimistic Scenario:**
- Units: 800
- Revenue: $115,000
- COGS: ~$39,000
- Gross Profit: ~$76,000
- Gross Margin: 66%

**Unit Economics Summary:**
| Kit | Price | COGS | Gross Profit | Margin |
|-----|-------|------|-------------|--------|
| Mini ($69) | $69.00 | $24.35 | $44.65 | 65% |
| Standard ($129) | $129.00 | $48.00 | $81.00 | 63% |
| Deluxe ($199) | $199.00 | $67.70 | $131.30 | 66% |

**Average Order Value Target:** $129 (Standard Kit is the anchor)

============================
LAUNCH PLAN — SPRING 2026
============================

**Phase 1 — Pre-Launch (Now through March 2026):**
- Finalize Shopify store setup
- Place first inventory order (50 Standard kits)
- Build email list from Dave's existing network
- Social media content calendar (Instagram, TikTok)
- Finalize all packaging and unboxing experience
- Professional product photography
- Influencer seeding (5-10 micro-influencers in coastal/decor niche)

**Phase 2 — Soft Launch (April 2026):**
- Launch Shopify store
- Email blast to Dave's network (friends, family, past clients)
- Instagram launch campaign
- First pop-up market event
- Local press / blog outreach (South Florida)

**Phase 3 — Growth (May-December 2026):**
- Facebook/Instagram ads (testing with $500-1000/month)
- Etsy store launch (additional channel)
- Amazon Handmade exploration
- Holiday season push (Q4 is critical for gift products)
- Corporate gifting program launch
- Event/party kit bundles

**Sales Channels:**
- Shopify Store (primary) — not yet set up
- Etsy — not yet set up
- Amazon Handmade — not yet set up
- Instagram Shop — not yet set up
- Local Markets / Pop-ups — planned Spring 2026
- Direct (Dave's network) — active, word of mouth
- Corporate gifting — planned

**Trade Shows (2026 targets):**
- Surf Expo — Orlando, FL (January / September)
- NY Now — New York (January / August)
- AmericasMart — Atlanta (January / July)
- Local craft fairs and artisan markets in South Florida

============================
TEAM
============================
- **Dave Wallis** — Founder. The face of the brand. Knows every customer, every vendor, every shell. Passion project turned real business. 954.275.9494.
- **Peter** — CEO / Strategy. Builds the systems, runs the tech, designs the AI tools, investor materials, and go-to-market strategy.

============================
ASSETS COMPLETED
============================
- Professional logo
- Business cards (printed)
- Marketing flyer (printed)
- Pitch deck V4 (PDF + PPTX)
- Video pitch reel V3 (MP4)
- Storefront HTML (complete)
- AI-generated product images (10+)
- Dave's voice transcripts
- Image generation prompts
- Domain registered (HatchlingBeach.com)
- Social handles claimed (@hatchlingbeach)
- Conservation partnership established
- Business plan V2 complete
- BOM & vendor sourcing complete
- This AI demo app

============================
YOUR BEHAVIOR
============================
- You are confident, specific, and data-driven. You answer like you OWN this business.
- When asked about products, give exact prices, SKUs, margins, and BOM costs.
- When asked about market data, cite the specific numbers above.
- When asked about strategy, think like a founder — practical, scrappy, ROI-focused.
- When asked about conservation, speak genuinely — this is real, not marketing fluff.
- When asked about competitors, emphasize the blue ocean — nobody does THIS specific thing.
- Keep responses concise but complete. Business-appropriate tone. No fluff.
- If someone asks a question outside your knowledge, say so — don't make up data.
- You can help with: investor Q&A, product recommendations, pricing strategy, marketing ideas, vendor decisions, financial modeling, pitch practice.
- Format responses with markdown when helpful (bold, lists, tables).
- Be enthusiastic about the business without being salesy. This is a real company with real potential."""


# ============================================================
# PRODUCT CATALOG DATA
# ============================================================

PRODUCTS = [
    # Classic Coastal Collection
    {
        "id": "HB-MINI-001",
        "name": "Classic Mini Kit",
        "collection": "Classic Coastal",
        "price": 69.00,
        "cogs": 24.35,
        "margin": 65,
        "gross_profit": 44.65,
        "description": "Compact coastal elegance. Perfect for shelves, desks, and small spaces.",
        "includes": {
            "bowl": '6" bubble bowl',
            "turtles": "3 premium figurines",
            "sand": "4 oz fine craft sand",
            "accents": "1 starfish, 1 sand dollar",
            "packaging": "Gift box, tissue, instruction card, branded sticker",
        },
        "bom": [
            {"component": '6" glass bubble bowl', "qty": 1, "unit_cost": 6.50, "vendor": "VaseMarket"},
            {"component": "Premium hatching turtle figurines", "qty": 3, "unit_cost": 5.50, "vendor": "CA Seashell / Amazon"},
            {"component": "Fine craft sand (4 oz)", "qty": 1, "unit_cost": 0.60, "vendor": "ACTIVA Products"},
            {"component": "Natural mini starfish", "qty": 1, "unit_cost": 0.25, "vendor": "Bulk suppliers"},
            {"component": "Natural sand dollar", "qty": 1, "unit_cost": 0.25, "vendor": "Bulk suppliers"},
            {"component": "Gift box + tissue", "qty": 1, "unit_cost": 1.50, "vendor": "Uline / Amazon"},
            {"component": "Instruction card", "qty": 1, "unit_cost": 0.25, "vendor": "Vistaprint"},
            {"component": "Branded sticker", "qty": 1, "unit_cost": 0.25, "vendor": "Vistaprint"},
        ],
    },
    {
        "id": "HB-STD-001",
        "name": "Classic Standard Kit",
        "collection": "Classic Coastal",
        "price": 129.00,
        "cogs": 48.00,
        "margin": 63,
        "gross_profit": 81.00,
        "description": "The signature Hatchling Beach experience. Our best seller and anchor product.",
        "includes": {
            "bowl": '8" scalloped bowl',
            "turtles": "6 premium figurines (mixed poses)",
            "sand": "8 oz fine craft sand",
            "accents": "1 starfish, 1 sand dollar, shell mix",
            "packaging": "Gift box, tissue, instruction card, branded sticker",
        },
        "bom": [
            {"component": '8" scalloped glass bubble bowl', "qty": 1, "unit_cost": 9.20, "vendor": "VaseMarket"},
            {"component": "Premium hatching turtle figurines", "qty": 6, "unit_cost": 5.50, "vendor": "CA Seashell / Amazon"},
            {"component": "Fine craft sand (8 oz)", "qty": 1, "unit_cost": 1.00, "vendor": "ACTIVA Products"},
            {"component": "Natural mini starfish", "qty": 1, "unit_cost": 0.25, "vendor": "Bulk suppliers"},
            {"component": "Natural sand dollar", "qty": 1, "unit_cost": 0.25, "vendor": "Bulk suppliers"},
            {"component": "Mixed shell accents", "qty": 1, "unit_cost": 0.80, "vendor": "Bulk suppliers"},
            {"component": "Gift box + tissue", "qty": 1, "unit_cost": 2.00, "vendor": "Uline / Amazon"},
            {"component": "Instruction card", "qty": 1, "unit_cost": 0.25, "vendor": "Vistaprint"},
            {"component": "Branded sticker", "qty": 1, "unit_cost": 0.25, "vendor": "Vistaprint"},
        ],
    },
    {
        "id": "HB-DLX-001",
        "name": "Classic Deluxe Kit",
        "collection": "Classic Coastal",
        "price": 199.00,
        "cogs": 67.70,
        "margin": 66,
        "gross_profit": 131.30,
        "description": "The ultimate coastal centerpiece. Premium everything. Statement piece.",
        "includes": {
            "bowl": '10" premium bowl',
            "turtles": "8 premium figurines (mixed poses)",
            "sand": "16 oz fine craft sand",
            "accents": "2 starfish, 1 sand dollar, premium shells, driftwood",
            "packaging": "Premium gift box, tissue, instruction card, branded sticker",
        },
        "bom": [
            {"component": '10" premium glass bowl', "qty": 1, "unit_cost": 14.00, "vendor": "VaseMarket"},
            {"component": "Premium hatching turtle figurines", "qty": 8, "unit_cost": 5.50, "vendor": "CA Seashell / Amazon"},
            {"component": "Fine craft sand (16 oz)", "qty": 1, "unit_cost": 1.75, "vendor": "ACTIVA Products"},
            {"component": "Natural mini starfish", "qty": 2, "unit_cost": 0.25, "vendor": "Bulk suppliers"},
            {"component": "Natural sand dollar", "qty": 1, "unit_cost": 0.25, "vendor": "Bulk suppliers"},
            {"component": "Premium shell mix", "qty": 1, "unit_cost": 1.50, "vendor": "Bulk suppliers"},
            {"component": "Driftwood piece", "qty": 1, "unit_cost": 1.20, "vendor": "Bulk suppliers"},
            {"component": "Premium gift box + tissue", "qty": 1, "unit_cost": 3.00, "vendor": "Uline / Amazon"},
            {"component": "Instruction card", "qty": 1, "unit_cost": 0.25, "vendor": "Vistaprint"},
            {"component": "Branded sticker", "qty": 1, "unit_cost": 0.25, "vendor": "Vistaprint"},
        ],
    },
    # Paint Your Own Collection
    {
        "id": "HB-PYO-MINI",
        "name": "Paint Your Own Mini",
        "collection": "Paint Your Own",
        "price": 49.00,
        "cogs": 17.00,
        "margin": 65,
        "gross_profit": 32.00,
        "description": "DIY creativity at its best. Paint your own turtles and build your scene.",
        "includes": {
            "bowl": '6" bowl',
            "turtles": "3 unpainted turtles",
            "paint": "6-color paint set + brush",
            "sand": "4 oz fine craft sand",
            "accents": "Basic accents",
            "packaging": "Gift box, instruction card",
        },
        "bom": [],
    },
    {
        "id": "HB-PYO-STD",
        "name": "Paint Your Own Standard",
        "collection": "Paint Your Own",
        "price": 89.00,
        "cogs": 32.00,
        "margin": 64,
        "gross_profit": 57.00,
        "description": "The full Paint Your Own experience. Great for date nights and family time.",
        "includes": {
            "bowl": '8" bowl',
            "turtles": "6 unpainted turtles",
            "paint": "8-color paint set + 2 brushes",
            "sand": "8 oz fine craft sand",
            "accents": "Shells and accents",
            "packaging": "Gift box, instruction card",
        },
        "bom": [],
    },
    {
        "id": "HB-PYO-DLX",
        "name": "Paint Your Own Deluxe",
        "collection": "Paint Your Own",
        "price": 129.00,
        "cogs": 45.00,
        "margin": 65,
        "gross_profit": 84.00,
        "description": "Premium DIY experience. Full paint set, sealant, and all the accents.",
        "includes": {
            "bowl": '10" bowl',
            "turtles": "8 unpainted turtles",
            "paint": "12-color paint set + 3 brushes + sealant",
            "sand": "16 oz fine craft sand",
            "accents": "Premium shells and accents",
            "packaging": "Premium gift box, instruction card",
        },
        "bom": [],
    },
    # Raw Bar Collection
    {
        "id": "HB-RAW-001",
        "name": "Raw Bar Kit",
        "collection": "Raw Bar",
        "price": 99.00,
        "cogs": 35.00,
        "margin": 65,
        "gross_profit": 64.00,
        "description": "Mix and match your own components. Choose your bowl, your turtles, your accents.",
        "includes": {
            "components": "Customizable selection of bowls, turtles, sand, shells, and accents",
            "packaging": "Gift box, instruction card",
        },
        "bom": [],
    },
    {
        "id": "HB-RAW-REF",
        "name": "Refill Pack",
        "collection": "Raw Bar",
        "price": 39.00,
        "cogs": 14.00,
        "margin": 64,
        "gross_profit": 25.00,
        "description": "Refresh your existing kit. New sand, new shells, new look.",
        "includes": {
            "components": "Sand, shells, accent refills for existing kits",
            "packaging": "Refill pouch",
        },
        "bom": [],
    },
    # Desert Bones Collection
    {
        "id": "HB-DSB-001",
        "name": "Desert Bones Kit",
        "collection": "Desert Bones",
        "price": 79.00,
        "cogs": 28.00,
        "margin": 65,
        "gross_profit": 51.00,
        "description": "Southwest desert variant. Same concept, different biome. Skeleton turtles meet desert landscape.",
        "includes": {
            "bowl": "Desert-style bowl",
            "turtles": "Skeleton/fossil turtle figurines",
            "sand": "Desert sand",
            "accents": "Cacti accents, stones",
            "packaging": "Gift box, instruction card",
        },
        "bom": [],
    },
    {
        "id": "HB-DSB-DLX",
        "name": "Desert Bones Deluxe",
        "collection": "Desert Bones",
        "price": 139.00,
        "cogs": 48.00,
        "margin": 65,
        "gross_profit": 91.00,
        "description": "The full desert experience. Larger bowl, more figurines, premium desert accents.",
        "includes": {
            "bowl": "Large desert bowl",
            "turtles": "Premium skeleton/fossil turtle figurines",
            "sand": "Desert sand (large)",
            "accents": "Premium cacti, stones, driftwood",
            "packaging": "Premium gift box, instruction card",
        },
        "bom": [],
    },
]


# ============================================================
# VENDOR DATA
# ============================================================

VENDORS = [
    {
        "name": "VaseMarket",
        "products": "Glass bowls (bubble, scalloped, premium)",
        "moq": "Low",
        "role": "Primary bowl supplier",
        "notes": "Premium quality glass. Scalloped edge is the Hatchling Beach signature. Reliable shipping.",
    },
    {
        "name": "CA Seashell",
        "products": "Premium turtle figurines",
        "moq": "Medium",
        "role": "Primary turtle supplier",
        "notes": "Hand-painted options available. Key differentiator for the product line. Quality and pose variety critical.",
    },
    {
        "name": "Amazon",
        "products": "Turtle figurines, shells, misc supplies",
        "moq": "Low (1+)",
        "role": "Backup / sampling",
        "notes": "Used for small orders, prototyping, and backup supply. Not primary for scale.",
    },
    {
        "name": "ACTIVA Products",
        "products": "Fine craft sand",
        "moq": "Low",
        "role": "Primary sand supplier",
        "notes": "Quality fine sand with color consistency. Must be craft-grade, not play sand.",
    },
    {
        "name": "Bulk Shell Suppliers",
        "products": "Starfish, sand dollars, shell mix, driftwood",
        "moq": "Medium",
        "role": "Natural accent components",
        "notes": "Multiple sources for redundancy. Seasonal availability varies. Quality inspection required.",
    },
    {
        "name": "Vistaprint",
        "products": "Business cards, instruction cards, branded stickers",
        "moq": "Low",
        "role": "Print materials",
        "notes": "Print on demand. Quick turnaround. Already have designs finalized.",
    },
    {
        "name": "Uline",
        "products": "Gift boxes, tissue paper, shipping supplies, packaging",
        "moq": "Medium",
        "role": "Packaging supplier",
        "notes": "Bulk packaging. Professional unboxing experience is part of the brand.",
    },
]


# ============================================================
# INVESTOR METRICS
# ============================================================

INVESTOR_DATA = {
    "market": {
        "home_decor": "$185 billion US market (growing ~5% annually)",
        "diy_craft": "$44 billion US market (post-COVID sustained growth, 15-20% YoY in kits)",
        "coastal_decor": "$2.8 billion+ niche within home decor",
        "competitive_position": "Blue ocean — no direct competitor offers premium DIY sea turtle centerpiece kits",
    },
    "unit_economics": [
        {"kit": "Mini", "price": 69.00, "cogs": 24.35, "gross_profit": 44.65, "margin": "65%"},
        {"kit": "Standard", "price": 129.00, "cogs": 48.00, "gross_profit": 81.00, "margin": "63%"},
        {"kit": "Deluxe", "price": 199.00, "cogs": 67.70, "gross_profit": 131.30, "margin": "66%"},
    ],
    "break_even": {
        "units": 78,
        "product": "Standard Kit",
        "calculation": "78 Standard Kits x $81 gross profit = ~$6,318 (covers startup costs minus inventory)",
    },
    "year_1_conservative": {
        "units": 500,
        "revenue": 65000,
        "cogs": 24000,
        "gross_profit": 41000,
        "gross_margin": "63%",
    },
    "year_1_optimistic": {
        "units": 800,
        "revenue": 115000,
        "cogs": 39000,
        "gross_profit": 76000,
        "gross_margin": "66%",
    },
    "startup_capital": {
        "total": 10000,
        "allocation": [
            {"category": "Initial Inventory (50 Standard kits)", "amount": 4500},
            {"category": "Packaging & Branding", "amount": 1500},
            {"category": "Shopify + Tools", "amount": 500},
            {"category": "Marketing & Ads", "amount": 2000},
            {"category": "Shipping Supplies", "amount": 500},
            {"category": "Reserve", "amount": 1000},
        ],
    },
    "avg_order_value": 129.00,
    "target_demographics": [
        "Women 25-55, homeowners, coastal lifestyle, gift buyers (primary)",
        "DIY crafters, event planners, home stagers (secondary)",
        "Corporate gifting, Airbnb/rental styling (tertiary)",
    ],
    "conservation_partner": "Loggerhead Marine Life Center — Juno Beach, FL",
}


# ============================================================
# LAUNCH TIMELINE
# ============================================================

LAUNCH_TIMELINE = {
    "target_launch": "Spring 2026",
    "phases": [
        {
            "phase": "Phase 1 — Pre-Launch",
            "timing": "Now through March 2026",
            "status": "In Progress",
            "milestones": [
                "Finalize Shopify store setup",
                "Place first inventory order (50 Standard kits)",
                "Build email list from Dave's existing network",
                "Social media content calendar (Instagram, TikTok)",
                "Finalize all packaging and unboxing experience",
                "Professional product photography",
                "Influencer seeding (5-10 micro-influencers in coastal/decor niche)",
            ],
        },
        {
            "phase": "Phase 2 — Soft Launch",
            "timing": "April 2026",
            "status": "Planned",
            "milestones": [
                "Launch Shopify store",
                "Email blast to Dave's network (friends, family, past clients)",
                "Instagram launch campaign",
                "First pop-up market event",
                "Local press / blog outreach (South Florida)",
            ],
        },
        {
            "phase": "Phase 3 — Growth",
            "timing": "May - December 2026",
            "status": "Planned",
            "milestones": [
                "Facebook/Instagram ads ($500-1000/month test budget)",
                "Etsy store launch (additional channel)",
                "Amazon Handmade exploration",
                "Holiday season push (Q4 — critical for gift products)",
                "Corporate gifting program launch",
                "Event/party kit bundles",
            ],
        },
    ],
    "sales_channels": [
        {"channel": "Shopify Store", "status": "Not set up", "priority": "Primary"},
        {"channel": "Etsy", "status": "Not set up", "priority": "Secondary"},
        {"channel": "Amazon Handmade", "status": "Not set up", "priority": "Exploratory"},
        {"channel": "Instagram Shop", "status": "Not set up", "priority": "Secondary"},
        {"channel": "Local Markets / Pop-ups", "status": "Planned Spring 2026", "priority": "High"},
        {"channel": "Direct (Dave's network)", "status": "Active — word of mouth", "priority": "Active"},
        {"channel": "Corporate Gifting", "status": "Planned", "priority": "Growth"},
    ],
    "trade_shows": [
        {"name": "Surf Expo", "location": "Orlando, FL", "timing": "January / September 2026"},
        {"name": "NY Now", "location": "New York, NY", "timing": "January / August 2026"},
        {"name": "AmericasMart", "location": "Atlanta, GA", "timing": "January / July 2026"},
        {"name": "Local Craft Fairs", "location": "South Florida", "timing": "Ongoing 2026"},
    ],
    "assets_completed": [
        "Professional logo",
        "Business cards (printed)",
        "Marketing flyer (printed)",
        "Pitch deck V4 (PDF + PPTX)",
        "Video pitch reel V3 (MP4)",
        "Storefront HTML (complete)",
        "AI-generated product images (10+)",
        "Domain registered (HatchlingBeach.com)",
        "Social handles claimed (@hatchlingbeach)",
        "Conservation partnership (Loggerhead Marine Life Center)",
        "Business plan V2 complete",
        "BOM & vendor sourcing complete",
        "AI demo app (this site)",
    ],
}


# ============================================================
# QUICK-START SUGGESTIONS
# ============================================================

QUICK_SUGGESTIONS = [
    "What products does Hatchling Beach offer?",
    "Break down the Standard Kit margins",
    "Who are the target customers?",
    "What makes this a blue ocean opportunity?",
    "Walk me through the launch plan",
    "What's the break-even analysis?",
]


# ============================================================
# CHAT COMPLETION
# ============================================================

async def chat_completion(session_id: str, user_message: str) -> str:
    """Send message to Azure OpenAI and get response."""
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    history = chat_sessions[session_id]
    history.append({"role": "user", "content": user_message})

    # Keep last 20 messages to avoid token overflow
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-20:]

    headers = {
        "api-key": AZURE_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(AZURE_CHAT_URL, json=payload, headers=headers, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                assistant_msg = data["choices"][0]["message"]["content"]
                history.append({"role": "assistant", "content": assistant_msg})
                return assistant_msg
            else:
                return f"Connection issue (status {response.status_code}). Try again."
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================================
# ROUTES
# ============================================================

@app.get("/health")
async def health():
    return JSONResponse({
        "status": "ok",
        "service": "hatchling-beach-demo",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/api/chat")
async def chat(request: Request):
    """AI Business Assistant — chat endpoint."""
    body = await request.json()
    user_msg = body.get("message", "")
    session_id = body.get("session_id", str(uuid.uuid4()))

    if not user_msg.strip():
        return JSONResponse({"error": "Empty message"}, status_code=400)

    response_text = await chat_completion(session_id, user_msg)

    return JSONResponse({
        "response": response_text,
        "session_id": session_id,
        "agent": {
            "name": "Hatchling Beach Mastermind",
            "icon": "turtle",
            "description": "AI Business Assistant — Products, Strategy, Financials, Launch Plan",
        },
        "suggestions": QUICK_SUGGESTIONS,
    })


@app.get("/api/products")
async def get_products():
    """Full product catalog with BOM breakdowns."""
    collections = {}
    for product in PRODUCTS:
        col = product["collection"]
        if col not in collections:
            collections[col] = []
        collections[col].append(product)

    return JSONResponse({
        "total_skus": len(PRODUCTS),
        "collections": list(collections.keys()),
        "products": PRODUCTS,
        "by_collection": collections,
    })


@app.get("/api/vendors")
async def get_vendors():
    """Vendor directory."""
    return JSONResponse({
        "total_vendors": len(VENDORS),
        "vendors": VENDORS,
    })


@app.get("/api/investor")
async def get_investor():
    """Investor metrics and financial projections."""
    return JSONResponse(INVESTOR_DATA)


@app.get("/api/launch")
async def get_launch():
    """Launch timeline, milestones, and trade shows."""
    return JSONResponse(LAUNCH_TIMELINE)



@app.post("/api/subscribe")
async def subscribe(request: Request):
    """Email signup — append to file-based lead list."""
    body = await request.json()
    email = body.get("email", "").strip().lower()
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return JSONResponse({"error": "Invalid email"}, status_code=400)

    leads_file = "leads.txt"
    # Check for duplicates
    existing = set()
    if os.path.exists(leads_file):
        with open(leads_file, "r") as f:
            existing = {line.strip().split(",")[0] for line in f if line.strip()}

    if email in existing:
        return JSONResponse({"status": "already_subscribed", "message": "You're already on the list!"})

    with open(leads_file, "a") as f:
        f.write(f"{email},{datetime.now(timezone.utc).isoformat()}\n")

    return JSONResponse({"status": "subscribed", "message": "Welcome to the nest! We'll be in touch."})


@app.get("/vision")
async def vision():
    return FileResponse("static/vision.html")


# ============================================================
# STATIC FILES — must be last
# ============================================================

app.mount("/static", StaticFiles(directory="static"), name="static")