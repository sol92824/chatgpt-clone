import streamlit as st

# streamlit을 쓸 때 주의사항
# 내부 데이터가 변경되면 전체 streamlit 소스가 재실행
# 리렌더링의 영향없이 유지하고 싶은 데이터는 session_state를 통해 저장

# session_state에 is_admin이 없다면 실행 (최초 1회만 실행)
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

st.header("Hello!")

name = st.text_input("What is your name?")

if name:
    st.write(f"Hello {name}")
    st.session_state["is_admin"] = True

print(st.session_state["is_admin"])