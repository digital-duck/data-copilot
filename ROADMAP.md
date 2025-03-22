
## Roadmap

### Generate Reports

#### report on past Q&A conversations in markdown format

- On `QA-Results` page, serialize sql/python code, dataframe, plotly chart
    - convert dataframe to markdown text
    - save chart to png into `reports/images/img_<id>.png`
    - format code as markdown blocks (sql, python)
    - save question/answer into `reports/raw_<id>.md`
    - all done 

- Add `Tag Question` button
    - include tagged question into report

- Add `Gen Report` button
    - specify `report-name`
    - generate aggregated report file `reports/dc_<report-name>_ts.md`
    - convert report from markdown to HTML

### Configure
- improve UI 
    - Select box on LLM providers, then radio button on Model-ID
      e.g. provider = Anthropic, model_id in (Claude 3 Sonnet, Claude 3.5 Sonnet,)

### LLM Model Supports
- Qwen
- Kimi
- xAI
- Gemini : more newer models

### Auth

optional for single user.

(Work in progress)

### Task Management

To-Do list based on [The 7 Habits of Highly Effective People](https://www.wikiwand.com/en/articles/The_7_Habits_of_Highly_Effective_People)

(Work in progress)

### Privacy

use technologies such as
- [Ollama](https://ollama.com/)
- [Llama.cpp](https://www.wikiwand.com/en/articles/Llama.cpp)

### Agent-framework

- AutoGen
- TaskWeaver (Microsoft)

### Ask Doc

- NotebookLLM (Google)



