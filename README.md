<div align="center">

# 🎬 CinePulse-Indic

### Cross-Linguistic Sentiment Mapping of Pan-Indian Cinema  
### using Multilingual Transformers

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Model](https://img.shields.io/badge/Model-XLM--RoBERTa-orange?logo=huggingface)](https://huggingface.co/cardiffnlp/twitter-xlm-roberta-base-sentiment)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

*Aspect-Based Sentiment Analysis across Hindi and Telugu communities — powered by XLM-RoBERTa + BART Zero-Shot NLI*

</div>

---

## 📌 Overview

CinePulse-Indic analyses YouTube and Reddit comments for Pan-Indian movies across multiple language communities and produces:

- **Global sentiment scores** (Positive / Negative / Neutral) per language
- **Aspect-Based Sentiment Analysis (ABSA)** across 6 movie aspects — Acting, Audio/BGM, Visuals, Plot, Dubbing, Direction
- **Cross-linguistic gap scores** revealing where Hindi and Telugu communities diverge
- **Temporal sentiment tracking** — daily sentiment scores from release date onwards
- **Director/Producer insight report** — auto-generated PDF with actionable recommendations

Currently analysing: **Dhurandhar (2025)** — Hindi and Telugu communities.

---

## 🏗️ Architecture

```
cinepulse-indic/
├── backend/
│   ├── scraper/              YouTube API comment scraper
│   ├── pipeline/             7-step ML processing pipeline
│   │   ├── merge_sources.py      Merge YouTube + Reddit CSVs
│   │   ├── language_detector.py  Unicode script + langdetect
│   │   ├── transliterator.py     Roman → native script (fallback mode)
│   │   ├── cleaner.py            Text cleaning + emoji handling
│   │   ├── sentiment_engine.py   XLM-RoBERTa sentiment inference
│   │   ├── aspect_extractor.py   BART zero-shot ABSA
│   │   └── aggregator.py         JSON output generation
│   ├── api/                  FastAPI backend (reads CSV/JSON, no DB)
│   ├── report/               ReportLab PDF generator
│   ├── data/                 CSV + JSON file storage
│   │   ├── raw/              Scraped comment CSVs
│   │   ├── processed/        Cleaned CSVs
│   │   ├── sentiment/        MuRIL/XLM-RoBERTa output CSVs
│   │   ├── aspects/          BART ABSA output CSVs
│   │   └── aggregated/       Dashboard-ready JSON files
│   └── run_pipeline.py       Single entry point for full pipeline
└── frontend/                 React.js + Recharts dashboard
    └── src/
        ├── components/
        │   ├── MovieHeader/        Title, stats, language badges
        │   ├── SentimentOverview/  Score gauges + donut charts
        │   ├── AspectAnalysis/     Radar chart + grouped bar chart
        │   ├── LanguageComparison/ Cross-linguistic gap bars
        │   ├── Timeline/           Daily sentiment line chart
        │   ├── CommentFeed/        Filterable paginated comment table
        │   └── ReportExport/       PDF download button
        └── pages/Dashboard.jsx
```

---

## 🤖 Models Used

| Model | Task | Size | Source |
|-------|------|------|--------|
| `cardiffnlp/twitter-xlm-roberta-base-sentiment` | Global sentiment (Pos/Neg/Neu) | ~1.1 GB | [HuggingFace](https://huggingface.co/cardiffnlp/twitter-xlm-roberta-base-sentiment) |
| `facebook/bart-large-mnli` | Zero-shot aspect classification | ~1.6 GB | [HuggingFace](https://huggingface.co/facebook/bart-large-mnli) |

Both models download automatically from Hugging Face on first run.

---

## 📐 Mathematical Framework

The full mathematical formalization is documented in:  
📄 [`CinePulse_Indic_Mathematical_Framework.pdf`](docs/CinePulse_Indic_Mathematical_Framework.pdf)

Key equations:

**Per-comment weighted sentiment score:**
```
s_i = d_i × p(ŷ_i) × w_i
```

**Engagement weight normalization:**
```
w_i = log(1 + l_i) / log(1 + l_max)
```

**Aggregate aspect sentiment score:**
```
S_{L,A} = Σ(d_i × p_i × w_i) / Σ(w_i)
```

**Cross-linguistic gap score:**
```
Δ_A = |S_{Hindi,A} − S_{Telugu,A}|
```

---

## ⚙️ Setup

### Prerequisites

- Python 3.10 or 3.11 recommended (3.12 works but `ai4bharat-transliteration` is unavailable)
- Node.js 18+
- YouTube Data API v3 key
- NVIDIA GPU strongly recommended for Steps 5 & 6 (CPU works but takes ~3–4 hrs)

---

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/cinepulse-indic.git
cd cinepulse-indic
```

### 2. Backend setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install PyTorch (do this BEFORE requirements.txt)

```bash
# CPU only
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# GPU — CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

Verify:
```bash
python -c "import torch; print(torch.__version__)"
```

### 4. Install remaining dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment

```bash
cp .env.example .env
# Open .env and add your YouTube API key
# Set DEVICE=cuda if you have a GPU, otherwise DEVICE=cpu
```

### 6. Download ML models (requires internet, ~2.7 GB total)

```bash
python -c "
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
# Sentiment model
name = 'cardiffnlp/twitter-xlm-roberta-base-sentiment'
AutoTokenizer.from_pretrained(name).save_pretrained('models/twitter-xlm-roberta-sentiment')
AutoModelForSequenceClassification.from_pretrained(name).save_pretrained('models/twitter-xlm-roberta-sentiment')
# Aspect model
pipeline('zero-shot-classification', model='facebook/bart-large-mnli')
print('All models downloaded.')
"
```

### 7. Frontend setup

```bash
cd ../frontend
npm install
```

---

## 📥 Data Collection

### YouTube Comments

```bash
cd backend

# Hindi community videos (replace with actual Dhurandhar video IDs)
python scraper/youtube_scraper.py --lang hindi --video-ids VIDEO_ID_1,VIDEO_ID_2,VIDEO_ID_3

# Telugu community videos
python scraper/youtube_scraper.py --lang telugu --video-ids VIDEO_ID_4,VIDEO_ID_5
```

Output: `data/raw/youtube_hindi_raw.csv` and `data/raw/youtube_telugu_raw.csv`

### Reddit Comments (Web Scraper Chrome Extension)

1. Install [Web Scraper](https://webscraper.io/) Chrome extension
2. Use **old.reddit.com** for easier scraping
3. Configure selectors to extract:
   - `comment_text` → `div.md p`
   - `author` → `a.author`
   - `published_at` → `time` element, **Attribute** type, attribute = `datetime`
   - `post_title` → `title`
4. Export as CSV → save to:
   - `backend/data/raw/reddit_hindi_raw.csv`
   - `backend/data/raw/reddit_telugu_raw.csv`

> Reddit comments receive uniform weight `w = 1.0` since upvote counts are unavailable via web scraping.

---

## 🚀 Running the Pipeline

```bash
cd backend

# Full pipeline — all 7 steps
python run_pipeline.py

# Resume from a specific step (e.g. after fixing an error)
python run_pipeline.py --from 5

# Run only one step
python run_pipeline.py --only 7
```

### Pipeline Steps

| Step | Module | Description | GPU Time | CPU Time |
|------|--------|-------------|----------|----------|
| 1 | `merge_sources.py` | Combine YouTube + Reddit CSVs | ~1 min | ~1 min |
| 2 | `language_detector.py` | Script detection per comment | ~2 min | ~2 min |
| 3 | `transliterator.py` | Roman → native script (fallback on Py 3.12) | ~3 min | ~3 min |
| 4 | `cleaner.py` | Text cleaning + emoji tagging | ~1 min | ~1 min |
| 5 | `sentiment_engine.py` | XLM-RoBERTa 3-class sentiment | ~10 min | ~90 min |
| 6 | `aspect_extractor.py` | BART zero-shot ABSA | ~20 min | ~120 min |
| 7 | `aggregator.py` | Build dashboard JSON files | ~1 min | ~1 min |

---

## 🖥️ Running the App

### Start backend API

```bash
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Start frontend dashboard

```bash
cd frontend
npm run dev
```

Dashboard: [http://localhost:5173](http://localhost:5173)

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/overview` | Overall + per-aspect scores per language |
| `GET` | `/api/timeline` | Daily sentiment time series |
| `GET` | `/api/report-data` | Gap analysis + recommendations |
| `GET` | `/api/status` | Pipeline run status |
| `GET` | `/api/comments` | Paginated filterable comment feed |
| `GET` | `/api/comments/stats` | Comment count by source |
| `GET` | `/api/report/download` | Generate + download PDF report |

**Comment feed filters:**
```
GET /api/comments?lang=hindi&aspect=audio&sentiment=NEGATIVE&page=1&page_size=20
```

---

## 📊 Aspects Analysed

| Key | Description | Example Keywords |
|-----|-------------|-----------------|
| `acting` | Cast performance | acting, hero, heroine, nailed, GOAT |
| `audio` | BGM, music, songs | BGM, music, DSP, Thaman, songs |
| `technical` | VFX, cinematography | VFX, visuals, editing, camera |
| `plot` | Story, screenplay | story, plot, twist, climax, boring |
| `dub_quality` | Dubbing quality | dubbing, voice, lip sync, dubbed |
| `direction` | Direction, pacing | direction, pacing, narration |
| `general` | No specific aspect | (fallback for unclassified comments) |

---

## 📁 Data Files Reference

| File | Description |
|------|-------------|
| `data/raw/youtube_{lang}_raw.csv` | Raw YouTube API output |
| `data/raw/reddit_{lang}_raw.csv` | Reddit Web Scraper export |
| `data/raw/merged_{lang}_raw.csv` | Merged + normalised |
| `data/processed/{lang}_processed.csv` | After all preprocessing |
| `data/sentiment/{lang}_sentiment.csv` | XLM-RoBERTa output |
| `data/aspects/{lang}_aspects.csv` | BART ABSA output |
| `data/aggregated/dhurandhar_scores.json` | Main dashboard data |
| `data/aggregated/dhurandhar_timeline.json` | Timeline chart data |
| `data/aggregated/dhurandhar_report_data.json` | PDF report input |
| `data/aggregated/pipeline_status.json` | Live pipeline status |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Data Collection | YouTube Data API v3 + Chrome Web Scraper |
| Language Detection | `langdetect` + Unicode script ranges |
| Transliteration | `ai4bharat-transliteration` (fallback on Python 3.12) |
| Text Cleaning | `re` + `emoji` library |
| Sentiment | `cardiffnlp/twitter-xlm-roberta-base-sentiment` |
| ABSA | `facebook/bart-large-mnli` (zero-shot NLI) |
| Storage | CSV + JSON files — no database |
| Backend API | FastAPI + pandas |
| Frontend | React 18 + Vite + Recharts |
| PDF Report | ReportLab |
| ML Framework | PyTorch + HuggingFace Transformers |

---

## ❓ Troubleshooting

**All comments labelled NEUTRAL**  
→ You are using `google/muril-base-cased` instead of the Cardiff model. Update `MODEL_NAME` in `sentiment_engine.py`.

**`[Errno 22] Invalid argument` on `import torch`**  
→ Corrupt PyTorch installation. Delete venv, reinstall on a stable connection (mobile hotspot recommended on restricted networks).

**`fairseq` build failure during `pip install`**  
→ Remove `ai4bharat-transliteration` from requirements. The transliterator runs in fallback mode on Python 3.12 (passes text through as-is; XLM-RoBERTa handles Roman-script natively).

**`ConnectionResetError` when downloading models**  
→ College/corporate network firewall blocking Hugging Face. Switch to mobile hotspot or download `.bin` files manually from [huggingface.co](https://huggingface.co).

**`AssertionError: Torch not compiled with CUDA enabled`**  
→ Set `DEVICE=cpu` in `.env`, or reinstall PyTorch with the CUDA build.

---

## 👥 Contributors

- **Jatin** — MCA Student, RV College of Engineering, Bangalore

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">
Made for academic research in Generative AI · RV College of Engineering · 2025
</div>
