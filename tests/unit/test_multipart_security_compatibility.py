"""Bounded parser and real upload-route canaries using synthetic inputs only."""

from datetime import datetime
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from python_multipart import MultipartParser, parse_form
from python_multipart.exceptions import MultipartParseError
from python_multipart.multipart import parse_options_header

from backend.api.dependencies.auth import get_current_user
from backend.api.dependencies.database import get_db_session
from backend.api.routers import governance
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.domain.enums.user_role import UserRole
from backend.main import app


USER_ID = UUID("00000000-0000-0000-0000-000000009201")
UPLOAD_URL = "/api/v1/governance/imports/upload"


@pytest.fixture
def upload_api(monkeypatch):
    user = UserResponseDTO(
        id=USER_ID, email="multipart@example.test", name="Synthetic Upload User",
        role=UserRole.VIEWER, is_active=True, is_verified=True,
        created_at=datetime(2026, 1, 1), last_login_at=None,
    )
    session = object()
    use_case = SimpleNamespace(execute=AsyncMock(return_value={"run_id": "synthetic-upload"}))
    monkeypatch.setattr(app, "dependency_overrides", {})
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db_session] = lambda: session
    monkeypatch.setattr(governance, "UploadImportUseCase", lambda db: use_case)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, use_case


def test_canonical_and_framework_legacy_imports_agree():
    from multipart.multipart import parse_options_header as legacy_parse

    header = b'multipart/form-data; boundary="synthetic-boundary"'
    assert parse_options_header(header) == legacy_parse(header) == (
        b"multipart/form-data", {b"boundary": b"synthetic-boundary"},
    )


@pytest.mark.parametrize(
    "extra",
    [b"; filename*=utf-8''different.csv", b"; filename*0=different; filename*1=.csv"],
)
def test_extended_disposition_cannot_override_plain_filename(extra):
    _, options = parse_options_header(
        b'form-data; name="file"; filename="synthetic.csv"' + extra
    )
    assert options[b"filename"] == b"synthetic.csv"
    assert options[b"name"] == b"file"


def test_negative_content_length_rejected_before_reading_stream():
    class NoReadStream(BytesIO):
        def read(self, size=-1):
            raise AssertionError("Negative Content-Length must fail before any body read")

    with pytest.raises(ValueError):
        parse_form(
            {"Content-Type": b"application/x-www-form-urlencoded", "Content-Length": b"-1"},
            NoReadStream(b"key=value"), None, None,
        )


def test_default_header_count_is_bounded_with_small_input():
    body = b"--safe\r\n" + b"X-Test: a\r\n" * 9 + b"\r\nvalue\r\n--safe--\r\n"
    assert len(body) < 256
    with pytest.raises(MultipartParseError):
        MultipartParser(b"safe").write(body)


def test_default_individual_header_size_is_bounded():
    body = b"--safe\r\nX-Test: " + b"a" * 4250 + b"\r\n\r\nvalue\r\n--safe--\r\n"
    assert len(body) < 5000
    with pytest.raises(MultipartParseError):
        MultipartParser(b"safe").write(body)


def test_upload_file_preserves_bytes_filename_and_owner(upload_api):
    client, use_case = upload_api
    content = b"symbol,quantity\nSYNTH,1\n"
    response = client.post(
        UPLOAD_URL, data={"source_type": "MYPROFIT_ATIVOS"},
        files={"file": ("synthetic.csv", content, "text/csv")},
    )
    assert response.status_code == 200
    assert response.json() == {"run_id": "synthetic-upload"}
    use_case.execute.assert_awaited_once_with(
        user_id=USER_ID, source_type="MYPROFIT_ATIVOS",
        file_content=content, filename="synthetic.csv",
    )


def test_urlencoded_form_keeps_semicolon_inside_value(upload_api):
    client, use_case = upload_api
    response = client.post(
        UPLOAD_URL,
        content=b"source_type=MYPROFIT_ATIVOS&raw_text=alpha;source_type=smuggled",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    use_case.execute.assert_awaited_once_with(
        user_id=USER_ID, source_type="MYPROFIT_ATIVOS",
        file_content=b"alpha;source_type=smuggled", filename="Pasted_Text",
    )


def test_quoted_boundary_with_short_preamble_epilogue_and_streamed_body(upload_api):
    client, use_case = upload_api
    body = (
        b"\r\n\r\n--safe\r\nContent-Disposition: form-data; name=\"source_type\"\r\n\r\n"
        b"MYPROFIT_ATIVOS\r\n--safe\r\nContent-Disposition: form-data; name=\"raw_text\"\r\n\r\n"
        b"synthetic-input\r\n--safe--\r\nshort-epilogue"
    )
    assert len(body) < 512
    response = client.post(
        UPLOAD_URL, content=iter(body[i:i + 17] for i in range(0, len(body), 17)),
        headers={"Content-Type": 'multipart/form-data; boundary="safe"'},
    )
    assert response.status_code == 200
    assert use_case.execute.await_args.kwargs["file_content"] == b"synthetic-input"


@pytest.mark.parametrize(
    "content_type,body,status",
    [
        ("multipart/form-data", b"small-invalid-body", 400),
        ("application/json", b'{"source_type":"MYPROFIT_ATIVOS","raw_text":"synthetic"}', 422),
        ("application/x-www-form-urlencoded", b"raw_text=synthetic", 422),
        ("application/x-www-form-urlencoded", b"source_type=MYPROFIT_ATIVOS", 400),
    ],
)
def test_invalid_forms_have_bounded_client_errors(upload_api, content_type, body, status):
    client, use_case = upload_api
    response = client.post(UPLOAD_URL, content=body, headers={"Content-Type": content_type})
    assert response.status_code == status
    assert "detail" in response.json()
    for internal in ("Traceback", "site-packages", "AssertionError", "synthetic-hash"):
        assert internal not in response.text
    use_case.execute.assert_not_awaited()


def test_upload_openapi_contract_and_application_startup(upload_api):
    client, _ = upload_api
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    upload = schema["paths"][UPLOAD_URL]["post"]
    body = upload["requestBody"]["content"]["multipart/form-data"]["schema"]
    fields = schema["components"]["schemas"][body["$ref"].rsplit("/", 1)[1]]
    assert set(fields["properties"]) == {"source_type", "file", "raw_text"}
    assert fields["required"] == ["source_type"]
    assert upload["security"] == [{"OAuth2PasswordBearer": []}]
    assert "/api/v1/auth/login" in schema["paths"]
    assert "/api/v1/planning/projection" in schema["paths"]
