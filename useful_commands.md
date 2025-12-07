### Generate and run migration

```bash
  alembic revision --autogenerate -m "First Migration" && alembic upgrade head
```

### Load all fixtures

```bash
  docker exec -it web python3 src/scripts/load_fixtures.py all
```

### Run celery search tasks

```bash
  docker exec -it web celery -A src.product_scrapers.celery.tasks call src.product_scrapers.celery.tasks.run_scraper_searches --args '["olx"]'
```

### Run tests

```bash
  pytest src/tests
```

```bash
  pytest -vv src/tests/app/infrastructure/repositories/test_product_repository.py
```

```bash
  pytest -vv src/tests/app/infrastructure/repositories/test_product_repository.py::test_get_product_by_id
```

```bash
  pytest --cov=src src/tests
```

```bash
  pytest --cov=src --cov-report=html src/tests
```
