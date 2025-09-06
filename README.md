### SlowDraft

## Installation / Setup

1. Install the python version listed in [runtime.txt](./runtime.txt)
1. Install [Postgres 16](https://postgresapp.com/downloads.html)
1. You may need to run this command so that the `pg_config` can be found: `export PATH=$PATH:/Applications/Postgres.app/Contents/Versions/16/bin`
1. Create a virtual environment, e.g. `python -m venv venv`
1. Enter virtual environment: `source venv/bin/activate`
1. Install packages: `pip install -r requirements.txt`
1. Start the server: `uvicorn app:app --reload`
