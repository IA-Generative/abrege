import json
import pytest

from src.clients import file_connector
from src.schemas.task import task_table, TaskForm, TaskModel, TaskStatus
from src.schemas.content import TextModel, URLModel, DocumentModel
from abrege_service.main import launch, ocr_service

is_ocr_available = False

try:
    ocr_service.ocr_mi_client.get_health()
    is_ocr_available = True
except Exception as e:
    print(e)


def test_task_process_text():
    user_id = "test"
    task = task_table.insert_new_task(
        user_id=user_id,
        form_data=TaskForm(
            type="summary",
            input=TextModel(text="test", created_at=0),
            status=TaskStatus.CREATED.value,
            extras={},
        ),
    )

    result = launch.apply(args=[json.dumps(task.model_dump())])
    result = result.get()
    actual = TaskModel.model_validate(result)
    assert actual.id == task.id
    assert actual.status == TaskStatus.COMPLETED.value


def test_task_process_url():
    user_id = "test"
    #############################################################
    # Test donwload html
    url_html = "https://google.com"
    task = task_table.insert_new_task(
        user_id=user_id,
        form_data=TaskForm(
            type="summary",
            input=URLModel(url=url_html, created_at=0),
            status=TaskStatus.CREATED.value,
            extras={},
        ),
    )

    result = launch.apply(args=[json.dumps(task.model_dump())])
    result = result.get()
    actual = TaskModel.model_validate(result)
    assert actual.id == task.id
    assert actual.status == TaskStatus.COMPLETED.value
    task_table.delete_task_by_id(task.id)

    #############################################################


@pytest.mark.skipif(condition=not is_ocr_available, reason="Ocr not available")
def test_task_process_url_pdf():
    user_id = "test"
    #############################################################
    # Test download pdf
    url_pdf = "https://www.i2m.univ-amu.fr/perso/thierry.gallouet/licence.d/topo/chap1.pdf"
    task = task_table.insert_new_task(
        user_id=user_id,
        form_data=TaskForm(
            type="summary",
            input=URLModel(url=url_pdf, created_at=0),
            status=TaskStatus.CREATED.value,
            extras={},
        ),
    )

    result = launch.apply(args=[json.dumps(task.model_dump())])
    result = result.get()
    actual = TaskModel.model_validate(result)
    assert actual.id == task.id
    assert actual.status == TaskStatus.COMPLETED.value
    assert actual.output.percentage == 1
    assert len(actual.output.summary.split()) > 0
    task_table.delete_task_by_id(task.id)

    #############################################################


def test_task_process_url_png():
    user_id = "test"
    #############################################################
    # Test download png (Not implemented yet)
    url_png = "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"

    task = task_table.insert_new_task(
        user_id=user_id,
        form_data=TaskForm(
            type="summary",
            input=URLModel(url=url_png, created_at=0),
            status=TaskStatus.CREATED.value,
            extras={},
        ),
    )

    launch.apply(args=[json.dumps(task.model_dump())])
    task = task_table.get_task_by_id(task_id=task.id)
    assert task.id == task.id
    assert task.status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]
    task_table.delete_task_by_id(task.id)
    #############################################################


def test_task_process_url_mp4():
    user_id = "test"
    #############################################################
    # Test mp4 :
    url_mp4 = "https://github.com/intel-iot-devkit/sample-videos/raw/master/bolt-detection.mp4"

    task = task_table.insert_new_task(
        user_id=user_id,
        form_data=TaskForm(
            type="summary",
            input=URLModel(url=url_mp4, created_at=0),
            status=TaskStatus.CREATED.value,
            extras={},
        ),
    )

    result = launch.apply(args=[json.dumps(task.model_dump())])
    result = result.get()
    actual = TaskModel.model_validate(result)
    assert actual.id == task.id
    assert actual.status == TaskStatus.COMPLETED.value
    task_table.delete_task_by_id(task.id)

    #############################################################


def test_task_process_url_ppt():
    user_id = "test"
    #############################################################
    # Test pptx
    url_ppt = "https://pedagogie.ac-toulouse.fr/philosophie/sites/default/files/fichiers/ppt_philosophie_et_ecologie.pptx"

    task = task_table.insert_new_task(
        user_id=user_id,
        form_data=TaskForm(
            type="summary",
            input=URLModel(url=url_ppt, created_at=0),
            status=TaskStatus.CREATED.value,
            extras={},
        ),
    )

    result = launch.apply(args=[json.dumps(task.model_dump())])
    result = result.get()
    actual = TaskModel.model_validate(result)
    assert actual.id == task.id
    assert actual.status == TaskStatus.COMPLETED.value
    assert actual.output.percentage == 1

    assert len(actual.output.summary.split()) > 0
    task_table.delete_task_by_id(task.id)

    #############################################################


def test_task_process_url_audio():
    user_id = "test"
    #############################################################
    # Test wav
    url_audio = "https://github.com/UniData-pro/french-speech-recognition-dataset/raw/refs/heads/main/audio/1.wav"

    task = task_table.insert_new_task(
        user_id=user_id,
        form_data=TaskForm(
            type="summary",
            input=URLModel(url=url_audio, created_at=0),
            status=TaskStatus.CREATED.value,
            extras={},
        ),
    )

    result = launch.apply(args=[json.dumps(task.model_dump())])
    result = result.get()
    actual = TaskModel.model_validate(result)
    assert actual.id == task.id
    assert actual.status == TaskStatus.COMPLETED.value
    assert actual.output.percentage == 1
    task_table.delete_task_by_id(task.id)

    #############################################################


def test_audio_document():
    audio_path = "tests/data/audio/1.wav"
    user_id = "test"
    task = task_table.insert_new_task(
        user_id=user_id,
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            extras={},
        ),
    )

    save_path = file_connector.save(user_id=task.user_id, task_id=task.id, file_path=audio_path)
    document = DocumentModel(
        created_at=0,
        file_path=save_path,
        raw_filename="2.wav",
        content_type="audio/wav",
        ext="wav",
        size=0,
    )
    task = task_table.update_task(
        task_id=task.id,
        form_data=TaskForm(
            type="summary",
            input=document,
            status=TaskStatus.CREATED.value,
            updated_at=1,
            extras={},
        ),
    )

    result = launch.apply(args=[json.dumps(task.model_dump())])
    result = result.get()
    actual = TaskModel.model_validate(result)
    assert actual.id == task.id
    assert actual.status == TaskStatus.COMPLETED.value
    assert "que" in actual.output.summary

    assert actual.output.percentage == 1
    task_table.delete_task_by_id(task.id)


def test_video_document():
    video_path = "tests/data/video/bonjour.mp4"
    user_id = "test"
    task = task_table.insert_new_task(
        user_id=user_id,
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            extras={},
        ),
    )

    save_path = file_connector.save(user_id=task.user_id, task_id=task.id, file_path=video_path)
    document = DocumentModel(
        created_at=0,
        file_path=save_path,
        raw_filename="2.mp4",
        content_type="video/mp4",
        ext="mp4",
        size=0,
    )
    task = task_table.update_task(
        task_id=task.id,
        form_data=TaskForm(
            type="summary",
            input=document,
            status=TaskStatus.CREATED.value,
            updated_at=1,
            extras={},
        ),
    )

    result = launch.apply(args=[json.dumps(task.model_dump())])
    result = result.get()
    actual = TaskModel.model_validate(result)
    assert actual.id == task.id
    assert actual.status == TaskStatus.COMPLETED.value
    assert actual.output.percentage == 1

    task_table.delete_task_by_id(task.id)


@pytest.mark.skipif(condition=not is_ocr_available, reason="Ocr not available")
def test_pdf_document():
    video_path = "tests/test_data/elysee-module-24161-fr.pdf"
    user_id = "test"
    task = task_table.insert_new_task(
        user_id=user_id,
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            extras={},
        ),
    )

    save_path = file_connector.save(user_id=task.user_id, task_id=task.id, file_path=video_path)
    document = DocumentModel(
        created_at=0,
        file_path=save_path,
        raw_filename="2.pdf",
        content_type="application/pdf",
        ext="pdf",
        size=0,
    )
    task = task_table.update_task(
        task_id=task.id,
        form_data=TaskForm(
            type="summary",
            input=document,
            status=TaskStatus.CREATED.value,
            updated_at=1,
            extras={},
        ),
    )

    result = launch.apply(args=[json.dumps(task.model_dump())])
    result = result.get()
    actual = TaskModel.model_validate(result)
    assert actual.id == task.id
    assert actual.status == TaskStatus.COMPLETED.value
    assert actual.output.percentage == 1

    task_table.delete_task_by_id(task.id)


def test_docx_document():
    video_path = "tests/test_data/Cadrage.docx"
    user_id = "test"
    task = task_table.insert_new_task(
        user_id=user_id,
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            extras={},
        ),
    )

    save_path = file_connector.save(user_id=task.user_id, task_id=task.id, file_path=video_path)
    document = DocumentModel(
        created_at=0,
        file_path=save_path,
        raw_filename="2.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ext="docx",
        size=0,
    )
    task = task_table.update_task(
        task_id=task.id,
        form_data=TaskForm(
            type="summary",
            input=document,
            status=TaskStatus.CREATED.value,
            updated_at=1,
            extras={},
        ),
    )

    result = launch.apply(args=[json.dumps(task.model_dump())])
    result = result.get()
    actual = TaskModel.model_validate(result)
    assert actual.id == task.id
    assert actual.status == TaskStatus.COMPLETED.value
    assert actual.output.percentage == 1

    task_table.delete_task_by_id(task.id)
