-- table to store user info
-- drop table t_user;
CREATE TABLE IF NOT EXISTS t_user
(
	id INTEGER PRIMARY KEY AUTOINCREMENT
	, email TEXT NOT NULL UNIQUE
	, username TEXT NOT NULL
	, password BLOB NOT NULL
	, profile TEXT
	, note TEXT

	, is_admin INTEGER DEFAULT 0 CHECK(is_admin IN (0, 1))
	, is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1))
	, created_at text -- strftime('%Y-%m-%d %H:%M:%S') - '2024-12-19 11:37:30'
	, updated_at text
	, created_by text  NOT NULL -- user email
	, updated_by text  
);

/*
insert into t_user(
	email, created_by, updated_by, 
	username, password, created_at, updated_at
) 
values(
	'joe_coder@gmail.com', 'joe_coder@gmail.com', 'joe_coder@gmail.com', 
	'joe_coder', 'joe_coder', '2024-12-19 11:37:30', '2024-12-19 11:37:30'
);


select * from t_user;
*/


-- table to store resource info such as 
-- SQL DB, Vector DB, LLM Model, local File, URL
-- drop table t_resource;
CREATE TABLE if not exists t_resource
(
    id INTEGER PRIMARY KEY AUTOINCREMENT

    , type text   -- SQL, VECTOR, LLM, FILE, URL
	, vendor text
	, name text   -- logic name
	, is_internal INTEGER DEFAULT 0 CHECK(is_internal IN (0, 1))
	, url text
	, user_id text
	, user_token BLOB   -- password or API_Key
	, host text
	, port text
	, instance text

	, note text

	, is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1))
	, created_at text
	, updated_at text
	, created_by text  NOT NULL -- user email
	, updated_by text  
);




-- drop table t_config;
CREATE TABLE if not exists t_config
(
    id INTEGER PRIMARY KEY AUTOINCREMENT

	, id_db INTEGER
	, id_vector INTEGER
	, id_llm INTEGER

	, note text

	, is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1))
	, created_at text
	, updated_at text
	, created_by text  NOT NULL -- user email
	, updated_by text  
);


-- drop table t_qa;
CREATE TABLE if not exists t_qa
(
    id INTEGER PRIMARY KEY AUTOINCREMENT

    , id_config INTEGER NOT NULL

    , question text NOT NULL
	, question_hash text
	, is_rag INTEGER DEFAULT 1
	, sql_generated text
	, sql_ts_delta float
	, sql_revised text
	, sql_hash text
	, sql_is_valid INTEGER  DEFAULT 0

	, df_ts_delta float

	, py_generated text
	, py_ts_delta float
	, py_revised text
	, py_hash text
	, py_is_valid text  DEFAULT 'Y'

	, fig_generated text
	, fig_ts_delta float
	
	, summary_generated text
	, summary_ts_delta float

	, note text
	
	, is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1))
	, created_at text
	, updated_at text
	, created_by text  NOT NULL -- user email
	, updated_by text  
);


-- drop table t_note;
CREATE TABLE if not exists t_note
( 
    id INTEGER PRIMARY KEY AUTOINCREMENT

    , note_name text NOT NULL
    , url text 
	, note_type TEXT DEFAULT '' CHECK(note_type IN ('', 'learning', 'research', 'project', 'journal'))
	, note text
	, tags text

	, is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1))
	, created_at text
	, updated_at text
	, created_by text  NOT NULL -- user email
	, updated_by text  
);
-- select * from t_note;


