import streamlit as st
import os
import base64
from audiorecorder import audiorecorder
from openai import OpenAI
from datetime import datetime
from gtts import gTTS
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

if "chat" not in st.session_state:
    st.session_state.chat = []

if "messages" not in st.session_state:
    st.session_state.messages = []

if "check_reset" not in st.session_state:
    st.session_state.check_reset = False

##### 기능 구현 함수 #####
def STT(audio):
    # 파일 저장
    filename = 'input.mp3'
    audio.export(filename, format="mp3")
    # 음원 파일 열기
    audio_file = open(filename, "rb")
    # Whisper 모델을 활용해 텍스트 얻기
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    audio_file.close()
    # 파일 삭제
    os.remove(filename)
    return transcript.text


def ask_gpt(prompt, model):
    response = client.chat.completions.create(model=model, messages=prompt)
    return response.choices[0].message.content
    # system_message = response["choices"][0]["message"]
    # return system_message["content"]


def TTS(response):
    # gTTS 를 활용하여 음성 파일 생성
    filename = "output.mp3"
    tts = gTTS(text=response, lang="ko")
    tts.save(filename)

    # 음원 파일 자동 재생생
    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True, )
    # 파일 삭제
    os.remove(filename)


## 메인 함수 ##
def main():
    st.set_page_config(
        page_title="음성 비서 프로그램",
        page_icon="🇰🇷",
        layout="wide"
    )

    # 제목
    st.header("음성 비서 프로그램")

    # 기본 설명
    with st.expander("음성비서 프로그램에 관하여", expanded=False):
        st.write(
            """
            - 음성 비서 프로그램의 UI는 스트림릿을 사용했습니다.
            - STT(Speech to Text)는 OpenAI의 Whisper AI를 활용했습니다.
            - 답변은 OpenAI의 GPT 모델을 활용했습니다.
            - TTS(Text-to-Speech)는 구글의 Google Translate TTS를 활용했습니다.
            """
        )

        st.markdown("")

    # 사이드바 생성
    with st.sidebar:
        # GPT 모델을 선택하기 위한 라디오 버튼 생성
        model = st.selectbox(label="GPT 모델", options=['gpt-4', 'gpt-3.5-turbo'])
        st.markdown("")

        # 리셋 버튼 생성
        if st.button(label="초기화", use_container_width=True):
            # 리셋 코드
            pass

    # 기능 구현 공간
    col1, col2 = st.columns(2)
    with col1:
        # 왼쪽 영역 작성
        st.subheader("질문하기")
        # 음성 녹음 아이콘 추가
        audio = audiorecorder("클릭하여 녹음하기", "녹음중...")
        if (audio.duration_seconds > 0) and (st.session_state.check_reset == False):
            # 음성 재생
            st.audio(audio.export().read())
            # 음원 파일에서 텍스트 추출
            question = STT(audio)
            # 채팅을 시각화하기 위해 질문 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state.chat = st.session_state.chat + [("user", now, question)]
            # GPT 모델에 넣을 프롬프트를 위해 질문 내용 저장
            st.session_state.messages = st.session_state.messages + [{"role": "user", "content": question}]

    with col2:
        # 오른쪽 영역 작성
        st.subheader("질문/답변")
        if (audio.duration_seconds > 0) and (st.session_state.check_reset == False):
            # ChatGPT에게 답변 얻기
            response = ask_gpt(st.session_state.messages, model)

            # GPT 모델에 넣을 프롬프트를 위해 답변 내용 저장
            st.session_state.messages = st.session_state.messages + [{"role": "system", "content": response}]

            # 채팅 시각화를 위한 답변 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state.chat = st.session_state.chat + [("bot", now, response)]

            # 채팅 형식으로 시각화 하기
            for sender, time, message in st.session_state.chat:
                if sender == "user":
                    st.write(
                        f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>',
                        unsafe_allow_html=True)
                    st.write("")
                else:
                    st.write(
                        f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>',
                        unsafe_allow_html=True)
                    st.write("")

            # gTTS 를 활용하여 음성 파일 생성 및 재생
            TTS(response)
        else:
            st.session_state.check_reset = False


if __name__ == "__main__":
    main()
