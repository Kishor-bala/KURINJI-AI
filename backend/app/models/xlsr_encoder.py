import torch
import numpy as np
from typing import Tuple, Optional
from transformers import Wav2Vec2Model, AutoFeatureExtractor
from backend.app.config import ENCODER_MODEL_NAME, TARGET_SAMPLE_RATE


class XLSREncoder:
    """
    Singleton wrapper for the frozen facebook/wav2vec2-xls-r-300m audio encoder.
    Extracts frame-level hidden representations H in R^(T x 1024).
    """

    _instance: Optional["XLSREncoder"] = None

    def __init__(self, model_name: str = ENCODER_MODEL_NAME, device: Optional[str] = None):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        print(f"Loading feature extractor: {self.model_name}")
        self.feature_extractor = AutoFeatureExtractor.from_pretrained(self.model_name)

        print(f"Loading frozen XLS-R model: {self.model_name} on {self.device}")
        self.model = Wav2Vec2Model.from_pretrained(self.model_name)

        # Freeze all model parameters strictly
        for param in self.model.parameters():
            param.requires_grad = False

        self.model.eval()
        self.model.to(self.device)
        print("XLS-R encoder loaded and frozen successfully.")

    @classmethod
    def get_instance(cls, model_name: str = ENCODER_MODEL_NAME) -> "XLSREncoder":
        """Returns the global singleton instance of XLSREncoder."""
        if cls._instance is None:
            cls._instance = cls(model_name=model_name)
        return cls._instance

    @torch.inference_mode()
    def extract_hidden_states(
        self,
        waveform: np.ndarray,
        sample_rate: int = TARGET_SAMPLE_RATE,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Extracts frame-level hidden representations from a 1D audio waveform.

        Args:
            waveform: 1D numpy array of audio samples (float32).
            sample_rate: Must be 16,000 Hz.

        Returns:
            hidden_states: Tensor of shape (1, T, 1024).
            valid_mask: Tensor of shape (1, T), boolean or binary mask indicating valid frames.
        """
        if sample_rate != TARGET_SAMPLE_RATE:
            raise ValueError(f"XLS-R requires {TARGET_SAMPLE_RATE} Hz audio, got {sample_rate} Hz.")

        if waveform.ndim != 1:
            waveform = waveform.squeeze()

        # Tokenize / preprocess audio through Hugging Face feature extractor
        inputs = self.feature_extractor(
            waveform,
            sampling_rate=sample_rate,
            return_tensors="pt",
            return_attention_mask=True,
            padding=True,
        )

        input_values = inputs.input_values.to(self.device)
        attention_mask = inputs.attention_mask.to(self.device)

        # Forward pass through frozen encoder
        outputs = self.model(input_values=input_values, attention_mask=attention_mask)
        hidden_states = outputs.last_hidden_state  # Shape: (1, T, 1024)

        # Calculate valid frame mask downsampled by the convolutional feature extractor
        if attention_mask is not None:
            # Wav2Vec2 feature extractor downsamples the input mask to match frame length T
            frame_mask = self.model._get_feature_vector_attention_mask(
                hidden_states.shape[1], attention_mask
            )
        else:
            frame_mask = torch.ones(
                (hidden_states.shape[0], hidden_states.shape[1]),
                dtype=torch.long,
                device=self.device,
            )

        return hidden_states, frame_mask
