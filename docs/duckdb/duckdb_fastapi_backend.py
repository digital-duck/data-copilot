from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import duckdb
import pandas as pd
import json
import os
import requests
from pathlib import Path
import uvicorn

app = FastAPI(title="DuckDB Data Copilot API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class DuckDBManager:
    """Enhanced DuckDB manager for analytical workloads"""
    
    def __init__(self):
        # Use persistent database for better performance
        self.conn = duckdb.connect('analytical_db.duckdb')
        self.setup_extensions()
        self.setup_chinook_data()
        self.setup_analytical_functions()
    
    def setup_extensions(self):
        """Install and load useful DuckDB extensions"""
        extensions = ['httpfs', 'json', 'parquet']
        
        for ext in extensions:
            try:
                self.conn.execute(f"INSTALL {ext}")
                self.conn.execute(f"LOAD {ext}")
            except Exception as e:
                print(f"Warning: Could not load extension {ext}: {e}")
    
    def setup_chinook_data(self):
        """Setup Chinook dataset in DuckDB"""
        try:
            # Check if data already exists
            tables = self.conn.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'main' AND table_name = 'Artist'
            """).fetchall()
            
            if tables:
                print("Chinook data already loaded")
                return
            
            # Download and setup Chinook data
            chinook_url = "https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"
            chinook_path = "chinook.sqlite"
            
            if not os.path.exists(chinook_path):
                print("Downloading Chinook database...")
                response = requests.get(chinook_url)
                with open(chinook_path, 'wb') as f:
                    f.write(response.content)
            
            # Install SQLite extension and load data
            self.conn.execute("INSTALL sqlite")
            self.conn.execute("LOAD sqlite")
            self.conn.execute(f"ATTACH '{chinook_path}' AS chinook_db (TYPE sqlite)")
            
            # Copy all tables
            tables = self.conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'chinook_db'
            """).fetchall()
            
            for (table_name,) in tables:
                self.conn.execute(f"""
                    CREATE TABLE {table_name} AS 
                    SELECT * FROM chinook_db.{table_name}
                """)
            
            self.conn.execute("DETACH chinook_db")
            self.create_analytical_views()
            print("Chinook data loaded successfully")
            
        except Exception as e:
            print(f"Error setting up Chinook data: {e}")
    
    def create_analytical_views(self):
        """Create optimized analytical views"""
        
        # Customer analytics view
        self.conn.execute("""
            CREATE OR REPLACE VIEW customer_analytics AS
            SELECT 
                c.CustomerId,
                c.FirstName || ' ' || c.LastName as CustomerName,
                c.Country,
                c.City,
                c.Email,
                COUNT(DISTINCT i.InvoiceId) as TotalOrders,
                SUM(i.Total) as TotalSpent,
                AVG(i.Total) as AvgOrderValue,
                MIN(i.InvoiceDate) as FirstOrderDate,
                MAX(i.InvoiceDate) as LastOrderDate,
                COUNT(DISTINCT il.TrackId) as UniqueTracksPurchased
            FROM Customer c
            LEFT JOIN Invoice i ON c.CustomerId = i.CustomerId
            LEFT JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId
            GROUP BY c.CustomerId, c.FirstName, c.LastName, c.Country, c.City, c.Email
        """)
        
        # Track performance view
        self.conn.execute("""
            CREATE OR REPLACE VIEW track_performance AS
            SELECT 
                t.TrackId,
                t.Name as TrackName,
                al.Title as AlbumTitle,
                ar.Name as ArtistName,
                g.Name as Genre,
                mt.Name as MediaType,
                t.UnitPrice,
                t.Milliseconds / 1000.0 / 60.0 as DurationMinutes,
                COALESCE(sales.TimesSold, 0) as TimesSold,
                COALESCE(sales.TotalQuantity, 0) as TotalQuantitySold,
                COALESCE(sales.TotalRevenue, 0) as TotalRevenue,
                CASE 
                    WHEN COALESCE(sales.TimesSold, 0) > 10 THEN 'Popular'
                    WHEN COALESCE(sales.TimesSold, 0) > 5 THEN 'Moderate'
                    WHEN COALESCE(sales.TimesSold, 0) > 0 THEN 'Low'
                    ELSE 'No Sales'
                END as PopularityTier
            FROM Track t
            JOIN Album al ON t.AlbumId = al.AlbumId
            JOIN Artist ar ON al.ArtistId = ar.ArtistId
            JOIN Genre g ON t.GenreId = g.GenreId
            JOIN MediaType mt ON t.MediaTypeId = mt.MediaTypeId
            LEFT JOIN (
                SELECT 
                    TrackId,
                    COUNT(*) as TimesSold,
                    SUM(Quantity) as TotalQuantity,
                    SUM(UnitPrice * Quantity) as TotalRevenue
                FROM InvoiceLine
                GROUP BY TrackId
            ) sales ON t.TrackId = sales.TrackId
        """)
        
        # Sales analytics view
        self.conn.execute("""
            CREATE OR REPLACE VIEW sales_analytics AS
            SELECT 
                DATE_TRUNC('month', InvoiceDate) as SalesMonth,
                YEAR(InvoiceDate) as SalesYear,
                MONTH(InvoiceDate) as Month,
                COUNT(DISTINCT InvoiceId) as TotalInvoices,
                COUNT(DISTINCT CustomerId) as UniqueCustomers,
                SUM(Total) as TotalRevenue,
                AVG(Total) as AvgInvoiceValue,
                MIN(Total) as MinInvoiceValue,
                MAX(Total) as MaxInvoiceValue
            FROM Invoice
            GROUP BY DATE_TRUNC('month', InvoiceDate), YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY SalesMonth
        """)
        
        # Genre performance view
        self.conn.execute("""
            CREATE OR REPLACE VIEW genre_analytics AS
            SELECT 
                g.Name as Genre,
                COUNT(DISTINCT t.TrackId) as TotalTracks,
                COUNT(DISTINCT al.AlbumId) as TotalAlbums,
                COUNT(DISTINCT ar.ArtistId) as TotalArtists,
                COALESCE(SUM(il.Quantity), 0) as TracksSold,
                COALESCE(SUM(il.UnitPrice * il.Quantity), 0) as TotalRevenue,
                COALESCE(AVG(il.UnitPrice), 0) as AvgTrackPrice
            FROM Genre g
            LEFT JOIN Track t ON g.GenreId = t.GenreId
            LEFT JOIN Album al ON t.AlbumId = al.AlbumId
            LEFT JOIN Artist ar ON al.ArtistId = ar.ArtistId
            LEFT JOIN InvoiceLine il ON t.TrackId = il.TrackId
            GROUP BY g.GenreId, g.Name
        """)
    
    def setup_analytical_functions(self):
        """Setup custom analytical functions"""
        # You can add custom DuckDB functions here if needed
        pass
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query and return results with metadata"""
        try:
            # Execute query
            result = self.conn.execute(sql)
            df = result.fetchdf()
            
            # Get execution stats
            query_stats = {
                'rows_returned': len(df),
                'columns': list(df.columns),
                'execution_time_ms': 0  # DuckDB doesn't expose this easily
            }
            
            return {
                'success': True,
                'data': df.to_dict('records'),
                'columns': df.columns.tolist(),
                'stats': query_stats
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'columns': [],
                'stats': {}
            }
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get comprehensive schema information"""
        schema = {}
        
        # Get all tables and views
        objects = self.conn.execute("""
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema = 'main'
            ORDER BY table_name
        """).fetchall()
        
        for table_name, table_type in objects:
            # Get columns
            columns = self.conn.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """).fetchall()
            
            # Get row count
            try:
                row_count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            except:
                row_count = 0
            
            schema[table_name] = {
                'type': table_type.lower(),
                'columns': [{'name': col[0], 'type': col[1], 'nullable': col[2]} for col in columns],
                'row_count': row_count
            }
        
        return schema
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """Get sample data from a table"""
        try:
            result = self.conn.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            df = result.fetchdf()
            
            return {
                'success': True,
                'data': df.to_dict('records'),
                'columns': df.columns.tolist()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global DuckDB manager instance
db_manager = DuckDBManager()

# Pydantic models
class QueryRequest(BaseModel):
    sql: str
    limit: Optional[int] = 1000

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = "chinook"

class ChartRequest(BaseModel):
    data: List[Dict[str, Any]]
    chart_type: str
    title: Optional[str] = ""

# API Routes
@app.get("/")
async def serve_frontend():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")

@app.get("/api/schema")
async def get_schema():
    """Get database schema information"""
    return db_manager.get_schema_info()

@app.get("/api/tables/{table_name}/sample")
async def get_table_sample(table_name: str, limit: int = 5):
    """Get sample data from a table"""
    return db_manager.get_sample_data(table_name, limit)

@app.post("/api/query")
async def execute_query(request: QueryRequest):
    """Execute SQL query"""
    result = db_manager.execute_query(request.sql)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    # Apply limit if specified
    if request.limit and len(result['data']) > request.limit:
        result['data'] = result['data'][:request.limit]
        result['stats']['limited'] = True
    
    return result

@app.post("/api/chat")
async def chat_with_data(request: ChatRequest):
    """Process natural language queries and generate SQL"""
    try:
        # Simple rule-based SQL generation (replace with Vanna.ai or LLM)
        sql_query = generate_sql_from_question(request.message)
        
        # Execute the query
        result = db_manager.execute_query(sql_query)
        
        if not result['success']:
            return {
                'response': f"I had trouble executing that query: {result['error']}",
                'sql': sql_query,
                'data': [],
                'success': False
            }
        
        # Generate response text
        response_text = generate_response_text(request.message, result)
        
        return {
            'response': response_text,
            'sql': sql_query,
            'data': result['data'][:50],  # Limit for frontend display
            'columns': result['columns'],
            'stats': result['stats'],
            'success': True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/suggestions")
async def get_query_suggestions():
    """Get sample query suggestions"""
    return {
        "suggestions": [
            {
                "category": "Sales Analysis",
                "questions": [
                    "Which artists generate the most revenue?",
                    "What are the monthly sales trends?",
                    "Which genres are most popular?",
                    "Show me the top selling tracks"
                ]
            },
            {
                "category": "Customer Insights",
                "questions": [
                    "Which customers spend the most money?",
                    "What countries have the most customers?",
                    "Show customer purchase patterns",
                    "Which customers haven't purchased recently?"
                ]
            },
            {
                "category": "Product Performance",
                "questions": [
                    "Which albums have the most tracks?",
                    "What's the average track length by genre?",
                    "Show tracks that have never been sold",
                    "Which media types are most popular?"
                ]
            }
        ]
    }

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and analyze CSV/Parquet files"""
    try:
        # Save uploaded file
        file_path = f"uploads/{file.filename}"
        os.makedirs("uploads", exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Determine file type and load into DuckDB
        if file.filename.endswith('.csv'):
            table_name = file.filename.replace('.csv', '').replace('-', '_').replace(' ', '_')
            db_manager.conn.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS 
                SELECT * FROM read_csv_auto('{file_path}')
            """)
        elif file.filename.endswith('.parquet'):
            table_name = file.filename.replace('.parquet', '').replace('-', '_').replace(' ', '_')
            db_manager.conn.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS 
                SELECT * FROM read_parquet('{file_path}')
            """)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Get table info
        sample_data = db_manager.get_sample_data(table_name)
        
        return {
            'success': True,
            'table_name': table_name,
            'message': f"File uploaded successfully as table '{table_name}'",
            'sample_data': sample_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
def generate_sql_from_question(question: str) -> str:
    """
    Simple rule-based SQL generation
    In production, replace with Vanna.ai or LLM-based text-to-SQL
    """
    question_lower = question.lower()
    
    # Artist revenue analysis
    if any(word in question_lower for word in ["artist", "musician"]) and any(word in question_lower for word in ["revenue", "money", "sales", "popular", "top"]):
        return """
            SELECT 
                ar.Name as Artist,
                COUNT(DISTINCT al.AlbumId) as Albums,
                COUNT(DISTINCT t.TrackId) as Tracks,
                COALESCE(SUM(il.Quantity), 0) as TracksSold,
                COALESCE(SUM(il.UnitPrice * il.Quantity), 0) as TotalRevenue
            FROM Artist ar
            LEFT JOIN Album al ON ar.ArtistId = al.ArtistId
            LEFT JOIN Track t ON al.AlbumId = t.AlbumId
            LEFT JOIN InvoiceLine il ON t.TrackId = il.TrackId
            GROUP BY ar.ArtistId, ar.Name
            HAVING TotalRevenue > 0
            ORDER BY TotalRevenue DESC
            LIMIT 15
        """
    
    # Genre analysis
    elif "genre" in question_lower:
        return """
            SELECT * FROM genre_analytics
            WHERE TotalRevenue > 0
            ORDER BY TotalRevenue DESC
        """
    
    # Customer analysis
    elif "customer" in question_lower and any(word in question_lower for word in ["spend", "top", "best", "most"]):
        return """
            SELECT 
                CustomerName,
                Country,
                TotalOrders,
                TotalSpent,
                AvgOrderValue,
                LastOrderDate
            FROM customer_analytics
            WHERE TotalSpent > 0
            ORDER BY TotalSpent DESC
            LIMIT 20
        """
    
    # Sales trends
    elif any(word in question_lower for word in ["trend", "monthly", "sales over time", "time series"]):
        return """
            SELECT 
                SalesMonth,
                TotalRevenue,
                TotalInvoices,
                UniqueCustomers,
                AvgInvoiceValue
            FROM sales_analytics
            ORDER BY SalesMonth
        """
    
    # Track performance
    elif any(word in question_lower for word in ["track", "song"]) and any(word in question_lower for word in ["popular", "selling", "top"]):
        return """
            SELECT 
                TrackName,
                ArtistName,
                Genre,
                TimesSold,
                TotalRevenue,
                PopularityTier
            FROM track_performance
            WHERE TimesSold > 0
            ORDER BY TotalRevenue DESC
            LIMIT 25
        """
    
    # Country analysis
    elif "country" in question_lower:
        return """
            SELECT 
                Country,
                COUNT(*) as CustomerCount,
                SUM(TotalSpent) as TotalRevenue,
                AVG(TotalSpent) as AvgCustomerValue,
                MAX(TotalSpent) as TopCustomerSpending
            FROM customer_analytics
            GROUP BY Country
            HAVING TotalRevenue > 0
            ORDER BY TotalRevenue DESC
        """
    
    # Employee performance
    elif "employee" in question_lower:
        return """
            SELECT 
                e.FirstName || ' ' || e.LastName as Employee,
                e.Title,
                COUNT(DISTINCT c.CustomerId) as CustomersManaged,
                COALESCE(SUM(ca.TotalSpent), 0) as TotalSalesGenerated,
                COALESCE(AVG(ca.TotalSpent), 0) as AvgCustomerValue
            FROM Employee e
            LEFT JOIN Customer c ON e.EmployeeId = c.SupportRepId
            LEFT JOIN customer_analytics ca ON c.CustomerId = ca.CustomerId
            GROUP BY e.EmployeeId, e.FirstName, e.LastName, e.Title
            ORDER BY TotalSalesGenerated DESC
        """
    
    # Default fallback
    else:
        return """
            SELECT 
                'Try asking about:' as suggestion,
                'artists, genres, customers, sales trends, tracks, countries, or employees' as examples
            UNION ALL
            SELECT 'Example:', 'Which artists generate the most revenue?'
            UNION ALL
            SELECT 'Example:', 'What are the monthly sales trends?'
            UNION ALL  
            SELECT 'Example:', 'Which customers spend the most money?'
        """

def generate_response_text(question: str, result: Dict[str, Any]) -> str:
    """Generate natural language response based on query results"""
    if not result['success'] or not result['data']:
        return "I couldn't find any data for that question."
    
    data_count = len(result['data'])
    question_lower = question.lower()
    
    if "artist" in question_lower and "revenue" in question_lower:
        top_artist = result['data'][0] if result['data'] else {}
        return f"I found {data_count} artists with sales data. The top artist is {top_artist.get('Artist', 'Unknown')} with ${top_artist.get('TotalRevenue', 0):,.2f} in total revenue."
    
    elif "genre" in question_lower:
        top_genre = result['data'][0] if result['data'] else {}
        return f"Here are {data_count} genres ranked by performance. {top_genre.get('Genre', 'Unknown')} leads with ${top_genre.get('TotalRevenue', 0):,.2f} in revenue."
    
    elif "customer" in question_lower:
        top_customer = result['data'][0] if result['data'] else {}
        return f"I found {data_count} customers. The top spender is {top_customer.get('CustomerName', 'Unknown')} who has spent ${top_customer.get('TotalSpent', 0):,.2f}."
    
    elif "trend" in question_lower or "monthly" in question_lower:
        return f"Here's the sales trend data with {data_count} data points showing revenue over time."
    
    elif "track" in question_lower or "song" in question_lower:
        top_track = result['data'][0] if result['data'] else {}
        return f"Found {data_count} tracks with sales data. '{top_track.get('TrackName', 'Unknown')}' by {top_track.get('ArtistName', 'Unknown')} is the top seller."
    
    elif "country" in question_lower:
        top_country = result['data'][0] if result['data'] else {}
        return f"Sales data by country shows {data_count} countries. {top_country.get('Country', 'Unknown')} leads with ${top_country.get('TotalRevenue', 0):,.2f} in revenue."
    
    else:
        return f"Here are the results for your query, showing {data_count} records."

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)