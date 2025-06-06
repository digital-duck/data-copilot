"""
# ToDo

# Done
"""

# basic libs
from datetime import datetime
from io import StringIO 
import os
import re
import shutil
from glob import glob
from traceback import format_exc
from pathlib import Path
from uuid import uuid4
import json
import jsonlines
from time import time

import click   # CLI interface

# special libs
from bs4 import BeautifulSoup
from lxml import html
import pandas as pd
import sqlite3

import google.generativeai as genai 

# streamlit libs
import streamlit as st
from streamlit_option_menu import option_menu
from st_aggrid import (
    AgGrid, GridOptionsBuilder, GridUpdateMode
    , JsCode, DataReturnMode
)

from ui_layout import *

from vanna_calls import (
    # helper functions
    is_sql_valid, 
    setup_vanna_cached,

    generate_sql_cached,
    run_sql_cached,
    generate_plotly_code_cached,
    generate_plot_cached,
    should_generate_chart_cached,
    generate_summary_cached,
    ask_llm_cached,

    generate_sql_not_cached,
    run_sql_not_cached,
    generate_plotly_code_not_cached,
    generate_plot_not_cached,
    should_generate_chart_not_cached,
    generate_summary_not_cached,
    ask_llm_not_cached,

    parse_llm_model_spec,
    get_ollama_models,

    # constants
    META_APP_NAME,
    DEFAULT_USER,
    DEFAULT_DB_DIALECT,
    DEFAULT_DB_NAME,
    DEFAULT_VECTOR_DB,
    DEFAULT_LLM_MODEL,
    LLM_MODEL_MAP, 
    LLM_MODEL_REVERSE_MAP, 
)

from vanna.base import SQL_DIALECTS, VECTOR_DB_LIST
from vanna.utils import convert_to_string_list,take_last_n_messages

import logging

# Configure the logging system
log_dir = Path(__file__).parent / "store/file/log/data_copilot"
log_dir.mkdir(parents=True, exist_ok=True)
log_path = log_dir / "data_copilot.log"
if not log_path.exists():
    with open(log_path, 'w'):
        pass

logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=log_path  # Optional: write to a file instead of console
)

#############################
# Config params (1st)
#############################
BLANK_STR_VALUE = ""   # place-holder blank LOV value

# VANNA_ICON_URL  = "https://vanna.ai/img/vanna.svg"
# VANNA_ICON_URL  = "https://github.com/wgong/py4kids/blob/master/lesson-18-ai/vanna/vanna-streamlit/ai_assistant.png"
VANNA_ICON_URL  = "https://cdn-icons-png.flaticon.com/128/13298/13298257.png"
# VANNA_AI_PROCESS_URL = "https://private-user-images.githubusercontent.com/7146154/299417072-1d2718ad-12a8-4a76-afa2-c61754462f93.gif?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MTczMzUxMjEsIm5iZiI6MTcxNzMzNDgyMSwicGF0aCI6Ii83MTQ2MTU0LzI5OTQxNzA3Mi0xZDI3MThhZC0xMmE4LTRhNzYtYWZhMi1jNjE3NTQ0NjJmOTMuZ2lmP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI0MDYwMiUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNDA2MDJUMTMyNzAxWiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9MmQ4MzU0ZDg1ZDg3ZWEzYjZlMWQxMDkzMTBiYjk1NGExNzYxYjQ4Y2YwMTNjYTkzZGU2N2IxMjU2YTgyZTZjNSZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QmYWN0b3JfaWQ9MCZrZXlfaWQ9MCZyZXBvX2lkPTAifQ.o-Q0S0zOeCJrfF4XP5WKc41Eh5qIdwEwEl2n_ZA_AoM"

STR_APP_NAME             = "Data Copilot"
STR_MENU_HOME            = "Welcome"
STR_MENU_CONFIG          = "Configure Settings"
STR_MENU_DB              = "Query Database"
STR_MENU_TRAIN           = "Train Knowledge-base"
STR_MENU_ASK_RAG         = "Ask Data (RAG)"
STR_MENU_ASK_LLM         = "Ask LLM"
STR_MENU_RESULT          = "Review Q&A History"
STR_MENU_EVAL            = "Evaluate LLM Models"
STR_MENU_NOTE            = "Take Notes"
STR_MENU_IMPORT_DATA     = "Import Data"
STR_MENU_ACKNOWLEDGE     = "Thank You"

STR_SAVE = "✅ Save" # 💾

DB_PATH_SQLITE = "store/sql/sqlite"

CFG = {
    "DEBUG_FLAG" : True, # False, # 
    "SQL_EXECUTION_FLAG" : True, #  False, #   control SQL
    
    "META_DB_URL" : Path(__file__).parent / DB_PATH_SQLITE / META_APP_NAME / f"{META_APP_NAME}.sqlite3",
    "META_DB_DDL" : Path(__file__).parent / DB_PATH_SQLITE / META_APP_NAME / f"{META_APP_NAME}_ddl.sql",

    # assign table names
    "TABLE_QA" : "t_qa",                # Question/Answer pair
    "TABLE_NOTE" : "t_note",            # User Notes
    "TABLE_CONFIG" : "t_config",        # Setting
    "TABLE_BUS_TERM" : "bus_term",      # table to store documentation in knowledgebase

    "NOTE_TYPE": [BLANK_STR_VALUE, 'learning', 'research', 'project', 'journal'],
    "STATUS_CODE": [BLANK_STR_VALUE, "ToDo","WIP", "Blocked", "Complete", "De-Scoped", "Others"],

    "DEFAULT_CFG" : {
        "vector_db": DEFAULT_VECTOR_DB.lower(),
        "llm_vendor": "OpenAI",
        "llm_model": "gpt-3.5-turbo",
        "db_type": DEFAULT_DB_DIALECT,
        "db_name": DEFAULT_DB_NAME,
        "db_url": Path(__file__).parent / DB_PATH_SQLITE / "chinook/chinook.sqlite3",
    },
}


# define options for selectbox column type, keyed on column name
BI_STATES = ["Y", BLANK_STR_VALUE, ]   # add empty-str as placeholder
TRI_STATES = ["Y", BLANK_STR_VALUE, None,]

SELECTBOX_OPTIONS = {
    "is_active": [0,1],
    "note_type": CFG["NOTE_TYPE"],
}



def fix_None_val(v):
    return "" if v is None else v

#############################
#  DB related  (2nd)
#############################
class DBConn(object):
    def __init__(self, db_file=CFG["META_DB_URL"]):
        self.conn = sqlite3.connect(db_file)

    def __enter__(self):
        return self.conn

    def __exit__(self, type, value, traceback):
        self.conn.close()

class DBUtils():
    """SQLite database query utility """

    def get_db_connection(self, file_db=CFG["META_DB_URL"]):
        if not file_db.exists():
            raise(f"DB file not found: {file_db}")
        return sqlite3.connect(file_db)

    def run_sql(self, sql_stmt, conn=None, DEBUG_SQL=CFG["DEBUG_FLAG"]):
        """helper to run SQL statement
        """
        if not sql_stmt:
            return
        
        if conn is None:
            # create new connection
            with DBConn() as _conn:

                if sql_stmt.lower().strip().startswith("select"):
                    return pd.read_sql(sql_stmt, _conn)
                        
                if DEBUG_SQL:  
                    logging.info(f"[DEBUG] {sql_stmt}")
                cur = _conn.cursor()
                cur.executescript(sql_stmt)
                _conn.commit()
                return
            
        else:
            # use existing connection
            _conn = conn
            if sql_stmt.lower().strip().startswith("select"):
                return pd.read_sql(sql_stmt, _conn)
                    
            if DEBUG_SQL:  
                logging.info(f"[DEBUG] {sql_stmt}")
            cur = _conn.cursor()
            cur.executescript(sql_stmt)
            _conn.commit()
            return


def remove_collections(vn, collection_name=None, ACCEPTED_TYPES = ["sql", "ddl", "documentation"]):
    if not collection_name:
        collections = ACCEPTED_TYPES
    elif isinstance(collection_name, str):
        collections = [collection_name]
    elif isinstance(collection_name, list):
        collections = collection_name
    else:
        logging.warning(f"\t{collection_name} is unknown: Skipped")
        return

    for c in collections:
        if not c in ACCEPTED_TYPES:
            logging.warning(f"\t{c} is unknown: Skipped")
            continue
            
        vn.remove_collection(c)

def strip_brackets(ddl):
    """
    This function removes square brackets from table and column names in a DDL script.
    
    Args:
        ddl (str): The DDL script containing square brackets.
    
    Returns:
        str: The DDL script with square brackets removed.
    """
    # Use regular expressions to match and replace square brackets
    pattern = r"\[([^\]]+)]"  # Match any character except ] within square brackets
    return re.sub(pattern, r"\1", ddl)        

def load_jsonl(file_path):
    if not file_path.exists():
        return
    
    chats = []
    with jsonlines.open(file_path) as reader:
        for obj in reader:
            chats.append(obj)
        st.session_state["my_results"] = chats

def dump_jsonl(file_path):
    if "my_results" not in st.session_state:
        return 
    
    with jsonlines.open(file_path, mode='w') as writer:
        for obj in st.session_state["my_results"]:
            writer.write(obj)  

def trim_str_col_val(data):
    data_new = {}
    for k,v in data.items():
        if isinstance(v, str):
            v = v.strip()
        data_new.update({k:v})
    return data_new

def list_datasets(db_type=DEFAULT_DB_DIALECT):
    """
    traverse subfolder to get all dataset files

    Returns:
        dict of datasets
    """
    sufix = db_type.lower()
    datasets = {}
    cwd = os.getcwd()
    for p in [i for i in glob(f"store/sql/**/*.{sufix}*", recursive=True) if META_APP_NAME not in i and sufix in i.lower()]:
        db_url = os.path.abspath(os.path.join(cwd, p))
        l = Path(db_url).parts
        db_name = l[l.index("sql")+2]
        datasets[db_name] = dict(db_type=db_type, db_url=db_url)
    return datasets

#############################
#  DB Helpers
#############################
def db_run_sql(sql_stmt, conn=None, debug=CFG["DEBUG_FLAG"]):
    """handles both select and insert/update/delete
    """
    if not sql_stmt or conn is None:
        return None
    
    debug_print(sql_stmt, debug=debug)

    x = sql_stmt.lower().strip()
    if x.startswith("select") or x.startswith("with"):
        return pd.read_sql(sql_stmt, conn)
    
    cur = conn.cursor()
    cur.executescript(sql_stmt)
    conn.commit()
    # conn.close()
    return None


def db_execute(sql_stmt, 
               debug=CFG["DEBUG_FLAG"], 
               execute_flag=CFG["SQL_EXECUTION_FLAG"],):
    """handles insert/update/delete
    """
    with DBConn() as _conn:
        debug_print(sql_stmt, debug=debug)
        if execute_flag:
            _conn.execute(sql_stmt)
            _conn.commit()
        else:
            logging.warning("[WARN] SQL Execution is off ! ")   

def db_list_tables_sqlite(db_url):
    """get a list of tables from SQLite database
    """
    with DBConn(db_url) as _conn:
        sql_stmt = f'''
        SELECT 
            name
        FROM 
            sqlite_schema
        WHERE 
            type ='table' AND 
            name NOT LIKE 'sqlite_%';
        '''
        df = pd.read_sql(sql_stmt, _conn)
    return df["name"].to_list()


def db_get_row_count(table_name):
    with DBConn() as _conn:
        sql_stmt = f"""
            select count(*)
            from {table_name};
        """
        df = pd.read_sql(sql_stmt, _conn)
        return df.iat[0,0]

def db_select_by_id(table_name, id_value=""):
    """Select row by primary key: id
    """
    if not id_value: return []

    with DBConn() as _conn:
        sql_stmt = f"""
            select *
            from {table_name} 
            where id = '{id_value}' ;
        """
        return pd.read_sql(sql_stmt, _conn).fillna("").to_dict('records')


def db_upsert(data, user_key_cols="note_name", call_meta_func=False):
    """ 
    """
    if not data: 
        return None

    table_name = data.get("table_name", "")
    if not table_name:
        raise Exception(f"[ERROR] Missing table_name: {data}")
    
    # build SQL
    if call_meta_func:
        visible_columns = get_columns(table_name, prop_name="is_visible")
    else:
        # temp workaround
        visible_columns = get_all_columns(table_name)


    data = trim_str_col_val(data)

    sql_type = "INSERT"
    uk_val = data.get(user_key_cols, "")
    if not uk_val:
        return

    with DBConn() as _conn:
        uk_val = escape_single_quote(uk_val)
        sql_stmt = f"""
            select *
            from {table_name} 
            where {user_key_cols} = '{uk_val}';
        """
        rows = pd.read_sql(sql_stmt, _conn).to_dict('records')

        if len(rows):
            sql_type = "UPDATE"  
            old_row = rows[0]
            id = old_row.get("id")         
           
    upsert_sql = ""
    if sql_type == "INSERT":
        col_clause = []
        val_clause = []
        for col,val in data.items():
            if col not in visible_columns:
                continue
            col_clause.append(col)
            col_val = escape_single_quote(val)
            val_clause.append(f"'{col_val}'")

        upsert_sql = f"""
            insert into {table_name} (
                {", ".join(col_clause)}
            )
            values (
                {", ".join(val_clause)}
            )  
            ;
        """

    else:
        set_clause = []
        for col in visible_columns:

            if col == "is_active":
                val = data.get(col, 1)
                old_val = old_row.get(col, 1)
                if old_val is None:
                    old_val = ""
            else:
                val = data.get(col, "")
                old_val = old_row.get(col, "")

            if isinstance(val, str):
                val = val.strip()
            if (val and old_val and val == old_val) or (not val and not old_val):
                continue

            col_val = escape_single_quote(val)
            set_clause.append(f" {col} = '{col_val}'")

        if set_clause:
            upsert_sql = f"""
                update {table_name} 
                set 
                    {", ".join(set_clause)}
                where id = {id};
            """

    if upsert_sql:
        try:
            with DBConn() as _conn:
                db_run_sql(upsert_sql, _conn)
        except Exception as ex:
            logging.error(f"[ERROR] db_upsert():\n\t{str(ex)}")

def db_query_data(db_url, table_name, limit=50, order_by=""):
    with DBConn(db_url) as _conn:
        order_by = order_by.strip()
        order_by_clause = f" order by {order_by} " if order_by else " "
        limit_clause = f" limit {limit} " if limit and limit > 0 else " "

        sql_stmt = f"""
            select 
                *
            from {table_name}
            {order_by_clause}
            {limit_clause}
            ;
        """
        return pd.read_sql(sql_stmt, _conn)

def db_current_cfg(id_config=None):
    if id_config:
        sql_stmt = f"""
            with vector_db as (
                select
                    id as id_vector
                    , vendor as vector_db
                from t_resource
                where type = 'VECTOR'
                    and is_active = 1
                    and updated_by = '{DEFAULT_USER}'
            )
            , sql_db as (
                select
                    id as id_db
                    , name as db_name
                    , vendor as db_type
                    , url as db_url
                    , instance as db_instance
                    , user_id as db_username
                    , user_token as db_password
                    , host as db_host
                    , port as db_port
                from t_resource
                where type = 'SQL'
                    and is_active = 1
                    and updated_by = '{DEFAULT_USER}'
            )
            , llm as (
                select
                    id as id_llm
                    , name as llm_model
                    , vendor as llm_vendor
                from t_resource
                where type = 'LLM'
                    and is_active = 1
                    and updated_by = '{DEFAULT_USER}'
            )
            select 
                cfg.id
                , sql_db.*
                , vector_db.*
                , llm.*
            from t_config cfg
            left join sql_db 
                on cfg.id_db = sql_db.id_db
            left join vector_db 
                on cfg.id_vector = vector_db.id_vector
            left join llm 
                on cfg.id_llm = llm.id_llm
            where id = '{id_config}'
                and updated_by = '{DEFAULT_USER}'
            ;
        """
    else:
        sql_stmt = f"""
            with cfg as (
                select 
                    *
                from t_config
                where 1=1
                    and updated_by = '{DEFAULT_USER}'
                    and is_active = 1
                order by updated_at desc
                limit 1
            )
            , vector_db as (
                select
                    id as id_vector
                    , vendor as vector_db
                from t_resource
                where type = 'VECTOR'
                    and is_active = 1
                    and updated_by = '{DEFAULT_USER}'
            )
            , sql_db as (
                select
                    id as id_db
                    , name as db_name
                    , vendor as db_type
                    , url as db_url
                    , instance as db_instance
                    , user_id as db_username
                    , user_token as db_password
                    , host as db_host
                    , port as db_port
                from t_resource
                where type = 'SQL'
                    and is_active = 1
                    and updated_by = '{DEFAULT_USER}'
            )
            , llm as (
                select
                    id as id_llm
                    , name as llm_model
                    , vendor as llm_vendor
                from t_resource
                where type = 'LLM'
                    and is_active = 1
                    and updated_by = '{DEFAULT_USER}'
            )
            select 
                cfg.id
                , sql_db.*
                , vector_db.*
                , llm.*
            from cfg
            left join sql_db 
                on cfg.id_db = sql_db.id_db
            left join vector_db 
                on cfg.id_vector = vector_db.id_vector
            left join llm 
                on cfg.id_llm = llm.id_llm
            ;
        """

    with DBConn(CFG["META_DB_URL"]) as _conn:
        df = pd.read_sql(sql_stmt, _conn)

    if df is None or df.empty:
        return {}
    
    return df.to_dict("records")[0]

def db_delete_by_id(data):
    if not data: 
        return None
    
    table_name = data.get("table_name", "")
    if not table_name:
        raise Exception(f"[ERROR] Missing table_name: {data}")

    id_val = data.get("id")
    if not id_val:
        return None
    
    delete_sql = f"""
        delete from {table_name}
        where id = {id_val};
    """
    with DBConn() as _conn:
        db_run_sql(delete_sql, _conn)


def db_update_by_id(data, update_changed=True):
    if not data: 
        return
    
    table_name = data.get("table_name", "")
    if not table_name:
        raise Exception(f"[ERROR] Missing table_name: {data}")

    id_val = data.get("id")
    if not id_val:
        return

    if update_changed:
        rows = db_select_by_id(table_name=table_name, id_value=id_val)
        if len(rows) < 1:
            return
        old_row = rows[0]

    editable_columns = get_columns(table_name, prop_name="is_editable")

    # build SQL
    set_clause = []
    for col,val in data.items():
        if col not in (editable_columns + ["updated_by"]): 
            continue

        if update_changed:
            # skip if no change
            old_val = old_row.get(col, "")
            if val != old_val:
                set_clause.append(f"{col} = '{escape_single_quote(val)}'")
        else:
            set_clause.append(f"{col} = '{escape_single_quote(val)}'")

    if set_clause:
        update_sql = f"""
            update {table_name}
            set {', '.join(set_clause)}
            where id = {id_val};
        """
        with DBConn() as _conn:
            db_run_sql(update_sql, _conn)

#############################
#  Misc Helpers
#############################
def debug_print(msg, debug=CFG["DEBUG_FLAG"]):
    if debug and msg:
        # st.write(f"[DEBUG] {str(msg)}")
        logging.debug(f"[DEBUG] {str(msg)}")

def convert_df2csv(df, index=True):
    return df.to_csv(index=index).encode('utf-8')

def convert_htm2txt(html_txt):
    return html.fromstring(html_txt).text_content().strip()

def is_noise_word(html_txt):
    return convert_htm2txt(html_txt) in CFG["NOISE_WORDS"]

def parse_bot_ver(bot_ver, sep="__"):
    return [x.strip() for x in bot_ver.split(sep) if x.strip()]

def parse_html_txt_claude(html_txt):
    """
    Extract question/answer from HTML text

    Returns:
        list of dialog content
    """
    cells = []
    if not html_txt: return cells

    soup = BeautifulSoup(html_txt, "html.parser")
    results=soup.findAll("div", class_="contents")
    for i in range(len(results)):
        v = results[i].prettify()
        if is_noise_word(v): continue
        # important to preserve HTML string because python code snippets are formatted
        cells.append(v)
    return cells

def escape_single_quote(s):
    if s is None or s == 'None':
        return ''
    if not "'" in s:
        return s
    return s.strip().replace("\'", "\'\'")

def list2sql_str(l):
    """convert a list into SQL in string
    """
    return str(l).replace("[", "(").replace("]", ")")

def get_uid():
    return os.getlogin()

def get_ts_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_uuid():
    return str(uuid4())

#############################
#  UI related
#############################
# Aggrid options
# how to set column width
# https://stackoverflow.com/questions/72624323/how-to-set-a-max-column-length-for-streamlit-aggrid
AGGRID_OPTIONS = {
    "paginationPageSize": 10,
    "grid_height": 370,
    "return_mode_value": DataReturnMode.__members__["FILTERED"],
    "update_mode_value": GridUpdateMode.__members__["MODEL_CHANGED"],
    "fit_columns_on_grid_load": True,
    "selection_mode": "single",  #  "multiple",  # 
    "allow_unsafe_jscode": True,
    "groupSelectsChildren": True,
    "groupSelectsFiltered": True,
    "enable_pagination": True,
}

# list of system columns in all tables
SYS_COLS = ["id","created_at","updated_at","created_by","updated_by","is_active"]

# column UI-properties
PROPS = [
    'is_system_col',
    'is_user_key',
    'is_required',
    'is_visible',
    'is_editable',
    'is_clickable',
    'form_column',
    'widget_type',
    'label_text',
    'kwargs'
]



def map_streamlit_widget_type(col_name, data_type):
    if data_type in ("real", "integer"):
        return "number_input"
    else:
        if (col_name.startswith("is_") or col_name.startswith("has_") or col_name.startswith("as_")):
            return "selectbox"
        else:
            return "text_input"

def init_cap(col_name):
    return " ".join([c.capitalize() for c in col_name.split("_")])

def parse_ddl_reserved(x):
    x = x.strip()
    for kw in ["--", "primary ", "not ", "default "]:
        if kw in x: 
            x = x.split(kw)[0].strip()
    return x

def parse_ddl_line(line):
    """handle , and --, returns a list of column definition
    """
    res = []
    x = line.strip()
    if x.startswith("--"):
        return res
    
    for j in [i.strip() for i in x.split(",") if i.strip()]:
        j = parse_ddl_reserved(j)
        if j:
            res.append(j)
    return res

def parse_ddl(ddl_str, filtered_types=[]):
    """Parse DDL text string into col_datatype map
    
    filtered_types = []: return all, else only specified types
    """
    out = []
    for i in ddl_str.lower().split("create "):
        if not i.startswith("table "): continue 
        out.append(i.split("\n"))
        
    # table_names = []
    col_datatypes = {}
    for t in out:
        if "table" in t[0]:
            table_name = t[0].split()[-1]
        # table_names.append(table_name)
        else:
            logging.error(f"[ERROR] Table name not found: {t}")
            continue
            
        t2 = t[1:]
        i_st = i_sp = -2
        for i in range(len(t2)):
            x = t2[i].strip()
            if x.startswith("("):
                i_st = i
            elif x.startswith(")"):
                i_sp = i
        if i_st == -2 or i_sp == -2:
            logging.error(f"[ERROR] Missing parathesis: {t2}")
            continue 

        t3 = []
        for i in t2[i_st+1:i_sp]:
            line = i.strip()
            res = parse_ddl_line(line)
            if res: 
                t3.extend(res)

        m = {}
        for x in t3:
            y = x.strip().split()
            if len(y) == 0: 
                continue
            col_name = y[0]
            datatype = "text" if len(y) < 2 else y[1]
            if not filtered_types or datatype in filtered_types:
                m[col_name] = datatype
                
        col_datatypes[table_name] = m
    
    return col_datatypes

def prepare_column_props(col_defn):
    """Prepare UI config
    """
    col_props = {}
    for table_name in col_defn.keys():
        col_types = col_defn[table_name]
        col_props[table_name] = {}
        for col_name, data_type in col_types.items():
            widget_type = map_streamlit_widget_type(col_name, data_type)
            label_text = init_cap(col_name)
            col_props[table_name].update({
                col_name : dict(
                    is_system_col=False,
                    is_user_key=False,
                    is_required=False,
                    is_visible=True,
                    is_editable=True,
                    is_clickable=False,
                    datatype=data_type,
                    form_column="COL_1-1",
                    widget_type=widget_type,
                    label_text=label_text,
                )})
    return col_props

def gen_label(col):
    "Convert table column into form label"
    if col == 'ts_created': return "Created At"
    if "_" not in col:
        if col.upper() in ["URL","ID"]:
            return col.upper()
        elif col.upper() == "TS":
            return "Timestamp"
        return col.capitalize()

    cols = []
    for c in col.split("_"):
        c  = c.strip()
        if not c: continue
        cols.append(c.capitalize())
    return " ".join(cols)



def get_all_columns(table_name):
    cols = COLUMN_PROPS[table_name].keys()
    out = [c.split()[0] for c in cols]
    if table_name == "t_zi_part":
        out = ZI_PART_COLS
    return out

def get_columns(table_name, prop_name="is_visible"):
    cols_bool = []
    cols_text = {}
    for k,v in COLUMN_PROPS[table_name].items():
        if prop_name.startswith("is_") and v.get(prop_name, False):
            cols_bool.append(k)
            
        if not prop_name.startswith("is_"):
            val = v.get(prop_name, "")
            if val:
                cols_text.update({k: val})
    
    return cols_bool or cols_text

def parse_column_props():
    """parse COLUMN_PROPS map
    """
    col_defs = {}
    for table_name in COLUMN_PROPS.keys():
        defs = {}
        cols_widget_type = {}
        cols_label_text = {}
        for p in PROPS:
            res = get_columns(table_name, prop_name=p)
            if p == 'widget_type':
                cols_widget_type = res
            elif p == 'label_text':
                cols_label_text = res
            defs[p] = res
            
        # reset label
        for col in cols_widget_type.keys():
            label = cols_label_text.get(col, "")
            if not label:
                label = gen_label(col)
            cols_label_text.update({col : label})
        defs['label_text'] = cols_label_text
        defs['all_columns'] = list(cols_widget_type.keys())

        # sort form_column alpha-numerically
        # max number of form columns = 3
        # add them
        tmp = {}
        for i in range(1,4):
            m = {k:v for k,v in defs['form_column'].items() if v.startswith(f"col{i}-")}
            tmp[f"col{str(i)}_columns"] = sorted(m, key=m.__getitem__)        
        defs.update(tmp)
        col_defs[table_name] = defs
        
    return col_defs

def ui_layout_form_fields(data,form_name,old_row,col,
                        widget_types,col_labels,system_columns):
    DISABLED = col in system_columns
    key_name_field = f"col_{form_name}_{col}"
    if old_row:
        old_val = old_row.get(col, "")
        widget_type = widget_types.get(col, "text_input")
        if widget_type == "text_area":
            kwargs = {"height":125}
            val = st.text_area(col_labels.get(col), value=old_val, disabled=DISABLED, key=key_name_field, kwargs=kwargs)
        elif widget_type == "date_input":
            old_date_input = old_val.split("T")[0]
            if old_date_input:
                val_date = datetime.strptime(old_date_input, "%Y-%m-%d")
            else:
                val_date = datetime.now().date()
            val = st.date_input(col_labels.get(col), value=val_date, disabled=DISABLED, key=key_name_field)
            val = datetime.strftime(val, "%Y-%m-%d")
        elif widget_type == "time_input":
            old_time_input = old_val
            if old_time_input:
                val_time = datetime.strptime(old_time_input.split(".")[0], "%H:%M:%S").time()
            else:
                val_time = datetime.now().time()
            val = st.time_input(col_labels.get(col), value=val_time, disabled=DISABLED, key=key_name_field)
        elif widget_type == "selectbox":
            # check if options is avail, otherwise display as text_input
            if col in SELECTBOX_OPTIONS:
                try:
                    _options = SELECTBOX_OPTIONS.get(col,[])
                    old_val = old_row.get(col, BLANK_STR_VALUE)
                    _idx = _options.index(old_val)
                    val = st.selectbox(col_labels.get(col), _options, index=_idx, key=key_name_field)
                except ValueError:
                    val = old_row.get(col, "")
            else:
                val = st.text_input(col_labels.get(col), value=old_val, disabled=DISABLED, key=key_name_field)
        elif widget_type == "multiselect":
            # check if options is avail, otherwise display as text_input
            if col in SELECTBOX_OPTIONS:
                try:
                    _options = SELECTBOX_OPTIONS.get(col,[])
                    old_val = old_row.get(col, BLANK_STR_VALUE).split(",")
                    val = st.multiselect(col_labels.get(col), _options, default=old_val, key=key_name_field)
                except ValueError:
                    val = old_row.get(col, "")
            else:
                val = st.text_input(col_labels.get(col), value=old_val, disabled=DISABLED, key=key_name_field)

        else:
            val = st.text_input(col_labels.get(col), value=old_val, disabled=DISABLED, key=key_name_field)

        if val != old_val:
            data.update({col : val})

    return data


def ui_layout_form(selected_row, table_name):

    form_name = table_name
    COLUMN_DEFS = parse_column_props()
    COL_DEFS = COLUMN_DEFS[table_name]
    visible_columns = COL_DEFS["is_visible"]
    system_columns = COL_DEFS["is_system_col"]
    form_columns = COL_DEFS["form_column"]
    col_labels = COL_DEFS["label_text"]
    widget_types = COL_DEFS["widget_type"]

    old_row = {}
    for col in visible_columns:
        old_row[col] = selected_row.get(col, "") if selected_row is not None else ""

    data = {
        "table_name": table_name,
        "updated_by": selected_row.get("updated_by", DEFAULT_USER) if selected_row else DEFAULT_USER,
    }

    # copy id if present
    id_val = old_row.get("id")
    if id_val:
        data.update({"id" : id_val})

    # display form and populate data dict
    col_col = {}
    col_prefix = [f"COL_{n}" for n in range(1,6)]  # max 5 columns
    for pfx in col_prefix:
        col_columns = col_col.get(pfx, [])
        for c in visible_columns:
            if form_columns.get(c, "").startswith(pfx):
                col_columns.append(c)
                col_col[pfx] = col_columns
    N_COLS = len(col_col.keys())

    key_names = []
    with st.form(form_name, clear_on_submit=True):
        st_cols = st.columns(N_COLS)
        id_col = 0
        if len(st_cols) > id_col:
            with st_cols[id_col]:
                for col in col_col[col_prefix[id_col]]:
                    data = ui_layout_form_fields(data,form_name,old_row,col,
                                widget_types,col_labels,system_columns)
                    key_names.append(f"col_{form_name}_{col}")

                if id_col == len(st_cols)-1:
                    # add checkbox for deleting this record
                    col = "delelte_record"
                    delete_flag = st.checkbox("Delelte Record?", value=False)
                    data.update({col: delete_flag})

        id_col = 1
        if len(st_cols) > id_col:
            with st_cols[id_col]:
                for col in col_col[col_prefix[id_col]]:
                    data = ui_layout_form_fields(data,form_name,old_row,col,
                                widget_types,col_labels,system_columns)
                    key_names.append(f"col_{form_name}_{col}")

                if id_col == len(st_cols)-1:
                    # add checkbox for deleting this record
                    col = "delelte_record"
                    delete_flag = st.checkbox("Delelte Record?", value=False)
                    data.update({col: delete_flag})

        id_col = 2
        if len(st_cols) > id_col:
            with st_cols[id_col]:
                for col in col_col[col_prefix[id_col]]:
                    data = ui_layout_form_fields(data,form_name,old_row,col,
                                widget_types,col_labels,system_columns)
                    key_names.append(f"col_{form_name}_{col}")

                if id_col == len(st_cols)-1:
                    # add checkbox for deleting this record
                    col = "delelte_record"
                    delete_flag = st.checkbox("Delelte Record?", value=False)
                    data.update({col: delete_flag})


        id_col = 3
        if len(st_cols) > id_col:
            with st_cols[id_col]:
                for col in col_col[col_prefix[id_col]]:
                    data = ui_layout_form_fields(data,form_name,old_row,col,
                                widget_types,col_labels,system_columns)
                    key_names.append(f"col_{form_name}_{col}")

                if id_col == len(st_cols)-1:
                    # add checkbox for deleting this record
                    col = "delelte_record"
                    delete_flag = st.checkbox("Delelte Record?", value=False)
                    data.update({col: delete_flag})

        id_col = 4
        if len(st_cols) > id_col:
            with st_cols[id_col]:
                for col in col_col[col_prefix[id_col]]:
                    data = ui_layout_form_fields(data,form_name,old_row,col,
                                widget_types,col_labels,system_columns)
                    key_names.append(f"col_{form_name}_{col}")

                if id_col == len(st_cols)-1:
                    # add checkbox for deleting this record
                    col = "delelte_record"
                    delete_flag = st.checkbox("Delelte Record?", value=False)
                    data.update({col: delete_flag})

        save_btn = st.form_submit_button(STR_SAVE)  
        if save_btn:
            try:
                delete_flag = data.get("delelte_record", False)
                if delete_flag:
                    if data.get("id"):
                        db_delete_by_id(data)
                else:
                    if data.get("id"):
                        data.update({"updated_at": get_ts_now(),
                                    })
                        db_update_by_id(data)
                    else:
                        data.update({
                                    "updated_at": get_ts_now(),
                                    "created_at": get_ts_now(),
                                    "updated_by": DEFAULT_USER,
                                    "created_by": DEFAULT_USER,
                                    })
                        db_upsert(data)

            except Exception as ex:
                st.error(f"{str(ex)}")

        # clear form
        try:
            for c in key_names:
                st.session_state[c] = ""
        except Exception as e:
            pass # ignore


def ui_display_df_grid(df, 
        selection_mode="single",  # "multiple", 
        fit_columns_on_grid_load=AGGRID_OPTIONS["fit_columns_on_grid_load"],
        page_size=AGGRID_OPTIONS["paginationPageSize"],
        grid_height=AGGRID_OPTIONS["grid_height"],
        clickable_columns=[],
        editable_columns=[],
        colored_columns={}
    ):
    """show input df in a grid and return selected row
    """

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection(selection_mode,
            use_checkbox=True,
            groupSelectsChildren=AGGRID_OPTIONS["groupSelectsChildren"], 
            groupSelectsFiltered=AGGRID_OPTIONS["groupSelectsFiltered"]
        )
    gb.configure_pagination(paginationAutoPageSize=False, 
        paginationPageSize=page_size)
    
    gb.configure_columns(editable_columns, editable=True)

    # color column
    for k,v in colored_columns.items():
        gb.configure_column(k, cellStyle=v)

    if clickable_columns:       # config clickable columns
        # js_code = """
        #     function(params) {return params.value ? `<a href=${params.value} target="_blank">${params.value}</a>` : "" }
        # """
        # fix
        cell_renderer_url =  JsCode("""
            class UrlCellRenderer {
                init(params) {
                    this.eGui = document.createElement('a');
                    this.eGui.innerText = params.value;
                    this.eGui.setAttribute('href', params.value);
                    this.eGui.setAttribute('style', "text-decoration:none");
                    this.eGui.setAttribute('target', "_blank");
                }
                getGui() {
                    return this.eGui;
                }
            }
        """)
        for col_name in clickable_columns:
            gb.configure_column(col_name, cellRenderer=cell_renderer_url)


    gb.configure_grid_options(domLayout='normal')
    grid_response = AgGrid(
        df, 
        gridOptions=gb.build(),
        data_return_mode=AGGRID_OPTIONS["return_mode_value"],
        update_mode=AGGRID_OPTIONS["update_mode_value"],
        height=grid_height, 
        # width='100%',
        fit_columns_on_grid_load=fit_columns_on_grid_load,
        allow_unsafe_jscode=True, #Set it to True to allow jsfunction to be injected
    )
 
    return grid_response

def df_to_csv(df, index=False):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=index).encode('utf-8')

def format_insert_sql(out_dict, table_name="w_zi_dup_merged"):
    """create SQL Insert statement using out_dict data
    """
    col_list = []
    val_list = []

    for k,v in out_dict.items():
        col_list.append(k)
        try:
            x = float(v)
            val_list.append(str(v)) 
        except:
            v = escape_single_quote(v)
            val_list.append(f"'{v}'") 

    col_str = ", ".join(col_list)
    val_str = ", ".join(val_list)
    sql_insert = f"""
        insert into {table_name} ({col_str}) 
        values ({val_str});
    """
    return sql_insert

def strip_null(data):
    data_new = []
    for d in data: 
        if isinstance(d,str):
            d = d.strip()
            if d: data_new.append(d)
            continue 
        data_new.append(d)
    return data_new 

def merge_data_col(data, sep = " / "):
    """ concat unique non-blank values
    """
    return sep.join(set(strip_null(data)))

def merge_single_col(data):
    """pick a single non-blank value
    https://stackoverflow.com/questions/59825/how-to-retrieve-an-element-from-a-set-without-removing-it
    """
    ds = set(strip_null(data))
    if not ds: return ""
    for d in ds:
        break
    return d


def gen_markdown_text(data, keys=["llm_vendor","llm_model","vector_db","db_type","db_name","db_url"]):
    table = "| Param | Value |\n|-----|-------|\n"
    table += "\n".join([f"| {k} | {v} |" for k,v in data.items() if k in keys])
    return table

def cfg_show_data(data):
    config_table_md = gen_markdown_text(data)
    st.markdown(config_table_md, unsafe_allow_html=True) 

def snake_case(s):
    """Convert string to snake_case."""
    # Replace any non-word character with underscore
    s = re.sub(r'[^\w\s]', '_', s)
    # Replace whitespace with underscore
    s = re.sub(r'\s+', '_', s)
    # Convert to lowercase
    return s.lower()

@click.command()
@click.option(
    '--input-dir', '-i',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default='.',
    help='Directory containing CSV files (default: current directory)'
)
@click.option(
    '--output', '-o',
    type=click.Path(dir_okay=False),
    default='combined_data.xlsx',
    help='Output Excel file name (default: combined_data.xlsx)'
)
@click.option(
    '--trim-prefix', '-t',
    type=click.STRING,
    default='',
    help='trim CSV filename with prefix avoiding 32 chars sheetname limitation'
)
def convert_csvs_to_excel(input_dir, output, trim_prefix):
    """
    Convert all CSV files in the specified directory to sheets in a single Excel file.
    Each CSV becomes a sheet named after the original file.
    """
    # Excel has a 31 character limit for sheet names
    MAX_SHEETNAME = 32 - 1
    trim_prefix = snake_case(trim_prefix)

    # Ensure output has .xlsx extension
    if not output.lower().endswith('.xlsx'):
        output += '.xlsx'
    
    try:
        # Get all CSV files in the directory
        csv_files = glob(f"{input_dir}/*.csv")
        
        if not csv_files:
            click.echo("No CSV files found in the specified directory.", err=True)
            return
        
        # Process each CSV file
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            with click.progressbar(csv_files, label='Processing CSV files') as files:
                for csv_path in files:
                    # Read the CSV file
                    df = pd.read_csv(csv_path)
                    
                    # Create sheet name from file name (remove .csv extension)
                    orig_csv_name = Path(csv_path).stem
                    logging.info(f"\nProcessing {csv_path} ...")
                    sheet_name = snake_case(orig_csv_name)

                    if sheet_name.startswith(trim_prefix):
                        sheet_name = sheet_name.replace(trim_prefix, "")

                    # remove extra '_'
                    sheet_name = "_".join([i for i in sheet_name.split("_") if i])

                    if len(sheet_name) > MAX_SHEETNAME:
                        sheet_name = sheet_name[:MAX_SHEETNAME]
                        click.echo(f"Warning: Sheet name '{orig_csv_name}' truncated to '{sheet_name}'")
                    
                    # Write the dataframe to Excel sheet
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        click.echo(f"\nSuccess! Created {output} with {len(csv_files)} sheets.")
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

def parse_id_list(ids):
    """split list of ID string into list
    """
    x = ids.replace(",", " ").replace(";", " ")
    return [i.strip() for i in x.split() if i.strip()]

def generate_sql(cfg_data, question: str, use_last_n_message: int=1, enable_st_cache: bool=True):
    if enable_st_cache:
        return generate_sql_cached(cfg_data, question, use_last_n_message=use_last_n_message)
    else:
        return generate_sql_not_cached(cfg_data, question, use_last_n_message=use_last_n_message)

def run_sql(cfg_data, sql: str, enable_st_cache: bool=True):
    if enable_st_cache:
        return run_sql_cached(cfg_data, sql)
    else:
        return run_sql_not_cached(cfg_data, sql)

def generate_plotly_code(cfg_data, question, sql, df, enable_st_cache: bool=True):
    if enable_st_cache:
        return generate_plotly_code_cached(cfg_data, question, sql, df)
    else:
        return generate_plotly_code_not_cached(cfg_data, question, sql, df)

def generate_plot(cfg_data, code, df, enable_st_cache: bool=True):
    if enable_st_cache:
        return generate_plot_cached(cfg_data, code, df)
    else:
        return generate_plot_not_cached(cfg_data, code, df)

def should_generate_chart(cfg_data, df, enable_st_cache: bool=True):
    if enable_st_cache:
        return should_generate_chart_cached(cfg_data, df)
    else:
        return should_generate_chart_not_cached(cfg_data, df)

def generate_summary(cfg_data, question, df, enable_st_cache: bool=True):
    if enable_st_cache:
        return generate_summary_cached(cfg_data, question, df)
    else:
        return generate_summary_not_cached(cfg_data, question, df)

def ask_llm(cfg_data, question, enable_st_cache: bool=True):
    if enable_st_cache:
        return ask_llm_cached(cfg_data, question)
    else:
        return ask_llm_not_cached(cfg_data, question)

def filter_by_ollama_model(llm_models):
    """
    If Ollama is not installed, open-source models will not be listed
    """
    model_list = []
    ollama_models = get_ollama_models()

    for m in llm_models:
        if "(Open)" not in m:
            model_list.append(m)
        else:
            ollama_model_name = LLM_MODEL_MAP.get(m, "")
            if ollama_models:
                for n in ollama_models:
                    if ollama_model_name and ollama_model_name in n:
                        model_list.append(m)
                        break
    return model_list


def snake_case(s):
    """Convert string to snake_case."""
    # Replace spaces and special chars with underscore
    s = re.sub(r'[^a-zA-Z0-9]', '_', s)
    # Convert camelCase to snake_case
    s = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s)
    # Convert to lowercase and remove multiple underscores
    return re.sub('_+', '_', s.lower()).strip('_')


def list_gemini_models():
    gemini_models = []
    try:
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        print("Attempting to list available Gemini models supporting generateContent:")

        # Iterate through all available models
        for model in genai.list_models():
            # Check if the model supports the 'generateContent' method
            if 'generateContent' in model.supported_generation_methods:
                # print(f"- {model.name} (Display Name: {model.display_name})")
                gemini_models.append(model.name)

    except Exception as e:
        print(f"Error listing models: {e}")
    
    return [i.split('/')[-1] for i in sorted(gemini_models)]

def prepend_chat_history(chat_history, question):
    """ Add past N chats to question as new prompt
    """
    if not chat_history:
        return question

    contents = []    
    for i in chat_history:
        if i.get("role") == "user":
            contents.append("\n User: " + i.get("content", "") + " \n")
        if i.get("role") == "assistant":
            contents.append("\n Assistant: " + i.get("content", "") + " \n")

    return "\n".join(contents) + f"\n User: {question} \n\n Assistant: \n"

if __name__ == "__main__":
    # pass
    # convert_csvs_to_excel()
    gemini_models = list_gemini_models()
    m = "\n".join(gemini_models)
    print(f"Gemini models:\n{m}")