# data-copilot

An streamlit app built for data professionals, powered by [vanna.ai](https://github.com/vanna-ai).

Data-Copilot is an AI Assistant, speaks both natural language (like English) and machine languages (such as SQL and Python), acts like an interpreter between Analysts and Data, Analysts can now talk to data and derive insight faster than ever. With gained productivity, they can spend more time on deep analysis and strategic decision-making.

## Demo Videos
- [Movie Explorer](https://youtu.be/szQX8chA2t0)
- [Music Store](https://www.youtube.com/watch?v=Xwf8UI5gM5k)

## Overview
![welcome](https://raw.githubusercontent.com/digital-duck/data-copilot/refs/heads/main/docs/00-data-copilot-arch-design.png)

## Features

- **<span style="color: red;">ChatGPT</span>**: ask general question on <span style="color: blue;">LLM</span> models of choice 
- **<span style="color: red;">RAG</span>**: ask dataset-specific question via Retrieval Augmented Generation
    - **<span style="color: blue;">Semantic Search</span>**: discover data schema
    - **<span style="color: blue;">Text-to-SQL</span>**: generate SQL from plain text
    - **<span style="color: blue;">Data-to-Plot</span>**: generate Python code to visualize data 
- **<span style="color: red;">Data Privacy</span>** (__optional__) : leverage  <span style="color: blue;">Ollama</span> and open-source LLM models locally 


### Configure
Choose data source, vector store, LLM model
![configure](https://raw.githubusercontent.com/digital-duck/data-copilot/refs/heads/main/docs/p1-config.png)


### Database
Review database schema, data
![database](https://raw.githubusercontent.com/digital-duck/data-copilot/refs/heads/main/docs/p2-database.png)


### Knowledge Base
Define knowledge base with table schema and documentation
![knowledgebase](https://raw.githubusercontent.com/digital-duck/data-copilot/refs/heads/main/docs/p3-knowledgebase.png)

### Ask AI
Ask question on data (built on RAG), get answer in SQL, dataframe, python, plotly chart
![rag1](https://raw.githubusercontent.com/digital-duck/data-copilot/refs/heads/main/docs/p4-rag-1.png)

![rag2](https://raw.githubusercontent.com/digital-duck/data-copilot/refs/heads/main/docs/p4-rag-2.png)

### Results
Question & answer pairs are saved to database
![results](https://raw.githubusercontent.com/digital-duck/data-copilot/refs/heads/main/docs/p5-results.png)

#### LLM benchmarks
Various LLM models for compared for chinook dataset, accuracy above 90% has been achieved for top proprietary models and open-source models.
![results](https://raw.githubusercontent.com/digital-duck/data-copilot/refs/heads/main/docs/p6-llm-benchmark.png)

### Import Tools
Import data from CSV or connect to database
![import](https://raw.githubusercontent.com/digital-duck/data-copilot/refs/heads/main/docs/p9-import-sqlite.png)



## Setup

```
## (1) create virtual env
## ============================
conda create -n data_copilot python=3.11
conda activate data_copilot

## (2) create your local working folder
mkdir ssa  # aka "self-service-analytics" or anything else of your choice

## (3) Install forked Vanna library from source
## =============================
cd ssa
git clone git@github.com:digital-duck/ssadata.git

cd ssadata
pip install -e .

## (4) Install Data-Copilot from source 
## ============================
cd ssa  # back to root folder
git clone git@github.com:digital-duck/data-copilot.git

cd data-copilot
pip install -r requirements.txt 

## (5) Enable LLM model access
## =============================
## available top LLM models are listed here: 
##  https://lmarena.ai/?leaderboard

## API_KEY is required to access proprietary models (such as Google/Anthropic/OpenAI)
cp .env.example .env   # add API_KEY in .env

## open-source LLM models are available locally via Ollama here: 
## https://ollama.com/
## no API_KEY is required

## (6) launch streamlit app
## =============================
cd src
streamlit run Data-Copilot.py
```

open browser at URL: http://localhost:8501

## More Notes

### Business Terminology
Add business terms and descriptions into knowledgebase to enhance context search
    - prepare a csv file with the following columns
        - business_term
        - business_description
        - related_tables
        - related_columns
    - import it into table `bus_term`
    - see [bus_term.csv](https://github.com/wgong/py4kids/blob/master/lesson-18-ai/vanna/note_book/data/company_rank/bus_term.csv) for example

### Ollama

Visit [ollama.ai](https://ollama.com/) to install open-source LLM models and run them locally. 




