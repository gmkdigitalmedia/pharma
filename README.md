# Pharma Application

A Flask-based web application for pharmaceutical data management and analysis.

## Features

- User authentication and authorization
- Dashboard interface
- File upload capabilities
- API endpoints for data access

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with the following variables:
   ```
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///pharma.db
   FLASK_ENV=development
   ```
5. Run the application:
   ```bash
   python app.py
   ```

## Development

The application uses:
- Flask for the web framework
- SQLAlchemy for database ORM
- Flask-Login for user authentication
- Python-dotenv for environment variable management

## License

MIT License 