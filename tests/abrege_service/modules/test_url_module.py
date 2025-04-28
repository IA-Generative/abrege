from abrege_service.modules.url import URLService
from abrege_service.modules.audio import AudioService
from abrege_service.modules.video import VideoService
from abrege_service.modules.doc import DocService

audio_service = AudioService()
video_service = VideoService(audio_service=audio_service)
doc_service = DocService()


def test_url_service_is_valid_url():
    url_service = URLService(
        audio_service=None,
        video_service=None,
        doc_service=None,
    )
    assert url_service.is_valid_url("https://google.com")


def test_get_contetnt_type():
    url_service = URLService(
        audio_service=None,
        video_service=None,
        doc_service=None,
    )
    assert url_service.get_content_type("https://google.com").split(";")[0] == "text/html"
    assert (
        url_service.get_content_type("https://www-fourier.ujf-grenoble.fr/~demailly/L3_topologie_B/topologie_nier_iftimie.pdf") == "application/pdf"
    )
    assert url_service.get_content_type("https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png") == "image/png"
    assert (
        url_service.get_content_type("https://www.youtube.com/watch?v=Ggq0c4e2hjA&list=PL8egiwZE1Lk5TPhNuXHprwMSCbMHTbOjz&index=3").split(";")[0]
        == "text/html"
    )
    assert (
        url_service.get_content_type("https://github.com/intel-iot-devkit/sample-videos/raw/master/bolt-detection.mp4") == "application/octet-stream"
    )
    assert url_service.get_content_type("https://www.google.com/robots.txt") == "text/plain"
    assert (
        url_service.get_content_type("https://github.com/UniData-pro/french-speech-recognition-dataset/raw/refs/heads/main/audio/1.wav")
        == "audio/wav"
    )
