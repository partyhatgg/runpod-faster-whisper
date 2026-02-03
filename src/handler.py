import base64
import tempfile

import runpod
from runpod.serverless.utils import download_files_from_urls, rp_cleanup
from runpod.serverless.utils.rp_validator import validate

from src.schema import INPUT_VALIDATIONS
from src.predict import Predictor

MODEL = Predictor()


def base64_to_tempfile(base64_file):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_file.write(base64.b64decode(base64_file))
    return temp_file.name


def handler(job):
    job_input = job["input"]

    input_validation = validate(job_input, INPUT_VALIDATIONS)
    if "errors" in input_validation:
        return {"error": input_validation["errors"]}
    job_input = input_validation["validated_input"]

    has_audio = job_input.get("audio")
    has_base64 = job_input.get("audio_base64")

    if not has_audio and not has_base64:
        return {"error": "Must provide either audio or audio_base64"}
    if has_audio and has_base64:
        return {"error": "Must provide either audio or audio_base64, not both"}

    if has_audio:
        audio_input = download_files_from_urls(job["id"], [job_input["audio"]])[0]
    else:
        audio_input = base64_to_tempfile(job_input["audio_base64"])

    whisper_results = MODEL.predict(
        audio=audio_input,
        model_name=job_input["model"],
        transcription=job_input["transcription"],
        translation=job_input["translation"],
        translate=job_input["translate"],
        language=job_input["language"],
        temperature=job_input["temperature"],
        best_of=job_input["best_of"],
        beam_size=job_input["beam_size"],
        patience=job_input["patience"],
        length_penalty=job_input["length_penalty"],
        suppress_tokens=job_input.get("suppress_tokens", "-1"),
        initial_prompt=job_input["initial_prompt"],
        condition_on_previous_text=job_input["condition_on_previous_text"],
        temperature_increment_on_fallback=job_input["temperature_increment_on_fallback"],
        compression_ratio_threshold=job_input["compression_ratio_threshold"],
        logprob_threshold=job_input["logprob_threshold"],
        no_speech_threshold=job_input["no_speech_threshold"],
        enable_vad=job_input["enable_vad"],
        word_timestamps=job_input["word_timestamps"],
    )

    rp_cleanup.clean(["input_objects"])

    return whisper_results


if __name__ == "__main__":
    MODEL.setup()
    runpod.serverless.start({"handler": handler})
