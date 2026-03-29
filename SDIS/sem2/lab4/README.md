# Lab 4 - Web Interface for Police Management System

This repository contains laboratory work 4 based on the result of laboratory work 1.
The project implements a client-server web application for the police management system and preserves a shared codebase for both CLI and Web interfaces.

## Project Goal

The goal of the work is to build a web interface for the domain model from laboratory work 1 and to separate the shared logic so that:

- the same domain model is used by both interfaces;
- the same service layer is used by both CLI and Web;
- the system state can be viewed and changed from the browser and from the command line;
- the implementation is documented in Markdown and ready to be published to GitHub.

## Implemented Stack

- Python 3
- Flask
- Jinja2 templates
- Pickle storage for persistent state

## Architecture

The project is organized into layers.

- `app/domain` contains domain entities from lab 1:
  `Police`, `Policeman`, `Citizen`, `Crime`, `Law`, `Investigation`, `Security`
- `app/services` contains the shared application service:
  `PoliceSystem`
- `app/storage` contains persistence logic:
  `PickleStorage`
- `app/cli` contains the command-line client
- `app/web` contains the Flask web application, routes, templates and static files

This means that business logic is not duplicated:

- CLI calls methods of `PoliceSystem`
- Web routes also call methods of `PoliceSystem`

## Project Structure

```text
lab4/
├── app/
│   ├── cli/                  # CLI client
│   ├── domain/               # shared domain model
│   ├── services/             # shared service layer
│   ├── storage/              # persistence layer
│   └── web/                  # Flask web interface
├── pickle_storage/           # serialized application state
├── run_cli.py                # CLI entry point
├── run_web.py                # Flask entry point
├── requirements.txt
└── README.md
```

## Features

The web interface supports the main operations of the model:

- dashboard with current system state
- citizen management
- zone management
- policeman management
- filing and deleting crime statements
- law management
- crime investigation
- arrest execution
- history viewing and clearing
- display of security levels by zones

The CLI interface is also preserved and works with the same shared code.

## Web Pages

- `/` - dashboard
- `/citizens` - citizens management
- `/police` - police officers and zones
- `/statements` - crime statements
- `/laws` - laws registry
- `/investigation` - investigation and arrest actions
- `/history` - system history

## How To Run

### 1. Create and activate virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the web application

```bash
python run_web.py
```

After startup, open:

```text
http://127.0.0.1:5000
```

### 4. Run the CLI client

```bash
python run_cli.py
```

Examples:

```bash
python run_cli.py police add-zone Downtown
python run_cli.py citizen add "John Smith" --zone Downtown
python run_cli.py law add 101 3 "Theft"
python run_cli.py statement add "Stole a bike" Downtown 0 0
python run_cli.py investigate --arrest
```

## Shared Code Between Lab 1 And Lab 4

The following reuse principle is implemented:

- domain classes from lab 1 were moved into `app/domain`
- the main application logic was moved into `app/services/police_system.py`
- persistence was separated into `app/storage/pickle_storage.py`
- CLI and Web use the same service methods instead of duplicating logic

This satisfies the requirement to preserve and explicitly выделить common code for both interfaces.

## Data Storage

Application data is stored in the `pickle_storage` directory:

- `police.pkl`
- `applications.pkl`
- `history.pkl`
- `citizens.pkl`
- `laws.pkl`
- `security.pkl`

## Verification

The project was checked with:

```bash
python -m compileall app run_cli.py run_web.py
```

The web routes were also tested through Flask test client for successful page rendering.

## Repository Publication

To publish the work on GitHub:

```bash
git init
git add .
git commit -m "Implement lab4 web interface"
git branch -M main
git remote add origin <your-repository-url>
git push -u origin main
```

## Conclusion

As a result, laboratory work 4 extends laboratory work 1 into a client-server application.
The project now contains:

- a shared domain model
- a shared service layer
- a working CLI client
- a working Flask-based web interface
- Markdown documentation suitable for GitHub
