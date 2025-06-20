import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any
import os
import requests
from pathlib import Path
import json

# Page configuration
st.set_page_config(
    page_title="DuckDB Data Copilot - Chinook Music Store",
    page_icon="🦆",
    layout="wide",
    initial_sidebar_state="expanded"
)

class DuckDBCopilot:
    """DuckDB-powered Data Copilot for analytical queries"""
    
    def __init__(self):
        self.conn = duckdb.connect(':memory:')  # In-memory database
        self.setup_chinook_data()
        self.setup_knowledge_base()
    
    def download_chinook_data(self):
        """Download Chinook SQLite database and convert to DuckDB"""
        chinook_url = "https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"
        chinook_path = "chinook.sqlite"
        
        if not os.path.exists(chinook_path):
            with st.spinner("Downloading Chinook database..."):
                response = requests.get(chinook_url)
                with open(chinook_path, 'wb') as f:
                    f.write(response.content)
                st.success("Chinook database downloaded!")
        
        return chinook_path
    
    def setup_chinook_data(self):
        """Load Chinook data into DuckDB"""
        try:
            # Download SQLite file
            sqlite_path = self.download_chinook_data()
            
            # Install and load sqlite extension
            self.conn.execute("INSTALL sqlite")
            self.conn.execute("LOAD sqlite")
            
            # Read all tables from SQLite into DuckDB
            self.conn.execute(f"ATTACH '{sqlite_path}' AS chinook_db (TYPE sqlite)")
            
            # Get all table names
            tables = self.conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'chinook_db'
            """).fetchall()
            
            # Copy each table to main database
            for (table_name,) in tables:
                self.conn.execute(f"""
                    CREATE TABLE {table_name} AS 
                    SELECT * FROM chinook_db.{table_name}
                """)
            
            # Detach SQLite database
            self.conn.execute("DETACH chinook_db")
            
            # Create some useful views for better analytics
            self.create_analytical_views()
            
        except Exception as e:
            st.error(f"Error setting up data: {str(e)}")
    
    def create_analytical_views(self):
        """Create analytical views for better querying"""
        
        # Customer sales summary
        self.conn.execute("""
            CREATE VIEW customer_sales AS
            SELECT 
                c.CustomerId,
                c.FirstName || ' ' || c.LastName as CustomerName,
                c.Country,
                c.City,
                COUNT(DISTINCT i.InvoiceId) as TotalOrders,
                SUM(i.Total) as TotalSpent,
                AVG(i.Total) as AvgOrderValue,
                MAX(i.InvoiceDate) as LastOrderDate
            FROM Customer c
            LEFT JOIN Invoice i ON c.CustomerId = i.CustomerId
            GROUP BY c.CustomerId, c.FirstName, c.LastName, c.Country, c.City
        """)
        
        # Track popularity analysis
        self.conn.execute("""
            CREATE VIEW track_popularity AS
            SELECT 
                t.TrackId,
                t.Name as TrackName,
                al.Title as AlbumTitle,
                ar.Name as ArtistName,
                g.Name as Genre,
                t.UnitPrice,
                COUNT(il.TrackId) as TimesSold,
                SUM(il.Quantity) as TotalQuantitySold,
                SUM(il.UnitPrice * il.Quantity) as TotalRevenue
            FROM Track t
            JOIN Album al ON t.AlbumId = al.AlbumId
            JOIN Artist ar ON al.ArtistId = ar.ArtistId
            JOIN Genre g ON t.GenreId = g.GenreId
            LEFT JOIN InvoiceLine il ON t.TrackId = il.TrackId
            GROUP BY t.TrackId, t.Name, al.Title, ar.Name, g.Name, t.UnitPrice
        """)
        
        # Monthly sales trends
        self.conn.execute("""
            CREATE VIEW monthly_sales AS
            SELECT 
                strftime('%Y-%m', InvoiceDate) as YearMonth,
                YEAR(InvoiceDate) as Year,
                MONTH(InvoiceDate) as Month,
                COUNT(DISTINCT InvoiceId) as TotalInvoices,
                COUNT(DISTINCT CustomerId) as UniqueCustomers,
                SUM(Total) as TotalRevenue,
                AVG(Total) as AvgInvoiceValue
            FROM Invoice
            GROUP BY strftime('%Y-%m', InvoiceDate), YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YearMonth
        """)
    
    def setup_knowledge_base(self):
        """Setup knowledge base for the Chinook music store domain"""
        self.business_context = {
            "domain": "Digital Music Store",
            "description": "Chinook is a digital music store with customers, invoices, tracks, albums, artists, and genres",
            "key_entities": {
                "Customer": "People who buy music from the store",
                "Invoice": "Purchase transactions with line items",
                "Track": "Individual songs that can be purchased",
                "Album": "Collections of tracks by artists",
                "Artist": "Musicians who create albums",
                "Genre": "Musical categories like Rock, Jazz, Pop",
                "Employee": "Store staff who serve customers",
                "Playlist": "Curated collections of tracks"
            },
            "common_questions": [
                "Which artists are most popular?",
                "What genres sell the best?",
                "Which customers spend the most?",
                "What are the monthly sales trends?",
                "Which tracks are bestsellers?",
                "What countries have the most customers?",
                "Which employees sell the most?",
                "What's the average order value?"
            ]
        }
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information"""
        schema_info = {}
        
        # Get all tables
        tables = self.conn.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'main'
            ORDER BY table_name
        """).fetchall()
        
        for (table_name,) in tables:
            # Get columns for each table
            columns = self.conn.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """).fetchall()
            
            # Get row count
            row_count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            
            schema_info[table_name] = {
                'columns': columns,
                'row_count': row_count
            }
        
        return schema_info
    
    def execute_query(self, sql: str) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""
        try:
            result = self.conn.execute(sql).fetchdf()
            return result
        except Exception as e:
            st.error(f"Query error: {str(e)}")
            return pd.DataFrame()
    
    def generate_sql_from_question(self, question: str) -> str:
        """
        Simple rule-based SQL generation (In real app, you'd use LLM here)
        This is a simplified version - in your actual Data Copilot, 
        you'd use Vanna.ai or similar for proper text-to-SQL
        """
        question_lower = question.lower()
        
        # Artist popularity queries
        if "popular artist" in question_lower or "top artist" in question_lower:
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
                ORDER BY TotalRevenue DESC
                LIMIT 10
            """
        
        # Genre analysis
        elif "genre" in question_lower and ("popular" in question_lower or "best" in question_lower):
            return """
                SELECT 
                    g.Name as Genre,
                    COUNT(DISTINCT t.TrackId) as TotalTracks,
                    COALESCE(SUM(il.Quantity), 0) as TracksSold,
                    COALESCE(SUM(il.UnitPrice * il.Quantity), 0) as Revenue
                FROM Genre g
                LEFT JOIN Track t ON g.GenreId = t.GenreId
                LEFT JOIN InvoiceLine il ON t.TrackId = il.TrackId
                GROUP BY g.GenreId, g.Name
                ORDER BY Revenue DESC
            """
        
        # Customer analysis
        elif "customer" in question_lower and ("spend" in question_lower or "top" in question_lower):
            return """
                SELECT * FROM customer_sales
                ORDER BY TotalSpent DESC
                LIMIT 10
            """
        
        # Sales trends
        elif "sales trend" in question_lower or "monthly sales" in question_lower:
            return """
                SELECT * FROM monthly_sales
                ORDER BY YearMonth
            """
        
        # Bestselling tracks
        elif "bestsell" in question_lower or "popular track" in question_lower:
            return """
                SELECT * FROM track_popularity
                WHERE TimesSold > 0
                ORDER BY TotalRevenue DESC
                LIMIT 20
            """
        
        # Country analysis
        elif "country" in question_lower:
            return """
                SELECT 
                    Country,
                    COUNT(DISTINCT CustomerId) as Customers,
                    SUM(TotalSpent) as TotalRevenue,
                    AVG(TotalSpent) as AvgCustomerValue
                FROM customer_sales
                GROUP BY Country
                ORDER BY TotalRevenue DESC
            """
        
        # Employee performance
        elif "employee" in question_lower:
            return """
                SELECT 
                    e.FirstName || ' ' || e.LastName as Employee,
                    e.Title,
                    COUNT(DISTINCT c.CustomerId) as CustomersManaged,
                    COALESCE(SUM(cs.TotalSpent), 0) as TotalSalesGenerated
                FROM Employee e
                LEFT JOIN Customer c ON e.EmployeeId = c.SupportRepId
                LEFT JOIN customer_sales cs ON c.CustomerId = cs.CustomerId
                GROUP BY e.EmployeeId, e.FirstName, e.LastName, e.Title
                ORDER BY TotalSalesGenerated DESC
            """
        
        else:
            return "SELECT 'Please ask about: popular artists, genres, customers, sales trends, bestsellers, countries, or employees' as suggestion"
    
    def create_chart(self, df: pd.DataFrame, chart_type: str, question: str):
        """Create appropriate chart based on data and question"""
        if df.empty:
            return None
        
        question_lower = question.lower()
        
        # Artist revenue chart
        if "artist" in question_lower and len(df) > 1:
            fig = px.bar(df.head(10), 
                        x='Artist', y='TotalRevenue',
                        title='Top Artists by Revenue',
                        labels={'TotalRevenue': 'Total Revenue ($)'})
            fig.update_xaxis(tickangle=45)
            return fig
        
        # Genre analysis
        elif "genre" in question_lower and 'Revenue' in df.columns:
            fig = px.pie(df.head(8), 
                        values='Revenue', names='Genre',
                        title='Revenue by Genre')
            return fig
        
        # Customer spending
        elif "customer" in question_lower and 'TotalSpent' in df.columns:
            fig = px.bar(df.head(10),
                        x='CustomerName', y='TotalSpent',
                        title='Top Customers by Total Spending',
                        labels={'TotalSpent': 'Total Spent ($)'})
            fig.update_xaxis(tickangle=45)
            return fig
        
        # Sales trends
        elif "trend" in question_lower and 'YearMonth' in df.columns:
            fig = px.line(df, 
                         x='YearMonth', y='TotalRevenue',
                         title='Monthly Sales Trends',
                         labels={'TotalRevenue': 'Revenue ($)', 'YearMonth': 'Month'})
            return fig
        
        # Country analysis
        elif "country" in question_lower and 'Country' in df.columns:
            fig = px.bar(df.head(10),
                        x='Country', y='TotalRevenue',
                        title='Revenue by Country',
                        labels={'TotalRevenue': 'Total Revenue ($)'})
            fig.update_xaxis(tickangle=45)
            return fig
        
        return None

# Initialize the copilot
@st.cache_resource
def get_copilot():
    return DuckDBCopilot()

def main():
    st.title("🦆 DuckDB Data Copilot - Chinook Music Store")
    st.markdown("### Ask questions about the Chinook digital music store data!")
    
    # Initialize copilot
    copilot = get_copilot()
    
    # Sidebar with schema information
    with st.sidebar:
        st.header("📊 Database Schema")
        
        schema_info = copilot.get_schema_info()
        
        for table_name, info in schema_info.items():
            with st.expander(f"📋 {table_name} ({info['row_count']} rows)"):
                for col_name, col_type in info['columns']:
                    st.text(f"• {col_name}: {col_type}")
        
        st.header("💡 Sample Questions")
        sample_questions = [
            "Which artists are most popular?",
            "What genres sell the best?",
            "Which customers spend the most?",
            "What are the monthly sales trends?",
            "Which tracks are bestsellers?",
            "What countries have the most revenue?",
            "How do employees perform?"
        ]
        
        for question in sample_questions:
            if st.button(question, key=f"sample_{question}"):
                st.session_state.selected_question = question
    
    # Main chat interface
    st.header("💬 Ask Your Question")
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'selected_question' not in st.session_state:
        st.session_state.selected_question = None
    
    # Handle selected question from sidebar
    if st.session_state.selected_question:
        user_question = st.session_state.selected_question
        st.session_state.selected_question = None
    else:
        user_question = st.chat_input("Ask about the Chinook music store data...")
    
    # Process question
    if user_question:
        # Add user message
        st.session_state.messages.append({
            "role": "user", 
            "content": user_question
        })
        
        # Generate SQL
        with st.spinner("Generating SQL query..."):
            sql_query = copilot.generate_sql_from_question(user_question)
        
        # Execute query
        with st.spinner("Executing query..."):
            df = copilot.execute_query(sql_query)
        
        # Add assistant response
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Here's what I found for: '{user_question}'",
            "sql": sql_query,
            "data": df
        })
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            if message["role"] == "assistant" and "sql" in message:
                # Show SQL query
                st.subheader("🔍 Generated SQL Query")
                st.code(message["sql"], language="sql")
                
                # Show data
                if not message["data"].empty:
                    st.subheader("📊 Query Results")
                    st.dataframe(message["data"], use_container_width=True)
                    
                    # Create chart if appropriate
                    chart = copilot.create_chart(
                        message["data"], 
                        "auto", 
                        st.session_state.messages[-2]["content"] if len(st.session_state.messages) >= 2 else ""
                    )
                    
                    if chart:
                        st.subheader("📈 Visualization")
                        st.plotly_chart(chart, use_container_width=True)
                    
                    # Show summary stats
                    if len(message["data"]) > 5:
                        st.subheader("📋 Summary")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Rows", len(message["data"]))
                        with col2:
                            st.metric("Columns", len(message["data"].columns))
                        with col3:
                            if any(col for col in message["data"].columns if 'revenue' in col.lower() or 'total' in col.lower()):
                                numeric_col = next(col for col in message["data"].columns if 'revenue' in col.lower() or 'total' in col.lower())
                                if pd.api.types.is_numeric_dtype(message["data"][numeric_col]):
                                    st.metric("Sum", f"${message['data'][numeric_col].sum():,.2f}")
    
    # Raw SQL interface
    st.header("🛠️ Raw SQL Interface")
    with st.expander("Execute Custom SQL"):
        custom_sql = st.text_area(
            "Enter your SQL query:",
            value="SELECT * FROM Artist LIMIT 10;",
            height=100
        )
        
        if st.button("Execute SQL"):
            try:
                result_df = copilot.execute_query(custom_sql)
                if not result_df.empty:
                    st.dataframe(result_df, use_container_width=True)
                    
                    # Download results
                    csv = result_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download CSV",
                        csv,
                        "query_results.csv",
                        "text/csv"
                    )
            except Exception as e:
                st.error(f"SQL Error: {str(e)}")
    
    # Performance info
    st.header("⚡ DuckDB Performance Info")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Get database size info
        total_rows = sum(info['row_count'] for info in schema_info.values())
        st.metric("Total Records", f"{total_rows:,}")
    
    with col2:
        st.metric("Tables", len(schema_info))
    
    with col3:
        st.metric("Database Type", "DuckDB In-Memory")

if __name__ == "__main__":
    main()