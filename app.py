from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

import sounddevice as sd
import soundfile as sf
import whisper
from dotenv import load_dotenv
from gtts import gTTS
from gtts.lang import tts_langs
from openai import OpenAI


EXIT_COMMANDS = {"sair", "exit", "quit"}


def temp_file(suffix: str) -> str:
    file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    file.close()
    return file.name


def cleanup(*paths: str | None) -> None:
    for path in paths:
        if path and os.path.exists(path):
            os.remove(path)


def record_audio(seconds: int, sample_rate: int) -> str:
    path = temp_file(".wav")
    print(f"Gravando por {seconds}s...")
    audio = sd.rec(int(seconds * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    sf.write(path, audio, sample_rate)
    return path


def transcribe_audio(model, path: str, language: str) -> tuple[str, str]:
    result = model.transcribe(path, fp16=False, language=None if language == "auto" else language)
    text = result.get("text", "").strip()
    detected_language = (result.get("language") or language or "pt").split("-")[0].lower()
    if not text:
        raise RuntimeError("Nenhuma fala foi detectada. Tente novamente.")
    return text, detected_language


def ask_chatgpt(client: OpenAI, model_name: str, text: str, language: str) -> str:
    response = client.responses.create(
        model=model_name,
        input=f"You are a multilingual voice assistant. Reply briefly and naturally in {language}. User said: {text}",
    )
    answer = (response.output_text or "").strip()
    if not answer:
        raise RuntimeError("A API retornou uma resposta vazia.")
    return answer


def speak(text: str, language: str) -> None:
    languages = tts_langs()
    language = language if language in languages else language.split("-")[0].lower()
    if language not in languages:
        language = "en"

    mp3_path = temp_file(".mp3")
    wav_path = temp_file(".wav")
    try:
        gTTS(text=text, lang=language, slow=False).save(mp3_path)
        result = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", mp3_path, wav_path],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Falha ao converter audio: {result.stderr.strip()}")
        audio, sample_rate = sf.read(wav_path, dtype="float32")
        sd.play(audio, sample_rate)
        sd.wait()
    finally:
        cleanup(mp3_path, wav_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assistente de Voz Multi-Idiomas com Whisper e ChatGPT")
    parser.add_argument("--whisper-model", default=os.getenv("WHISPER_MODEL", "small"))
    parser.add_argument("--chat-model", default=os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini"))
    parser.add_argument("--input-language", default=os.getenv("INPUT_LANGUAGE", "auto"))
    parser.add_argument("--output-language", default=os.getenv("OUTPUT_LANGUAGE") or None)
    parser.add_argument("--record-seconds", type=int, default=int(os.getenv("RECORD_SECONDS", "6")))
    parser.add_argument("--sample-rate", type=int, default=int(os.getenv("SAMPLE_RATE", "16000")))
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("Erro: defina OPENAI_API_KEY no ambiente ou em .env.", file=sys.stderr)
        return 1
    if shutil.which("ffmpeg") is None:
        print("Erro: FFmpeg nao foi encontrado no PATH.", file=sys.stderr)
        return 1

    client = OpenAI(api_key=api_key)
    whisper_model = whisper.load_model(args.whisper_model)

    print("Assistente iniciado. Pressione Enter para gravar ou digite 'sair' para encerrar.\n")
    while True:
        if input("> ").strip().lower() in EXIT_COMMANDS:
            return 0

        audio_path = None
        try:
            audio_path = record_audio(args.record_seconds, args.sample_rate)
            text, detected_language = transcribe_audio(whisper_model, audio_path, args.input_language)
            reply_language = args.output_language or detected_language
            answer = ask_chatgpt(client, args.chat_model, text, reply_language)
            print(f"Voce: {text}")
            print(f"Assistente: {answer}")
            speak(answer, reply_language)
        except KeyboardInterrupt:
            print("\nExecucao interrompida pelo usuario.")
            return 130
        except Exception as exc:
            print(f"Erro: {exc}", file=sys.stderr)
        finally:
            cleanup(audio_path)


if __name__ == "__main__":
    raise SystemExit(main())

    def synthesize_response(self, response_text: str, detected_language: str) -> Path:
        tts_language = self.resolve_tts_language(detected_language)
        mp3_path = Path(tempfile.mkstemp(suffix=".mp3", prefix="voice_reply_")[1])
        wav_path = Path(tempfile.mkstemp(suffix=".wav", prefix="voice_reply_")[1])
        gTTS(text=response_text, lang=tts_language, slow=False).save(str(mp3_path))
        self.convert_mp3_to_wav(mp3_path, wav_path)
        self.cleanup_file(mp3_path)
        return wav_path

    def play_audio(self, audio_path: Path) -> None:
        audio_data, sample_rate = sf.read(str(audio_path), dtype="float32")
        sd.play(audio_data, sample_rate)
        sd.wait()

    def resolve_tts_language(self, detected_language: str) -> str:
        preferred_language = self.config.output_language or detected_language or "pt"
        primary_code = preferred_language.split("-")[0].lower()

        if preferred_language in self._tts_languages:
            return preferred_language

        if primary_code in self._tts_languages:
            return primary_code

        return "en"

    def get_whisper_model(self):
        if self._whisper_model is None:
            if shutil.which("ffmpeg") is None:
                raise RuntimeError(
                    "FFmpeg nao foi encontrado no PATH. Instale o FFmpeg antes de usar o Whisper localmente."
                )

            print(f"Carregando modelo Whisper '{self.config.whisper_model_name}'...")
            self._whisper_model = whisper.load_model(self.config.whisper_model_name)

        return self._whisper_model

    @staticmethod
    def convert_mp3_to_wav(source_path: Path, target_path: Path) -> None:
        command = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(source_path),
            str(target_path),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(
                f"Falha ao converter audio de resposta com ffmpeg: {completed.stderr.strip()}"
            )

    @staticmethod
    def extract_response_text(response) -> str:
        output_text = getattr(response, "output_text", "")
        if output_text:
            return output_text

        texts: list[str] = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text_value = getattr(content, "text", None)
                if text_value:
                    texts.append(text_value)

        return "\n".join(texts)

    @staticmethod
    def cleanup_file(file_path: Path | None) -> None:
        if file_path and file_path.exists():
            file_path.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assistente de Voz Multi-Idiomas com Whisper e ChatGPT"
    )
    parser.add_argument(
        "--whisper-model",
        default=os.getenv("WHISPER_MODEL", DEFAULT_WHISPER_MODEL),
        help="Modelo Whisper local. Ex.: tiny, base, small, medium, large.",
    )
    parser.add_argument(
        "--chat-model",
        default=os.getenv("OPENAI_CHAT_MODEL", DEFAULT_CHAT_MODEL),
        help="Modelo da OpenAI para gerar a resposta.",
    )
    parser.add_argument(
        "--input-language",
        choices=WHISPER_LANGUAGE_OPTIONS,
        default=os.getenv("INPUT_LANGUAGE", "auto"),
        help="Idioma esperado na fala. Use 'auto' para deteccao automatica.",
    )
    parser.add_argument(
        "--output-language",
        choices=TTS_LANGUAGE_OPTIONS,
        default=os.getenv("OUTPUT_LANGUAGE") or None,
        help="Idioma forcado para a resposta em texto e voz.",
    )
    parser.add_argument(
        "--record-seconds",
        type=int,
        default=int(os.getenv("RECORD_SECONDS", "6")),
        help="Tempo de gravacao em segundos.",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=int(os.getenv("SAMPLE_RATE", "16000")),
        help="Taxa de amostragem do audio.",
    )
    return parser


def validate_environment(api_key: str | None) -> str:
    if not api_key:
        raise RuntimeError(
            "Defina OPENAI_API_KEY no ambiente ou em um arquivo .env antes de executar o app."
        )

    return api_key


def main() -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()

    try:
        api_key = validate_environment(os.getenv("OPENAI_API_KEY"))
        assistant = VoiceAssistant(
            AssistantConfig(
                api_key=api_key,
                whisper_model_name=args.whisper_model,
                chat_model_name=args.chat_model,
                input_language=args.input_language,
                output_language=args.output_language,
                record_seconds=args.record_seconds,
                sample_rate=args.sample_rate,
            )
        )
        assistant.run()
        return 0
    except KeyboardInterrupt:
        print("\nExecucao interrompida pelo usuario.")
        return 130
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
