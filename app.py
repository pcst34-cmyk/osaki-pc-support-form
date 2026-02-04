import json
import os
import streamlit as st
import smtplib
from email.mime.text import MIMEText
import ssl

# ==========================================
# --- ページ設定 ---
st.set_page_config(page_title="大崎市出張パソコン修理サポート", page_icon="💻")

# カスタムCSSの適用
st.markdown("""
<style>
/* フォント設定 */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');

:root {
    --primary-color: #C06014;
    --bg-color: #F3EFEA;
    --text-color: #333333;
    --accent-color: #EAAA79;
    --white-color: #FFFFFF;
    --border-color: #C06014;
    --chat-bg: #FFFFFF;
}

/* 全体のスタイル */
.stApp {
    background-color: var(--bg-color);
    color: var(--text-color);
    font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
}

h1, h2, h3, p, div, span, label, .stMarkdown {
    color: var(--text-color);
    font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
}

/* ヘッダーのスタイル - 特異性を高める */
div.main-header {
    text-align: center;
    padding: 30px 20px;
    background-color: #C06014 !important;
    color: #ffffff !important;
    border-radius: 12px;
    margin-bottom: 40px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
div.main-header h1 {
    font-size: 1.8rem;
    font-weight: 700;
    color: #ffffff !important;
    letter-spacing: 1px;
    text-shadow: 0 2px 5px rgba(0,0,0,0.5) !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #ffffff !important;
}
div.main-header p {
    margin-top: 10px;
    color: #f0f0f0 !important;
    font-size: 1rem;
    opacity: 1 !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.3) !important;
}

/* チャットメッセージ */
.stChatMessage {
    background-color: var(--chat-bg);
    padding: 20px;
    border-radius: 20px;
    margin-bottom: 20px;
    border: 2px dotted var(--primary-color);
    box-shadow: none;
}
.stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
    background-color: var(--chat-bg);
    border: 2px dotted var(--primary-color);
}
.stChatMessage p {
    line-height: 1.8;
}

/* フォームのカードスタイル化 */
[data-testid="stForm"] {
    background-color: #FFFFFF;
    padding: 30px;
    border-radius: 15px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    border: 1px solid #E0E0E0;
}

/* 入力フィールド */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
    border-radius: 8px;
    border: 1px solid #ccc;
    padding: 12px;
    background-color: #FAFAFA;
    color: var(--text-color);
    font-size: 1rem;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 2px rgba(192, 96, 20, 0.2);
    background-color: #FFFFFF;
}

/* --- ボタンのスタイル強制適用 (最強設定) --- */
/* Base Button, Primary, Secondary 全て対象 */
button[kind="primary"], 
button[kind="secondary"], 
[data-testid="baseButton-secondary"], 
[data-testid="baseButton-primary"],
.stButton > button {
    width: 100% !important;
    border-radius: 30px !important;
    padding: 0.6rem 1rem !important;
    font-weight: bold !important;
    border: none !important;
    background-color: #C06014 !important; /* オレンジ強制 */
    color: #ffffff !important; /* 白文字強制 */
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
}

/* コンテナ内のボタン内テキスト自体の色も白に強制 */
button[kind="primary"] *, 
button[kind="secondary"] *,
[data-testid="baseButton-secondary"] *, 
[data-testid="baseButton-primary"] *,
.stButton > button * {
    color: #ffffff !important;
    fill: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

/* ホバー設定 */
button[kind="primary"]:hover, 
button[kind="secondary"]:hover, 
[data-testid="baseButton-secondary"]:hover, 
[data-testid="baseButton-primary"]:hover,
.stButton > button:hover {
    background-color: #d17025 !important;
    color: #ffffff !important;
    border-color: #d17025 !important;
}

/* フォーカス時の枠線消去 or 色合わせ */
button:focus {
    outline: none !important;
    box-shadow: 0 0 0 2px #EAAA79 !important;
    color: #ffffff !important;
}

/* スピナー */
.stSpinner > div > div {
    border-top-color: var(--primary-color) !important;
}


</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. データ・設定
# ==========================================
DATA_FILE = "diagnosis_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    """データを保存する"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def send_email(booking_name, booking_tel, booking_email, booking_zip, booking_address, booking_detail):
    """予約完了メールを送信する"""
    if "email" not in st.secrets:
        st.error("メール設定が見つかりません。.streamlit/secrets.toml を設定してください。")
        return False

    sender_email = st.secrets["email"]["sender_email"]
    sender_password = st.secrets["email"]["sender_password"]
    receiver_email = st.secrets["email"]["receiver_email"]

    # デフォルト設定チェック
    if sender_email == "your-email@gmail.com":
        st.warning("⚠️ メール設定が完了していません。通知は送信されませんでした。")
        return True

    subject = f"【修理予約】{booking_name}様からの依頼"
    body = f"""
    新しい修理予約が入りました。
    
    ■お名前: {booking_name}
    ■電話番号: {booking_tel}
    ■メールアドレス: {booking_email}
    ■郵便番号: {booking_zip}
    ■ご住所: {booking_address}
    
    ■症状詳細:
    {booking_detail}
    """

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"メール送信エラー: {e}")
        return False

import urllib.request

def search_address_by_zip(zipcode):
    """郵便番号から住所を検索する"""
    if not zipcode:
        return None
    try:
        url = f"https://zipcloud.ibsnet.co.jp/api/search?zipcode={zipcode}"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data["results"]:
                result = data["results"][0]
                return f"{result['address1']}{result['address2']}{result['address3']}"
    except Exception:
        pass
    return None

# ==========================================
# 2. アプリ初期化 (設定済み)
# ==========================================

# セッション初期化
if "diagnosis_data" not in st.session_state:
    st.session_state.diagnosis_data = load_data()

# ==========================================
# 3. メイン処理
# ==========================================

# サイドバー
with st.sidebar:
    st.header("⚙️ 設定")
    admin_mode = st.toggle("管理者モード（項目編集）", key="admin_mode_toggle")

def close_admin_mode():
    st.session_state.admin_mode_toggle = False

if admin_mode:
    # ---------------------------
    # 管理者モード
    # ---------------------------
    st.title("🔧 診断シナリオ編集")
    
    st.button("← ホーム（診断画面）に戻る", on_click=close_admin_mode)
    
    data = st.session_state.diagnosis_data
    step_ids = list(data.keys())
    selected_step = st.selectbox("編集するステップを選択", ["(新規作成)"] + step_ids)
    
    target_id = ""
    current_data = None

    if selected_step == "(新規作成)":
        new_id = st.text_input("新しいステップID（英数字 例: sound_issue）")
        if new_id:
            target_id = new_id
            current_data = {"message": "", "options": []}
    else:
        target_id = selected_step
        current_data = data[selected_step]

    if current_data is not None:
        st.markdown("---")
        with st.form("edit_step_form"):
            st.subheader(f"ステップ: {target_id}")
            new_message = st.text_area("表示するメッセージ", current_data["message"], height=100)
            
            st.write("▼ 選択肢 (最大4つまで)")
            new_options = []
            
            current_options = current_data.get("options", [])
            for i in range(4):
                col1, col2 = st.columns(2)
                default_label = current_options[i]["label"] if i < len(current_options) else ""
                default_next = current_options[i]["next_step"] if i < len(current_options) else ""
                
                with col1:
                    lbl = st.text_input(f"選択肢{i+1} ラベル", default_label, key=f"lbl_{i}")
                with col2:
                    special_steps = ["booking", "solved"]
                    all_targets = special_steps + step_ids
                    idx = 0
                    if default_next in all_targets:
                        idx = all_targets.index(default_next) + 1
                    
                    nxt = st.selectbox(f"選択肢{i+1} 移動先", [""] + all_targets, index=idx, key=f"nxt_{i}")

                if lbl and nxt:
                    new_options.append({"label": lbl, "next_step": nxt})
            
            if st.form_submit_button("保存する"):
                st.session_state.diagnosis_data[target_id] = {
                    "message": new_message,
                    "options": new_options
                }
                save_data(st.session_state.diagnosis_data)
                st.success(f"ステップ `{target_id}` を保存しました！")
                st.rerun()

else:
    # ---------------------------
    # ユーザーモード
    # ---------------------------
    st.markdown("""
    <div class="main-header">
        <h1>🔧 大崎市出張パソコン修理サポート</h1>
        <p>パソコントラブル、まずはこちらで診断！</p>
    </div>
    """, unsafe_allow_html=True)

    # チャット初期化
    if "messages" not in st.session_state or not st.session_state.messages:
        start_msg = st.session_state.diagnosis_data.get("start", {}).get("message", "こんにちは！")
        st.session_state.messages = [{"role": "assistant", "content": start_msg}]
    
    if "step" not in st.session_state:
        st.session_state.step = "start"

    # 履歴表示
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 入力処理ハンドラ
    def handle_input(response_text, next_step):
        st.session_state.messages.append({"role": "user", "content": response_text})
        st.session_state.step = next_step
        
        # 次のメッセージを追加
        if next_step not in ["booking", "solved", "completed"]:
            next_data = st.session_state.diagnosis_data.get(next_step)
            if next_data:
                st.session_state.messages.append({"role": "assistant", "content": next_data["message"]})
        
        st.rerun()

    current_step = st.session_state.step

    # === ステップごとの表示分岐 ===
    
    if current_step == "booking":
        # 予約フォーム
        with st.chat_message("assistant"):
            st.write("承知いたしました。出張修理・診断の予約を受け付けます。")
            st.write("以下のフォームに必要事項を入力して「送信」を押してください。")
        
        # 郵便番号検索用の一時変数
        if "form_address" not in st.session_state:
            st.session_state.form_address = ""
            
        # フォームの外で検索処理（フォーム内だとボタンで送信されてしまうため、またはform_submitと分ける）
        # ただしレイアウト的にフォームっぽく見せる。
        # シンプルに実装するため、フォーム内ボタンにするか、colを使う。
        # ユーザー体験的には「検索」推して自動入力がいい。

        with st.form("booking_form"):
            st.markdown("### お客様情報入力")
            name = st.text_input("お名前 *")
            
            # 郵便番号と検索
            col_zip, col_btn = st.columns([2, 1])
            with col_zip:
                zip_code = st.text_input("郵便番号 (例: 9896162) *")
            with col_btn:
                st.write("") # スペース調整
                st.write("")
                search_clicked = st.form_submit_button("住所検索", type="primary")
            
            # 住所検索ロジック (再描画時に反映させる工夫)
            if search_clicked and zip_code:
                found_addr = search_address_by_zip(zip_code)
                if found_addr:
                    st.session_state.form_address = found_addr
                else:
                    st.toast("住所が見つかりませんでした", icon="⚠️")

            # 住所入力（SessionStateから値をいれる）
            address = st.text_input("ご住所 *", value=st.session_state.form_address)
            
            tel = st.text_input("電話番号 *")
            email = st.text_input("メールアドレス")
            detail = st.text_area("詳しい症状（任意）")
            
            st.markdown("---")
            submit_btn = st.form_submit_button("内容を送信する", type="primary")
            
            if submit_btn:
                if name and tel and address:
                    with st.spinner("送信中..."):
                        if send_email(name, tel, email, zip_code, address, detail):

                            st.session_state.step = "completed"
                            st.session_state.booking_info = f"{name}様"
                            st.rerun()
                else:
                    st.error("お名前、電話番号、ご住所は必須項目です。")

    elif current_step == "solved":
        # 解決
        with st.chat_message("assistant"):
            st.write("解決してよかったです！また何かあればいつでもご相談ください。")
            st.write("大崎市出張PCサポート")
        if st.button("最初に戻る"):
            st.session_state.messages = []
            st.session_state.step = "start"
            st.rerun()

    elif current_step == "completed":
        # 送信完了
        with st.chat_message("assistant"):
            st.success("予約を受け付けました")
            st.write(f"{st.session_state.booking_info}、お問い合わせありがとうございます。")
            st.write("ご入力いただいた電話番号またはメールアドレスへ、担当者より折り返しご連絡いたします。")
            st.info("※確認メールは送信されませんので、折り返しをお待ちください。")
        
        if st.button("トップに戻る"):
            st.session_state.messages = []
            st.session_state.step = "start"
            st.rerun()

    else:
        # 汎用シナリオ（JSONから）
        step_data = st.session_state.diagnosis_data.get(current_step)
        
        if step_data:
            options = step_data.get("options", [])
            cols = st.columns(2)
            for i, opt in enumerate(options):
                with cols[i % 2]:
                    if st.button(opt["label"], key=f"btn_{current_step}_{i}"):
                        handle_input(opt["label"], opt["next_step"])
        else:
            st.error(f"エラー: ステップ '{current_step}' が見つかりません。")
            if st.button("リセット"):
                st.session_state.step = "start"
                st.rerun()
