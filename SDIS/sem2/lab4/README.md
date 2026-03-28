# Lab 4 - Web Interface for Police Management System

This project is a scaffold for laboratory work 4 based on the result of laboratory work 1.

## Goals

- keep a shared codebase for CLI and Web;
- build a Flask web interface for the existing model;
- document the architecture and launch steps in Markdown.

## Project Structure

```text
lab4/
├── app/
│   ├── cli/
│   ├── domain/
│   ├── services/
│   └── web/
├── data/
├── docs/
├── tests/
├── run_cli.py
├── run_web.py
└── requirements.txt
```

## Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the web application:

```bash
python run_web.py
```

Run the CLI scaffold:

```bash
python run_cli.py --status
```

## Next Steps

1. Move the model classes from lab1 into `app/domain`.
2. Move `PoliceSystem` from lab1 into `app/services/police_system.py`.
3. Replace placeholder pages with forms and tables for real operations.
4. Add tests for shared services and web routes.
