# Contextual Post Explainer

An AI agent that explains social media posts by searching for and synthesizing relevant context. Given any confusing or reference-heavy post, it returns 3-5 bullet point explanations with source citations.

## Features

- **Smart Search**: Automatically extracts key terms and searches for context
- **AI Synthesis**: Uses GPT-4 to synthesize search results into clear explanations
- **Source Citations**: Every explanation includes numbered citations to sources
- **Streaming Responses**: See explanations as they're generated in real-time
- **Caching**: Results are cached to reduce API costs and latency
- **Evaluation Harness**: 12 test cases with automated metrics

### Bonus Features

- **🖼️ Image Understanding**: Analyze images in posts using GPT-4 Vision / Claude Vision
- **🔄 Multi-Provider Comparison**: Compare GPT-4 vs Claude side-by-side
- **🧑‍⚖️ LLM-as-Judge Evaluation**: Automated quality scoring using GPT-4

## Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INPUT                              │
│  Text Post + Optional Image URL                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CACHE CHECK                                  │
│  Hash-based lookup (24h TTL)                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │ Cache Miss
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              QUERY EXTRACTION                                   │
│  • Full post text (truncated)                                   │
│  • Quoted phrases                                               │
│  • Hashtags                                                     │
│  • Capitalized terms                                            │
│  (No LLM needed - regex-based)                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WEB SEARCH                                   │
│  Primary: Tavily AI (optimized for AI agents)                   │
│  Fallback: Brave Search API (optional)                          │
│  Returns: 8-10 search results with snippets                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              IMAGE PROCESSING (Optional)                         │
│  • Download image from URL                                      │
│  • Encode to base64                                             │
│  • Prepare for vision model                                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              LLM SYNTHESIS                                      │
│  Provider: OpenAI GPT-4o (default)                              │
│  Alternative: Anthropic Claude (with fallback)                  │
│  Input: Post + Search Results + Optional Image                  │
│  Output: 3-5 bullet points with citations                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              RESPONSE PARSING                                   │
│  • Extract bullet points                                        │
│  • Parse citations [1], [2]                                    │
│  • Build source list                                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CACHE STORE                                  │
│  Save result for 24 hours                                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USER OUTPUT                                  │
│  • Bullet points                                                │
│  • Clickable source citations                                   │
│  • Streaming (SSE) or complete                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ PostInput    │→ │ Streaming    │→ │ Explanation     │   │
│  │ • Text       │  │ Display      │  │ Display         │   │
│  │ • Image URL  │  │ • SSE Client │  │ • Bullets       │   │
│  │ • Compare    │  │ • Typewriter │  │ • Sources       │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                            │ HTTP/SSE
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                          │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ API Layer (routes.py)                                  │  │
│  │ • POST /api/explain                                    │  │
│  │ • POST /api/explain/stream                             │  │
│  │ • POST /api/explain/compare                            │  │
│  │ • GET /api/providers                                   │  │
│  └────────────────┬───────────────────────────────────────┘  │
│                   │                                            │
│                   ▼                                            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ PostExplainer (explainer.py)                           │  │
│  │ Main orchestration service                             │  │
│  └───────┬────────────────────────────────────────────────┘  │
│          │                                                    │
│          ├──→ QueryExtractor (query_extractor.py)            │
│          │    • Regex-based extraction                        │
│          │    • No LLM needed                                │
│          │                                                    │
│          ├──→ SearchService (search.py)                      │
│          │    • TavilySearchProvider                          │
│          │    • BraveSearchProvider (fallback)               │
│          │    • Deduplication & ranking                      │
│          │                                                    │
│          ├──→ ImageProcessor (image_processor.py)           │
│          │    • Download & encode images                     │
│          │    • Prepare for vision models                    │
│          │                                                    │
│          ├──→ LLMService (llm.py)                           │
│          │    • OpenAIProvider (GPT-4o)                      │
│          │    • AnthropicProvider (Claude)                   │
│          │    • Model fallback logic                         │
│          │    • Vision support                               │
│          │                                                    │
│          └──→ CacheService (cache.py)                        │
│               • In-memory cache                              │
│               • SHA256-based keys                            │
│               • 24h TTL                                      │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                          │
│  • Tavily AI Search API                                       │
│  • OpenAI API (GPT-4o, GPT-4 Vision)                         │
│  • Anthropic API (Claude 3.5 Sonnet, Opus, Haiku)            │
└──────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Single LLM Call**: Unlike multi-step approaches, we use one LLM call for synthesis. This reduces latency (~3-5s vs ~8-12s) and cost while maintaining quality.

2. **No LLM for Query Generation**: Simple regex-based extraction works well for short social media posts. Saves an API call and reduces latency.

3. **Search Snippets Only**: We don't scrape full pages. Search snippets provide enough context and are more reliable (no 403 errors, faster).

4. **Streaming First**: The UI streams responses as they're generated for better UX. Users see results immediately.

5. **Tavily for Search**: Optimized for AI agents with high-quality snippets. Brave Search as optional fallback.

6. **Model Fallback**: Claude provider tries multiple model names automatically if one isn't available.

7. **In-Memory Cache**: Simple dict-based cache for MVP. Can be replaced with Redis for production.

8. **Provider Abstraction**: Clean abstraction allows easy addition of new LLM providers.

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + Python 3.11+
- **LLM**: OpenAI GPT-4o (default), Anthropic Claude (optional)
- **Search**: Tavily AI Search API (primary), Brave Search (fallback)
- **Evaluation**: sentence-transformers for semantic similarity
- **Streaming**: Server-Sent Events (SSE)

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- API Keys:
  - OpenAI API key (required)
  - Tavily API key (required) - get one free at https://tavily.com
  - Anthropic API key (optional, for Claude comparison)

### 1. Clone the Repository

```bash
git clone https://github.com/charlesblakely0701-star/post-explainer.git
cd post-explainer
```

### 2. Backend Setup

```bash
# Create virtual environment
cd backend
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file in project root
cd ..
cp env.example .env
# Edit .env and add your API keys
```

**Required `.env` configuration:**
```env
OPENAI_API_KEY=sk-your-openai-api-key
TAVILY_API_KEY=tvly-your-tavily-api-key

# Optional
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
BRAVE_API_KEY=your-brave-search-key
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

### 4. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Open http://localhost:3000 in your browser.

## API Endpoints

### POST /api/explain

Explain a social media post.

**Request:**
```json
{
  "text": "Been using the Ralph Wiggum technique all week",
  "image_url": "https://example.com/image.jpg"
}
```

**Response:**
```json
{
  "bullets": [
    "The Ralph Wiggum technique is a bash-loop method for iterating AI coding agents [1]",
    "Named after the Simpsons character for its trial-and-error style [1][2]",
    "Coined by Geoffrey Huntley in mid-2025 [2]"
  ],
  "sources": [
    {"id": 1, "title": "...", "url": "...", "snippet": "..."},
    {"id": 2, "title": "...", "url": "...", "snippet": "..."}
  ],
  "cached": false
}
```

### POST /api/explain/stream

Same as above but streams response via Server-Sent Events (SSE).

**Events:**
- `sources`: Initial sources data
- `chunk`: Text chunks as they're generated
- `done`: Completion signal

### POST /api/explain/compare

Compare explanations from multiple LLM providers (GPT-4 vs Claude).

**Request:**
```json
{
  "text": "Vibe coding is the future",
  "image_url": null
}
```

**Response:**
```json
{
  "providers": {
    "openai": {
      "bullets": ["..."],
      "sources": [...]
    },
    "anthropic": {
      "bullets": ["..."],
      "sources": [...]
    }
  },
  "available_providers": ["openai", "anthropic"]
}
```

### GET /api/providers

List available LLM providers.

**Response:**
```json
{
  "providers": ["openai", "anthropic"]
}
```

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## Evaluation Harness

The evaluation harness tests the agent against 12 diverse posts across categories (tech, culture, news, memes, finance).

### Run Evaluation

**Important:** Make sure you're in the virtual environment before running evaluation.

```bash
# Activate virtual environment first
cd backend
# On Windows:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Go back to project root
cd ..

# Run all tests
python -m evaluation.cli run

# Run a single test
python -m evaluation.cli run --case tech-01

# Run tests by category
python -m evaluation.cli run --category tech

# List available tests
python -m evaluation.cli list

# Generate report from results
python -m evaluation.cli report --format markdown
```

### Evaluation Metrics

1. **Keyword Coverage**: % of expected keywords in output
2. **Topic Coverage**: % of expected topics addressed
3. **Semantic Similarity**: Embedding similarity to reference explanation (sentence-transformers)
4. **Citation Quality**: Presence and validity of citations
5. **Format Quality**: Adherence to bullet point format

### LLM-as-Judge Evaluation

Use GPT-4 to evaluate explanation quality:

```bash
# First run regular evaluation
python -m evaluation.cli run

# Then run LLM judge on results
python evaluation/llm_judge.py evaluation/results/results_YYYYMMDD_HHMMSS.json
```

**LLM Judge Metrics:**
- Accuracy (1-5): Factual correctness
- Relevance (1-5): Addresses the post's context
- Completeness (1-5): Covers main points
- Clarity (1-5): Easy to understand
- Citation Quality (1-5): Proper source attribution

### Test Cases

| ID | Category | Difficulty | Post Preview |
|----|----------|------------|--------------|
| tech-01 | tech | medium | Ralph Wiggum technique... |
| tech-02 | tech | easy | Enshittification of the internet... |
| tech-03 | tech | easy | Vibe coding is the future... |
| tech-04 | tech | easy | Just discovered htmx... |
| tech-05 | tech | easy | Local LLMs are getting scary good... |
| culture-01 | culture | medium | Lindy effect... |
| culture-02 | culture | easy | Touch grass energy... |
| news-01 | news | easy | OpenAI announced GPT-5... |
| news-02 | news | medium | Dead Internet Theory... |
| meme-01 | meme | easy | 10x engineer... |
| meme-02 | meme | easy | Skill issue tbh... |
| finance-01 | finance | medium | Diamond hands... WAGMI... |

## Project Structure

```
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Configuration & env loading
│   ├── prompts.py                 # LLM prompt templates
│   │
│   ├── api/
│   │   ├── routes.py              # API endpoints
│   │   └── errors.py              # Custom exception handlers
│   │
│   ├── services/
│   │   ├── explainer.py           # Main orchestration
│   │   ├── search.py              # Search providers (Tavily, Brave)
│   │   ├── llm.py                  # LLM providers (OpenAI, Anthropic)
│   │   ├── query_extractor.py     # Regex-based query extraction
│   │   ├── cache.py               # In-memory caching
│   │   └── image_processor.py     # Image download & encoding
│   │
│   ├── models/
│   │   └── schemas.py             # Pydantic request/response models
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                # Main React component
│   │   ├── api/client.ts          # API client (fetch, SSE)
│   │   ├── components/
│   │   │   ├── PostInput.tsx      # Input form with image URL
│   │   │   ├── ExplanationDisplay.tsx
│   │   │   ├── ComparisonDisplay.tsx  # Side-by-side provider comparison
│   │   │   ├── ExamplePosts.tsx
│   │   │   ├── ErrorDisplay.tsx
│   │   │   └── LoadingSkeleton.tsx
│   │   └── data/examples.ts       # Example posts
│   ├── package.json
│   └── vite.config.ts
│
├── evaluation/
│   ├── cli.py                     # CLI entry point
│   ├── runner.py                  # Async test runner
│   ├── metrics.py                 # Evaluation metrics (5 types)
│   ├── llm_judge.py               # LLM-as-judge evaluation
│   ├── test_cases.json            # 12 test cases
│   └── results/                   # Output directory
│
├── .env.example                   # Environment template
├── PLAN.md                        # Implementation plan
└── README.md                      # This file
```

## Performance Characteristics

- **Average Response Time**: 3-5 seconds (non-streaming)
- **Streaming Start**: ~1-2 seconds (first chunk)
- **Cache Hit Rate**: ~30-50% for repeated queries
- **Search Results**: 8-10 per query
- **LLM Tokens**: ~500-800 per explanation

## Future Improvements

- [x] **Image Understanding**: Use GPT-4 Vision for posts with images ✅
- [x] **Multi-Provider Comparison**: Compare explanations from different LLMs ✅
- [x] **LLM-as-Judge**: Add GPT-4 based evaluation for quality scoring ✅
- [ ] **Redis Caching**: Replace in-memory cache for production
- [ ] **Rate Limiting**: Add request rate limiting
- [ ] **User Feedback**: Allow users to rate explanations
- [ ] **Batch Processing**: Process multiple posts at once
- [ ] **Custom Prompts**: Allow users to customize explanation style


