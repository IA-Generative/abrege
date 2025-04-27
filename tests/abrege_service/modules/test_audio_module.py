import os
import pytest
from abrege_service.modules.audio import AudioService, AudioModel


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
