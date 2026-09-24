import json
from pathlib import Path

def test_sample_query_dataset_exists_and_has_questions():
    path=Path(__file__).resolve().parents[1]/"data"/"sample_queries.json"
    data=json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data,list)
    assert data
    assert all(isinstance(item,dict) for item in data)
    assert all(any(k in item for k in ("question","query")) for item in data)
