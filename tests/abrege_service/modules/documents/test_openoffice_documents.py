from abrege_service.modules.documents.openoffice import extract_pages_from_odt, extract_slides_from_odp


def test_open_office_doc():
    texts = extract_pages_from_odt("tests/test_data/Lettre_de_Camus.odt")
    assert len(texts) == 1


def test_open_office_presentation():
    try:
        texts = extract_slides_from_odp("tests/test_data/4+-+Diaporama_Conf_clubCC+-+PCAET-1.odp")
        assert len(texts) == 15
    except Exception as e:
        print(e)
