import os
import pytest
from abrege_service.modules.audio import AudioService, AudioModel, AudioBaseService


@pytest.mark.skipif(
    os.path.exists("abrege_service/data/models/vosk-model-small-fr-0.22") is False,
    reason="Model not found",
)
def test_audio_service():
    # wget https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip
    # unzip vosk-model-small-fr-0.22.zip -d abrege_service/data/models
    audio_service = AudioService("abrege_service/data/models/vosk-model-small-fr-0.22")
    assert audio_service.is_availble("audio/mpeg") is True
    assert audio_service.is_availble("application/pdf") is False
    for audio in audio_service.audio_to_text("tests/data/audio/1.wav"):
        assert isinstance(audio, AudioModel)

    assert isinstance(
        audio_service.transform_to_text("tests/data/audio/1.wav", content_type="audio/mpeg"),
        str,
    )
    with pytest.raises(NotImplementedError):
        audio_service.transform_to_text("tests/data/audio/1.wav", content_type="application/pdf")


def test_AudioBaseService_is_available():
    class MockAudioService(AudioBaseService):
        def audio_to_text(self, file_path: str, **kwargs) -> str:
            return "mocked text"

        def transform_to_text(self, file_path, content_type, **kwargs):
            return "mocked text"

    mock_service = MockAudioService()

    assert mock_service.is_availble("audio/mpeg") is True
    assert mock_service.is_availble("application/pdf") is False
    assert mock_service.audio_to_text("mocked_file_path") == "mocked text"
    assert mock_service.transform_to_text("mocked_file_path", content_type="audio/mpeg") == "mocked text"
