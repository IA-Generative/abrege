import os
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


def test_download_type():
    url_service = URLService(
        audio_service=None,
        video_service=None,
        doc_service=None,
    )

    # Test donwload html
    url_html = "https://google.com"
    url_service.download_file(url=url_html)
    assert os.path.exists("google.com")
    os.remove("google.com")

    # Test download pdf
    url_pdf = "https://www-fourier.ujf-grenoble.fr/~demailly/L3_topologie_B/topologie_nier_iftimie.pdf"
    url_service.download_file(url=url_pdf)
    assert os.path.exists("topologie_nier_iftimie.pdf")
    os.remove("topologie_nier_iftimie.pdf")

    # Test png :
    url_png = "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
    url_service.download_file(url=url_png)
    assert os.path.exists("googlelogo_color_272x92dp.png")
    os.remove("googlelogo_color_272x92dp.png")

    # Test mp4 :
    url_mp4 = "https://github.com/intel-iot-devkit/sample-videos/raw/master/bolt-detection.mp4"
    url_service.download_file(url=url_mp4)
    assert os.path.exists("bolt-detection.mp4")
    os.remove("bolt-detection.mp4")

    # Test pptx
    url_ppt = "https://pedagogie.ac-toulouse.fr/philosophie/sites/default/files/fichiers/ppt_philosophie_et_ecologie.pptx"
    url_service.download_file(url=url_ppt)
    assert os.path.exists("ppt_philosophie_et_ecologie.pptx")
    os.remove("ppt_philosophie_et_ecologie.pptx")

    # test audio
    url_audio = "https://github.com/UniData-pro/french-speech-recognition-dataset/raw/refs/heads/main/audio/1.wav"
    url_service.download_file(url=url_audio)
    assert os.path.exists("1.wav")
    os.remove("1.wav")


def test_get_text():
    url_service = URLService(
        audio_service=audio_service,
        video_service=video_service,
        doc_service=doc_service,
    )

    # Test donwload html
    url_html = "https://this-is-tobi.com/"
    actual = url_service.transform_to_text(url_html)
    assert "Tobi's projects" in "\n".join([item.text for item in actual])
    os.remove("downloaded_file")

    # Test download pdf
    url_pdf = "https://www-fourier.ujf-grenoble.fr/~demailly/L3_topologie_B/topologie_nier_iftimie.pdf"
    actual = url_service.transform_to_text(url_pdf)
    assert "topologie" in "\n".join([item.text for item in actual])
    os.remove("topologie_nier_iftimie.pdf")

    # Test pptx
    url_ppt = "https://pedagogie.ac-toulouse.fr/philosophie/sites/default/files/fichiers/ppt_philosophie_et_ecologie.pptx"
    actual = url_service.transform_to_text(url_ppt)

    assert "biologiste" in "\n".join([item.text for item in actual])
    os.remove("ppt_philosophie_et_ecologie.pptx")

    # test audio
    url_audio = "https://github.com/UniData-pro/french-speech-recognition-dataset/raw/refs/heads/main/audio/1.wav"
    actual = url_service.transform_to_text(url_audio)
    assert "que" in "\n".join([item.text for item in actual])
    os.remove("1.wav")

    # Test mp4 :
    url_mp4 = "https://github.com/intel-iot-devkit/sample-videos/raw/master/bolt-detection.mp4"
    actual = url_service.transform_to_text(url_mp4)
    assert "" in "\n".join([item.text for item in actual])
    os.remove("bolt-detection.mp4")
