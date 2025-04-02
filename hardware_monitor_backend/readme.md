# Hardware Health Monitoring System

A Django REST API for monitoring hardware health using machine learning.

## Features

- Real-time hardware metrics collection using psutil
- Anomaly detection with machine learning
- Hardware issue identification and recommendations
- Historical data tracking and visualization
- REST API for integration with other systems

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```
   python manage.py migrate
   ```
4. Create a superuser:
   ```
   python manage.py createsuperuser
   ```
5. Run the server:
   ```
   python manage.py runserver
   ```

## Running the Monitor

Start the hardware monitoring service:

```
python manage.py monitor_hardware --interval 60
```

Options:
- `--interval`: Time in seconds between metric collections (default: 60)
- `--train`: Train a new model before starting monitoring

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/metrics/` | GET | List all system metrics |
| `/api/metrics/latest/` | GET | Get the latest system metrics |
| `/api/metrics/collect/` | POST | Collect and save current system metrics |
| `/api/metrics/statistics/` | GET | Get statistics about system metrics |
| `/api/issues/` | GET | List all hardware issues |
| `/api/issues/unresolved/` | GET | Get all unresolved hardware issues |
| `/api/issues/{id}/resolve/` | POST | Mark an issue as resolved |
| `/api/training/` | GET | List all model training history |
| `/api/training/train/` | POST | Train a new model |
| `/api/training/latest/` | GET | Get the latest model training record |
| `/api/dashboard/` | GET | Get dashboard summary data |
| `/api/health/` | GET | Simple health check endpoint |

## Authentication

All API endpoints except for the health check require authentication.

## License

MIT