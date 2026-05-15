# AI-Powered PDF Price Verification System

An AI-based system that analyzes product prices from PDF invoices/contracts and compares them with prices stored in a local database. If a product is not found in the database, the system searches for an approximate market price online and highlights price differences.

## Features

- Extracts product names and prices from PDF files
- AI-powered document analysis
- Compares extracted prices with local JSON database
- Searches approximate internet prices for unknown products
- Displays price differences and anomalies
- Product matching based on product names
- Separate backend and frontend architecture

---

## Technologies Used

### Backend
- Python
- FastAPI
- PDF Processing Libraries (`pdfplumber`)
- JSON Database
- Requests / google.genai for web scraping
- AI/NLP for product name matching

### Frontend
- streamlit dashboard

---

## Project Structure

```bash
  pdf_analyzer/
│
├── backend/
│   ├── main.py
│   ├── db.json
│   ├── pdf_parser.py
│   ├── web_search.py
│   ├── comparator.py
│   ├── ai_extractor.py
│   └── requirements.txt
│
├── frontend/
│   ├── app.py
│   └── requirements.txt
```

---

## How It Works

1. User uploads a PDF invoice or contract.
2. Backend extracts:
   - Product names
   - Product prices
3. System searches product prices in the local JSON database.
4. If product exists:
   - Compare PDF price with database price.
5. If product does not exist:
   - Search approximate market price on the internet.
6. Calculate and display:
   - Price differences
   - Suspiciously high/low prices
7. Results are shown in the frontend dashboard.

---

## Example Database

```json
{
  "Dorilangan urug'lik chigit tukli": 25000000,
  "Dorilangan urug'lik chigit tuksiz": 10000000
}
```

---

## Example PDF Analysis

### Extracted Products

| Product Name | PDF Price | Database/Internet Price | Difference |
|---|---|---|---|
| Dorilangan urug'lik chigit tukli | 25,000,000 | 25,000,000 | 0 |
| Dorilangan urug'lik chigit tuksiz | 30,000,000 | 10,000,000 | +20,000,000 |

---

## 🔐 Environment Variables

Create a `.env` file inside the `backend` folder and add your Gemini API key:

```env
GEMINI_API_KEY=your_api_key_here
```

---

## 🤖 Gemini Model

This project uses:

```bash
gemini-2.5-flash
```

for:
- PDF content understanding
- Product extraction
- Intelligent comparison
- Smart analysis
---

## Backend Setup

### 1. Navigate to backend

```bash
cd backend
```

### 2. Create virtual environment

```bash
python -m venv venv
```

### 3. Activate virtual environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux/Mac

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run backend server

```bash
uvicorn main:app --reload
```

Backend runs on:

```bash
http://127.0.0.1:8000
```

---

## Frontend Setup

### 1. Navigate to frontend

```bash
cd frontend
```

### 2. Create virtual environment

```bash
python -m venv venv
```

### 3. Activate virtual environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux/Mac

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run frontend

```bash
streamlit run app.py
```

Browser automatically open

## AI Capabilities

- Product name extraction
- Fuzzy matching for similar product names
- Smart comparison logic
- Approximate internet price estimation
- Detection of unusual pricing

---

## Internet Price Search

If a product is unavailable in the local database:

- The system searches online marketplaces or websites
- Finds approximate market prices
- Uses search results for comparison

---
