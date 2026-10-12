
## Testing Workflow

Lumio uses `pytest` for modular, automated testing of the implemented pipeline stages.

### Run Tests

Run the complete test suite:

```bash
pytest
```

Run tests for a specific stage:

```bash
pytest tests/test_chunking.py -v
pytest tests/test_data_sources.py -v
pytest tests/test_retrieval_pipeline.py -v
pytest tests/test_retrieval.py -v
pytest tests/test_grading.py -v
pytest tests/test_generation_verification.py -v
pytest tests/test_graph_and_api.py -v
```

### Test Organization

- **`tests/`** — Modular pytest tests for individual pipeline stages, isolated behavior, edge cases, and regression checks. These tests are intended to run automatically and provide fast feedback after code changes.
- **`verify/`** — Broader validation scripts for checking integrated pipeline behavior, often using real documentation data and retrieval components.

Use `tests/` for routine development and regression testing. Use `verify/` for broader manual validation of pipeline behavior.

### Current Coverage

The implemented pipeline stages covered by the test suite include:

- Data sources and document chunking
- Retrieval pipeline and hybrid retrieval
- Query understanding and routing
- Document grading and retry handling
- Migration decomposition
- Answer generation and verification
- Graph orchestration and conditional routing

The API layer is not yet implemented and will be tested after its implementation.

