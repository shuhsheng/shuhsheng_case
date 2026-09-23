import streamlit as st
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from supabase import create_client, Client

# ==========================================
# 1. 頁面基礎設定與精緻高對比深色主題 CSS
# ==========================================
st.set_page_config(
    page_title="業務管理與服務追蹤系統",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* 全域背景與文字基礎 */
    .stApp {
        background-color: #0b0f19 !important;
        color: #f8fafc !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    
    /* 側邊欄深色統一 */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    [data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
    }
    
    /* 1. 欄位標籤與文字亮化 */
    label, [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] span {
        color: #f8fafc !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    
    /* 2. 頁籤 (Tabs) 高亮 */
    button[data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        background-color: transparent !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #f8fafc !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #38bdf8 !important;
        font-weight: 700 !important;
        border-bottom: 2px solid #38bdf8 !important;
    }
    
    /* 3. 輸入框美化 (深色微透質感) */
    div[data-baseweb="input"], div[data-baseweb="base-input"] {
        background-color: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.3) !important;
    }
    input[data-testid="stTextInputRootElement"], 
    div[data-baseweb="input"] input,
    textarea {
        color: #ffffff !important;
        background-color: #1e293b !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    input::placeholder, textarea::placeholder {
        color: #64748b !important;
    }
    
    /* 下拉選單 Selectbox */
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }
    div[data-baseweb="select"] span {
        color: #ffffff !important;
    }
    
    /* 數字與日期輸入框 */
    div[data-testid="stNumberInput"] input, div[data-testid="stDateInput"] input {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }
    
    /* 4. Expander 展開卡片深色科技化 */
    [data-testid="stExpander"] {
        background-color: #111827 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        margin-bottom: 0.75rem !important;
    }
    [data-testid="stExpander"] details summary {
        background-color: #111827 !important;
        color: #f8fafc !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        padding: 0.75rem 1rem !important;
    }
    [data-testid="stExpander"] details summary:hover {
        background-color: #1e293b !important;
    }
    
    /* 5. KPI 統計卡片 */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background: #111827;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.15rem 1.35rem;
        box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.4);
    }
    .kpi-title {
        font-size: 0.82rem;
        color: #94a3b8;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.35rem;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.2;
    }
    .kpi-badge {
        display: inline-block;
        font-size: 0.72rem;
        padding: 0.2rem 0.55rem;
        border-radius: 9999px;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    .badge-blue { background: rgba(56, 189, 248, 0.18); color: #38bdf8; }
    .badge-green { background: rgba(16, 185, 129, 0.18); color: #34d399; }
    .badge-amber { background: rgba(245, 158, 11, 0.18); color: #fbbf24; }
    .badge-red { background: rgba(239, 68, 68, 0.18); color: #f87171; }
    
    /* 原生提示框與按鈕 */
    .stAlert {
        background-color: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #f1f5f9 !important;
        border-radius: 10px !important;
    }
    .stButton>button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.4rem 1.2rem !important;
    }
    .stButton>button:hover {
        background-color: #1d4ed8 !important;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. 資料庫連線 (Supabase)
# ==========================================
@st.cache_resource
def get_supabase_client() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"無法讀取 Supabase 連線憑證，請檢查 Streamlit Secrets 設定：{e}")
        return None

supabase = get_supabase_client()


# ==========================================
# 3. 側邊欄導航
# ==========================================
with st.sidebar:
    st.markdown("### 📌 系統選單")
    st.markdown("<p style='font-size:0.85rem; color:#94a3b8;'>業務管理與週期服務作業流程</p>", unsafe_allow_html=True)
    
    menu = st.radio(
        "請選擇作業功能：",
        ["📖 突發案件與處置知識庫", "📅 移工雙月服務週期排程"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("<div style='font-size:0.75rem; color:#64748b;'>資料庫狀態：連線中 (Supabase)<br>雲端伺服器正常運作</div>", unsafe_allow_html=True)


# ==========================================
# 4. 功能一：突發案件與處置知識庫 (cases)
# ==========================================
if menu == "📖 突發案件與處置知識庫":
    st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.7rem; font-weight: 700; color: #f8fafc;">📖 突發案件處置知識庫</h2>
            <p style="margin: 0.35rem 0 0 0; color: #94a3b8; font-size: 0.9rem;">
                點選案例條目展開詳細處置 SOP，可直接進行編輯更新或刪除。
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    cases_data = []
    if supabase:
        try:
            res = supabase.table("cases").select("*").execute()
            cases_data = res.data or []
        except Exception as e:
            st.error(f"讀取資料庫失敗: {e}")

    total_cases = len(cases_data)
    cat_count = len(set([c.get("category", "") for c in cases_data if c.get("category")]))
    
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">收錄案例總數</div>
            <div class="kpi-value">{total_cases} <span style="font-size: 0.9rem; color: #64748b; font-weight: 400;">筆</span></div>
            <span class="kpi-badge badge-blue">處置 SOP 資料庫</span>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">涵蓋類別</div>
            <div class="kpi-value">{cat_count} <span style="font-size: 0.9rem; color: #64748b; font-weight: 400;">大類</span></div>
            <span class="kpi-badge badge-green">完整分類歸檔</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_search, tab_add = st.tabs(["🔍 案例知識庫清單 (點選展開編輯)", "➕ 建立新案例紀錄"])
    
    with tab_search:
        col_search, col_cat = st.columns([3, 1])
        with col_search:
            search_query = st.text_input("輸入關鍵字查詢 (如：健檢不合格、失聯、急診、證件補發...)", placeholder="輸入搜尋關鍵字...")
        with col_cat:
            all_categories = ["全部分類"] + sorted(list(set([c.get("category", "其他") for c in cases_data if c.get("category")])))
            selected_cat = st.selectbox("分類篩選", all_categories)
        
        filtered_cases = cases_data
        if selected_cat != "全部分類":
            filtered_cases = [c for c in filtered_cases if c.get("category") == selected_cat]
        if search_query:
            filtered_cases = [
                c for c in filtered_cases 
                if search_query.lower() in str(c.get("title", "")).lower() 
                or search_query.lower() in str(c.get("solution", "")).lower()
                or search_query.lower() in str(c.get("description", "")).lower()
            ]
        
        st.markdown(f"<div style='margin: 0.5rem 0 1rem 0; color: #94a3b8; font-size: 0.85rem;'>共找到 <b>{len(filtered_cases)}</b> 筆案例</div>", unsafe_allow_html=True)
        
        if filtered_cases:
            for item in filtered_cases:
                case_id = item.get("id")
                title = item.get("title", "未命名案件")
                cat = item.get("category", "其他")
                sol = item.get("solution") or item.get("description") or ""
                created = str(item.get("created_at", ""))[:10]
                
                expander_title = f"📋 【{cat}】{title} ｜ 建檔日期：{created}"
                
                with st.expander(expander_title):
                    with st.form(f"edit_case_form_{case_id}"):
                        edit_col1, edit_col2 = st.columns([3, 1])
                        with edit_col1:
                            new_title_val = st.text_input("案例名稱", value=title, key=f"t_{case_id}")
                        with edit_col2:
                            new_cat_val = st.text_input("分類標籤", value=cat, key=f"c_{case_id}")
                            
                        new_sol_val = st.text_area("處置 SOP 說明與經驗", value=sol, height=180, key=f"s_{case_id}")
                        
                        btn_c1, btn_c2 = st.columns([1, 5])
                        with btn_c1:
                            save_btn = st.form_submit_button("💾 儲存修改")
                        
                        if save_btn:
                            try:
                                supabase.table("cases").update({
                                    "title": new_title_val.strip(),
                                    "category": new_cat_val.strip(),
                                    "solution": new_sol_val.strip()
                                }).eq("id", case_id).execute()
                                st.success("✅ 案例已更新完成！")
                                st.rerun()
                            except Exception as e:
                                st.error(f"更新失敗：{e}")
                    
                    del_col1, del_col2 = st.columns([1, 6])
                    with del_col1:
                        if st.button("🗑️ 刪除此案例", key=f"del_case_{case_id}"):
                            try:
                                supabase.table("cases").delete().eq("id", case_id).execute()
                                st.success("已成功刪除該案例！")
                                st.rerun()
                            except Exception as e:
                                st.error(f"刪除失敗：{e}")
        else:
            st.info("查無相關案例。")

    with tab_add:
        st.markdown("#### 建立新的突發案例 SOP")
        with st.form("add_case_form", clear_on_submit=True):
            new_title = st.text_input("案例名稱 / 狀況主旨*", placeholder="例如：印尼籍移工初次健檢異常複檢流程")
            new_category = st.text_input("分類標籤*", placeholder="例如：健康檢查、入出國管理、勞資爭議、急診就醫")
            new_solution = st.text_area("處置 SOP 流程與經驗說明*", placeholder="請詳細條列處理步驟、法規依據、通報對象或配合單位聯絡方式...", height=160)
            
            submitted = st.form_submit_button("儲存新案例至雲端知識庫")
            if submitted:
                if not new_title or not new_solution:
                    st.warning("請填寫完整的案例名稱與處置說明！")
                else:
                    try:
                        payload = {
                            "title": new_title.strip(),
                            "category": new_category.strip() if new_category else "其他",
                            "solution": new_solution.strip()
                        }
                        supabase.table("cases").insert(payload).execute()
                        st.success("✅ 案例已成功儲存至知識庫！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"儲存失敗：{e}")


# ==========================================
# 5. 功能二：移工雙月服務週期排程 (隱藏編號 + 期數置中 + 唯一分組)
# ==========================================
elif menu == "📅 移工雙月服務週期排程":
    st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.7rem; font-weight: 700; color: #f8fafc;">📅 移工雙月服務週期排程</h2>
            <p style="margin: 0.35rem 0 0 0; color: #94a3b8; font-size: 0.9rem;">
                依每位移工合約排程獨立分組。點擊展開可直接勾選「完成?」並同步存回資料庫。
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    schedule_data = []
    if supabase:
        try:
            res = supabase.table("worker_service_schedules").select("*").execute()
            schedule_data = res.data or []
        except Exception as e:
            st.error(f"讀取資料庫失敗: {e}")

    df_raw = pd.DataFrame(schedule_data) if schedule_data else pd.DataFrame()

    if not df_raw.empty:
        df_raw["worker_name"] = df_raw["worker_name"].fillna("未命名移工").astype(str).str.strip()
        df_raw["employer_name"] = df_raw["employer_name"].fillna("未指定單位").astype(str).str.strip()
        df_raw["start_date"] = df_raw["start_date"].fillna("").astype(str).str[:10]
        df_raw["target_date"] = df_raw["target_date"].fillna("").astype(str).str[:10]
        df_raw["status"] = df_raw["status"].fillna("待訪視").astype(str).str.strip()
        
        if "period_number" in df_raw.columns:
            df_raw["period_number"] = pd.to_numeric(df_raw["period_number"], errors="coerce").fillna(0).astype(int)
        
        # 精準識別鍵 (姓名 + 雇主 + 起始日期)，徹底防止不同工人混在同一條
        df_raw["worker_group_key"] = df_raw["worker_name"] + "___" + df_raw["employer_name"] + "___" + df_raw["start_date"]

    # 頂部 KPI 統計
    today = date.today()
    urgent_count = 0
    overdue_count = 0
    
    for row in schedule_data:
        d_str = str(row.get("target_date", ""))[:10]
        status_val = str(row.get("status", "")).strip()
        if d_str and status_val != "已完成":
            try:
                target_d = datetime.strptime(d_str, "%Y-%m-%d").date()
                days_left = (target_d - today).days
                if days_left < 0:
                    overdue_count += 1
                elif days_left <= 14:
                    urgent_count += 1
            except:
                pass

    unique_groups = []
    if not df_raw.empty:
        unique_groups = df_raw[["worker_group_key", "worker_name", "employer_name", "start_date"]].drop_duplicates().to_dict(orient="records")

    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">獨立列管移工總數</div>
            <div class="kpi-value">{len(unique_groups)} <span style="font-size: 0.9rem; color: #64748b; font-weight: 400;">人</span></div>
            <span class="kpi-badge badge-blue">服務排程管理</span>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">14 天內即將到期</div>
            <div class="kpi-value" style="color: #fbbf24;">{urgent_count} <span style="font-size: 0.9rem; color: #64748b; font-weight: 400;">件</span></div>
            <span class="kpi-badge badge-amber">待安排入廠訪視</span>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">已逾期未完成</div>
            <div class="kpi-value" style="color: #f87171;">{overdue_count} <span style="font-size: 0.9rem; color: #64748b; font-weight: 400;">件</span></div>
            <span class="kpi-badge badge-red">請儘速確認進度</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_sched_list, tab_sched_add = st.tabs(["📋 移工排程列表 (點選展開)", "➕ 新增雙月服務週期"])

    with tab_sched_list:
        if not df_raw.empty:
            search_kw = st.text_input("🔍 快速搜尋工人姓名或雇主：", placeholder="輸入工人姓名、雇主名稱搜尋...")
            
            filtered_groups = unique_groups
            if search_kw:
                filtered_groups = [
                    g for g in unique_groups 
                    if search_kw.lower() in g["worker_name"].lower() 
                    or search_kw.lower() in g["employer_name"].lower()
                ]

            st.markdown(f"<div style='margin-bottom: 0.75rem; color: #94a3b8; font-size: 0.85rem;'>共 <b>{len(filtered_groups)}</b> 位獨立移工排程</div>", unsafe_allow_html=True)

            for idx, g in enumerate(filtered_groups):
                g_key = g["worker_group_key"]
                w_name = g["worker_name"]
                e_name = g["employer_name"]
                s_date = g["start_date"]
                
                w_df = df_raw[df_raw["worker_group_key"] == g_key].sort_values(by="period_number").copy()
                
                total_p = len(w_df)
                done_p = len(w_df[w_df["status"] == "已完成"])
                
                pending_df = w_df[w_df["status"] != "已完成"]
                if not pending_df.empty:
                    next_target = pending_df.iloc[0]["target_date"]
                    next_period = pending_df.iloc[0]["period_number"]
                    status_text = f"⏳ 第 {next_period} 期待訪視（目標日：{next_target}）"
                else:
                    status_text = "🎉 所有期數已全數完成"

                start_hint = f"（合約起始：{s_date}）" if s_date else ""
                expander_label = f"👤 {w_name} ｜ 🏢 雇主：{e_name} {start_hint} ｜ 進度：{done_p}/{total_p} 期 ｜ {status_text}"
                
                with st.expander(expander_label):
                    subset_df = pd.DataFrame()
                    subset_df["完成?"] = (w_df["status"] == "已完成")
                    subset_df["狀態"] = w_df["status"]
                    # 格式化為置中字串格式，讓期數排在正中央
                    subset_df["期數"] = w_df["period_number"].apply(lambda x: f"第 {x} 期")
                    subset_df["目標服務日期"] = w_df["target_date"]
                    subset_df["_hidden_id"] = w_df["id"]

                    st.caption("提示：直接勾選「完成?」或修改「狀態」，再點下方按鈕即可同步存入資料庫。")
                    
                    edited_subset = st.data_editor(
                        subset_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "完成?": st.column_config.CheckboxColumn("完成?", help="勾選即完成此期服務"),
                            "狀態": st.column_config.SelectboxColumn(
                                "狀態", 
                                options=["待訪視", "已完成", "安排中", "待追蹤"],
                                required=True
                            ),
                            "期數": st.column_config.TextColumn("期數", disabled=True),
                            "目標服務日期": st.column_config.TextColumn("目標服務日期", disabled=True),
                            "_hidden_id": None,  # 完全隱藏編號
                        },
                        key=f"editor_worker_{idx}"
                    )
                    
                    if st.button(f"💾 儲存【{w_name}】的排程變更", key=f"btn_save_{idx}"):
                        saved_count = 0
                        for _, row in edited_subset.iterrows():
                            rec_id = int(row["_hidden_id"])
                            orig_status = w_df.loc[w_df["id"] == rec_id, "status"].values[0]
                            
                            new_status = row["狀態"]
                            if row["完成?"] and new_status != "已完成":
                                new_status = "已完成"
                            elif not row["完成?"] and orig_status == "已完成" and new_status == "已完成":
                                new_status = "待訪視"
                                
                            if new_status != orig_status:
                                try:
                                    supabase.table("worker_service_schedules").update({
                                        "status": new_status
                                    }).eq("id", rec_id).execute()
                                    saved_count += 1
                                except Exception as err:
                                    st.error(f"更新失敗: {err}")
                        
                        if saved_count > 0:
                            st.success(f"✅ 【{w_name}】已成功更新 {saved_count} 期狀態！")
                            st.rerun()
                        else:
                            st.info("沒有偵測到任何狀態變更。")
        else:
            st.info("目前尚無移工服務排程紀錄。")

    with tab_sched_add:
        st.markdown("#### 新增雙月服務週期紀錄")
        with st.form("add_sched_form", clear_on_submit=True):
            col_w1, col_w2 = st.columns(2)
            with col_w1:
                worker_name = st.text_input("移工姓名*")
                employer_name = st.text_input("雇主/廠區名稱*")
                period_num = st.number_input("服務期數 (第幾期)", min_value=1, value=1, step=1)
            with col_w2:
                start_d = st.date_input("起始基準日期*", value=date.today())
                default_target = start_d + relativedelta(months=2)
                target_d = st.date_input("目標服務日期 (雙月)*", value=default_target)
                status_choice = st.selectbox("初始狀態", ["待訪視", "已完成", "安排中", "待追蹤"])
            
            submitted_sched = st.form_submit_button("建立排程紀錄")
            if submitted_sched:
                if not worker_name or not employer_name:
                    st.warning("請填寫移工姓名與雇主名稱！")
                else:
                    try:
                        payload = {
                            "worker_name": worker_name.strip(),
                            "employer_name": employer_name.strip(),
                            "start_date": str(start_d),
                            "period_number": int(period_num),
                            "target_date": str(target_d),
                            "status": status_choice
                        }
                        supabase.table("worker_service_schedules").insert(payload).execute()
                        st.success("✅ 排程紀錄已成功新增至 Supabase！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"新增失敗：{e}")
