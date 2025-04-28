from typing import List
from abc import abstractmethod
import json

from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
import wave

from abrege_service.schemas import AUDIO_CONTENT_TYPES
from abrege_service.schemas.audio import AudioModel
from abrege_service.modules.base import BaseService
from abrege_service.schemas.text import TextModel

# audio dataset : https://github.com/facebookresearch/voxpopuli
# https://lbourdois.github.io/blog/audio/dataset_audio_fr/
# SAMPLE https://github.com/UniData-pro/french-speech-recognition-dataset/tree/main


def convertir_audio(chemin_entree, chemin_sortie):
    # Charger le fichier audio
    audio = AudioSegment.from_file(chemin_entree)

    # Convertir en mono et définir le taux d'échantillonnage à 16 kHz
    audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)

    # Exporter en WAV avec une profondeur de bits de 16 bits
    audio.export(chemin_sortie, format="wav", bitrate="16k")


class AudioBaseService(BaseService):
    def is_availble(self, content_type: str) -> bool:
        """
        Check if the content type is available for processing.

        Args:
            content_type (str): The content type to check.

        Returns:
            bool: True if the content type is available for processing, False otherwise.
        """
        return content_type in AUDIO_CONTENT_TYPES

    @abstractmethod
    def audio_to_text(self, file_path: str, **kwargs) -> str: ...


class AudioService(AudioBaseService):
    def __init__(self, path_model: str = "abrege_service/data/models/vosk-model-small-fr-0.22"):
        self.model = Model(path_model)
        self.rec = KaldiRecognizer(self.model, 16000)
        self.rec.SetWords(True)

    def audio_to_text(self, file_path: str, **kwargs) -> List[AudioModel]:
        convertir_audio(file_path, "temp.wav")
        file_path = "temp.wav"
        wf = wave.open(file_path, "rb")

        rec = KaldiRecognizer(self.model, wf.getframerate())
        rec.SetWords(True)
        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                results.append(AudioModel.model_validate(res))

        final_res = json.loads(rec.FinalResult())
        if "result" not in final_res:
            final_res["result"] = []
        results.append(AudioModel.model_validate(final_res))
        wf.close()

        return results

    def transform_to_text(self, file_path, content_type, **kwargs) -> List[TextModel]:
        if not self.is_availble(content_type):
            raise NotImplementedError(f"Content type {content_type} is not implemented for {self.__class__.__name__}.")

        return [TextModel(text=audio.text, extras=audio.model_dump()) for audio in self.audio_to_text(file_path, **kwargs)]
