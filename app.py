import streamlit as st
import google.generativeai as genai
import docx
import json
from datetime import datetime
from streamlit_mic_recorder import mic_recorder
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Cấu hình giao diện ứng dụng 
st.set_page_config(page_title="Ôn tập Vật lý 12 - AI Pro", layout="centered")

# Cấu hình API Gemini (Thầy/cô thay mã API thật vào trong ngoặc kép hoặc dùng st.secrets)
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-3.5-flash-lite')

 
# Khởi tạo Session State lưu ma trận và trạng thái hệ thống
if 'matrices_dict' not in st.session_state:
    st.session_state['matrices_dict'] = {
        "Kiểm tra Giữa kỳ 1": "",
        "Kiểm tra Cuối kỳ 1": "",
        "Kiểm tra Giữa kỳ 2": "",
        "Kiểm tra Cuối kỳ 2": ""
    }

if 'matrix_parts' not in st.session_state:
    st.session_state['matrix_parts'] = {
        "Kiểm tra Giữa kỳ 1": None,
        "Kiểm tra Cuối kỳ 1": None,
        "Kiểm tra Giữa kỳ 2": None,
        "Kiểm tra Cuối kỳ 2": None
    }
# Bổ sung trạng thái quản lý đăng xuất an toàn cho giáo viên
if 'teacher_logged_in' not in st.session_state:
    st.session_state['teacher_logged_in'] = False
st.title("⚡ HỆ THỐNG ÔN TẬP VẬT LÝ 12 THÔNG MINH")
st.write("Ứng dụng tương tác thông minh hỗ trợ học sinh ôn tập bám sát ma trận đặc tả chuẩn mới.")

# Tạo các Tab chức năng chính
tab1, tab2, tab3 = st.tabs(["📂 1. Chọn Kỳ Thi & Ma Trận", "📝 2. Làm Bài & Tương Tác AI", "📊 3. Lịch Sử & Tiến Bộ"])

with tab1:
    st.subheader("Bước 1: Phân loại người dùng và chọn kỳ thi")
    
    # Phân tách 2 tab nhỏ: Học sinh và Giáo viên quản trị
    sub_tab_hs, sub_tab_gv = st.tabs(["👨‍🎓 Học sinh ôn tập", "🔐 Giáo viên quản trị"])
    
    with sub_tab_hs:
        st.markdown("### 📝 Thông tin học sinh & Chọn kỳ kiểm tra")
        st.markdown("##### 📌 Vui lòng điền thông tin cá nhân và bấm xác nhận trước khi chọn kỳ thi:")
        
        # Ô nhập liệu tối ưu trên điện thoại (không bắt buộc nhấn phím Enter trên bàn phím ảo)
        input_name = st.text_input("Họ và tên học sinh:", value=st.session_state.get('student_name', ''))
        input_class = st.text_input("Lớp:", value=st.session_state.get('student_class', ''))
        
        # Nút bấm hành động thân thiện với màn hình cảm ứng di động
        if st.button("🚀 Xác nhận thông tin học sinh"):
            if input_name.strip() and input_class.strip():
                st.session_state['student_name'] = input_name.strip()
                st.session_state['student_class'] = input_class.strip()
                st.success(f"Đã lưu thông tin: **{input_name.strip()}** - Lớp **{input_class.strip()}**! Em có thể chọn kỳ thi bên dưới.")
            else:
                st.warning("⚠️ Em vui lòng nhập đầy đủ cả Họ tên và Lớp nhé!")

        # Hộp chọn kỳ thi chỉ hiển thị sau khi học sinh đã xác nhận thông tin thành công
        if st.session_state.get('student_name') and st.session_state.get('student_class'):
            st.divider()
            exam_type = st.selectbox(
                "Chọn kỳ thi cần ôn tập:",
                ["-- Chọn kỳ thi --", "Kiểm tra Giữa kỳ 1", "Kiểm tra Cuối kỳ 1", "Kiểm tra Giữa kỳ 2", "Kiểm tra Cuối kỳ 2"],
                key="student_exam_select"
            )
            
            if exam_type != "-- Chọn kỳ thi --":
                st.session_state['selected_exam'] = exam_type
                matrix_content = st.session_state['matrices_dict'].get(exam_type, "")
                matrix_file_obj = st.session_state['matrix_parts'].get(exam_type, None)
                
                if matrix_content.strip() != "" or matrix_file_obj is not None:
                    st.success(f"✅ Kỳ thi **{exam_type}** đã sẵn sàng ma trận ôn tập!")
                    st.info("👉 Mời em chuyển sang **Tab 2 - Làm Bài & Tương Tác AI** ở phía trên để bắt đầu làm bài.")
                else:
                    st.error(f"❌ Kỳ thi **{exam_type}** hiện chưa được giáo viên cho phép ôn tập (chưa có ma trận). Em vui lòng chọn kỳ thi khác!")            
            
    with sub_tab_gv:
        st.markdown("### 🔒 Khu vực Quản trị dành cho Giáo viên")
        
        # Kiểm tra nếu chưa đăng nhập thì hiện ô nhập mật khẩu
        if not st.session_state['teacher_logged_in']:
            teacher_pass = st.text_input("Nhập mật mã quản trị giáo viên:", type="password", key="pwd_input_box_v2")
            col_p1, _ = st.columns([1, 4])
            with col_p1:
                if st.button("🔓 Đăng nhập quản trị"):
                    if teacher_pass == "vatly123":
                        st.session_state['teacher_logged_in'] = True
                        st.success("✅ Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("❌ Sai mật mã giáo viên!")
        else:
            st.success("🟢 Bạn đang ở phiên làm việc Quản trị viên.")
            
            # Nút đăng xuất xóa ngay trạng thái mật khẩu khỏi bộ nhớ phiên
            if st.button("🔒 Đăng xuất / Khóa phiên quản trị an toàn"):
                st.session_state['teacher_logged_in'] = False
                st.success("Đã khóa khu vực quản trị an toàn! Mật khẩu đã được xóa khỏi bộ nhớ.")
                st.rerun()
                
            st.divider()
            target_exam = st.selectbox("Chọn kỳ thi cần cập nhật ma trận:", ["Kiểm tra Giữa kỳ 1", "Kiểm tra Cuối kỳ 1", "Kiểm tra Giữa kỳ 2", "Kiểm tra Cuối kỳ 2"])
            
            current_text = st.session_state['matrices_dict'][target_exam]
            if current_text or st.session_state['matrix_parts'][target_exam] is not None:
                if st.button(f"🗑️ Xóa ma trận hiện tại của {target_exam}", key=f"del_{target_exam}"):
                    st.session_state['matrices_dict'][target_exam] = ""
                    st.session_state['matrix_parts'][target_exam] = None
                    st.success(f"Đã xóa ma trận của {target_exam} thành công!")
                    st.rerun()
            
            up_file = st.file_uploader(f"Tải file ma trận cho {target_exam} (.txt, .docx, .pdf, ảnh):", type=["txt", "docx", "pdf", "png", "jpg"], key=f"up_{target_exam}")
            matrix_input = st.text_area("Hoặc dán nội dung ma trận đặc tả:", value=current_text if not str(current_text).startswith("File") else "", key=f"txt_{target_exam}")
            
            if st.button("💾 Lưu ma trận vào hệ thống", key=f"save_{target_exam}"):
                extracted = matrix_input
                f_part = None
                if up_file is not None:
                    ext = up_file.name.split('.')[-1].lower()
                    if ext == "txt":
                        extracted = up_file.read().decode("utf-8")
                    elif ext == "docx":
                        doc = docx.Document(up_file)
                        extracted = "\n".join([p.text for p in doc.paragraphs])
                    elif ext in ["pdf", "png", "jpg"]:
                        f_bytes = up_file.read()
                        mime = "application/pdf" if ext == "pdf" else f"image/{ext}"
                        f_part = {"mime_type": mime, "data": f_bytes}
                        extracted = f"[File đính kèm: {up_file.name}]"
                
                st.session_state['matrices_dict'][target_exam] = extracted
                st.session_state['matrix_parts'][target_exam] = f_part
                st.success(f"Đã lưu thành công ma trận cho **{target_exam}**! Hãy bấm nút Đăng xuất bên trên khi làm xong.")
with tab2:
    # Lấy thông tin học sinh đã nhập ở Tab 1 (sub_tab_hs)
    name = st.session_state.get('student_name', '')
    cl = st.session_state.get('student_class', '')
    current_exam = st.session_state.get('selected_exam', '-- Chọn kỳ thi --')
    
    if not name or not cl:
        st.warning("⚠️ Vui lòng quay lại **Tab 1 -> Học sinh ôn tập** để nhập Họ tên và Lớp trước khi làm bài!")
    elif current_exam == '-- Chọn kỳ thi --':
        st.warning("⚠️ Em chưa chọn kỳ thi ôn tập ở Tab 1! Vui lòng quay lại Tab 1 để chọn kỳ thi.")
    else:
        # Kiểm tra lại tính sẵn sàng của ma trận
        active_matrix = st.session_state['matrices_dict'].get(current_exam, "")
        if not active_matrix.strip() and st.session_state['matrix_parts'].get(current_exam, None) is None:
            st.error(f"❌ Kỳ thi **{current_exam}** chưa có ma trận từ giáo viên. Em chưa thể tạo đề thi ở phần này.")
        else:
            st.write(f"Học sinh: **{name}** (Lớp **{cl}**) | Đang ôn tập kỳ thi: **{current_exam}**")        
        # CSS tùy biến nút bấm nổi bật
        st.markdown("""
            <style>
            div.stButton > button:first-child {
                background-color: #0066cc;
                color: white;
                font-weight: bold;
                font-size: 18px;
                padding: 10px 24px;
                border-radius: 8px;
                border: none;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            div.stButton > button:first-child:hover {
                background-color: #004080;
                color: #ffffff;
            }
            </style>
        """, unsafe_allow_html=True)
        if st.button("🚀 Bắt đầu tạo đề tương tác bám sát ma trận"):
            with st.spinner("🤖 AI đang phân tích ma trận và biên soạn đề thi chuẩn hóa cấu trúc Bộ GD&ĐT..."):
                active_matrix = st.session_state['matrices_dict'].get(current_exam, "")
             
                prompt = f"""
                Bạn là chuyên gia công nghệ thông tin và là chuyên gia ứng dụng trí tuệ nhân tạo AI vào dạy học môn Vật lí. Dựa vào ma trận đặc tả sau: {active_matrix}, hãy tạo các câu hỏi ôn tập cho phần '{section}'.
                
                LƯU Ý CỰC KỲ QUAN TRỌNG VỀ TRÌNH BÀY:
                1. Không dùng mã lệnh LaTeX phức tạp như \\frac, \\text. Hãy dùng Unicode symbol như Δ, λ và dấu / cho phân số.
                2. QUY ĐỊNH BẮT BUỘC VỀ ĐÁP ÁN (options): Trong mảng options của Phần I, mỗi phương án BẮT BUỘC phải bắt đầu bằng định dạng chữ cái kèm dấu chấm (Ví dụ: ["A. Nội dung đáp án A", "B. Nội dung đáp án B", "C. Nội dung đáp án C", "D. Nội dung đáp án D"]).
                
                BẮT BUỘC trả về kết quả dưới dạng một chuỗi JSON thuần túy (không kèm định dạng markdown hay ```json), bao gồm danh sách các câu hỏi theo đúng cấu trúc sau:

                1. Nếu chọn Phần I (Trắc nghiệm nhiều lựa chọn):
                [
                  {{
                    "type": "part1",
                    "id": 1,
                    "question": "Nội dung câu hỏi...",
                    "options": ["A. Đáp án 1", "B. Đáp án 2", "C. Đáp án 3", "D. Đáp án 4"],
                    "answer": "A",
                    "explanation": "Hướng dẫn giải..."
                  }}
                ]

                2. Nếu chọn Phần II (Trắc nghiệm đúng sai - Đúng chuẩn Bộ GD&ĐT gồm 4 ý a, b, c, d):
                [
                  {{
                    "type": "part2",
                    "id": 1,
                    "stem": "Đoạn văn cảnh / Ngữ cảnh bài tập...",
                    "sub_questions": [
                      {{"id": "a", "text": "Phát biểu a...", "answer": "Đúng", "explanation": "Giải thích a..."}},
                      {{"id": "b", "text": "Phát biểu b...", "answer": "Sai", "explanation": "Giải thích b..."}},
                      {{"id": "c", "text": "Phát biểu c...", "answer": "Đúng", "explanation": "Giải thích c..."}},
                      {{"id": "d", "text": "Phát biểu d...", "answer": "Sai", "explanation": "Giải thích d..."}}
                    ]
                  }}
                ]

                3. Nếu chọn Phần III (Trắc nghiệm trả lời ngắn):
                [
                  {{
                    "type": "part3",
                    "id": 1,
                    "question": "Nội dung câu hỏi bài tập...",
                    "answer": "12.5",
                    "explanation": "Lời giải chi tiết và con số đáp án..."
                  }}
                ]

                4. Nếu chọn 'Toàn bộ đề kiểm tra': Trả về mảng gồm đủ các câu hỏi theo đúng 3 loại cấu trúc (part1, part2, part3) ở trên.
                """
                
                # Điểm cuối: Dấu ngoặc kép đóng chuỗi prompt
                response = model.generate_content(prompt)
            try:
                clean_text = response.text.strip().replace("```json", "").replace("```", "")
                st.session_state['quiz_data'] = json.loads(clean_text)
                st.session_state['submitted'] = False
                if 'chat_session' in st.session_state:
                    del st.session_state['chat_session']
                if 'messages' in st.session_state:
                    del st.session_state['messages']
            except:
                st.error("AI đang bận hoặc định dạng phản hồi chưa khớp, vui lòng bấm tạo lại đề giúp em nhé!")
                st.session_state['quiz_data'] = []

        # Hiển thị bài làm tương tác
        if 'quiz_data' in st.session_state and st.session_state['quiz_data']:
            if 'submitted' not in st.session_state:
                st.session_state['submitted'] = False

            user_answers = {}
            
            for idx, q in enumerate(st.session_state['quiz_data']):
                q_type = q.get('type', 'part1')
                
                if q_type == 'part1':
                    st.markdown(f"**Câu {q.get('id', idx+1)}:** {q.get('question')}")
                    user_answers[idx] = st.radio(f"Chọn đáp án câu {idx+1}:", q.get('options', []), key=f"q_{idx}")
                    st.divider()
                
                elif q_type == 'part2':
                    st.markdown(f"**Câu {q.get('id', idx+1)} (Đúng/Sai):** {q.get('stem')}")
                    sub_ans = {}
                    for sub in q.get('sub_questions', []):
                        sub_id = sub.get('id')
                        sub_text = sub.get('text')
                        sub_ans[sub_id] = st.radio(
                            f"Ý {sub_id}) {sub_text}",
                            ["Chưa chọn", "Đúng", "Sai"],
                            horizontal=True,
                            key=f"q_{idx}_{sub_id}"
                        )
                    user_answers[idx] = sub_ans
                    st.divider()
                
                elif q_type == 'part3':
                    st.markdown(f"**Câu {q.get('id', idx+1)} (Trả lời ngắn):** {q.get('question')}")
                    user_answers[idx] = st.text_input(f"Điền kết quả số của em cho câu {idx+1}:", key=f"q_{idx}_short", placeholder="Ví dụ: 12.5 hoặc -3")
                    st.divider()
                
            # NÚT NỘP BÀI VÀ XEM KẾT QUẢ
            if st.button("📌 Nộp bài và Xem kết quả"):
                st.session_state['submitted'] = True
                st.session_state['user_answers'] = user_answers

            # Hiển thị kết quả khi đã bấm nộp bài
            if st.session_state.get('submitted', False):
                correct_count = 0
                total_items = len(st.session_state['quiz_data'])
                saved_answers = st.session_state.get('user_answers', {})
                
                st.markdown("### 🔍 Hướng dẫn giải chi tiết & Kết quả:")
                
                for idx, q in enumerate(st.session_state['quiz_data']):
                    q_type = q.get('type', 'part1')
                    
                    if q_type == 'part1':
                        chosen = str(saved_answers.get(idx, ""))
                        correct_ans = str(q.get('answer', '')).strip().upper() # Ví dụ: "A"
                        
                        # Trích xuất chữ cái đầu tiên từ lựa chọn của học sinh (Ví dụ: "A. Nội dung" -> lấy "A")
                        user_choice_letter = chosen.strip()[:1].upper()
                        
                        is_correct = (user_choice_letter == correct_ans)
                        if is_correct:
                            correct_count += 1
                            
                        st.write(f"**Câu {idx+1}:** {'✅ Đúng' if is_correct else '❌ Sai'} (Đáp án học sinh chọn: **{user_choice_letter}** | Đáp án đúng: **{correct_ans}**)")
                        st.write(f"👉 *Giải thích:* {q.get('explanation')}")
                    
                    elif q_type == 'part2':
                        st.write(f"**Câu {idx+1} (Đúng/Sai):** {q.get('stem')}")
                        sub_ans = saved_answers.get(idx, {})
                        sub_correct_all = True
                        for sub in q.get('sub_questions', []):
                            sub_id = sub.get('id')
                            user_sub_ans = sub_ans.get(sub_id, "Chưa chọn")
                            correct_sub_ans = sub.get('answer')
                            is_sub_correct = (user_sub_ans == correct_sub_ans)
                            if not is_sub_correct:
                                sub_correct_all = False
                            st.write(f"- Ý {sub_id}): Em chọn **{user_sub_ans}** | Đáp án đúng: **{correct_sub_ans}** {'✅' if is_sub_correct else '❌'}")
                            st.write(f"  *Giải thích:* {sub.get('explanation')}")
                        if sub_correct_all:
                            correct_count += 1
                    
                    elif q_type == 'part3':
                        user_short = str(saved_answers.get(idx, "")).strip()
                        correct_short = str(q.get('answer', '')).strip()
                        is_short_correct = (user_short == correct_short)
                        if is_short_correct:
                            correct_count += 1
                        st.write(f"**Câu {idx+1}:** Em điền **'{user_short}'** | Đáp án chuẩn: **'{correct_short}'** {'✅' if is_short_correct else '❌'}")
                        st.write(f"👉 *Giải thích:* {q.get('explanation')}")
                    
                    st.divider()
                
                final_score = round((correct_count / total_items) * 10, 2)
                st.success(f"🎉 Em đã hoàn thành bài! Điểm tổng kết: **{final_score} / 10 điểm**.")

               # Tự động lưu vào Google Sheets (Chỉ lưu 1 lần khi nộp)
                if not st.session_state.get('saved_to_sheets', False):
                    try:
                        # Khai báo chuẩn các scope cần thiết cho Google Sheets & Drive
                        scopes = [
                            "https://www.googleapis.com/auth/spreadsheets",
                            "https://www.googleapis.com/auth/drive"
                        ]
                        
                        # Đọc thông tin trực tiếp từ st.secrets thay vì đọc file json
                        creds_dict = dict(st.secrets["gcp_service_account"])
                        # [QUAN TRỌNG] Chuyển đổi các ký tự "\n" dạng text thành ngắt dòng thực sự cho private_key
                        if "private_key" in creds_dict:
                            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
                        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        
                        client = gspread.authorize(creds)
                        
                        # Mở Google Sheet và ghi dữ liệu
                        sheet = client.open("LichSuOnTapVatLy12").sheet1
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        sheet.append_row([now_str, name, cl, current_exam, section, final_score])
                        
                        st.session_state['saved_to_sheets'] = True
                        st.balloons()
                        st.toast("✅ Đã tự động lưu kết quả vào hệ thống!", icon="📊")
                        
                    except Exception as e:
                        st.error(f"Lưu kết quả lỗi, Chi tiết lỗi: {e}")

            # --- CỬA SỔ CHAT ĐA LƯỢT (THU ÂM TRỰC TIẾP AN TOÀN) ---
            st.markdown("---")
            st.subheader("💬 Góc thắc mắc cùng AI (Hỏi - Đáp linh hoạt)")
            st.markdown("_Em có thể gõ chữ hoặc bấm nút thu âm trực tiếp để AI lắng nghe và giải đáp ngay lập tức!_")
            
            if 'chat_session' not in st.session_state:
                initial_context = f"Đây là đề thi Vật lý 12 học sinh vừa làm: {str(st.session_state.get('quiz_data', ''))}. Hãy đóng vai trò gia sư Vật lý thân thiện, kiên nhẫn giải đáp mọi thắc mắc liên tục cho học sinh."
                st.session_state['chat_session'] = model.start_chat(history=[
                    {"role": "user", "parts": [initial_context]},
                    {"role": "model", "parts": ["Em chào thầy/cô/AI, em đã nắm được đề thi và sẵn sàng giải đáp thắc mắc cho học sinh ạ!"]}
                ])

            if 'messages' not in st.session_state:
                st.session_state['messages'] = []

            if 'last_processed_audio_hash' not in st.session_state:
                st.session_state['last_processed_audio_hash'] = None

            for message in st.session_state['messages']:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            col_mic, col_space = st.columns([1, 4])
            with col_mic:
                audio_info = mic_recorder(start_prompt="🎙️ Nói câu hỏi", stop_prompt="⏹️ Dừng", key='recorder_safe_vfix2')

            if audio_info is not None:
                audio_bytes = audio_info.get('bytes')
                if audio_bytes:
                    current_audio_hash = hash(audio_bytes)
                    if current_audio_hash != st.session_state['last_processed_audio_hash']:
                        st.session_state['last_processed_audio_hash'] = current_audio_hash
                        
                        audio_label = "🎤 *(Học sinh đã gửi một câu hỏi bằng giọng nói)*"
                        st.session_state['messages'].append({"role": "user", "content": audio_label})
                        with st.chat_message("user"):
                            st.markdown(audio_label)
                        
                        with st.chat_message("assistant"):
                            with st.spinner("🤖 AI đang lắng nghe câu hỏi và suy nghĩ giải đáp..."):
                                try:
                                    audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
                                    chat_response = st.session_state['chat_session'].send_message([
                                        "Học sinh vừa đặt câu hỏi bằng giọng nói liên quan đến đề thi Vật lý 12 ở trên, hãy lắng nghe và giải đáp thật chi tiết, dễ hiểu:",
                                        audio_part
                                    ])
                                    ai_reply = chat_response.text
                                    st.markdown(ai_reply)
                                    st.session_state['messages'].append({"role": "assistant", "content": ai_reply})
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Đã xảy ra lỗi khi xử lý âm thanh: {e}")

            user_prompt = st.chat_input("Hoặc nhập câu hỏi thắc mắc của em tại đây...")
            if user_prompt:
                st.session_state['messages'].append({"role": "user", "content": user_prompt})
                with st.chat_message("user"):
                    st.markdown(user_prompt)
                
                with st.chat_message("assistant"):
                    with st.spinner("🤖 AI đang suy nghĩ và giải đáp..."):
                        try:
                            chat_response = st.session_state['chat_session'].send_message(user_prompt)
                            ai_reply = chat_response.text
                            st.markdown(ai_reply)
                            st.session_state['messages'].append({"role": "assistant", "content": ai_reply})
                        except Exception as e:
                            st.error(f"Đã xảy ra lỗi khi trò chuyện với AI: {e}")

with tab3:
    st.subheader("📊 Theo dõi và đánh giá sự tiến bộ")
    role = st.radio("Bạn là ai?", ["Học sinh", " Giáo viên"])
    if role == "Học sinh":
        st.info(f"Lịch sử ôn tập của học sinh: **{name} ({cl})**. Hệ thống ghi nhận mọi nỗ lực học tập của em qua các lần làm bài.")
    else:
        pwd = st.text_input("Nhập mật mã quản trị giáo viên:", type="password", key="p_hist_admin")
        if pwd == "vatly123":
            st.success("✅ Đăng nhập quyền Giáo viên thành công!")
            st.write("📋 **Bảng tổng hợp lịch sử luyện tập thực tế từ Google Sheets:**")
            
            try:
                # Khai báo chuẩn các scope cần thiết cho Google Sheets & Drive
                scopes = [
                            "https://www.googleapis.com/auth/spreadsheets",
                            "https://www.googleapis.com/auth/drive"
                        ]
                        
                # Đọc thông tin trực tiếp từ st.secrets thay vì đọc file json
                creds_dict = dict(st.secrets["gcp_service_account"])
                # [QUAN TRỌNG] Chuyển đổi các ký tự "\n" dạng text thành ngắt dòng thực sự cho private_key
                if "private_key" in creds_dict:
                    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
                creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
                client = gspread.authorize(creds)
                sheet = client.open("LichSuOnTapVatLy12").sheet1
                data = sheet.get_all_records()
                
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Chưa có học sinh nào nộp bài trên hệ thống.")
            except Exception as e:
                st.error(f"Không thể tải dữ liệu từ Google Sheets. Vui lòng kiểm tra lại file credentials.json. Chi tiết lỗi: {e}")
                
        elif pwd:
            st.error("❌ Sai mật mã giáo viên!")
