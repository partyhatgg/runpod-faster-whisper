from concurrent.futures import ThreadPoolExecutor

import numpy as np
from faster_whisper import WhisperModel
from faster_whisper.utils import format_timestamp
from runpod.serverless.utils import rp_cuda

MODEL_NAMES = ["medium", "turbo"]


class Predictor:
    def __init__(self):
        self.models = {}

    def load_model(self, model_name):
        loaded_model = WhisperModel(
            model_name,
            device="cuda" if rp_cuda.is_available() else "cpu",
            compute_type="float16" if rp_cuda.is_available() else "int8",
        )
        return model_name, loaded_model

    def setup(self):
        with ThreadPoolExecutor() as executor:
            for model_name, model in executor.map(self.load_model, MODEL_NAMES):
                if model_name is not None:
                    self.models[model_name] = model

    def predict(
        self,
        audio,
        model_name="medium",
        transcription="plain_text",
        translate=False,
        translation="plain_text",
        language=None,
        temperature=0,
        best_of=5,
        beam_size=5,
        patience=1,
        length_penalty=None,
        suppress_tokens="-1",
        initial_prompt=None,
        condition_on_previous_text=True,
        temperature_increment_on_fallback=0.2,
        compression_ratio_threshold=2.4,
        logprob_threshold=-1.0,
        no_speech_threshold=0.6,
        enable_vad=False,
        word_timestamps=False,
    ):
        model = self.models.get(model_name)
        if not model:
            raise ValueError(f"Model '{model_name}' not found.")

        if temperature_increment_on_fallback is not None:
            temperature = tuple(np.arange(temperature, 1.0 + 1e-6, temperature_increment_on_fallback))
        else:
            temperature = [temperature]

        segments, info = model.transcribe(
            str(audio),
            language=language,
            task="transcribe",
            beam_size=beam_size,
            best_of=best_of,
            patience=patience,
            length_penalty=length_penalty,
            temperature=temperature,
            compression_ratio_threshold=compression_ratio_threshold,
            log_prob_threshold=logprob_threshold,
            no_speech_threshold=no_speech_threshold,
            condition_on_previous_text=condition_on_previous_text,
            initial_prompt=initial_prompt,
            prefix=None,
            suppress_blank=True,
            suppress_tokens=[-1],
            without_timestamps=False,
            max_initial_timestamp=1.0,
            word_timestamps=word_timestamps,
            vad_filter=enable_vad,
        )

        segments = list(segments)
        transcription_output = format_segments(transcription, segments)

        translation_output = None
        if translate:
            translation_segments, _ = model.transcribe(str(audio), task="translate", temperature=temperature)
            translation_output = format_segments(translation, translation_segments)

        results = {
            "segments": serialize_segments(segments),
            "detected_language": info.language,
            "transcription": transcription_output,
            "translation": translation_output,
            "device": "cuda" if rp_cuda.is_available() else "cpu",
            "model": model_name,
        }

        if word_timestamps:
            results["word_timestamps"] = [
                {"word": word.word, "start": word.start, "end": word.end}
                for segment in segments
                for word in segment.words
            ]

        return results


def serialize_segments(transcript):
    return [
        {
            "id": segment.id,
            "seek": segment.seek,
            "start": segment.start,
            "end": segment.end,
            "text": segment.text,
            "tokens": segment.tokens,
            "temperature": segment.temperature,
            "avg_logprob": segment.avg_logprob,
            "compression_ratio": segment.compression_ratio,
            "no_speech_prob": segment.no_speech_prob,
        }
        for segment in transcript
    ]


def format_segments(output_format, segments):
    if output_format == "plain_text":
        return " ".join(segment.text.lstrip() for segment in segments)
    if output_format == "formatted_text":
        return "\n".join(segment.text.lstrip() for segment in segments)
    if output_format == "srt":
        return write_srt(segments)
    return write_vtt(segments)


def write_vtt(transcript):
    lines = []
    for segment in transcript:
        lines.append(f"{format_timestamp(segment.start)} --> {format_timestamp(segment.end)}")
        lines.append(segment.text.strip().replace("-->", "->"))
        lines.append("")
    return "\n".join(lines)


def write_srt(transcript):
    lines = []
    for i, segment in enumerate(transcript, start=1):
        lines.append(str(i))
        start = format_timestamp(segment.start, always_include_hours=True, decimal_marker=",")
        end = format_timestamp(segment.end, always_include_hours=True, decimal_marker=",")
        lines.append(f"{start} --> {end}")
        lines.append(segment.text.strip().replace("-->", "->"))
        lines.append("")
    return "\n".join(lines)
