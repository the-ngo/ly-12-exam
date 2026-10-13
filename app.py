import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="On tap Ly 12 - AI", layout="centered")
API_KEY=""
genai.configure(api_key="API_KEY")
model=genai.GenerativeModel('gemini-1.5-flash')
st.title("On Tap Kiem Tra Ly Lop 12")
st.write("Ung dung thong minh ho tro on tap bam sat ma tran de thi")
st.sidebar.header("Thong tin hoc sinh")
name=st.sidebar.text_input("Ho va ten:")
cl = st.sidebar.text_input("Lop:")
if not name or not cl:
  st.warning("Thay/Co va cac em hoc sinh vui long nhap ho ten va lop o thanh ben trai de bat dau")
  st.stop()
st.success(f"Chao em **{name}** - Lop **{cl}**! Hay chon noi dung on tap ben duoi.")
tab1, tab2, tab3 = st.tabs(["1. Chon bai kiem tra", "2. Chon phan on tap", "Lich su & tien bo"])
with tab1:
  st.subheader("Chon ky thi can on tap")
  exam_type = st.selectbox("Ky thi:", ["-- Chon ky thi --","Kiem tra giua ky 1", "Kiem tra cuoi ky 1", "Kiem tra giua ky 2", "Kiem tra cuoi ky 2"])
  if exam_period := exam_type != "--Chon ky thi --" :
    st.info(f"Da chon: **{exam_type}**. Vui long chuyen sang **Tab 2** de chon hinh thuc lam bai")
with tab2:
  st.subheader("Chon cau truc phan on tap:")
  section = st.radio("Hinh thuc:",[
    "Phan 1 - Trac nghiem nhieu lua chon (16 cau)",
    "Phan 2 - Trac nghiem dung sai (3cau)",
    "Phan 3 - Trac nghiem tra loi ngan (6 cau)",
    "Toan bo de kiem tra (Day du 3 phan)"])
  if st.button("Tao de on tap bang AI"):
    with st.spinner("AI dang bien soan de on tap bam sat ma tran cho em ..."):
      prompt = f"Hay tao 1 de on tap mon Vat ly lop 12 phan {section}. Trinh bay ro rang cau hoi, cac dap an va chua khoang trong."
      response = model.generate_content(prompt)
      st.session_state['de_thi'] = response.text
      st.markdown("### De on tap cua em:")
      format_text = st.session_state.get('de_thi','')
      st.write(format_text)
      st.divider()
      if st.button("Xem ket qua va huong dan giai"):
        st.success("He thong da ghi nhan bai lam")
        st.markdown("### Phan tich dap an va loi giai chi tiet tu AI:")
        explain_prompt = f"Dua tren de thi vua tao, hay cung cap bang dap an chi tiet va huong dan giai thich tung cau that de hieu cho hoc sinh lop 12"
        explaination = model.generate_content(explain_prompt)
        st.write(explaination.text)
        st.markdown("---")
        st.subheader("... Goc thac mac voi AI")
        st.markdown("_Neu em co thac mac nao, hay viet vao day:_")
        user_q = st.text_input("Cau hoi thac mac cua em:")
        if user_q:
          ans = model.generate_content(f"Giai dap thac mac cho hoc sinh: {user_q}")
          st.write(ans.text)
with tab3:
  st.subheader("Theo doi su tien bo")
  role = st.radio("Ban la ai?",["Hoc sinh","Giao vien"])
  if role == "Hoc sinh":
    st.info(f"Lich su on tap cua hoc sinh **{name} ({cl})**. He thong dang luu vet cac bai lam cua em")
  else:
    password = st.text_input("Nhap ma giao vien:",type="password")
    if password == "vatly123":
      st.success("Dang nhap quyen giao vien thanh cong")
      st.write("Tong hop lich su luyen tap cua toan bo hoc sinh lop 12(Du lieu mau).")
    elif password:
      st.error("Sai mat ma")
  
