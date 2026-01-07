# 🔬 PubMed Research Trend Analyzer

Analyze research trends in any medical field using PubMed data and AI.

## 🌟 Features

- 🔍 **PubMed Search**: Search up to 500 papers by keyword
- ☁️ **Word Clouds**: Visualize frequent terms and bigrams
- 📊 **Keyword Ranking**: Top 30 single words and 2-word phrases
- 🤖 **AI Analysis**: Ollama-powered trend interpretation
- 📥 **Downloads**: Export word clouds and AI analysis

## 🚀 Quick Start

### Deploy to Streamlit Cloud

1. Push to GitHub:
```bash
git add app.py requirements.txt .gitignore .streamlit/secrets.toml.example README.md
git commit -m "Deploy PubMed Trend Analyzer"
git push origin main
```

2. Deploy on [share.streamlit.io](https://share.streamlit.io/)

3. Add Secrets:
```toml
ENTREZ_EMAIL = "your@email.com"
OLLAMA_MODEL = "llama3"
OLLAMA_API_KEY = "your_key"
```

## 📖 Usage

1. Enter research keyword (e.g., "GLP-1 cardiovascular")
2. Click "🚀 Analyze"
3. View word clouds, top terms, and AI analysis
4. Download results

## 📦 Files

- `app.py` - Main application
- `requirements.txt` - Dependencies
- `.gitignore` - Git ignore rules
- `.streamlit/secrets.toml.example` - Secrets template

## 🛠️ Tech Stack

- Streamlit
- PubMed Entrez API (Biopython)
- WordCloud + Matplotlib
- Ollama Cloud

---
**Built for Medical Research Analysis**
