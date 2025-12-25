# Price Monitoring System

This project offers a solution for automated price monitoring and product data collection on online shopping sites such as OLX, Mercado Livre, Enjoei and Estante Virtual. It allows users to track price variations, identify market trends and make informed decisions about purchases, sales or pricing strategies. The system is valuable for anyone interested in data collection automation, as it centralizes and organizes information from multiple sources in a single robust backend, with asynchronous tasks and a modern API interface.

### Features

- **Product Management**: Add, edit, and remove products.
- **Price History**: View the price history of collected products.
- **Search Settings**: Define parameters for data collection.
- **Authentication**: Manage users and authentication.

## System Structure

- **API Backend**: Manages products, search settings, and users.
- **Scrapers Module**: Collects product data from external sites.
- **Database**: Stores information about products, users, price history, and settings.
- **Celery**: Manages asynchronous and scheduled tasks.

## Installing and running the Project

### Install Docker

1. Clone the repository
   ```bash
   git clone git@github.com:pattersonrptr/product_tracker_backend.git
   ```
   cd product_tracker_backend
2. Make sure you have Docker and Docker Compose installed. Follow the instructions on the [Docker website](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) to install Docker.
3. Build and start the containers:
   ```bash
   docker compose up --build
   ```

### Accessing the API

1. Access the API at http://localhost:8000/docs for the Swagger UI or http://localhost:8000/redoc for the ReDoc documentation.
   - You will be able to see the available endpoints and test them directly from the browser.
   - **Default superuser credentials** (created automatically on first run):
     - Username: `admin`
     - Password: `admin`
   - Authenticate using the `/auth/login` endpoint to obtain a token. Once you have the token, you can use it to access the other endpoints by including it in the `Authorization` header as a Bearer token (set the auth token in the `Authorize` button in the Swagger UI).
2. **(Optional)**. You can run **load_fixtures.py** to populate the database with initial testing data:
   ```bash
   docker exec -it web python3 src/scripts/load_fixtures.py all
   ```
3. **(Optional)**. If you want to test running the scrapers manually, you can execute the following commands to start the scrapers:
   ```bash
   docker exec -it web celery -A src.product_scrapers.celery.tasks call src.product_scrapers.celery.tasks.run_scraper_search --args '["3"]'
   ```
   This example runs a scraper for the search setting with ID 3. You can change the ID to run other scrapers.

## Run tests

### Unit/Integration Tests (pytest)

To run the tests, you can use the following commands:

Run all the tests.

```bash
  pytest src/tests
```

Run tests for a specific module.

```bash
  pytest -vv src/tests/app/infrastructure/repositories/test_product_repository.py
```

Run tests for a specific function.

```bash
  pytest -vv src/tests/app/infrastructure/repositories/test_product_repository.py::test_get_product_by_id
```

Run tests with coverage.

```bash
  pytest --cov=src src/tests
```

or to generate an HTML report:

```bash
  pytest --cov=src --cov-report=html src/tests
```

### API Smoke Tests (bash scripts)

Quick bash scripts for testing endpoints during development:

```bash
# Test auth endpoints
./src/scripts/api_tests/test_auth.sh

# Test with custom credentials
./src/scripts/api_tests/test_auth.sh myuser mypassword

# Run all API tests
./src/scripts/api_tests/run_all_tests.sh
```

See [src/scripts/api_tests/README.md](src/scripts/api_tests/README.md) for more details.
