import time
import json
import os

from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
import wave

from abrege_service.schemas import AUDIO_CONTENT_TYPES
from abrege_service.modules.base import BaseService
from src.schemas.task import TaskModel, TaskStatus
from src.schemas.result import ResultModel
from src.utils.logger import logger_abrege

folder_dest = os.environ.get("CACHE_FOLDER")

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
    def __init__(self, content_type_allowed=AUDIO_CONTENT_TYPES):
        super().__init__(content_type_allowed)


class AudioVoskTranscriptionService(AudioBaseService):
    def __init__(
        self,
        path_model: str = "abrege_service/data/models/vosk-model-small-fr-0.22",
        second_per_process: float = 4000 / 16000.0,
        service_ratio_representaion: float = 1.0,
    ):
        super().__init__()

        self.model = Model(path_model)
        self.rec = KaldiRecognizer(self.model, 16000)
        self.rec.SetWords(True)
        self.second_per_process = second_per_process
        self.service_ratio_representaion = service_ratio_representaion

    def task_to_text(self, task: TaskModel, **kwargs) -> TaskModel:
        logger_abrege.debug(f"Start transciption for {task.id}")
        if task.extras is None:
            task.extras = {}
        if task.output is None:
            task.output = ResultModel(
                type="audio",
                created_at=int(time.time()),
                model_name="vosk",
                model_version="vosk-model-small-fr-0.22",
                updated_at=int(time.time()),
                percentage=0,
            )
        file_path = os.path.join(folder_dest, "temp.wav") if folder_dest else "temp.wav"
        convertir_audio(task.input.file_path, file_path)
        wf = wave.open(file_path, "rb")
        frames = wf.getnframes()
        framerate = wf.getframerate()
        duration = frames / float(framerate)
        task.extras["audio_duration"] = duration
        rec = KaldiRecognizer(self.model, wf.getframerate())
        rec.SetWords(True)
        results = []
        read_frames = int(self.second_per_process * framerate)
        red_frames = 0
        while True:
            data = wf.readframes(read_frames)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                results.append(res)
            red_frames += read_frames
            if red_frames > frames:
                red_frames = frames
            task.output.percentage = self.service_ratio_representaion * (red_frames / frames)
            task.extras["audio"] = {"result": results}
            logger_abrege.debug(f"{task.id}: percentage : {task.output.percentage} - {red_frames}/{frames}")
            task.output.texts_found = [item.get("text") for item in results]
            task = self.update_task(task=task, status=TaskStatus.IN_PROGRESS.value, result=task.output)

        final_res = json.loads(rec.FinalResult())
        if "result" not in final_res:
            final_res["result"] = []
        results.append(final_res)
        wf.close()
        logger_abrege.debug(f"{task.id}: percentage : {task.output.percentage} - {red_frames}/{frames}")
        task.extras["audio"] = {"result": results}
        task.output.texts_found = [item.get("text") for item in results]

        task = self.update_task(task=task, status=TaskStatus.IN_PROGRESS.value, result=task.output)
        if os.path.exists(file_path):
            os.remove(file_path)

        return task
