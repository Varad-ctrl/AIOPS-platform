"""
Log and AI endpoint tests. There's no live Loki/LLM provider in the test
environment, so these assert graceful degradation (available=False, empty
results, no 500s) and response-schema correctness rather than real output.
"""


def test_logs_recent_requires_auth(client):
    response = client.get("/api/v1/logs/recent")
    assert response.status_code == 401


def test_logs_root_alias_degrades_gracefully(client, auth_headers):
    response = client.get("/api/v1/logs", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["items"] == []


def test_logs_recent_degrades_gracefully_without_loki(client, auth_headers):
    response = client.get("/api/v1/logs/recent", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["count"] == 0
    assert body["items"] == []


def test_logs_search_degrades_gracefully(client, auth_headers):
    response = client.get(
        "/api/v1/logs/search?query=error&namespace=production", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["available"] is False


def test_logs_for_pod_degrades_gracefully(client, auth_headers):
    response = client.get("/api/v1/logs/pods/nginx-abc123", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["items"] == []


def test_logs_for_container_degrades_gracefully(client, auth_headers):
    response = client.get("/api/v1/logs/containers/aiops-backend", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["available"] is False


def test_logs_errors_only_degrades_gracefully(client, auth_headers):
    response = client.get("/api/v1/logs/errors", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["available"] is False


def test_logs_label_values_degrades_gracefully(client, auth_headers):
    response = client.get("/api/v1/logs/labels/container", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["values"] == []


def test_ai_chat_requires_auth(client):
    response = client.post("/api/v1/ai/chat", json={"question": "why is cpu high?"})
    assert response.status_code == 401


def test_ai_chat_degrades_gracefully_without_llm_key(client, auth_headers):
    response = client.post(
        "/api/v1/ai/chat", json={"question": "why is cpu high?"}, headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert "LLM_API_KEY" in body["answer"] or "OPENAI_API_KEY" in body["answer"]


def test_ai_query_alias_still_works(client, auth_headers):
    response = client.post(
        "/api/v1/ai/query", json={"question": "still works?"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["available"] is False


def test_ai_chat_persists_to_history(client, auth_headers):
    client.post("/api/v1/ai/chat", json={"question": "first question"}, headers=auth_headers)
    client.post("/api/v1/ai/chat", json={"question": "second question"}, headers=auth_headers)

    history = client.get("/api/v1/ai/chat/history", headers=auth_headers)
    assert history.status_code == 200
    body = history.json()
    assert len(body) == 4  # 2 user + 2 assistant fallback replies, oldest first
    assert body[0]["role"] == "user"
    assert body[0]["message"] == "first question"
    assert body[2]["message"] == "second question"


def test_ai_log_summary_degrades_gracefully(client, auth_headers):
    response = client.get("/api/v1/ai/logs/summary", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["log_count"] == 0


def test_ai_log_anomalies_degrades_gracefully(client, auth_headers):
    response = client.get("/api/v1/ai/logs/anomalies", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["available"] is False


def test_ai_log_analysis_combined_endpoint(client, auth_headers):
    response = client.post("/api/v1/ai/log-analysis", json={}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert "summary" in body and "findings" in body


def test_ai_root_cause_freeform(client, auth_headers):
    response = client.post(
        "/api/v1/ai/root-cause",
        json={"description": "why is nginx restarting?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["confidence"] == "low"
    assert body["evidence"] == []
    assert body["incident_id"] is None


def test_ai_root_cause_for_missing_incident(client, auth_headers):
    response = client.post(
        "/api/v1/ai/root-cause", json={"incident_id": 9999}, headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["incident_id"] == 9999
    assert "not found" in body["root_cause"].lower()


def test_ai_root_cause_for_real_incident_backcompat_route(client, admin_headers):
    created = client.post(
        "/api/v1/incidents",
        json={"title": "Test incident for RCA", "severity": "high"},
        headers=admin_headers,
    )
    incident_id = created.json()["id"]

    response = client.post(
        f"/api/v1/ai/incidents/{incident_id}/root-cause", headers=admin_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["incident_id"] == incident_id
    assert body["available"] is False  # no LLM key in test env


def test_ai_incident_summary_for_missing_incident(client, auth_headers):
    response = client.post(
        "/api/v1/ai/incident-summary", json={"incident_id": 9999}, headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert "not found" in body["summary"].lower()


def test_ai_recommendations_degrades_gracefully(client, auth_headers):
    response = client.post("/api/v1/ai/recommendations", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert "LLM_API_KEY" in body["recommendations"] or "OPENAI_API_KEY" in body["recommendations"]
