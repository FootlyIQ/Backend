# 🔙 FootlyIQ Backend (Flask API)

FootlyIQ Backend is built using Flask (Python) and serves as the core API layer for the FootlyIQ platform. It handles communication between the frontend, microservices, Firebase (Firestore), AWS S3 data lake, and external football APIs. The backend exposes REST endpoints to retrieve live match data, player stats, machine learning insights (like xG and pass clustering), and betting odds. It also processes and aggregates data from the Fantasy Premier League API via a custom home-server proxy.

## 🛠️Tech Highlights:
- Python + Flask REST API
- Firebase Firestore for real-time structured data
- AWS S3 (Bronze/Silver/Gold zones) for ML datasets using boto3, DuckDB, and pandas
- Integrated with Express microservices (Match & Odds) & home-server  proxy
- Unit tests for matches, teams, API handlers and database operations

## Full overview
For full documentation please visit our organization page at https://github.com/FootlyIQ
