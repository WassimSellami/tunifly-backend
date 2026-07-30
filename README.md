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

## Tunisair fare-calendar endpoints

The Tunisair scraper obtains fare calendars from market-specific endpoints:

| Market | Endpoint |
|--------|----------|
| Germany | `https://flights.tunisair.com/en-de/prices/per-day` |
| Belgium | `https://flights.tunisair.com/en-be/prices/per-day` |
| Tunisia | `https://flights.tunisair.com/en-tn/prices/per-day` |

The Germany and Belgium endpoints (`TUNISAIR_BASE_URL_DE` and
`TUNISAIR_BASE_URL_BE`) were identified by inspecting the browser network calls
made by Tunisair booking pages, such as
`https://flights.tunisair.com/fr-tn/TUN-MUC`, and by testing other destination
pages. They are not a documented public API.

Each endpoint accepts fare-calendar query parameters such as:

```text
?date=YYYY-MM-DD&from=AAA&to=BBB&tripDuration=0&tripType=O
```

### Currency and price conversion

The scraper keeps both the fare as returned by the airline (`price`) and a
normalized EUR value (`priceEur`) used for comparisons, price history, ordering,
and email-alert thresholds.

| Source | Native fare currency | `priceEur` handling |
|--------|----------------------|---------------------|
| Nouvelair | EUR | Stored unchanged |
| Tunisair, Germany/Belgium to Tunisia | EUR | Stored unchanged |
| Tunisair, Tunisia to Germany/Belgium | TND | Converted to EUR by the backend |

For Tunisia-origin Tunisair routes, the fare calendar returns TND. The backend
multiplies that amount by the TND-to-EUR rate returned by ExchangeRate-API; it
uses `0.29` as a fallback when the provider is unavailable. This is an external
EUR-equivalent calculation, not a conversion calculated or guaranteed by
Tunisair, so the final airline checkout price can differ.

## Nouvelair availability endpoint

Nouvelair flight availability is retrieved from:

```text
https://webapi.nouvelair.com/api/reservation/availability
```

The endpoint requires a temporary `x-api-key`. The scraper opens
`https://www.nouvelair.com/` in a headless browser and captures that header from
one of the website's own API requests before querying availability. The key is
not hard-coded and may expire between scraper runs.

The availability request uses parameters such as:

```text
?departure_code=FRA&destination_code=TUN&trip_type=1&currency_id=2
```

The scraper requests Nouvelair's EUR currency setting (`currency_id=2`). It
therefore stores each returned fare unchanged in both `price` and `priceEur`.

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
RATE_LIMIT_EXEMPT_PATHS=/docs,/redoc,/openapi.json
# Comma-separated proxy IPs/networks trusted to supply X-Forwarded-For.
# Do not use * when the app can be reached directly from the internet.
FORWARDED_ALLOW_IPS=10.0.0.0/8
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
| `FORWARDED_ALLOW_IPS`        | Comma-separated trusted proxy IPs or CIDR networks allowed to provide forwarded client IPs |
| `EXCHANGE_RATE_API_KEY`      | API key for currency exchange rate lookups        |
| `USE_PREDEFINED_ROUTES`      | Whether to use predefined routes (`true` / `false`) |
| `SUPABASE_URL`               | Supabase project URL used to validate access-token issuer and signing keys |
| `SUPABASE_JWT_SECRET`        | Legacy HS256 JWT secret; leave unset for modern JWKS-backed projects |

By default, the backend allows `60` requests per `60` seconds per client IP on most routes, including `GET /ping`, and `20` requests per `60` seconds on `GET /flights/`, `GET /flights/{flight_id}`, and `GET /price-history/flight/{flight_id}`. Successful responses include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers. Rate-limited responses return HTTP `429` with a `Retry-After` header.

When the service is behind a reverse proxy, Uvicorn uses `X-Forwarded-For` only when the immediate proxy's address is included in `FORWARDED_ALLOW_IPS`. Set this to the actual proxy addresses or private network ranges used by your platform. Never set it to `*` if clients can connect directly to the service, because they could spoof their IP address and evade rate limiting.

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
