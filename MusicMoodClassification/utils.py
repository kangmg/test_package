import pytube
from pytube import YouTube
import os
from IPython.display import clear_output
import time
from scipy.io import wavfile
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_audio
from scipy.io.wavfile import write


def is_ipython():
  try:
    __IPYTHON__
    return True
  except NameError:
    return False

"""
def convertor(filepath:str, id:str, sr:int=22050, max_length:str|int="full"):
    '''
    Description
    -----------
    mp4 파일을 지정한 길이로 자른 후 wav 파일로 저장하는 함수

    Parameters
    ----------
    - filepath(str) : mp4 파일의 경로
    - id(str) : 유튜브 영상의 ID 정보
    - sr(int) : 음원의 sampling rate
    - max_length(int|str)
      - full -> 자르지 않음
      - 

    mp4 -> wav (first 30 seconds)
    Ensure the audio has a consistent length of sampling_rate * 30 samples.
    sampling_rate: sampling rate for the output audio file (default is 22050 Hz)
    '''
    input_path = os.path.join(path, f"{id}.mp4")
    output_wav_path = os.path.join(path, f"{id}.wav")
    temp_output_path = os.path.join(path, f"{id}_temp.wav")

    # Extract audio from the video using ffmpeg directly
    ffmpeg_extract_audio(input_path, temp_output_path, fps=sr, )
    time.sleep(0.1)
    # Load the audio data from the temporary file
    sr, audio_array = wavfile.read(temp_output_path)
    # Ensure the audio has a consistent length of sampling_rate * 30 samples
      target_length = int(sr * 30)
      # Flatten to mono if stereo
      if audio_array.ndim > 1:
        audio_array = audio_array.mean(axis=1)
    # ensure 30 sec
    audio_array = audio_array[:target_length]
    # Save the adjusted audio data to the output path
    write(output_wav_path, sr, audio_array)

    # Remove the temporary and original MP4 files
    os.remove(temp_output_path)
    os.remove(input_path)
"""

def YT_link_downloader(youtube_url:str, download_path:str="./tmp", sr=22050, clear_log:bool=True):
    """
    Description
    -----------
    youtube 링크의 음원 파일을 다운로드 하는 함수

    Parameters
    ----------
    - youtube_url(str) : 다운받을 youtube 영상의 링크
    - download_path(str) : 음원을 저장할 위치
    - sr(int) : sampling rate (default : 22,050 Hz)
    - clear_log(bool) : 결과 log를 제거할 것인지 여부

    Returns
    -------
    status : 
    """
    # 폴더가 존재하는지 확인
    if not os.path.exists(download_path):
        os.mkdir(download_path)

    yt = YouTube(youtube_url)
    yt_id = yt.video_id
    audio = yt.streams.filter(only_audio=True).first()
    name = yt_id + ".mp4"
    try:
        audio.download(output_path=download_path, filename=name)
        time.sleep(0.2)
        convertor(download_path, yt_id,  sampling_rate=sr)
    except:
        # [TODO] download 는 성공했는데 convertor 실패시에 mp4 파일 삭제 
        print(f"[Warning] 영상 다운 실패 : {youtube_url}")
    
    # 출력 로그 지우기
    if clear_log and is_ipython():
       clear_output()
