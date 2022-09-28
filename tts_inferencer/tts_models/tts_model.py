from abc import ABC, abstractmethod

class TtsModel(ABC):
    def __init__(self, device) -> None:
        self.device = device

    @abstractmethod
    def inference(self, input, speaker_id=None):
        pass