# py_uds_demo

## Overview
`py_uds_demo` is a Python package for learning and practicing the Unified Diagnostic Services (UDS) protocol. It provides a simulator with CLI, GUI, and Web interfaces, allowing users to send diagnostic requests and view responses as per ISO 14229.

### Features
- UDS protocol simulation (ISO 14229)
- CLI, GUI (CustomTkinter), and Web (Gradio) interfaces
- Diagnostic session management, data transmission, input/output control, and more
- Extensible and modular codebase

---

## Installation

### Requirements
- Python 3.10–3.14
- Windows OS (recommended)

### Install via pip
```sh
pip install git+https://github.com/chaitu-ycr/py_uds_demo.git
```

---

## How to Use

### CLI Mode
```sh
python -m py_uds_demo --mode cli
```
Enter diagnostic requests in hex (e.g., `22 F1 87`). Type `help` for instructions.

### GUI Mode
```sh
python -m py_uds_demo --mode gui
```
Launches a graphical interface for sending requests.

### Web Mode
```sh
python -m py_uds_demo --mode web
```
Opens a Gradio web app at `http://<your-host>:7865`.

---

## Documentation

- **User Guide:** See [docs/index.md](docs/index.md) for a full guide.
- **API Reference:** See [docs/src_manual.md](docs/src_manual.md) for module/class documentation.
- **Source Code:** Main package is in `src/py_uds_demo/`.

### Main Components
- `core/`: UDS client/server logic
- `interface/`: CLI, GUI, and Web interfaces
- `core/utils/`: Helpers, responses, and UDS services

### Testing
Run all tests:
```sh
uv run pytest
```
Test reports are in `tests/report/`.

---

## License
MIT License. See [LICENSE](LICENSE).
