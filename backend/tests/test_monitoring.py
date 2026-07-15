"""
Phase 2 endpoint tests. Since there's no live Prometheus/Kubernetes/Jenkins
in the test environment, these assert the *contract* - correct status
codes, correct shape, and graceful degradation (available=False /
connected=False) - rather than real metric values.
"""


def test_metric_requires_auth(client):
    response = client.get("/api/v1/metrics/cpu")
    assert response.status_code == 401


def test_metric_unknown_name_returns_404(client, auth_headers):
    response = client.get("/api/v1/metrics/not-a-real-metric", headers=auth_headers)
    assert response.status_code == 404


def test_metric_cpu_degrades_gracefully_without_prometheus(client, auth_headers):
    response = client.get("/api/v1/metrics/cpu", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["metric"] == "cpu"
    assert body["unit"] == "%"
    # No Prometheus running in tests, so the value should be unavailable rather than crash
    assert body["available"] is False
    assert body["value"] is None


def test_metric_history_shape(client, auth_headers):
    response = client.get("/api/v1/metrics/history/cpu?hours=1", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []  # no Prometheus in test env


def test_metric_history_supports_all_six_metrics(client, auth_headers):
    for metric_name in ["cpu", "memory", "disk", "network", "load", "filesystem"]:
        response = client.get(f"/api/v1/metrics/history/{metric_name}?hours=1", headers=auth_headers)
        assert response.status_code == 200, f"{metric_name} history should be supported"
        assert response.json() == []  # no Prometheus in test env, but no 404 either


def test_metric_history_rejects_unsupported_metric(client, auth_headers):
    response = client.get("/api/v1/metrics/history/not-a-real-metric", headers=auth_headers)
    assert response.status_code == 404


def test_kubernetes_pods_degrades_gracefully(client, auth_headers):
    response = client.get("/api/v1/kubernetes/pods", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is False
    assert body["items"] == []


def test_cluster_health_shape(client, auth_headers):
    response = client.get("/api/v1/cluster/health", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {
        "cluster",
        "nodes",
        "pods",
        "deployments",
        "cpu_usage",
        "memory_usage",
        "disk_usage",
    }


def test_jenkins_jobs_not_configured(client, auth_headers):
    response = client.get("/api/v1/jenkins/jobs", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["configured"] is False
    assert body["items"] == []


def test_alerts_list_empty_by_default(client, auth_headers):
    response = client.get("/api/v1/alerts", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_alerts_active_requires_auth(client):
    response = client.get("/api/v1/alerts/active")
    assert response.status_code == 401


def test_alertmanager_webhook_creates_alert(client, auth_headers):
    payload = {
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "HighCPUUsage", "severity": "critical"},
                "annotations": {"description": "CPU usage is over 90%."},
            }
        ]
    }
    response = client.post("/api/v1/alerts/webhook", json=payload)
    assert response.status_code == 200
    assert response.json()["alerts_raised"] == 1

    active = client.get("/api/v1/alerts/active", headers=auth_headers)
    assert active.status_code == 200
    assert len(active.json()) == 1
    assert active.json()[0]["title"] == "HighCPUUsage"


def test_alertmanager_webhook_resolves_alert(client, auth_headers):
    firing = {
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "HighMemoryUsage", "severity": "critical"},
                "annotations": {"description": "Memory usage is over 90%."},
            }
        ]
    }
    client.post("/api/v1/alerts/webhook", json=firing)

    resolved = {
        "alerts": [
            {
                "status": "resolved",
                "labels": {"alertname": "HighMemoryUsage", "severity": "critical"},
                "annotations": {},
            }
        ]
    }
    response = client.post("/api/v1/alerts/webhook", json=resolved)
    assert response.status_code == 200

    active = client.get("/api/v1/alerts/active", headers=auth_headers)
    assert active.json() == []


def _fire_alert(client, alertname="HighCPUUsage", severity="critical"):
    payload = {
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": alertname, "severity": severity},
                "annotations": {"description": "synthetic test alert"},
            }
        ]
    }
    client.post("/api/v1/alerts/webhook", json=payload)
    return client  # convenience for chaining in tests


def test_acknowledge_alert_lifecycle(client, auth_headers):
    _fire_alert(client)
    alert_id = client.get("/api/v1/alerts/active", headers=auth_headers).json()[0]["id"]

    ack = client.post(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        json={"acknowledged_by": "oncall@example.com"},
        headers=auth_headers,
    )
    assert ack.status_code == 200
    body = ack.json()
    assert body["status"] == "acknowledged"
    assert body["acknowledged_by"] == "oncall@example.com"
    assert body["resolved"] is False  # acknowledged is still open, not resolved

    # still shows up under /active since acknowledged is an open state
    active = client.get("/api/v1/alerts/active", headers=auth_headers)
    assert len(active.json()) == 1
    assert active.json()[0]["status"] == "acknowledged"


def test_resolve_alert_endpoint(client, auth_headers):
    _fire_alert(client)
    alert_id = client.get("/api/v1/alerts/active", headers=auth_headers).json()[0]["id"]

    resolved = client.post(f"/api/v1/alerts/{alert_id}/resolve", headers=auth_headers)
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["resolved"] is True

    active = client.get("/api/v1/alerts/active", headers=auth_headers)
    assert active.json() == []


def test_acknowledge_nonexistent_alert_404s(client, auth_headers):
    response = client.post("/api/v1/alerts/9999/acknowledge", json={}, headers=auth_headers)
    assert response.status_code == 404


def test_viewer_cannot_acknowledge(client, auth_headers):
    _fire_alert(client)
    alert_id = client.get("/api/v1/alerts/active", headers=auth_headers).json()[0]["id"]
    # auth_headers fixture is a "viewer" role - acknowledge requires devops_or_admin
    response = client.post(f"/api/v1/alerts/{alert_id}/acknowledge", json={}, headers=auth_headers)
    assert response.status_code == 403


def test_alert_search_filters(client, auth_headers):
    _fire_alert(client, alertname="HighCPUUsage", severity="critical")
    _fire_alert(client, alertname="LowDiskSpace", severity="warning")

    by_severity = client.get("/api/v1/alerts?severity=warning", headers=auth_headers)
    assert by_severity.status_code == 200
    assert len(by_severity.json()) == 1
    assert by_severity.json()[0]["title"] == "LowDiskSpace"

    by_source = client.get("/api/v1/alerts?source=alertmanager", headers=auth_headers)
    assert len(by_source.json()) == 2

    by_resolved = client.get("/api/v1/alerts?resolved=false", headers=auth_headers)
    assert len(by_resolved.json()) == 2


def test_alert_dashboard_summary(client, auth_headers):
    _fire_alert(client, alertname="CriticalOne", severity="critical")
    _fire_alert(client, alertname="WarningOne", severity="warning")

    response = client.get("/api/v1/alerts/dashboard", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["active_alerts"] == 2
    assert body["critical"] == 1
    assert body["warning"] == 1
    assert body["resolved_today"] == 0


def test_alert_stats(client, auth_headers):
    _fire_alert(client, alertname="StatsAlertOne", severity="critical")
    alert_id = client.get("/api/v1/alerts/active", headers=auth_headers).json()[0]["id"]
    client.post(f"/api/v1/alerts/{alert_id}/resolve", headers=auth_headers)

    response = client.get("/api/v1/alerts/stats", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["active"] == 0
    assert body["resolved"] == 1
    assert body["critical"] == 1


# --- Incidents ---------------------------------------------------------


def test_create_incident_requires_devops_or_admin(client, auth_headers):
    response = client.post(
        "/api/v1/incidents",
        json={"title": "Manual incident", "severity": "high", "description": "test"},
        headers=auth_headers,  # viewer role
    )
    assert response.status_code == 403


def test_admin_can_create_incident(client, admin_headers):
    response = client.post(
        "/api/v1/incidents",
        json={"title": "Manual incident", "severity": "high", "description": "test"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Manual incident"
    assert body["status"] == "open"
    assert body["alert_id"] is None


def test_promote_alert_to_incident(client, auth_headers, admin_headers):
    _fire_alert(client, alertname="PromoteMe", severity="critical")
    alert_id = client.get("/api/v1/alerts/active", headers=auth_headers).json()[0]["id"]

    response = client.post(f"/api/v1/incidents/from-alert/{alert_id}", headers=admin_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["alert_id"] == alert_id
    assert body["title"] == "PromoteMe"
    assert body["status"] == "open"

    # promoting the same alert again is idempotent - returns the same incident
    again = client.post(f"/api/v1/incidents/from-alert/{alert_id}", headers=admin_headers)
    assert again.status_code == 201
    assert again.json()["id"] == body["id"]


def test_promote_nonexistent_alert_404s(client, admin_headers):
    response = client.post("/api/v1/incidents/from-alert/9999", headers=admin_headers)
    assert response.status_code == 404


def test_incident_list_requires_auth(client):
    response = client.get("/api/v1/incidents")
    assert response.status_code == 401


def test_incident_status_lifecycle(client, admin_headers):
    created = client.post(
        "/api/v1/incidents",
        json={"title": "Lifecycle test", "severity": "medium"},
        headers=admin_headers,
    )
    incident_id = created.json()["id"]

    ack = client.patch(
        f"/api/v1/incidents/{incident_id}", json={"status": "acknowledged"}, headers=admin_headers
    )
    assert ack.status_code == 200
    assert ack.json()["status"] == "acknowledged"

    resolved = client.patch(
        f"/api/v1/incidents/{incident_id}", json={"status": "resolved"}, headers=admin_headers
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"


def test_incident_update_invalid_status(client, admin_headers):
    created = client.post(
        "/api/v1/incidents", json={"title": "Bad status test"}, headers=admin_headers
    )
    incident_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/incidents/{incident_id}",
        json={"status": "not-a-real-status"},
        headers=admin_headers,
    )
    assert response.status_code == 400


def test_incident_filter_by_status(client, admin_headers):
    client.post("/api/v1/incidents", json={"title": "Open one"}, headers=admin_headers)
    second = client.post("/api/v1/incidents", json={"title": "Resolved one"}, headers=admin_headers)
    client.patch(
        f"/api/v1/incidents/{second.json()['id']}",
        json={"status": "resolved"},
        headers=admin_headers,
    )

    open_only = client.get("/api/v1/incidents?status=open", headers=admin_headers)
    assert len(open_only.json()) == 1
    assert open_only.json()[0]["title"] == "Open one"
