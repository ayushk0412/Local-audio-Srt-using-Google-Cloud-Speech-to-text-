import os
import io
from google.cloud import speech
import datetime
import srt

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "folkloric-byway-315305-45857f71933e.json"

client = speech.SpeechClient()
path = 'media/audio_file1.wav'
with io.open(path, "rb") as audio_file:
    content = audio_file.read()

audio = speech.RecognitionAudio(content=content)
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=24000,
    language_code="en-US",
    use_enhanced=True,
    enable_automatic_punctuation=True,
    # A model must be specified to use enhanced model.
    model="phone_call",
    enable_word_time_offsets=True

)

response = client.recognize(config=config, audio=audio)

for i, result in enumerate(response.results):
    alternative = result.alternatives[0]
    print("-" * 20)
    print("First alternative of result {}".format(i))
    print("Transcript: {}".format(alternative.transcript))

for word in alternative.words:
    start_s = word.start_time.total_seconds()
    end_s = word.end_time.total_seconds()
    word = word.word
    print(f"{start_s:>7.3f} | {end_s:>7.3f} | {word}")


def subtitle_generation(speech_to_text_response, bin_size=3):
    """We define a bin of time period to display the words in sync with audio. 
    Here, bin_size = 3 means each bin is of 3 secs. 
    All the words in the interval of 3 secs in result will be grouped togather."""
    transcriptions = []
    index = 0

    for result in response.results:
        try:
            if result.alternatives[0].words[0].start_time.seconds:
                # bin start -> for first word of result
                start_sec = result.alternatives[0].words[0].start_time.seconds
                start_microsec = result.alternatives[0].words[0].start_time.microseconds * 0.001
            else:
                # bin start -> For First word of response
                start_sec = 0
                start_microsec = 0
            end_sec = start_sec + bin_size  # bin end sec

            # for last word of result
            last_word_end_sec = result.alternatives[0].words[-1].end_time.seconds
            last_word_end_microsec = result.alternatives[0].words[-1].end_time.microseconds * 0.001

            # bin transcript
            transcript = result.alternatives[0].words[0].word

            index += 1  # subtitle index

            for i in range(len(result.alternatives[0].words) - 1):
                try:
                    word = result.alternatives[0].words[i + 1].word
                    word_start_sec = result.alternatives[0].words[i +
                                                                  1].start_time.seconds
                    # 0.001 to convert nana -> micro
                    word_start_microsec = result.alternatives[0].words[i +
                                                                       1].start_time.microseconds * 0.001
                    word_end_sec = result.alternatives[0].words[i +
                                                                1].end_time.seconds
                    word_end_microsec = result.alternatives[0].words[i +
                                                                     1].end_time.microseconds * 0.001

                    if word_end_sec < end_sec:
                        transcript = transcript + " " + word
                    else:
                        previous_word_end_sec = result.alternatives[0].words[i].end_time.seconds
                        previous_word_end_microsec = result.alternatives[
                            0].words[i].end_time.microseconds * 0.001

                        # append bin transcript
                        transcriptions.append(srt.Subtitle(index, datetime.timedelta(0, start_sec, start_microsec), datetime.timedelta(
                            0, previous_word_end_sec, previous_word_end_microsec), transcript))

                        # reset bin parameters
                        start_sec = word_start_sec
                        start_microsec = word_start_microsec
                        end_sec = start_sec + bin_size
                        transcript = result.alternatives[0].words[i + 1].word

                        index += 1
                except IndexError:
                    pass
            # append transcript of last transcript in bin
            transcriptions.append(srt.Subtitle(index, datetime.timedelta(
                0, start_sec, start_microsec), datetime.timedelta(0, last_word_end_sec, last_word_end_microsec), transcript))
            index += 1
        except IndexError:
            pass

    # turn transcription list into subtitles
    subtitles = srt.compose(transcriptions)
    return subtitles


subtitles = subtitle_generation(response)
with open("subtitles.srt", "w") as f:
    f.write(subtitles)
