# py-querier

Simple graphql app that allows to query a database of books and authors. Purpose of this app is to get more
familiar with graphql. It is built using FastAPI and code-first approach using [strawberry](https://strawberry.rocks/).

## How to run

1. Install dependencies
```shell
uv venv -p 3.12 
source .venv/bin/activate
uv pip install -r requirements.txt 
```

2. Create db
```shell
python app/db.py
```

3. Run the app
```shell
python main.py
```
