# TuniFly Backend

A RESTful backend API for tracking, scraping, and monitoring flight data to and from Tunisia. Built with **FastAPI** and **PostgreSQL**, supporting price history tracking, email alert subscriptions, automated flight data scraping, and API rate limiting.

**Website:** [tunifly.me](https://tunifly.onrender.com) - [Frontend repo](https://github.com/WassimSellami/tunifly-frontend)

## Features

- Flight, airline, and airport APIs
- Price history tracking
- Web scraping with Playwright
- Email alerts for price changes
- User and subscription management
- API rate limiting
- Booking URL generation
- Docker support

## Tech Stack

| Layer         | Technology                         |
|---------------|------------------------------------|
| Framework     | FastAPI + Uvicorn                  |
| Database      | PostgreSQL (SQLAlchemy + psycopg2) |
| Scraping      | Playwright, BeautifulSoup4, httpx  |
| Scheduling    | APScheduler                        |
| Notifications | Email alerts (email-validator)     |
| Config        | python-dotenv                      |
| Deployment    | Docker                             |

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL
- Docker (optional)

### Installation

```bash
git clone https://github.com/WassimSellami/tunifly-backend.git
cd TuniFly-backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install
```

### Environment Variables

Create a `.env` file in the root:

```env
DATABASE_URL=
EMAIL_USER=
EMAIL_PASS=
CORS_ORIGINS=
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_HEAVY_ROUTE_REQUESTS=20
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_EXEMPT_PATHS=/docs,/redoc,/openapi.json,/ping
EXCHANGE_RATE_API_KEY=
USE_PREDEFINED_ROUTES=true
SUPABASE_URL=https://your-project.supabase.co
# Required only for legacy Supabase projects that issue HS256 access tokens
SUPABASE_JWT_SECRET=
```

| Variable                     | Description                                        |
|------------------------------|----------------------------------------------------|
| `DATABASE_URL`               | PostgreSQL connection string                      |
| `EMAIL_USER`                 | Email address used to send price alert emails     |
| `EMAIL_PASS`                 | Password or app password for the email account    |
| `CORS_ORIGINS`               | Comma-separated list of allowed frontend origins  |
| `RATE_LIMIT_REQUESTS`        | Default maximum requests allowed per client in each window |
| `RATE_LIMIT_HEAVY_ROUTE_REQUESTS` | Limit for `GET /flights/`, `GET /flights/{flight_id}`, and `GET /price-history/flight/{flight_id}` |
| `RATE_LIMIT_WINDOW_SECONDS`  | Size of the rate-limit window in seconds          |
| `RATE_LIMIT_EXEMPT_PATHS`    | Comma-separated paths excluded from throttling    |
| `EXCHANGE_RATE_API_KEY`      | API key for currency exchange rate lookups        |
| `USE_PREDEFINED_ROUTES`      | Whether to use predefined routes (`true` / `false`) |
| `SUPABASE_URL`               | Supabase project URL used to validate access-token issuer and signing keys |
| `SUPABASE_JWT_SECRET`        | Legacy HS256 JWT secret; leave unset for modern JWKS-backed projects |

By default, the backend allows `60` requests per `60` seconds per client IP on most routes and `20` requests per `60` seconds on `GET /flights/`, `GET /flights/{flight_id}`, and `GET /price-history/flight/{flight_id}`. Successful responses include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers. Rate-limited responses return HTTP `429` with a `Retry-After` header.

### Run

```bash
uvicorn main:app --reload --port 10000
```

Swagger, ReDoc, and the OpenAPI schema endpoints are disabled.

## Docker

```bash
docker build -t tunifly-backend .
docker run -p 10000:10000 --env-file .env tunifly-backend
```

## API Endpoints

| Prefix                  | Description             |
|-------------------------|-------------------------|
| `GET /ping`             | Health check            |
| `/user`                 | User management         |
| `/airline`              | Airline data            |
| `/airport`              | Airport data            |
| `/flight`               | Flight search and listing |
| `/flight-price-history` | Price history per flight |
| `/subscription`         | Email alert subscriptions |
