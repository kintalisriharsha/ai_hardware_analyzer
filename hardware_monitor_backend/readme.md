# Hardware Health Monitoring System

A comprehensive system for monitoring hardware health metrics with machine learning-based anomaly detection and fan monitoring capabilities.

## Features

- **Real-time Monitoring**: Collect and visualize CPU, memory, disk, and network usage metrics
- **Fan Detection**: Monitor cooling system status using platform-specific techniques
- **Anomaly Detection**: ML-powered detection of unusual hardware behavior
- **System Analysis**: Evaluate hardware capabilities for gaming and development tasks
- **Historical Data**: Track performance trends over time
- **Recommendations**: Receive actionable suggestions for hardware issues

## Backend Setup

The backend is built with Django and Django REST Framework.

### Prerequisites

- Python 3.9+
- PowerShell (Windows) or lm-sensors (Linux)
- Administrator access (for hardware sensor access)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/hardware-health-monitor.git
   cd hardware-health-monitor
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```
   python manage.py makemigrations hardware_api
   python manage.py migrate
   ```

5. Create a superuser (optional):
   ```
   python manage.py createsuperuser
   ```

6. Set up the ML models directory:
   ```
   mkdir ml_models
   ```

### Running the Backend

1. Start the Django development server:
   ```
   python manage.py runserver
   ```

2. For continuous metric collection, run in a separate terminal:
   ```
   python manage.py monitor_hardware --interval 60
   ```

### Fan Detection Setup

For Windows systems:
- No additional setup required as the application uses PowerShell for fan detection
- For best results, run the server with administrator privileges

For Linux systems:
- Install lm-sensors:
  ```
  sudo apt-get install lm-sensors
  sudo sensors-detect --auto
  ```

## Frontend Setup

The frontend is built with React + Vite.

### Prerequisites

- Node.js 14+
- npm or yarn

### Installation

1. Navigate to the frontend directory:
   ```
   cd hardware-monitor-frontend
   ```

2. Install dependencies:
   ```
   npm install
   # or
   yarn
   ```

### Running the Frontend

1. Start the development server:
   ```
   npm run dev
   # or
   yarn dev
   ```

2. Access the application at:
   ```
   http://localhost:3000
   ```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/metrics/` | List all system metrics |
| `/api/metrics/latest/` | Get the latest system metrics |
| `/api/metrics/collect/` | Collect new metrics |
| `/api/metrics/statistics/` | Get metrics statistics |
| `/api/issues/` | List all hardware issues |
| `/api/fans/` | Get cooling fan information |
| `/api/system-info/` | Get detailed system information |
| `/api/dashboard/` | Get dashboard summary |
| `/api/training/train/` | Train the anomaly detection model |

## Troubleshooting

### Fan Detection Issues

- **No fan data**: Run the server with administrative privileges
- **Incorrect fan speeds**: Verify your system exposes fan sensor data
- **Error messages**: Check the server logs for specific error details

### Anomaly Detection Issues

- **Model training fails**: Ensure you have at least 50 metric samples collected
- **False positives**: Retrain the model with more diverse system state samples
- **No anomalies detected**: Adjust thresholds in hardware_monitor.py

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.