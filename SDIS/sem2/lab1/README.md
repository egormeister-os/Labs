# Police Management System

A command-line application for managing police departments, crime investigations, and public security.

## Requirements

- Python 3.10+
- No external dependencies required (uses only standard library)
- For UML diagrams: PlantUML

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd lab1
```

2. (Optional) Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install development dependencies (for testing):
```bash
pip install pytest
```

## Usage

### Interactive Mode

Run the application without arguments to enter interactive mode:

```bash
python main.py
```

Example session:
```bash
# Create zones
police> police add-zone Downtown
police> police add-zone Suburbs

# Add citizens (with optional zone assignment)
police> citizen add "John Smith" --zone Downtown
police> citizen add "Mary Johnson" --zone Suburbs

# Hire officers
police> police hire "Miller" Downtown
police> police hire "Moore" Downtown

# Add a law
police> law add 101 3 "Theft"

# File crime reports
police> statement add "Stole a bike" Downtown 0 0
police> statement add "Breaking and entering" Downtown 1 0

# Investigate all crimes with arrests
police> investigate --arrest

# Check remaining crimes
police> statement list

# Show zone info with fatigue and rest status
police> police info

# Recover exhausted officers
police> police recover
```

### Command-Line Mode

Execute specific commands directly:

```bash
# Add a citizen with zone
python main.py citizen add "John Doe" --zone Downtown

# Add a zone
python main.py police add-zone "Downtown"

# Hire an officer
python main.py police hire "Smith" "Downtown"

# Add a law
python main.py law add 101 3 "Theft"

# File a crime report
python main.py statement add "Stole a bike" "Downtown" 0 0

# List all crimes
python main.py statement list

# Investigate crimes
python main.py investigate

# Investigate and attempt arrests
python main.py investigate --arrest

# Recover resting officers
python main.py police recover

# Show history
python main.py history show

# Save and exit
python main.py save
```

## Project Structure

```
lab1/
├── main.py                 # Main CLI application
├── police/                 # Domain model package
│   ├── __init__.py
│   ├── Police.py          # Police department management
│   ├── Policeman.py       # Police officer class
│   ├── Citizen.py         # Citizen class
│   ├── Crime.py           # Crime class
│   ├── Law.py             # Law/statute class
│   ├── Investigation.py   # Crime investigation logic
│   └── Security.py        # Security level evaluation
├── tests/                  # Unit tests
│   ├── __init__.py
│   └── test_police.py
├── docs/                   # Documentation
│   └── uml/               # UML diagrams (PlantUML)
│       ├── class_diagram.puml
│       ├── state_diagram.puml
│       └── sequence_diagram.puml
├── data/                   # Persistent data storage
├── pyproject.toml         # Project configuration
└── README.md              # This file
```

## Domain Model

### Core Entities

| Entity | Description |
|--------|-------------|
| **Police** | Manages zones and officers |
| **Policeman** | Law enforcement officer (with fatigue and rest mechanics) |
| **Citizen** | Civilian in the system (can be assigned to a zone) |
| **Crime** | Criminal offense record |
| **Law** | Legal statute with severity |
| **Investigation** | Crime analysis process |
| **Security** | Public safety evaluation |

### Operations

1. **Crime Investigation** - Analyze crimes and identify suspects
2. **Public Order Maintenance** - Maintain security through officer deployment
3. **Citizen Interaction** - Accept crime reports from citizens (with zone assignment)
4. **Crime Prevention** - Monitor and respond to security levels per zone
5. **Criminal Arrest** - Apprehend identified criminals (affected by officer fatigue)
6. **Officer Recovery** - Restore exhausted officers to duty

## Testing

Run all unit tests:

```bash
pytest
```

Run with verbose output and coverage report:

```bash
pytest -v --cov=police --cov-report=term-missing
```

**Code Coverage: 92%** (73 tests)

## UML Diagrams

### Class Diagram
Shows the structure and relationships between all system entities.

![Class Diagram](docs/uml/class_diagram.png)

**Source:** `docs/uml/class_diagram.puml`

### State Diagram
Shows the policeman state machine during arrest operations.

![State Diagram](docs/uml/state_diagram.png)

**Source:** `docs/uml/state_diagram.puml`

### Sequence Diagram
Shows the crime investigation process and component interactions.

![Sequence Diagram](docs/uml/sequence_diagram.png)

**Source:** `docs/uml/sequence_diagram.puml`

### Viewing UML Diagrams

Diagrams are created in PlantUML format (.puml). To view or regenerate them:

1. **VS Code**: Install "PlantUML" extension by jebbs
2. **IntelliJ IDEA**: Install "PlantUML Integration" plugin
3. **Online**: Use [PlantText](https://www.planttext.com/)
4. **CLI**: Install PlantUML and run:
   ```bash
   plantuml docs/uml/*.puml
   ```

## CLI Commands Reference

### Citizen Commands
| Command | Description |
|---------|-------------|
| `citizen add <name> [--zone <zone>]` | Add a new citizen (optionally assign to zone) |
| `citizen delete <index>` | Remove a citizen |
| `citizen list` | Show all citizens |

### Police Commands
| Command | Description |
|---------|-------------|
| `police hire <lastname> <zone>` | Hire an officer |
| `police fire <lastname>` | Fire an officer |
| `police add-zone <zone>` | Create a new zone |
| `police list` | Show all officers |
| `police info` | Show zone details with fatigue and rest status |
| `police recover` | Recover all exhausted officers |
| `police relocate <idx...> <zone>` | Move officers to a new zone |

### Crime Commands
| Command | Description |
|---------|-------------|
| `statement add <desc> <zone> <suspect_idx> <law_idx>` | File report |
| `statement delete <index>` | Remove a report |
| `statement list` | Show all reports |

### Investigation Commands
| Command | Description |
|---------|-------------|
| `investigate` | Analyze crimes |
| `investigate --arrest` | Investigate and arrest |

### Law Commands
| Command | Description |
|---------|-------------|
| `law add <article> <severity> <desc>` | Add a law |
| `law list` | Show all laws |

### System Commands
| Command | Description |
|---------|-------------|
| `help`, `?` | Show available commands |
| `history show` | View action history |
| `history clear` | Clear history |
| `save` | Save data |
| `exit`, `quit`, `q` | Save and quit |

## Data Persistence

Data is automatically saved to the `data/` directory in pickle format:

- `police.pkl` - Police department data
- `applications.pkl` - Crime reports
- `history.pkl` - Action history
- `citizens.pkl` - Citizen records
- `laws.pkl` - Legal statutes
- `security.pkl` - Security levels

## Features

- **PEP8 Compliant** - Follows Python style guidelines
- **Type Hints** - Full type annotation throughout
- **Exception Handling** - Custom exception hierarchy
- **CLI Interface** - Both interactive and command-line modes
- **Data Persistence** - State saved between sessions (pickle files)
- **Unit Tests** - 73 tests with 92% coverage
- **UML Documentation** - Class, state, and sequence diagrams (UML 2.x)
- **Per-Zone Security Tracking** - Security levels calculated per zone (citizens/crimes ratio)
- **Fatigue System** - Officer fatigue accumulates after each arrest attempt
  - 🟢 Fresh: fatigue 0-2
  - 🟡 Tired: fatigue 3-5
  - 🔴 Exhausted/⏸️ Resting: fatigue ≥ 6 (officer goes on rest)
- **Recovery Command** - `police recover` to restore exhausted officers
- **Zone Assignment** - Citizens can be assigned to specific zones

## License

This project is created for educational purposes.

## Author

Mukhamedzianau Egor

## Version

0.1.0
