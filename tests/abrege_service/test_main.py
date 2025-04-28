import os

from src.schemas.task import task_table, TaskForm, TaskModel, TaskStatus
from src.schemas.content import TextModel, URLModel
from abrege_service.main import launch
import json


def test_task_process_text():
    user_id = "test"
    task = task_table.insert_new_task(
        user_id=user_id,
        form_data=TaskForm(
            type="summary",
            content=TextModel(text="test", created_at=0),
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
            content=URLModel(url=url_html, created_at=0),
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
    os.remove("google.com")
    #############################################################


def test_task_process_url_pdf():
    user_id = "test"
    #############################################################
    # Test download pdf
    url_pdf = "https://www.i2m.univ-amu.fr/perso/thierry.gallouet/licence.d/topo/chap1.pdf"
    task = task_table.insert_new_task(
        user_id=user_id,
        form_data=TaskForm(
            type="summary",
            content=URLModel(url=url_pdf, created_at=0),
            status=TaskStatus.CREATED.value,
            extras={},
        ),
    )

    result = launch.apply(args=[json.dumps(task.model_dump())])
    result = result.get()
    actual = TaskModel.model_validate(result)
    assert actual.id == task.id
    assert actual.status == TaskStatus.COMPLETED.value
    assert actual.result.percentage == 1
    assert len(actual.result.summary.split()) > 0
    task_table.delete_task_by_id(task.id)
    os.remove("chap1.pdf")
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
            content=URLModel(url=url_png, created_at=0),
            status=TaskStatus.CREATED.value,
            extras={},
        ),
    )

    launch.apply(args=[json.dumps(task.model_dump())])
    task = task_table.get_task_by_id(task_id=task.id)
    assert task.id == task.id
    assert task.status == TaskStatus.FAILED.value
    task_table.delete_task_by_id(task.id)
    os.remove("googlelogo_color_272x92dp.png")
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
            content=URLModel(url=url_mp4, created_at=0),
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
    os.remove("bolt-detection.mp4")
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
            content=URLModel(url=url_ppt, created_at=0),
            status=TaskStatus.CREATED.value,
            extras={},
        ),
    )

    result = launch.apply(args=[json.dumps(task.model_dump())])
    result = result.get()
    actual = TaskModel.model_validate(result)
    assert actual.id == task.id
    assert actual.status == TaskStatus.COMPLETED.value
    assert actual.result.percentage == 1
    assert len(actual.result.summary.split()) > 0
    task_table.delete_task_by_id(task.id)
    os.remove("ppt_philosophie_et_ecologie.pptx")
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
            content=URLModel(url=url_audio, created_at=0),
            status=TaskStatus.CREATED.value,
            extras={},
        ),
    )

    result = launch.apply(args=[json.dumps(task.model_dump())])
    result = result.get()
    actual = TaskModel.model_validate(result)
    assert actual.id == task.id
    assert actual.status == TaskStatus.COMPLETED.value
    assert actual.result.percentage == 1
    task_table.delete_task_by_id(task.id)
    os.remove("1.wav")
    #############################################################
