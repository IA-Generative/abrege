import os
from src.utils.url import get_content_type, download_file


def test_get_content_type():
    assert get_content_type("https://google.com").split(";")[0] == "text/html"
    assert get_content_type("https://www.osureunion.fr/wp-content/uploads/2022/03/pdf-exemple.pdf") == "application/pdf"
    assert get_content_type("https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png") == "image/png"
    assert (
        get_content_type("https://www.youtube.com/watch?v=Ggq0c4e2hjA&list=PL8egiwZE1Lk5TPhNuXHprwMSCbMHTbOjz&index=3").split(";")[0] == "text/html"
    )
    assert get_content_type("https://github.com/intel-iot-devkit/sample-videos/raw/master/bolt-detection.mp4") == "application/octet-stream"
    assert get_content_type("https://www.google.com/robots.txt") == "text/plain"
    assert get_content_type("https://fr.getsamplefiles.com/download/wav/sample-3.wav") == "audio/x-wav"


def test_download_type():
    # Test donwload html
    url_html = "https://google.com"
    download_file(url=url_html)
    assert os.path.exists("google.com")
    os.remove("google.com")

    # Test download pdf
    url_pdf = "https://www.osureunion.fr/wp-content/uploads/2022/03/pdf-exemple.pdf"
    download_file(url=url_pdf)
    assert os.path.exists("pdf-exemple.pdf")
    os.remove("pdf-exemple.pdf")

    # Test png :
    url_png = "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
    download_file(url=url_png)
    assert os.path.exists("googlelogo_color_272x92dp.png")
    os.remove("googlelogo_color_272x92dp.png")

    # Test mp4 :
    url_mp4 = "https://github.com/intel-iot-devkit/sample-videos/raw/master/bolt-detection.mp4"
    download_file(url=url_mp4)
    assert os.path.exists("bolt-detection.mp4")
    os.remove("bolt-detection.mp4")

    # Test pptx
    # url_ppt = "https://pedagogie.ac-toulouse.fr/philosophie/sites/default/files/fichiers/ppt_philosophie_et_ecologie.pptx"
    # download_file(url=url_ppt)
    # assert os.path.exists("ppt_philosophie_et_ecologie.pptx")
    # os.remove("ppt_philosophie_et_ecologie.pptx")

    # test audio
    url_audio = "https://fr.getsamplefiles.com/download/wav/sample-3.wav"
    download_file(url=url_audio)
    assert os.path.exists("sample-3.wav")
    os.remove("sample-3.wav")
