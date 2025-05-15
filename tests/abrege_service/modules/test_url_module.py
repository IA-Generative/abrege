import os
from abrege_service.modules.url import URLService
from src.schemas.task import TaskModel, TaskForm, task_table, TaskStatus
from src.schemas.content import URLModel
import pytest


def mock_task(url) -> TaskModel:
    task = task_table.insert_new_task(
        user_id="1",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            updated_at=0,
            content=URLModel(created_at=0, url=url),
        ),
    )

    return task


def test_task_not_implemented():
    url_service = URLService()

    # Test donwload html
    dummy_task = mock_task("https://this-is-tobi.com/")
    with pytest.raises(NotImplementedError):
        url_service.task_to_text(dummy_task)

    if os.path.exists("downloaded_file"):
        os.remove("downloaded_file")


def test_get_text_from_pdf():
    from abrege_service.modules.doc import PDFTOMD4LLMService

    url_service = URLService(services=[PDFTOMD4LLMService()])

    # Test download pdf
    dummy_task = mock_task("https://www-fourier.ujf-grenoble.fr/~demailly/L3_topologie_B/topologie_nier_iftimie.pdf")
    actual = url_service.task_to_text(dummy_task)
    assert "topologie" in "\n".join([item for item in actual.result.texts_found])


def test_get_text_from_microsoft():
    from abrege_service.modules.doc import MicrosoftDocumnentToMdService

    url_service = URLService(services=[MicrosoftDocumnentToMdService()])
    # Test pptx
    dummy_task = mock_task("https://pedagogie.ac-toulouse.fr/philosophie/sites/default/files/fichiers/ppt_philosophie_et_ecologie.pptx")
    actual = url_service.task_to_text(dummy_task)

    assert "biologiste" in "\n".join([item for item in actual.result.texts_found])


def test_get_text_from_audio():
    from abrege_service.modules.audio import AudioVoskTranscriptionService

    url_service = URLService(services=[AudioVoskTranscriptionService(second_per_process=0.5)])
    # test audio
    dummy_task = mock_task("https://github.com/UniData-pro/french-speech-recognition-dataset/raw/refs/heads/main/audio/1.wav")
    actual = url_service.task_to_text(dummy_task)
    assert "que" in "\n".join([item for item in actual.result.texts_found])


def test_get_text_from_audio_video():
    from abrege_service.modules.video import VideoTranscriptionService

    url_service = URLService(services=[VideoTranscriptionService()])
    # Test mp4 :
    dummy_task = mock_task("https://github.com/intel-iot-devkit/sample-videos/raw/master/bolt-detection.mp4")
    actual = url_service.task_to_text(dummy_task)
    assert "" in "\n".join([item for item in actual.result.texts_found])


def test_get_text_html():
    from abrege_service.modules.doc import MicrosoftDocumnentToMdService

    url_service = URLService(services=[MicrosoftDocumnentToMdService()])

    # Test donwload html
    dummy_task = mock_task("https://this-is-tobi.com/")

    actual = url_service.task_to_text(dummy_task)
    assert "Tobi's projects" in "\n".join([item for item in actual.result.texts_found])
