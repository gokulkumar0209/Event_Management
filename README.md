# Event Management API

## Overview
This is a FastAPI-based Event Management System that allows users to create events, register attendees, and manage check-ins.


## Installation

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Step 1: Clone the Repository
```sh
git clone https://github.com/gokulkumar0209/Event_Management.git
cd Event_Management/Event_Management
```

### Step 2: Create a Virtual Environment
```sh
python -m venv env
source env/bin/activate  # On Windows use `env\Scripts\activate`
```

### Step 3: Install Dependencies
```sh
pip install -r requirements.txt
```

## Running the Application

### Step 4: Start FastAPI Server
```sh
uvicorn main:app --reload
```
By default, the server runs at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

### API Documentation
- Interactive Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc Docs: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Running Tests
To run tests using **pytest**, execute:
```sh
pytest
```

## API Endpoints

### Authentication
| Method | Endpoint   | Description  |
|--------|-----------|--------------|
| POST   | `/token`  | Obtain JWT token |

### Events
| Method | Endpoint         | Description  |
|--------|-----------------|--------------|
| POST   | `/events/`       | Create a new event |
| GET    | `/events/`       | List all events |

### Attendees
| Method | Endpoint             | Description  |
|--------|----------------------|--------------|
| POST   | `/attendees/`        | Register an attendee |
| PUT    | `/attendees/{id}/checkin/` | Check-in an attendee |



## Author
[Gokulkumar](https://github.com/gokulkumar0209)

