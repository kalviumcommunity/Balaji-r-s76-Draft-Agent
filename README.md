# LinkedIn AI Agent

A complete CLI-based LinkedIn content automation system that combines **Prompting**, **RAG (Retrieval-Augmented Generation)**, **Structured Output**, and **Function Calling** to plan, draft, schedule, and analyze LinkedIn content.

## 🚀 Features

### 📅 Weekly Content Planner
- Generates **Now-Next-Later** posting schedules as structured JSON
- Recommends optimal posting windows based on engagement data
- Balances immediate needs with experimental content

### ✍️ Post Drafter  
- Uses RAG to find similar previous posts for context
- Generates structured posts with hooks, value, and CTAs
- Supports multiple formats: short, story, carousel
- Grounds content in past performance data

### ⏰ Smart Scheduler
- Assigns posts to optimal time windows using engagement best practices
- Considers historical performance data
- Prevents scheduling conflicts and validates schedules

### 📊 Metrics Ingester
- Reads post analytics from CSV files
- Analyzes performance trends by time, format, and topic
- Updates recommendations based on actual engagement data

### 💬 Comment Coach (Framework)
- Suggests replies for top-performing threads
- Identifies engagement opportunities
- Helps build relationships through thoughtful responses

## 🏗️ Architecture

```
linkedin-agent/
├── cli/              # Command handlers
│   ├── plan.py       # Weekly planning
│   ├── draft.py      # Post generation
│   ├── queue.py      # Scheduling
│   └── metrics.py    # Analytics
├── core/             # Business logic
│   ├── scheduler.py  # Time optimization
│   ├── prompting.py  # Content generation
│   ├── retrieval.py  # RAG system
│   └── schemas.py    # JSON validation
├── data/             # Persistent storage
│   ├── posts/        # Historical posts
│   ├── metrics/      # Performance data
│   └── schedules/    # Weekly plans
└── config.json       # Configuration
```

## 🛠️ Installation

```bash
# Clone and setup
git clone <repository>
cd linkedin-agent

# Install dependencies
pip install -r requirements.txt

# Initialize workspace
python li.py init
```

## 📖 Usage Examples

### 1. Generate Weekly Plan
```bash
# Create a Now-Next-Later content plan
python li.py plan --accept

# Include performance-based suggestions
python li.py plan --suggest

# Plan for specific week
python li.py plan --week-start 2025-08-25
```

### 2. Draft Posts
```bash
# Generate a story-format post
python li.py draft "3 lessons from building our MVP" --format story

# Create a carousel post
python li.py draft "Product management tips" --format carousel

# Preview without saving
python li.py draft "Quick engineering insight" --format short --preview
```

### 3. Queue and Schedule
```bash
# Queue draft for optimal time
python li.py queue draft.json

# Override posting time
python li.py queue draft.json --time "Thu 14"

# Preview scheduling
python li.py queue draft.json --preview
```

### 4. Analyze Performance
```bash
# Import metrics from CSV
python li.py metrics --import metrics.csv

# Show performance summary
python li.py metrics --since 7d --summary

# Export analysis
python li.py metrics --export report.json
```

### 5. Post Content
```bash
# Output ready-to-post content
python li.py post draft.json --now

# Process scheduled posts
python li.py post --schedule schedule.json
```

## 📁 Data Formats

### CSV Metrics Format
```csv
post_id,impressions,reactions,comments,shares,clicks,published_at
post_123,1500,120,25,8,45,2025-08-10T10:00:00Z
post_456,2200,180,40,15,75,2025-08-12T14:00:00Z
```

### Generated Post Structure
```json
{
  "id": "post_abc123",
  "title": "Story: Product Management",
  "body": "Here's what I learned about product management...",
  "tags": ["product", "management", "insights"],
  "cta": "What's your biggest product challenge?",
  "target_window": {"day": "Tue", "hour": 10},
  "source_snippets": [
    {"post_id": "similar_post", "reason": "semantic similarity"}
  ]
}
```

### Weekly Plan Structure
```json
{
  "week_of": "2025-08-25",
  "now": [
    {
      "topic": "Latest insights on product",
      "priority": "high",
      "target_window": {"day": "Tue", "hour": 10}
    }
  ],
  "next": [...],
  "later": [...]
}
```

## ⚙️ Configuration

Edit `config.json` to customize:

```json
{
  "topics": ["product", "engineering", "founder"],
  "tone": "practical, concise, conversational",
  "windows": [
    {"day": "Tue", "hour": 10},
    {"day": "Thu", "hour": 11}
  ],
  "experiment_spread_hours": 2,
  "manual_mode": true
}
```

## 🔄 Workflow

1. **Plan**: `li plan --accept` → Generate weekly content strategy
2. **Draft**: `li draft "topic"` → Create grounded posts using RAG
3. **Queue**: `li queue draft.json` → Schedule to optimal windows
4. **Post**: `li post draft.json --now` → Output for manual posting
5. **Analyze**: `li metrics --import data.csv` → Learn from performance

## 🎯 Key Design Principles

- **Manual-first**: Operates on local data, outputs copy-paste ready content
- **RAG-grounded**: Every post references similar historical content
- **Schema-validated**: All outputs comply with defined JSON schemas
- **Performance-informed**: Recommendations improve based on actual metrics
- **Modular**: Clean separation between CLI, core logic, and data

## 🔮 Future Enhancements

- Direct LinkedIn API integration (with approved access)
- Advanced NLP for content optimization
- A/B testing framework for posting times
- Automated comment analysis and reply suggestions
- Visual content generation integration

## 📊 Analytics Features

The system tracks and analyzes:
- Engagement rates by posting time
- Content performance by format and topic
- Optimal posting windows based on actual data
- Best-performing content for future reference

This creates a learning system that continuously improves recommendations based on real performance data.

---

**Note**: Currently operates in manual mode. LinkedIn API integration requires approved developer access. The system is designed to be compliance-ready with rate limiting and exponential backoff for future API use.
