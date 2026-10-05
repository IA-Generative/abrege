import pytest

from api.main import app

GENERATED_SCHEMAS = {"HTTPValidationError", "ValidationError"}
HTTP_METHODS = ("get", "post", "put", "delete", "patch")


@pytest.fixture(scope="module")
def spec():
    return app.openapi()


def _operations(spec):
    for path, item in spec["paths"].items():
        for method, operation in item.items():
            if method in HTTP_METHODS:
                yield method.upper(), path, operation


def test_api_has_a_real_description_and_tag_descriptions(spec):
    assert len(spec["info"]["description"]) > 500
    declared = {tag["name"]: tag.get("description") for tag in spec["tags"]}
    used = {tag for _, _, operation in _operations(spec) for tag in operation.get("tags", [])}
    assert used <= declared.keys(), f"tags without metadata: {used - declared.keys()}"
    assert all(declared[name] for name in used), "every used tag needs a description"


def test_every_operation_has_a_summary_and_a_description(spec):
    missing = [f"{m} {p}" for m, p, op in _operations(spec) if not op.get("description")]
    assert not missing, f"operations without description: {missing}"
    default_summaries = [f"{m} {p}" for m, p, op in _operations(spec) if op.get("summary") == op["operationId"].split("_api_")[0].replace("_", " ").title()]
    assert not default_summaries, f"operations still using the auto-generated summary: {default_summaries}"


def test_every_parameter_is_described(spec):
    missing = [f"{m} {p} ({param['name']})" for m, p, op in _operations(spec) for param in op.get("parameters", []) if not param.get("description")]
    assert not missing, f"undocumented parameters: {missing}"


def test_every_schema_property_is_described(spec):
    missing = []
    for name, schema in spec["components"]["schemas"].items():
        if name in GENERATED_SCHEMAS:
            continue
        for prop, definition in schema.get("properties", {}).items():
            if not definition.get("description") and "$ref" not in definition:
                missing.append(f"{name}.{prop}")
    assert not missing, f"undocumented schema properties: {missing}"


def test_authenticated_operations_declare_their_security(spec):
    public = {"/api/auth/login", "/api/auth/token", "/api/auth/refresh", "/api/auth/callback", "/api/auth/logout", "/api/auth/me", "/api/health"}
    assert set(spec["components"]["securitySchemes"]) == {"bearerAuth", "sessionCookie", "internalToken"}
    for method, path, operation in _operations(spec):
        if path in public:
            continue
        assert operation.get("security"), f"{method} {path} does not declare its security"


def test_internal_endpoints_are_tagged_and_use_the_internal_token(spec):
    internal = [(m, p, op) for m, p, op in _operations(spec) if "Internal (worker)" in op.get("tags", [])]
    assert len(internal) == 5
    for method, path, operation in internal:
        assert method == "POST"
        assert operation["security"] == [{"internalToken": []}], path


def test_task_endpoint_documents_the_status_code_mapping(spec):
    responses = spec["paths"]["/api/task/{id}"]["get"]["responses"]
    assert {"200", "202", "206", "208", "401", "404", "500", "504"} <= responses.keys()


def test_list_endpoints_explain_that_offset_is_a_page_number(spec):
    for path in ("/api/task/user/", "/api/task/{id}/qa", "/api/task/{id}/entities", "/api/task/{id}/topics"):
        offset = next(p for p in spec["paths"][path]["get"]["parameters"] if p["name"] == "offset")
        assert "page number" in offset["description"]


def test_metrics_endpoint_is_not_exposed_in_the_docs(spec):
    assert "/metrics" not in spec["paths"]
