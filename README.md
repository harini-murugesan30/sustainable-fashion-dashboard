# Sustainable Fashion Thesis Code & Data

This repository contains all code and data supporting my MSc thesis.

## Contents

- **data/**  
  - `log_data.csv` — raw logs for the main analysis  
  - `ffnetboost_predictions.csv` — model predictions for the dashboard  
- **notebooks/**  
  - `Analysis_Code.ipynb` — main data-analysis pipeline  
  - `Survey.ipynb` — exploratory analysis of the survey responses  
- **dashboard/**  
  - `dashboard.py` — Streamlit app source  
  - `requirements.txt` — Python dependencies  

## Deployment

The interactive dashboard is live on Streamlit:  
https://sustainable-fashion-dashboard.streamlit.app/

## How to run locally

```bash
# 1. Clone
git clone https://github.com/your-username/sustainable-fashion-dashboard.git
cd sustainable-fashion-dashboard

# 2. Install
pip install -r dashboard/requirements.txt

# 3. Analysis
jupyter notebook notebooks/Analysis_Code.ipynb

# 4. Dashboard
streamlit run dashboard/dashboard.py
