import os
from TTS.utils.manage import ModelManager
from TTS.utils.synthesizer import Synthesizer
from src.utils.config import ROOT_DIR


class TTS:
    def __init__(self) -> None:
        venv_site_packages = ".venv\\Lib\\site-packages"
        models_json_path = os.path.join(
            ROOT_DIR,
            venv_site_packages,
            "TTS",
            ".models.json",
        )
        self._model_manager = ModelManager(models_json_path)
        self._model_path, self._config_path, self._model_item = \
            self._model_manager.download_model("tts_models/en/ljspeech/tacotron2-DDC_ph")
        voc_path, voc_config_path, _ = self._model_manager. \
            download_model("vocoder_models/en/ljspeech/univnet")
        self._synthesizer = Synthesizer(
            tts_checkpoint=self._model_path,
            tts_config_path=self._config_path,
            vocoder_checkpoint=voc_path,
            vocoder_config=voc_config_path
        )
    @property
    def synthesizer(self) -> Synthesizer:
        return self._synthesizer
        
    def synthesize(self, text: str, output_file: str = os.path.join(ROOT_DIR, "temp", "audio.wav")) -> str:
        outputs = self.synthesizer.tts(text)
        self.synthesizer.save_wav(outputs, output_file)
        return output_file
