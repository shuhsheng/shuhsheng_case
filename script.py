from datetime import datetime
import re
import pandas as pd
import streamlit as st
from supabase import Client, create_client

# 初始化 Supabase 連線
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = get_supabase_client()


def auto_generate_tags(text_content):
    words = re.findall(r"[\u4e00-\u9fa5]{2,6}|[a-zA-Z0-9_\-\.]{3,}", text_content)
    stopwords = {
        "問題",
        "處理",
        "結果",
        "方案",
        "情況",
        "以及",
        "發生",
        "進行",
        "規定",
        "申請",
    }
    filtered_words = [w for w in words if w not in stopwords]
    unique_tags = list(dict.fromkeys(filtered_words))[:5]
    return ", ".join(unique_tags) if unique_tags else "一般案件"


def insert_case(
    case_title, case_problem, case_solution, case_result, case_tags
):
    data = {
        "title": case_title,
        "problem": case_problem,
        "solution": case_solution,
        "result": case_result,
        "tags": case_tags,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    supabase.table("cases").insert(data).execute()
    st.cache_data.clear()


def update_case(
    case_id, case_title, case_problem, case_solution, case_result, case_tags
):
    data = {
        "title": case_title,
        "problem": case_problem,
        "solution": case_solution,
        "result": case_result,
        "tags": case_tags,
    }
    supabase.table("cases").update(data).eq("id", case_id).execute()
    st.cache_data.clear()


def delete_case(case_id):
    supabase.table("cases").delete().eq("id", case_id).execute()
    st.cache_data.clear()


@st.cache_data(show_spinner=False)
def query_cases(search_keyword):
    response = (
        supabase.table("cases").select("*").order("id", desc=True).execute()
    )
    data = response.data
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    if search_keyword.strip():
        kw = search_keyword.strip().lower()
        mask = (
            df["title"].astype(str).str.lower().str.contains(kw)
            | df["problem"].astype(str).str.lower().str.contains(kw)
            | df["solution"].astype(str).str.lower().str.contains(kw)
            | df["result"].astype(str).str.lower().str.contains(kw)
            | df["tags"].astype(str).str.lower().str.contains(kw)
        )
        df = df[mask]

    return df


def format_text(text):
    if not text:
        return ""
    cleaned = str(text).replace("~", r"\~")
    return cleaned.replace("\r\n", "  \n").replace("\n", "  \n")


# 介面設定
st.set_page_config(page_title="雲端團隊案件知識庫", layout="wide")

st.markdown(
    """
    <meta name="google" content="notranslate">
    <style>
        html, body, [data-testid="stAppViewContainer"] {
            translate: no !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("☁️ 雲端團隊案件知識庫與智慧歸檔系統")

tab_record, tab_search = st.tabs(["📝 案件歸檔建檔", "🔍 歷年案件檢索與管理"])

# 頁籤 1：建檔
with tab_record:
    st.subheader("新增案件資訊")
    with st.form("case_form", clear_on_submit=True):
        input_title = st.text_input(
            "案件主旨 / 標題", placeholder="例如：移工續聘/離境/重招期限規範"
        )
        input_problem = st.text_area(
            "案件問題描述",
            placeholder="請輸入案件背景、錯誤細節或相關情境...",
            height=120,
        )
        input_solution = st.text_area(
            "處理方式 / 步驟",
            placeholder="請詳細記錄處理流程、法規依據或應對步驟...",
            height=120,
        )
        input_result = st.text_area(
            "最終結果 / 結論",
            placeholder="請填寫辦理結果、期限說明或注意事項（直接按 Enter 換行）...",
            height=120,
        )
        manual_tags = st.text_input(
            "自訂標籤（選填，逗號分隔；若留空系統會自動萃取）",
            placeholder="續聘, 離境, 重招, 轉出",
        )

        submit_btn = st.form_submit_button("自動歸檔儲存")

        if submit_btn:
            clean_title = input_title.strip()
            clean_problem = input_problem.strip()
            if not clean_title or not clean_problem:
                st.error("請至少填寫『案件標題』與『問題描述』！")
            else:
                dup_check = (
                    supabase.table("cases")
                    .select("id")
                    .eq("title", clean_title)
                    .eq("problem", clean_problem)
                    .execute()
                )
                if dup_check.data:
                    st.warning(
                        "⚠️ 雲端已存在相同標題與問題的案件，請勿重複提交！"
                    )
                else:
                    combined_text = (
                        f"{clean_title} {clean_problem} {input_solution.strip()}"
                    )
                    final_tags = (
                        manual_tags.strip()
                        if manual_tags.strip()
                        else auto_generate_tags(combined_text)
                    )

                    insert_case(
                        clean_title,
                        clean_problem,
                        input_solution.strip(),
                        input_result.strip(),
                        final_tags,
                    )
                    st.success(
                        f"案件已成功同步至雲端資料庫！標籤：{final_tags}"
                    )
                    st.rerun()

# 頁籤 2：搜尋與管理
with tab_search:
    st.subheader("歷年案件檢索與管理")

    col_search, col_refresh = st.columns([5, 1])
    with col_search:
        search_input = st.text_input(
            "搜尋關鍵字",
            placeholder="輸入關鍵字進行全文檢索（如：逃跑、續聘、離境、24個月）...",
            label_visibility="collapsed",
        )
    with col_refresh:
        if st.button("🔄 重新整理資料", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    content_container = st.container()

    with content_container:
        results_df = query_cases(search_keyword=search_input)
        st.caption(f"共檢索到 {len(results_df)} 筆案件資料")

        if not results_df.empty:
            for _, row in results_df.iterrows():
                c_id = int(row["id"])
                with st.expander(
                    f"📌 [{row['tags']}] {row['title']} (記錄時間: {row['created_at']})"
                ):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**【問題描述】**")
                        st.info(format_text(row["problem"]))
                    with col2:
                        st.markdown("**【處理方式】**")
                        st.warning(format_text(row["solution"]))

                    st.markdown("**【最終結果】**")
                    st.success(format_text(row["result"]))

                    st.divider()

                    edit_mode = st.checkbox(
                        "✏️ 編輯這筆資料", key=f"edit_toggle_{c_id}"
                    )
                    if edit_mode:
                        with st.form(key=f"edit_form_{c_id}"):
                            edit_title = st.text_input(
                                "修改標題", value=row["title"]
                            )
                            edit_problem = st.text_area(
                                "修改問題描述",
                                value=row["problem"],
                                height=100,
                            )
                            edit_solution = st.text_area(
                                "修改處理方式",
                                value=row["solution"],
                                height=100,
                            )
                            edit_result = st.text_area(
                                "修改最終結果",
                                value=row["result"],
                                height=100,
                            )
                            edit_tags = st.text_input(
                                "修改標籤", value=row["tags"]
                            )

                            save_btn = st.form_submit_button("💾 儲存修改")
                            if save_btn:
                                update_case(
                                    c_id,
                                    edit_title.strip(),
                                    edit_problem.strip(),
                                    edit_solution.strip(),
                                    edit_result.strip(),
                                    edit_tags.strip(),
                                )
                                st.toast("雲端案件資料已同步更新！")
                                st.rerun()

                    delete_confirm = st.checkbox(
                        "⚠️ 刪除此案件", key=f"del_confirm_{c_id}"
                    )
                    if delete_confirm:
                        if st.button(
                            "🗑️ 確認永久刪除",
                            key=f"del_btn_{c_id}",
                            type="primary",
                        ):
                            delete_case(c_id)
                            st.toast("案件已自雲端移除！")
                            st.rerun()
        else:
            st.info("查無符合條件的案件記錄。")