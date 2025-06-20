# Data Copilot: Streamlit to Alpine.js Migration Plan

## 🎯 Current Architecture Analysis

Based on your Data Copilot repository, here's what I understand about your current Streamlit application:

### **Core Features**
- **RAG-powered Q&A**: Ask questions about datasets using natural language
- **Text-to-SQL**: Generate SQL queries from plain English
- **Data Visualization**: Create charts and plots from query results  
- **Multiple LLM Support**: OpenAI, Anthropic, Ollama (local models)
- **Vector Store Integration**: Knowledge base with table schemas and documentation
- **Database Connectivity**: SQLite, PostgreSQL, CSV import
- **Business Glossary**: Custom terms and definitions for domain context

### **Current Streamlit Components**
```python
# Typical Streamlit patterns in Data Copilot
st.chat_input("Ask about your data...")
st.dataframe(query_results)
st.plotly_chart(generated_chart)
st.sidebar.selectbox("Choose LLM Model", models)
st.file_uploader("Upload CSV")
st.session_state.messages.append({"role": "user", "content": prompt})
```

## 🚀 Alpine.js Migration Architecture

### **New Architecture: FastAPI + Alpine.js**

```
┌─────────────────────────────────────────────────────────────┐
│                    Alpine.js Frontend                      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ Chat Interface│ │   SQL Editor │ │ Data Explorer│      │
│  │              │ │              │ │              │      │
│  │ x-data="chat" │ │x-data="sql"  │ │x-data="data" │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                    REST API Layer                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │   FastAPI    │ │  Vanna.ai    │ │   Vector     │      │
│  │   Backend    │ │   RAG Core   │ │    Store     │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer                              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │   SQLite     │ │ PostgreSQL   │ │  CSV Files   │      │
│  │   (IMDB)     │ │   Database   │ │   Upload     │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Migration Roadmap

### **Phase 1: Backend API Creation (Week 1-2)**

#### 1.1 FastAPI Core Structure
```python
# main.py
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import vanna
from pydantic import BaseModel

app = FastAPI(title="Data Copilot API")

# Enable CORS for Alpine.js frontend
app.add_middleware(CORSMiddleware, allow_origins=["*"])

class ChatMessage(BaseModel):
    message: str
    model_name: str = "gpt-4"
    database_url: str = None

class SQLQuery(BaseModel):
    sql: str
    database_url: str

@app.post("/api/chat")
async def chat_with_data(request: ChatMessage):
    # Port your Streamlit chat logic here
    response = vanna_instance.ask(request.message)
    return {"response": response, "sql": response.sql if hasattr(response, 'sql') else None}

@app.post("/api/sql/execute")
async def execute_sql(request: SQLQuery):
    # Execute SQL and return results
    results = vanna_instance.run_sql(request.sql)
    return {"data": results.to_dict('records'), "columns": results.columns.tolist()}

@app.post("/api/data/upload")
async def upload_csv(file: UploadFile):
    # Handle CSV uploads
    pass
```

#### 1.2 Core API Endpoints
- `POST /api/chat` - RAG-powered Q&A
- `POST /api/sql/execute` - Run generated SQL
- `GET /api/models` - Available LLM models
- `POST /api/data/upload` - CSV file upload
- `GET /api/schema/{database}` - Database schema
- `POST /api/knowledge/add` - Add business terms
- `GET /api/knowledge/search` - Semantic search

### **Phase 2: Alpine.js Frontend (Week 3-4)**

#### 2.1 Chat Interface Component
```html
<div x-data="chatApp()" class="h-screen flex flex-col">
    <!-- Chat Messages -->
    <div class="flex-1 overflow-y-auto p-4 space-y-4">
        <template x-for="message in messages" :key="message.id">
            <div class="flex" :class="message.role === 'user' ? 'justify-end' : 'justify-start'">
                <div class="max-w-3xl p-4 rounded-lg" 
                     :class="message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100'">
                    <div x-text="message.content"></div>
                    
                    <!-- SQL Code Block (for assistant responses) -->
                    <div x-show="message.sql" class="mt-3 p-3 bg-gray-800 text-green-400 rounded text-sm font-mono">
                        <pre x-text="message.sql"></pre>
                        <button @click="executeSQL(message.sql)" 
                                class="mt-2 bg-green-600 text-white px-3 py-1 rounded text-xs">
                            Execute Query
                        </button>
                    </div>
                    
                    <!-- Data Results Table -->
                    <div x-show="message.data" class="mt-3">
                        <div id="results-grid" class="ag-theme-alpine" style="height: 300px;"></div>
                    </div>
                    
                    <!-- Generated Chart -->
                    <div x-show="message.chart" class="mt-3">
                        <div x-ref="chartContainer"></div>
                    </div>
                </div>
            </div>
        </template>
    </div>
    
    <!-- Chat Input -->
    <div class="border-t p-4">
        <form @submit.prevent="sendMessage()">
            <div class="flex space-x-2">
                <input x-model="currentMessage" 
                       placeholder="Ask about your data..." 
                       class="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <button type="submit" :disabled="loading" 
                        class="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 disabled:bg-blue-300">
                    <span x-show="!loading">Send</span>
                    <span x-show="loading">...</span>
                </button>
            </div>
        </form>
    </div>
</div>

<script>
function chatApp() {
    return {
        messages: [],
        currentMessage: '',
        loading: false,
        selectedModel: 'gpt-4',
        
        async sendMessage() {
            if (!this.currentMessage.trim()) return;
            
            // Add user message
            this.messages.push({
                id: Date.now(),
                role: 'user',
                content: this.currentMessage
            });
            
            const userMessage = this.currentMessage;
            this.currentMessage = '';
            this.loading = true;
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        message: userMessage,
                        model_name: this.selectedModel
                    })
                });
                
                const data = await response.json();
                
                // Add assistant response
                this.messages.push({
                    id: Date.now() + 1,
                    role: 'assistant',
                    content: data.response,
                    sql: data.sql
                });
                
            } catch (error) {
                console.error('Chat error:', error);
            } finally {
                this.loading = false;
            }
        },
        
        async executeSQL(sql) {
            try {
                const response = await fetch('/api/sql/execute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        sql: sql,
                        database_url: this.currentDatabase
                    })
                });
                
                const data = await response.json();
                
                // Update message with results
                const lastMessage = this.messages[this.messages.length - 1];
                lastMessage.data = data.data;
                lastMessage.columns = data.columns;
                
                // Render AG-Grid with results
                this.renderDataGrid(data.data, data.columns);
                
            } catch (error) {
                console.error('SQL execution error:', error);
            }
        },
        
        renderDataGrid(data, columns) {
            const columnDefs = columns.map(col => ({
                headerName: col,
                field: col,
                sortable: true,
                filter: true
            }));
            
            const gridOptions = {
                columnDefs: columnDefs,
                rowData: data,
                pagination: true,
                paginationPageSize: 50
            };
            
            const gridDiv = document.querySelector('#results-grid');
            agGrid.createGrid(gridDiv, gridOptions);
        }
    }
}
</script>
```

#### 2.2 SQL Editor Component
```html
<div x-data="sqlEditor()" class="h-full flex flex-col">
    <!-- SQL Editor Toolbar -->
    <div class="border-b p-4 flex justify-between items-center">
        <h2 class="text-xl font-semibold">SQL Editor</h2>
        <div class="flex space-x-2">
            <select x-model="selectedDatabase" class="border rounded p-2">
                <option value="imdb.db">IMDB Movies</option>
                <option value="custom.db">Custom Database</option>
            </select>
            <button @click="executeQuery()" 
                    class="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
                Execute (Ctrl+Enter)
            </button>
        </div>
    </div>
    
    <!-- Code Editor -->
    <div class="flex-1 flex">
        <div class="w-1/2 border-r">
            <textarea x-model="sqlQuery" 
                      @keydown.ctrl.enter="executeQuery()"
                      class="w-full h-full p-4 font-mono text-sm border-none outline-none resize-none"
                      placeholder="-- Enter your SQL query here&#10;SELECT * FROM movies WHERE genre = 'Action' LIMIT 10;"></textarea>
        </div>
        
        <!-- Results Panel -->
        <div class="w-1/2 flex flex-col">
            <div class="border-b p-2 bg-gray-50">
                <span x-text="`Results (${results.length} rows)`"></span>
            </div>
            <div class="flex-1">
                <div id="sql-results-grid" class="ag-theme-alpine h-full"></div>
            </div>
        </div>
    </div>
</div>
```

### **Phase 3: Advanced Features (Week 5-6)**

#### 3.1 File Upload & Data Management
```html
<div x-data="dataManager()">
    <!-- File Upload Area -->
    <div class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center"
         @drop="handleDrop($event)" 
         @dragover.prevent 
         @dragenter.prevent>
        <input type="file" @change="handleFileSelect($event)" accept=".csv,.db" class="hidden" x-ref="fileInput">
        <button @click="$refs.fileInput.click()" class="bg-blue-500 text-white px-6 py-3 rounded-lg">
            Upload CSV or Database
        </button>
        <p class="mt-2 text-gray-600">Or drag and drop files here</p>
    </div>
    
    <!-- Database Tables Explorer -->
    <div class="mt-8">
        <h3 class="text-lg font-semibold mb-4">Available Tables</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <template x-for="table in tables" :key="table.name">
                <div class="border rounded-lg p-4 hover:shadow-md cursor-pointer"
                     @click="exploreTable(table.name)">
                    <h4 class="font-medium" x-text="table.name"></h4>
                    <p class="text-sm text-gray-600" x-text="`${table.row_count} rows`"></p>
                    <div class="mt-2">
                        <span class="text-xs bg-gray-100 px-2 py-1 rounded" 
                              x-text="`${table.columns.length} columns`"></span>
                    </div>
                </div>
            </template>
        </div>
    </div>
</div>
```

#### 3.2 Chart Generation
```javascript
// Integration with Chart.js or Plotly
async generateChart(data, chartType = 'auto') {
    const response = await fetch('/api/chart/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            data: data,
            chart_type: chartType,
            auto_detect: true
        })
    });
    
    const chartConfig = await response.json();
    
    // Render with Chart.js
    const ctx = this.$refs.chartContainer.getContext('2d');
    new Chart(ctx, chartConfig);
}
```

## 🎬 IMDB Movie Recommender Example

Here's how your IMDB use case would work in Alpine.js:

```html
<div x-data="movieRecommender()" class="max-w-4xl mx-auto p-6">
    <h1 class="text-3xl font-bold mb-6">🎬 IMDB Movie Recommender</h1>
    
    <!-- Chat Interface -->
    <div class="bg-white rounded-lg shadow-sm border h-96 flex flex-col">
        <div class="flex-1 overflow-y-auto p-4 space-y-3">
            <template x-for="message in conversation" :key="message.id">
                <div class="flex" :class="message.role === 'user' ? 'justify-end' : 'justify-start'">
                    <div class="max-w-lg p-3 rounded-lg" 
                         :class="message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100'">
                        <div x-text="message.content"></div>
                        
                        <!-- Movie Cards for recommendations -->
                        <div x-show="message.movies" class="mt-3 grid grid-cols-2 gap-2">
                            <template x-for="movie in message.movies" :key="movie.id">
                                <div class="bg-white text-black p-2 rounded border">
                                    <h4 class="font-medium text-sm" x-text="movie.title"></h4>
                                    <p class="text-xs text-gray-600" x-text="`${movie.year} • ${movie.rating}/10`"></p>
                                    <p class="text-xs" x-text="movie.genre"></p>
                                </div>
                            </template>
                        </div>
                    </div>
                </div>
            </template>
        </div>
        
        <div class="border-t p-4">
            <form @submit.prevent="askForRecommendation()">
                <input x-model="userQuery" 
                       placeholder="I want a sci-fi movie like Blade Runner but more recent..." 
                       class="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            </form>
        </div>
    </div>
    
    <!-- Quick Filters -->
    <div class="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <button @click="quickQuery('action movies from 2020s')" 
                class="p-3 bg-gray-100 rounded-lg hover:bg-gray-200">
            🎬 Recent Action
        </button>
        <button @click="quickQuery('highly rated comedies')" 
                class="p-3 bg-gray-100 rounded-lg hover:bg-gray-200">
            😂 Top Comedies
        </button>
        <button @click="quickQuery('oscar winning dramas')" 
                class="p-3 bg-gray-100 rounded-lg hover:bg-gray-200">
            🏆 Award Winners
        </button>
        <button @click="quickQuery('underrated gems')" 
                class="p-3 bg-gray-100 rounded-lg hover:bg-gray-200">
            💎 Hidden Gems
        </button>
    </div>
</div>

<script>
function movieRecommender() {
    return {
        conversation: [
            {
                id: 1,
                role: 'assistant',
                content: 'Hi! I can help you find movies to watch. What kind of movie are you in the mood for?'
            }
        ],
        userQuery: '',
        
        async askForRecommendation() {
            if (!this.userQuery.trim()) return;
            
            // Add user message
            this.conversation.push({
                id: Date.now(),
                role: 'user',
                content: this.userQuery
            });
            
            const query = this.userQuery;
            this.userQuery = '';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        message: query,
                        context: 'movie_recommendations',
                        database: 'imdb'
                    })
                });
                
                const data = await response.json();
                
                // Add assistant response with movie data
                this.conversation.push({
                    id: Date.now() + 1,
                    role: 'assistant',
                    content: data.response,
                    movies: data.movies // Parsed movie results
                });
                
            } catch (error) {
                console.error('Recommendation error:', error);
            }
        },
        
        quickQuery(query) {
            this.userQuery = query;
            this.askForRecommendation();
        }
    }
}
</script>
```

## 📊 Component Mapping Comparison

| Streamlit Component | Alpine.js + FastAPI Equivalent |
|-------------------|--------------------------------|
| `st.chat_input()` | `<input x-model="message" @submit.prevent="sendMessage()">` |
| `st.chat_message()` | `<template x-for="msg in messages">` |
| `st.dataframe()` | AG-Grid with `agGrid.createGrid()` |
| `st.plotly_chart()` | Chart.js or Plotly.js integration |
| `st.file_uploader()` | `<input type="file" @change="uploadFile()">` |
| `st.selectbox()` | `<select x-model="selectedOption">` |
| `st.sidebar` | `<div class="w-64 border-r">` (sidebar layout) |
| `st.session_state` | Alpine.js reactive data object |
| `st.form()` | `<form @submit.prevent="handleSubmit()">` |
| `st.spinner()` | `<div x-show="loading">Loading...</div>` |

## 🚀 Migration Benefits

### **User Experience Improvements**
- **Real-time chat** - No page reloads during conversation
- **Instant SQL execution** - Results appear immediately
- **Progressive loading** - Charts and tables stream in
- **Better mobile experience** - Responsive Alpine.js components

### **Developer Experience**
- **API-first architecture** - Can build mobile app later
- **Component modularity** - Easier to maintain and test
- **Custom styling** - Full control over UI/UX
- **Performance** - Faster than Streamlit for interactive features

### **Deployment & Scaling**
- **Standard web deployment** - Works on any hosting platform
- **CDN-friendly** - Static assets can be cached
- **Horizontal scaling** - API and frontend scale independently
- **Docker-ready** - Container deployment

## 🛠️ Implementation Strategy

### **Week 1-2: Foundation**
1. Extract Vanna.ai logic into FastAPI endpoints
2. Create basic chat API with existing models
3. Set up CORS and basic Alpine.js frontend

### **Week 3-4: Core Features**
1. Implement chat interface with message history
2. Add SQL editor with syntax highlighting
3. Integrate AG-Grid for data display
4. Add file upload functionality

### **Week 5-6: Advanced Features**
1. Chart generation and visualization
2. Knowledge base management UI
3. Model selection and configuration
4. Advanced search and filtering

### **Week 7-8: Polish & Deploy**
1. Performance optimization
2. Error handling and user feedback
3. Responsive design improvements
4. Production deployment setup

This migration will give you a modern, scalable architecture while preserving all the powerful RAG capabilities of your current Data Copilot application!

## 🎯 Next Steps

1. **Start with API extraction** - Move your core Vanna.ai logic to FastAPI
2. **Build chat MVP** - Simple chat interface to prove the concept  
3. **Add data visualization** - AG-Grid + Chart.js integration
4. **Iterate and enhance** - Add advanced features gradually

Would you like me to help you start with any specific component? I can create the FastAPI backend structure or the Alpine.js chat interface first!