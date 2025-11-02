from google import genai
import asyncio
from hume import AsyncHumeClient
from hume.expression_measurement.stream import Config
from hume.expression_measurement.stream.socket_client import StreamConnectOptions

from decouple import config

import pyaudio
import wave


def record_audio(filename="temp.wav", record_seconds=5, channels=1, rate=44100, chunk=1024):
    p = pyaudio.PyAudio()

    print("Recording... Speak now!")

    stream = p.open(format=pyaudio.paInt16,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)

    frames = []

    for _ in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)

    print("Recording finished.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    print(f"Audio saved as {filename}")

def split_hume_thingy(result):
    for res in result:
        for x in res:
            print(x)
            
                

if __name__ == "__main__":
    record_audio()

async def main():
    client = AsyncHumeClient(api_key=config("HUME_API_KEY"))
    model_config = Config(prosody={})
    stream_options = StreamConnectOptions(config=model_config)
    async with client.expression_measurement.stream.connect(options=stream_options) as socket:
        result = await socket.send_file("temp.wav")
        return result
if __name__ == "__main__":

    result = asyncio.run(main())
    split_hume_thingy(result)