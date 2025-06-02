from src.schemas.code_error import TASK_STATUS_TO_HTTP
from src.schemas.task import TaskStatus
from http import HTTPStatus


def test_code_error():
    assert TASK_STATUS_TO_HTTP[TaskStatus.CREATED] == HTTPStatus.CREATED
    assert TASK_STATUS_TO_HTTP[TaskStatus.QUEUED] == HTTPStatus.ACCEPTED
    assert TASK_STATUS_TO_HTTP[TaskStatus.STARTED] == HTTPStatus.ACCEPTED
    assert TASK_STATUS_TO_HTTP[TaskStatus.IN_PROGRESS] == HTTPStatus.PARTIAL_CONTENT
    assert TASK_STATUS_TO_HTTP[TaskStatus.COMPLETED] == HTTPStatus.OK
    assert TASK_STATUS_TO_HTTP[TaskStatus.FAILED] == HTTPStatus.INTERNAL_SERVER_ERROR
    assert TASK_STATUS_TO_HTTP[TaskStatus.RETRYING] == HTTPStatus.ALREADY_REPORTED
    assert TASK_STATUS_TO_HTTP[TaskStatus.CANCELED] == HTTPStatus.INTERNAL_SERVER_ERROR
    assert TASK_STATUS_TO_HTTP[TaskStatus.TIMEOUT] == HTTPStatus.GATEWAY_TIMEOUT
