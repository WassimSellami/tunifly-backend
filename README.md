# TuniFly Backend

A RESTful backend API for tracking, scraping, and monitoring flight data to and from Tunisia. Built with **FastAPI** and **PostgreSQL**, supporting price history tracking, email alert subscriptions, and automated flight data scraping.

## Features

- **Flight & Airline & Airport APIs** – Query flights, airlines, and airports
- **Price History Tracking** – Monitor how flight prices evolve over time
- **Web Scraping** – Automated scraper using Playwright to collect real-time flight data
- **Email Alerts** – Notify subscribed users when prices change
- **User & Subscription Management** – Register users and manage price alert subscriptions
- **Booking URL Generation** – Generate direct booking links for flights
- **Docker Support** – Fully containerized using a Playwright-compatible image

## Tech Stack

| Layer         | Technology                              |
|---------------|-----------------------------------------|
| Framework     | FastAPI + Uvicorn                       |
| Database      | PostgreSQL (SQLAlchemy + psycopg2)      |
| Scraping      | Playwright, BeautifulSoup4, httpx       |
| Scheduling    | APScheduler                             |
| Notifications | Email alerts (email-validator)          |
| Config        | python-dotenv                           |
| Deployment    | Docker                                  |

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL
- Docker (optional)

### Installation

```bash
git clone https://github.com/WassimSellami/tunisia-flights-backend.git
cd tunisia-flights-backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install
```

### Environment Variables

Create a `.env` file in the root:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/tunisia_flights
CORS_ORIGINS=http://localhost:3000
```

### Run

```bash
uvicorn main:app --reload --port 10000
```

Swagger docs available at `http://localhost:10000/docs`.

## Docker

```bash
docker build -t tunisia-flights-backend .
docker run -p 10000:10000 --env-file .env tunisia-flights-backend
```

## API Endpoints

| Prefix                  | Description                  |
|-------------------------|------------------------------|
| `GET /ping`             | Health check                 |
| `/user`                 | User management              |
| `/airline`              | Airline data                 |
| `/airport`              | Airport data                 |
| `/flight`               | Flight search & listing      |
| `/flight-price-history` | Price history per flight     |
| `/subscription`         | Email alert subscriptions    |
| `/scraper`              | Trigger scraping jobs        |
