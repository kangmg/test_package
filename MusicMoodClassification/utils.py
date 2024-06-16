import pytube
from pytube import YouTube, Search
import os
from IPython.display import clear_output
import time
from scipy.io import wavfile
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_audio
from scipy.io.wavfile import write
import polars as pl
import glob

def is_ipython():
  try:
    __IPYTHON__
    return True
  except NameError:
    return False

def get_top_yt_url(search_query:str, MaxLen:int, warning_msg:bool=True):
    '''
    Description
    -----------
    - youtube에서 qurey를 검색하고 가장 상단의 영상 링크를 반환하는 함수
        - 만약 영상의 길이가 MaxLen[s] 이상이면 두번째 영상의 링크를 반환
    - 개인화 추천 시스템으로 인해서 직접 검색했을 때랑 결과가 다를 수 있음

    Parameters
    ----------
    - search_query(str): 검색어
    - warning_msg(bool): 검색 실패 시 경고 메시지 출력 여부

    Returns
    -------
    - yt_link(str): 영상 유튜브 링크
    '''
    # search
    try:
        search = Search(search_query)
        first_content = search.results[0]
        # 영상 길이가 최대 길이 제한보다 작은지 확인
        if first_content.length > 600:
            # 2번째도 10분보다 길면 None 반환 / 3번째 부터는 음원 신뢰도가 떨어진다고 판단
            if search.results[1].length > 600: return None
            yt_link = search.results[1].watch_url
        else:
            yt_link = first_content.watch_url
        return yt_link
    except:
        if warning_msg : print(f"[Warning] 검색 실패 : {search_query}")
        return None


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
      - 'full' -> 자르지 않음
      - int [s] e.g. 
        - 30 --> 30 sec로 고정
    '''
    input_path = os.path.join(filepath, f"{id}.mp4")
    output_wav_path = os.path.join(filepath, f"{id}.wav")
    temp_output_path = os.path.join(filepath, f"{id}_temp.wav")

    # Extract audio from the video using ffmpeg directly
    ffmpeg_extract_audio(input_path, temp_output_path, fps=sr)
    time.sleep(0.1)

    # Load the audio data from the temporary file
    _, audio_array = wavfile.read(temp_output_path)
    
    # Flatten to mono if stereo
    if audio_array.ndim > 1:
        audio_array = audio_array.mean(axis=1)

    if not max_length == 'full':
        target_length = int(sr * max_length)
        audio_array = audio_array[:target_length]
        # Save the adjusted audio data to the output path
    
    # save audio
    write(output_wav_path, sr, audio_array)

    # Remove the temporary and original MP4 files
    os.remove(temp_output_path)
    os.remove(input_path)


def YT_link_downloader(youtube_url:str, download_path:str="./tmp", sr=22050, music_len_sec:int|str=120, clear_log:bool=True):
    """
    Description
    -----------
    youtube 링크의 음원 파일을 다운로드 하는 함수

    Parameters
    ----------
    - youtube_url(str) : 다운받을 youtube 영상의 링크
    - download_path(str) : 음원을 저장할 위치
    - sr(int) : sampling rate (default : 22,050 Hz)
    - music_len_sec(int|str) : 자를 음원의 길이 ( default 120 sec )
    - clear_log(bool) : 결과 log 출력을 지울 것인지 여부
    """
    # 폴더가 존재하는지 확인
    if not os.path.exists(download_path):
        os.mkdir(download_path)

   # download music from youtube
    yt = YouTube(youtube_url)
    yt_id = yt.video_id

    # check length > music_len_sec [s]
    if yt.length < music_len_sec:
        print(f"[Warning] 영상 다운 실패 : {youtube_url}")
        raise Exception(f"Music length is shorter than {music_len_sec}")

    audio = yt.streams.filter(only_audio=True).first()
    name = yt_id + ".mp4"
    try:
        audio.download(output_path=download_path, filename=name)
        time.sleep(0.2)
        convertor(filepath=download_path, id=yt_id, sampling_rate=sr, max_length=music_len_sec)
    except:
        # [TODO] download 는 성공했는데 convertor 실패시에 mp4 파일 삭제 
        print(f"[Warning] 영상 다운 실패 : {youtube_url}")
    
    # 출력 로그 지우기
    if clear_log and is_ipython():
        clear_output()


def YT_query_downloader(youtube_query:str, download_path:str="./tmp", sr=22050, music_len_sec:int|str=120, MaxLen:int=600, clear_log:bool=True):
    '''
    Description
    -----------
    youtube 검색어를 활용하여 음원 파일을 다운로드 하는 함수
    가장 상단의 음원 다운로드를 시도하고 영상의 길이가 MaxLen 보다 크면 두번째 영상을 다운로드함. 두번째 영상도 조건에 맞지 않으면 에러 반환

    Parameters
    ----------
    - youtube_url(str) : 다운받을 youtube 영상의 검색
    - download_path(str) : 음원을 저장할 위치
    - sr(int) : sampling rate (default : 22,050 Hz)
    - music_len_sec(int|str) : 자를 음원의 길이 ( default 120 sec )
    - MaxLen(int) : 600 sec ( 음원이 10분 이상이면 다운로드 제한 )
    - clear_log(bool) : 결과 log 출력을 지울 것인지 여부
    '''
    # 폴더가 존재하는지 확인
    if not os.path.exists(download_path):
        os.mkdir(download_path)

    # search
    youtube_url = get_top_yt_url(
        search_query=youtube_query,
        MaxLen=MaxLen,
        warning_msg=True,
    )
    if youtube_url == None: raise Exception(f"[Warning] Youtube 검색 결과의 신뢰성 문제 : {youtube_query}")

   # download music from youtube
    yt = YouTube(youtube_url)
    yt_id = yt.video_id

    # check length > music_len_sec [s]
    if yt.length < music_len_sec:
        print(f"[Warning] 영상 다운 실패 : {youtube_url}")
        raise Exception(f"Music length is shorter than {music_len_sec}")

    audio = yt.streams.filter(only_audio=True).first()
    name = yt_id + ".mp4"
    try:
        audio.download(output_path=download_path, filename=name)
        time.sleep(0.2)
        convertor(filepath=download_path, id=yt_id, sampling_rate=sr, max_length=music_len_sec)
    except:
        # [TODO] download 는 성공했는데 convertor 실패시에 mp4 파일 삭제 
        print(f"[Warning] 영상 다운 실패 : {youtube_url}")
    
    # 출력 로그 지우기
    if clear_log and is_ipython():
        clear_output()


from preprocessing import get_mcff, get_centroid, get_crossing
def dataset_builder(data_dir:str):
    datafiles = glob.glob(os.path.join(data_dir, '*.wav'))
    datafile_names = [os.path.basename(filepath) for filepath in datafiles]
    DataSet = pl.DataFrame({
        "FileName" : datafile_names,
        "FilePath" : datafiles
    })
    FeatureDF = DataSet.with_columns(
    (pl.col("FilePath").apply(get_mcff)).alias("MCFF"),
    (pl.col("FilePath").apply(get_centroid)).alias("centroid"),
    (pl.col("FilePath").apply(get_crossing)).alias("crossing")
    ).select(["MCFF", "centroid", "crossing"])

    # mood prediction
    



