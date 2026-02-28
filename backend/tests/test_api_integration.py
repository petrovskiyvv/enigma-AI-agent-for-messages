"""
Интеграционные тесты: все API-маршруты через FastAPI TestClient

Тесты проверяют полный стек: HTTP → router → service → store.
Store подменяется на изолированный (через фикстуры из conftest.py),
поэтому тесты не трогают production tickets.json.

Покрытие маршрутов:
  GET  /health
  GET  /api/tickets
  GET  /api/tickets?status=&tone=&category=&search=
  GET  /api/tickets/{id}
  POST /api/tickets
  PATCH /api/tickets/{id}
  POST /api/analyze
  GET  /api/stats
  GET  /api/export/csv
"""

import csv
import io


# ═══════════════════════════════════════════
# Health
# ═══════════════════════════════════════════

class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_returns_version(self, client):
        r = client.get("/health")
        assert "version" in r.json()


# ═══════════════════════════════════════════
# GET /api/tickets
# ═══════════════════════════════════════════

class TestListTickets:
    def test_returns_200(self, client_with_data):
        r = client_with_data.get("/api/tickets")
        assert r.status_code == 200

    def test_returns_list(self, client_with_data):
        r = client_with_data.get("/api/tickets")
        assert isinstance(r.json(), list)

    def test_returns_all_three(self, client_with_data):
        r = client_with_data.get("/api/tickets")
        assert len(r.json()) == 3

    def test_empty_store_returns_empty_list(self, client):
        r = client.get("/api/tickets")
        assert r.json() == []

    def test_filter_by_status(self, client_with_data):
        r = client_with_data.get("/api/tickets?status=Новое")
        data = r.json()
        assert len(data) == 1
        assert data[0]["status"] == "Новое"

    def test_filter_by_tone(self, client_with_data):
        r = client_with_data.get("/api/tickets?tone=Негатив")
        data = r.json()
        assert len(data) == 1
        assert data[0]["emotional_tone"] == "Негатив"

    def test_filter_by_category(self, client_with_data):
        r = client_with_data.get("/api/tickets?category=Документация")
        assert len(r.json()) == 1

    def test_search_by_name(self, client_with_data):
        r = client_with_data.get("/api/tickets?search=петрова")
        data = r.json()
        assert len(data) == 1
        assert "петрова" in data[0]["full_name"]

    def test_combined_filters(self, client_with_data):
        r = client_with_data.get("/api/tickets?status=Новое&category=Неисправность")
        assert len(r.json()) == 1

    def test_no_match_returns_empty(self, client_with_data):
        r = client_with_data.get("/api/tickets?status=НесуществующийСтатус")
        assert r.json() == []


# ═══════════════════════════════════════════
# GET /api/tickets/{id}
# ═══════════════════════════════════════════

class TestGetTicket:
    def test_returns_200_for_existing(self, client_with_data):
        all_t = client_with_data.get("/api/tickets").json()
        tid = all_t[0]["id"]
        r = client_with_data.get(f"/api/tickets/{tid}")
        assert r.status_code == 200

    def test_returns_correct_ticket(self, client_with_data):
        all_t = client_with_data.get("/api/tickets").json()
        tid = all_t[0]["id"]
        r = client_with_data.get(f"/api/tickets/{tid}")
        assert r.json()["id"] == tid

    def test_returns_404_for_missing(self, client):
        r = client.get("/api/tickets/9999")
        assert r.status_code == 404

    def test_404_detail_message(self, client):
        r = client.get("/api/tickets/9999")
        assert "не найден" in r.json()["detail"]


# ═══════════════════════════════════════════
# POST /api/tickets
# ═══════════════════════════════════════════

class TestCreateTicket:
    def test_returns_201(self, client):
        r = client.post("/api/tickets", json={"original_text": "Тест"})
        assert r.status_code == 201

    def test_ticket_has_id(self, client):
        r = client.post("/api/tickets", json={})
        assert "id" in r.json()

    def test_ticket_has_created_at(self, client):
        r = client.post("/api/tickets", json={})
        assert "created_at" in r.json()

    def test_status_is_new(self, client):
        r = client.post("/api/tickets", json={})
        assert r.json()["status"] == "Новое"

    def test_text_triggers_analysis(self, client):
        r = client.post("/api/tickets", json={"original_text": "Срочно! Авария на линии."})
        data = r.json()
        assert data["emotional_tone"] == "Негатив"
        assert data["category"] == "Неисправность"

    def test_fields_saved(self, client):
        r = client.post("/api/tickets", json={
            "full_name": "Иванов Иван",
            "facility": "Завод",
            "email": "ivan@test.ru",
        })
        data = r.json()
        assert data["full_name"] == "Иванов Иван"
        assert data["email"] == "ivan@test.ru"

    def test_empty_text_defaults(self, client):
        r = client.post("/api/tickets", json={"original_text": ""})
        data = r.json()
        assert data["emotional_tone"] == "Нейтрально"
        assert data["ai_response"] == ""

    def test_ticket_appears_in_list(self, client):
        client.post("/api/tickets", json={"full_name": "Новый клиент"})
        all_t = client.get("/api/tickets").json()
        names = [t["full_name"] for t in all_t]
        assert "Новый клиент" in names

    def test_invalid_json_returns_422(self, client):
        r = client.post("/api/tickets", content=b"not json",
                        headers={"Content-Type": "application/json"})
        assert r.status_code == 422


# ═══════════════════════════════════════════
# PATCH /api/tickets/{id}
# ═══════════════════════════════════════════

class TestUpdateTicket:
    def _create_ticket(self, client):
        r = client.post("/api/tickets", json={"full_name": "Для обновления"})
        return r.json()["id"]

    def test_returns_200(self, client):
        tid = self._create_ticket(client)
        r = client.patch(f"/api/tickets/{tid}", json={"status": "В работе"})
        assert r.status_code == 200

    def test_status_updated(self, client):
        tid = self._create_ticket(client)
        r = client.patch(f"/api/tickets/{tid}", json={"status": "Закрыто"})
        assert r.json()["status"] == "Закрыто"

    def test_ai_response_updated(self, client):
        tid = self._create_ticket(client)
        r = client.patch(f"/api/tickets/{tid}", json={"ai_response": "Новый ответ"})
        assert r.json()["ai_response"] == "Новый ответ"

    def test_other_fields_unchanged(self, client):
        tid = self._create_ticket(client)
        client.patch(f"/api/tickets/{tid}", json={"status": "Закрыто"})
        r = client.get(f"/api/tickets/{tid}")
        assert r.json()["full_name"] == "Для обновления"

    def test_404_for_missing(self, client):
        r = client.patch("/api/tickets/9999", json={"status": "Закрыто"})
        assert r.status_code == 404

    def test_partial_update_empty_body(self, client):
        tid = self._create_ticket(client)
        r = client.patch(f"/api/tickets/{tid}", json={})
        assert r.status_code == 200


# ═══════════════════════════════════════════
# POST /api/analyze
# ═══════════════════════════════════════════

class TestAnalyze:
    SAMPLE = (
        "Добрый день! Прибор не работает, срочно! "
        "Зав. номер: НК-001. "
        "Тел: +7 (999) 123-45-67. "
        "С уважением, Иванов Иван Иванович"
    )

    def test_returns_200(self, client):
        r = client.post("/api/analyze", json={"text": self.SAMPLE})
        assert r.status_code == 200

    def test_ticket_created(self, client):
        client.post("/api/analyze", json={"text": self.SAMPLE})
        tickets = client.get("/api/tickets").json()
        assert len(tickets) == 1

    def test_tone_detected(self, client):
        r = client.post("/api/analyze", json={"text": self.SAMPLE})
        assert r.json()["emotional_tone"] == "Негатив"

    def test_category_detected(self, client):
        r = client.post("/api/analyze", json={"text": self.SAMPLE})
        assert r.json()["category"] == "Неисправность"

    def test_phone_extracted(self, client):
        r = client.post("/api/analyze", json={"text": self.SAMPLE})
        assert "999" in r.json()["phone"]

    def test_name_extracted(self, client):
        r = client.post("/api/analyze", json={"text": self.SAMPLE})
        assert "Иванов" in r.json()["full_name"]

    def test_ai_response_generated(self, client):
        r = client.post("/api/analyze", json={"text": self.SAMPLE})
        assert r.json()["ai_response"] != ""

    def test_status_is_new(self, client):
        r = client.post("/api/analyze", json={"text": self.SAMPLE})
        assert r.json()["status"] == "Новое"

    def test_missing_text_returns_422(self, client):
        r = client.post("/api/analyze", json={})
        assert r.status_code == 422

    def test_positive_text(self, client):
        r = client.post("/api/analyze", json={"text": "Спасибо, отлично помогли!"})
        assert r.json()["emotional_tone"] == "Позитив"

    def test_document_category(self, client):
        r = client.post("/api/analyze", json={"text": "Пришлите паспорт прибора."})
        assert r.json()["category"] == "Документация"


# ═══════════════════════════════════════════
# GET /api/stats
# ═══════════════════════════════════════════

class TestStats:
    def test_returns_200(self, client_with_data):
        r = client_with_data.get("/api/stats")
        assert r.status_code == 200

    def test_has_required_keys(self, client_with_data):
        data = client_with_data.get("/api/stats").json()
        assert "total" in data
        assert "by_tone" in data
        assert "by_category" in data
        assert "by_status" in data

    def test_total_count(self, client_with_data):
        assert client_with_data.get("/api/stats").json()["total"] == 3

    def test_empty_store_stats(self, client):
        data = client.get("/api/stats").json()
        assert data["total"] == 0

    def test_stats_reflect_created_tickets(self, client):
        client.post("/api/tickets", json={"original_text": "не работает"})
        client.post("/api/tickets", json={"original_text": "спасибо"})
        data = client.get("/api/stats").json()
        assert data["total"] == 2

    def test_by_tone_keys(self, client_with_data):
        by_tone = client_with_data.get("/api/stats").json()["by_tone"]
        assert "Негатив" in by_tone
        assert "Нейтрально" in by_tone
        assert "Позитив" in by_tone


# ═══════════════════════════════════════════
# GET /api/export/csv
# ═══════════════════════════════════════════

class TestExportCsv:
    def test_returns_200(self, client_with_data):
        r = client_with_data.get("/api/export/csv")
        assert r.status_code == 200

    def test_content_type_csv(self, client_with_data):
        r = client_with_data.get("/api/export/csv")
        assert "text/csv" in r.headers["content-type"]

    def test_content_disposition_header(self, client_with_data):
        r = client_with_data.get("/api/export/csv")
        assert "attachment" in r.headers["content-disposition"]
        assert "tickets_export.csv" in r.headers["content-disposition"]

    def test_has_header_row(self, client_with_data):
        r = client_with_data.get("/api/export/csv")
        content = r.content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        assert "id" in reader.fieldnames
        assert "full_name" in reader.fieldnames
        assert "status" in reader.fieldnames

    def test_rows_match_ticket_count(self, client_with_data):
        r = client_with_data.get("/api/export/csv")
        content = r.content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) == 3

    def test_empty_store_only_header(self, client):
        r = client.get("/api/export/csv")
        content = r.content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        assert list(reader) == []

    def test_data_correct(self, client):
        client.post("/api/tickets", json={"full_name": "CSV Тест"})
        r = client.get("/api/export/csv")
        content = r.content.decode("utf-8-sig")
        assert "CSV Тест" in content
