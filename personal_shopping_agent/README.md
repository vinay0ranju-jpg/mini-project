# Personal Shopping Agent – AI-Powered Smart Shopping and Price Comparison System

An intelligent, full-stack Python application that compares product prices across multiple major e-commerce platforms (Amazon India, Flipkart, Croma, Reliance Digital), summarizes authentic customer reviews using NLP/LLMs, and generates smart recommendations using a multi-criteria scoring algorithm.

---

## 1. Abstract

Finding the best online deals usually forces shoppers to juggle dozens of browser tabs across disparate platforms, compare confusing variant names, and read through hundreds of conflicting customer reviews. The **Personal Shopping Agent** solves this by automating multi-store product retrieval, normalizing variants (RAM, storage, models), calculating net savings, distilling genuine customer sentiment, and ranking products using a transparent mathematical scoring model combined with AI justifications.

---

## 2. Problem Statement

1. **Price Fragmentation:** The same gadget or apparel item is frequently priced differently across Amazon, Flipkart, Croma, and Reliance Digital due to dynamic seller pricing and flash sales.
2. **Review Overload:** Products accumulate thousands of user reviews, making it tedious for buyers to distinguish recurrent defects (e.g., heating, battery drainage) from superficial comments.
3. **Variant Confusion:** Different storage sizes (128GB vs 256GB) or processor generations (M2 vs M3) are often confused by basic search bars, misleading consumers on the true lowest price.
4. **Opaque Recommendations:** E-commerce sponsored ads prioritize promoted items over consumer value.

---

## 3. Project Objectives

- Provide a single unified search console with customizable budget, category, store, and rating filters.
- Ethically retrieve live or demonstration product data across Amazon India, Flipkart, Croma, and Reliance Digital.
- Accurately match equivalent variants and identify the lowest verified price.
- Provide side-by-side specification matrices and historical price observation charts.
- Analyze authentic customer reviews using Google Gemini LLM with a reliable deterministic local fallback.
- Recommend winners for **Lowest Price**, **Best Rated**, and **Best Overall** using transparent criteria.
- Persist product catalog records, price history trends, and user search history in a lightweight SQLite database.

---

## 4. Scope

- **Target Audience:** College students, budget shoppers, electronic buyers, and everyday consumers comparing smartphones, laptops, audio gear, appliances, and footwear.
- **Coverage:** Multi-platform product lookup across four major Indian retail platforms with built-in academic demonstration datasets.

---

## 5. Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons, Chart.js, Jinja2 Templates |
| **Backend** | Python 3, Flask Application Factory, WSGI |
| **Database** | SQLite3, SQLAlchemy ORM |
| **Data Retrieval** | Requests, BeautifulSoup4, User-Agent rotation, ethical error handling |
| **AI / NLP** | Google Gemini LLM API (SDK & REST), Sandboxed Prompting, Rule-Based Deterministic NLP |
| **Testing** | Pytest, In-Memory SQLite Isolation |

---

## 6. System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    Web Browser (Client)                     │
│        Bootstrap 5 UI + Jinja2 Templates + Chart.js         │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP Requests (GET / POST)
┌──────────────────────────────▼──────────────────────────────┐
│                  Flask Application (entry.py)               │
│               Routes, Validation & Controllers              │
└──────┬───────────────┬───────────────┬───────────────┬──────┘
       │               │               │               │
┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│   Search    │ │ Comparison  │ │   Review    │ │Recommender  │
│   Service   │ │   Service   │ │   Service   │ │   Service   │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │               │
┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│  Scrapers   │ │   Product   │ │ReviewAnalyzer│ │ Deterministic│
│(Amazon/FK/  │ │   Matcher   │ │ (Gemini LLM /│ │   Scoring    │
│Croma/Rel.)  │ │(Equivalence)│ │Local Rule NLP│ │  Engine    │
└──────┬──────┘ └─────────────┘ └─────────────┘ └─────────────┘
       │
┌──────▼──────────────────────────────────────────────────────┐
│             SQLite Database (instance/shopping.db)          │
│   Products | PriceHistory | SearchHistory | Recommendations │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Project Folder Structure

```text
personal_shopping_agent/
│
├── entry.py                # Main Flask application entry point
├── config.py               # Environment and app configuration classes
├── requirements.txt        # Production dependencies
├── .env.example            # Sample environment variables
├── .env                    # Active local environment variables
├── .gitignore              # Git ignored files and virtual environments
├── README.md               # Complete project documentation
│
├── scraper/                # E-commerce retrieval modules
│   ├── __init__.py
│   ├── base_scraper.py     # Base abstract class with timeout & normalization
│   ├── amazon.py           # Amazon India scraper & demonstration feed
│   ├── flipkart.py         # Flipkart scraper & demonstration feed
│   ├── croma.py            # Croma scraper & demonstration feed
│   └── reliance.py         # Reliance Digital scraper & demonstration feed
│
├── services/               # Core business logic services
│   ├── __init__.py
│   ├── product_service.py  # Multi-source coordination & catalog persistence
│   ├── search_service.py   # Query filtering, sorting & search logging
│   ├── comparison_service.py # Cross-store price diffs & specs matrix
│   ├── review_service.py   # Review retrieval & sentiment caching
│   └── recommendation_service.py # Scoring execution & recommendation history
│
├── ai/                     # AI & NLP intelligence layer
│   ├── __init__.py
│   ├── llm_client.py       # Google Gemini SDK & REST client with sandboxing
│   ├── review_analyzer.py  # Review sentiment, pros/cons, & aspect summarizer
│   └── recommender.py      # 5-factor scoring engine & grounded explanations
│
├── database/               # Database management
│   ├── __init__.py
│   ├── db.py               # Shared SQLAlchemy instance
│   ├── models.py           # Product, PriceHistory, SearchHistory, ReviewAnalysis
│   └── init_db.py          # Auto-table creation & seed catalog initialization
│
├── utils/                  # Helper utilities
│   ├── __init__.py
│   ├── validators.py       # Search & price input validation
│   ├── price_utils.py      # INR currency formatting & discount math
│   ├── product_matcher.py  # Variant equivalence & specs conflict detector
│   └── helpers.py          # Star ratings, datetime & badge styling
│
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Layout, responsive navbar, floating compare tray
│   ├── index.html          # Hero section, search console, quick category filters
│   ├── products.html       # Responsive product grid, lowest price badges
│   ├── compare.html        # Side-by-side comparison table & savings banner
│   ├── details.html        # Specs, Chart.js price trend, AI review analysis
│   ├── recommendations.html# Winner cards, score breakdown, & rankings table
│   ├── history.html        # Search history log & one-click repeat actions
│   ├── about.html          # Ethical scraping, architecture & formulas
│   └── error.html          # Friendly 404/500 error display
│
├── static/                 # Static assets
│   ├── css/style.css       # Custom modern CSS styling
│   ├── js/script.js        # Form validation, reset & loading spinner
│   ├── js/comparison.js    # Interactive checkbox comparison tray manager
│   └── images/
│       └── placeholder.png # Fallback product image
│
├── instance/
│   └── shopping.db         # SQLite database file (created automatically)
│
└── tests/                  # Automated pytest test suite
    ├── __init__.py
    ├── test_entry.py       # Flask route & HTTP endpoint integration tests
    ├── test_database.py    # Database models, CRUD, and cascades
    ├── test_search.py      # Filtering, sorting, and lowest-price logic
    ├── test_comparison.py  # Multi-store price comparison & specs alignment
    ├── test_recommendation.py # Mathematical scoring & weight redistribution
    └── test_reviews.py     # AI review sentiment & local fallback NLP
```

---

## 8. Installation Steps

### Prerequisites
- Python 3.10+ installed
- Git installed (optional)

### 1. Clone or Navigate to Project Directory
```bash
cd personal_shopping_agent
```

### 2. Create and Activate Virtual Environment
**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 9. Environment Configuration

Copy `.env.example` to `.env` (already pre-configured for instant execution):
```bash
cp .env.example .env
```

Key environment variables in `.env`:
```ini
FLASK_SECRET_KEY=dev-secret-shopping-agent-key-2025
LLM_PROVIDER=gemini
LLM_API_KEY=YOUR_GEMINI_API_KEY_HERE   # (Optional - deterministic fallback works automatically if blank!)
LLM_MODEL=gemini-1.5-flash
DATABASE_URL=sqlite:///shopping.db
USE_SAMPLE_DATA=true
REQUEST_TIMEOUT=6
```

> **Note on AI Keys:** The application is built to run 100% out of the box without any paid API key! If `LLM_API_KEY` is not provided, the system seamlessly uses its built-in rule-based deterministic NLP analyzer and mathematical explanation engine.

---

## 10. Database Setup

The database tables and baseline demonstration products are created **automatically** the first time the application runs via `init_database(app)`. No manual migration commands are required!

---

## 11. Running the Application

Start the Flask development server:
```bash
python entry.py
```

Open your web browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 12. Running Automated Tests

Run the full pytest test suite across all 6 test modules:
```bash
pytest -v
```

All tests execute in an isolated in-memory SQLite database without making external network calls.

---

## 13. Recommendation Scoring Algorithm

The Recommendation Engine calculates a transparent score on a scale of 0 to 100 using five normalized components:

$$\text{Score} = (0.40 \times \text{PriceScore}) + (0.25 \times \text{RatingScore}) + (0.15 \times \text{ReviewVolume}) + (0.10 \times \text{Sentiment}) + (0.10 \times \text{Specs})$$

### Dynamic Weight Redistribution
If sentiment or technical specifications are unavailable for a specific product, their weights are proportionally redistributed across the remaining active metrics. Products are never penalized for missing optional data.

---

## 14. Ethical Scraping & Responsible Data Notice

- Respects website terms of service and does not bypass CAPTCHAs, bot verifications, or login walls.
- When an anti-bot challenge is encountered, the module logs the event cleanly and switches to verified demonstration data without interrupting user workflows.
- Applies strict request timeouts to prevent application hanging.

---

## 15. College Demonstration Checklist

1. **Homepage:** Search for `"iPhone 15"` or click the popular badge.
2. **Product Grid:** Observe store badges (Amazon, Flipkart, Croma, Reliance Digital) and the **Lowest Price!** badge on Flipkart (₹68,999).
3. **Filter Panel:** Filter by category `"Mobile phones"` and set minimum rating to `4.5★`.
4. **Compare Mode:** Select checkboxes on 2 or more products and click **Compare Now** in the floating tray.
5. **Product Details:** Open Apple iPhone 15 details to inspect technical specifications, the interactive Chart.js price trend chart, and the AI Customer Review Intelligence box.
6. **AI Recommendations:** Click the **Recommendations** link in the navbar to view the Lowest Price Champion, Best Rated by Users, and Best Overall Value cards with score breakdowns.
7. **Search History:** Visit **Search History** to review logged queries and click **Repeat** to re-run any search.
