from agent_work_memory.extractor import extract_candidates


def test_extractor_discards_unverifiable_claims(monkeypatch) -> None:
    import io
    import json
    from urllib.request import urlopen

    payload = {"choices": [{"message": {"content": json.dumps({"memories": [
        {"kind": "decision", "claim": "Use SQLite", "evidence_quote": "We chose SQLite", "confidence": 0.9},
        {"kind": "action", "claim": "Deployed to prod", "evidence_quote": "not present in source", "confidence": 1},
    ]})}}]}
    class Response(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *args): self.close()
    monkeypatch.setattr(urlopen, lambda *args, **kwargs: Response(json.dumps(payload).encode()))
    candidates = extract_candidates("We chose SQLite for the prototype.", base_url="http://localhost:11434/v1", model="test", api_key="local")
    assert len(candidates) == 1
    assert candidates[0].kind == "decision"
    assert candidates[0].evidence_quote == "We chose SQLite"
