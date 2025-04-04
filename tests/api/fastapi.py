

import unittest
import requests
from pathlib import Path
import json


class TestSummarizer(unittest.TestCase):
    def setUp(self):
        pass

    def test_text(self):

        test_text = (Path(__file__).resolve().parent / Path("../test_data/albert_camus.txt")).read_text()

        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }

        json_data = {
            'method': 'map_reduce',
            'model': 'qwen2.5',
            'context_size': 10000,
            'temperature': 0,
            'language': 'French',
            'size': 4000,
            'map_prompt': 'Rédigez un résumé concis des éléments suivants :\\n\\n{context}',
            'reduce_prompt': '\nVoici une série de résumés:\n{docs}\nRassemblez ces éléments et faites-en un résumé final et consolidé dans {language} en {size} mots au maximum. Rédigez uniquement en {language}.\n',
            'text': test_text,
        }

        response = requests.post('http://0.0.0.0:8000/api/text', headers=headers, json=json_data)
        self.assertEqual(response.status_code, 200)
        data_dict = json.loads(response.content.decode())

        self.assertIsInstance(data_dict["time"], float)
        self.assertIsInstance(data_dict["summary"], str)

        self.assertLessEqual(len(data_dict["summary"]), len(test_text))

    def test_url(self):

        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }

        json_data = {
            'method': 'map_reduce',
            'model': 'qwen2.5',
            'context_size': 10000,
            'temperature': 0,
            'language': 'French',
            'size': 4000,
            'map_prompt': 'Rédigez un résumé concis des éléments suivants :\\n\\n{context}',
            'reduce_prompt': '\nVoici une série de résumés:\n{docs}\nRassemblez ces éléments et faites-en un résumé final et consolidé dans {language} en {size} mots au maximum. Rédigez uniquement en {language}.\n',
            'url': 'https://fr.wikipedia.org/wiki/%C3%89lys%C3%A9e-Montmartre',
        }

        response = requests.post('http://0.0.0.0:8000/api/url', headers=headers, json=json_data)
        self.assertEqual(response.status_code, 200)
        data_dict = json.loads(response.content.decode())

        self.assertIsInstance(data_dict["time"], float)
        self.assertIsInstance(data_dict["summary"], str)

    def test_doc_fail(self):
        headers = {
            'accept': 'application/json',
            # requests won't add a boundary if this header is set when you pass files=
            # 'Content-Type': 'multipart/form-data',
        }

        path_doc = (Path(__file__).resolve().parent / Path("../test_data/Malo_Adler_Thesis.pdf")).resolve().absolute()
        assert path_doc.exists() and path_doc.is_file()

        files = {
            'docData': (None, '{"size":4000,"method":"map_reduce","map_prompt":"Rédigez un résumé concis des éléments suivants :\\\\n\\\\n{context}","model":"qwen2.5","pdf_mode_ocr":"full_ocr","context_size":10000,"temperature":0,"language":"French","reduce_prompt":"\\nVoici une série de résumés:\\n{docs}\\nRassemblez ces éléments et faites-en un résumé final et consolidé dans {language} en {size} mots au maximum. Rédigez uniquement en {language}.\\n"}'),
            'file': ('Malo_Adler_Thesis.pdf', open(str(path_doc), 'rb'), 'application/pdf'),
        }

        response = requests.post('http://0.0.0.0:8000/api/doc', headers=headers, files=files)
        self.assertEqual(response.status_code, 422)
        data_dict = json.loads(response.content.decode())
        self.assertIsInstance(data_dict["detail"], str)


    def test_doc(self):
        headers = {
            'accept': 'application/json',
            # requests won't add a boundary if this header is set when you pass files=
            # 'Content-Type': 'multipart/form-data',
        }

        path_doc = (Path(__file__).resolve().parent / Path("../test_data/elysee-module-24161-fr.pdf")).resolve().absolute()
        assert path_doc.exists() and path_doc.is_file()

        files = {
            'docData': (None, '{"size":4000,"method":"map_reduce","map_prompt":"Rédigez un résumé concis des éléments suivants :\\\\n\\\\n{context}","model":"qwen2.5","pdf_mode_ocr":"full_ocr","context_size":10000,"temperature":0,"language":"French","reduce_prompt":"\\nVoici une série de résumés:\\n{docs}\\nRassemblez ces éléments et faites-en un résumé final et consolidé dans {language} en {size} mots au maximum. Rédigez uniquement en {language}.\\n"}'),
            'file': ('elysee-module-24161-fr.pdf', open(str(path_doc), 'rb'), 'application/pdf'),
        }

        response = requests.post('http://0.0.0.0:8000/api/doc', headers=headers, files=files)
        self.assertEqual(response.status_code, 200)
        data_dict = json.loads(response.content.decode())
        self.assertIsInstance(data_dict["time"], float)
        self.assertIsInstance(data_dict["summary"], str)



if __name__ == "__main__":
    unittest.main()
