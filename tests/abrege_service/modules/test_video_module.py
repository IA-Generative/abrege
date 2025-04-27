import os
import pytest
from abrege_service.modules.video import VideoService
from abrege_service.modules.audio import AudioService


@pytest.mark.skipif(
    os.path.exists("abrege_service/data/models/vosk-model-small-fr-0.22") is False,
    reason="Model not found",
)
def test_video_service():
    audio_service = AudioService("abrege_service/data/models/vosk-model-small-fr-0.22")
    video_service = VideoService(audio_service)
    assert video_service.is_availble("video/mp4") is True
    assert video_service.is_availble("application/pdf") is False
    assert isinstance(video_service.video_audio_to_text("tests/data/audio/1.wav"), str)
    actual = video_service.transform_to_text("tests/data/video/bonjour.mp4", content_type="video/mp4")
    assert isinstance(actual, str)
    with pytest.raises(NotImplementedError):
        video_service.transform_to_text("tests/data/video/bonjour.mp4", content_type="application/pdf")
