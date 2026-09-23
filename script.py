import streamlit as st
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from supabase import create_client, Client

# ==========================================
# 0. 系統預設業務分類常數
# ==========================================
DEFAULT_CATEGORIES = [
    "入境",
    "出境",
    "健檢",
    "轉出",
    "失聯",
    "逃跑",
    "生病",
    "過世",
    "事故",
    "其他"
]

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
    
    /* 欄位標籤與文字亮化 */
    label, [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] span {
        color: #f8fafc !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    
    /* 頁籤 (Tabs) 高亮 */
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
    
    /* 側邊欄與全域輸入框、下拉選單樣式 */
    div[data-baseweb="input"], 
    div[data-baseweb="base-input"],
    div[data-baseweb="select"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="select"] div {
        background-color: #1e293b !important;
        border-color: rgba(255, 255, 255, 0.25) !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.3) !important;
    }

    input, 
    input[type="text"], 
    input[type="password"],
    textarea,
    div[data-baseweb="input"] input {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        background-color: #1e293b !important;
        caret-color: #38bdf8 !important;
    }
    input::placeholder, textarea::placeholder {
        color: #94a3b8 !important;
    }

    div[data-baseweb="select"] * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    ul[data-baseweb="menu"], 
    div[data-baseweb="popover"] div {
        background-color: #1e293b !important;
    }
    li[data-baseweb="menu-item"] {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }
    li[data-baseweb="menu-item"]:hover {
        background-color: #334155 !important;
    }

    div[data-testid="stNumberInput"] input, div[data-testid="stDateInput"] input {
        color: #ffffff !important;
        background-color: #1e293b !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    /* Expander 展開卡片深色科技化 */
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
    
    /* KPI 統計卡片 */
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

    .sop-view-box {
        background-color: #1e293b;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 0.75rem 0;
        white-space: pre-wrap;
        line-height: 1.6;
        color: #cbd5e1;
    }

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
# 3. 側邊欄身分切換與選單導航
# ==========================================
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "外務"

ADMIN_PIN = "1111"
BOSS_PIN = "8888"

with st.sidebar:
    st.markdown("### 🔐 作業權限切換")
    role_choice = st.selectbox(
        "選擇當前身分：",
        ["外務", "行政", "老闆"],
        index=["外務", "行政", "老闆"].index(st.session_state["user_role"])
    )
    
    if role_choice == "外務":
        st.session_state["user_role"] = "外務"
        st.success("🟢 模式：外務（現場訪視回報）")
    elif role_choice == "行政":
        entered_pin = st.text_input("輸入行政通行碼：", type="password", key="pin_admin")
        if entered_pin == ADMIN_PIN:
            st.session_state["user_role"] = "行政"
            st.success("🔵 模式：行政（案件維護與排程建檔）")
        else:
            st.session_state["user_role"] = "外務"
            if entered_pin:
                st.error("通行碼錯誤！保持外務身分。")
    elif role_choice == "老闆":
        entered_pin = st.text_input("輸入老闆最高通行碼：", type="password", key="pin_boss")
        if entered_pin == BOSS_PIN:
            st.session_state["user_role"] = "老闆"
            st.success("🟣 模式：老闆（最高管理者全權限）")
        else:
            st.session_state["user_role"] = "外務"
            if entered_pin:
                st.error("通行碼錯誤！保持外務身分。")

    st.markdown("---")
    st.markdown("### 📌 系統功能")
    menu = st.radio(
        "請選擇作業模組：",
        ["📅 移工雙月服務週期排程", "📖 突發案件與處置知識庫"],
        index=0
    )
    st.markdown("---")
    st.markdown(f"<div style='font-size:0.75rem; color:#64748b;'>當前有效身分：<b>{st.session_state['user_role']}</b><br>資料庫狀態：連線中 (Supabase)</div>", unsafe_allow_html=True)

current_role = st.session_state["user_role"]


# ==========================================
# 4. 模組一：移工雙月服務週期排程 (支援編輯基本資料與老闆刪除)
# ==========================================
if menu == "📅 移工雙月服務週期排程":
    st.markdown(f"""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.7rem; font-weight: 700; color: #f8fafc;">📅 移工雙月服務週期排程</h2>
            <p style="margin: 0.35rem 0 0 0; color: #94a3b8; font-size: 0.9rem;">
                依每位移工合約排程獨立分組。身分：<span style="color:#38bdf8; font-weight:600;">{current_role}</span>。
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
        
        df_raw["worker_group_key"] = df_raw["worker_name"] + "___" + df_raw["employer_name"] + "___" + df_raw["start_date"]

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

    if current_role in ["行政", "老闆"]:
        tabs = st.tabs(["📋 移工排程列表 (點選展開)", "⚡ 自動批次推算移工合約排程"])
        tab_sched_list = tabs[0]
        tab_sched_add = tabs[1]
    else:
        tab_sched_list = st.container()
        tab_sched_add = None

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
                    # 表格資料展示與勾選
                    subset_df = pd.DataFrame()
                    subset_df["完成?"] = (w_df["status"] == "已完成")
                    subset_df["狀態"] = w_df["status"]
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
                            "_hidden_id": None,
                        },
                        key=f"editor_worker_{idx}"
                    )
                    
                    # 儲存勾選按鈕
                    if st.button(f"💾 儲存【{w_name}】的訪視狀態變更", key=f"btn_save_status_{idx}"):
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

                    # ==========================================
                    # 行政/老闆專用：基本資料打錯時的修改面板
                    # ==========================================
                    if current_role in ["行政", "老闆"]:
                        st.markdown("---")
                        st.markdown("##### ✏️ 修正移工基本資料（打錯字時批次修正所有期數）")
                        col_m1, col_m2, col_m3 = st.columns([2, 2, 2])
                        with col_m1:
                            edit_w_name = st.text_input("移工姓名", value=w_name, key=f"edit_wn_{idx}")
                        with col_m2:
                            edit_e_name = st.text_input("雇主/廠區名稱", value=e_name, key=f"edit_en_{idx}")
                        with col_m3:
                            curr_start_d = datetime.strptime(s_date, "%Y-%m-%d").date() if s_date else date.today()
                            edit_s_date = st.date_input("合約起始基準日", value=curr_start_d, key=f"edit_sd_{idx}")
                        
                        btn_c1, btn_c2 = st.columns([2, 2])
                        with btn_c1:
                            if st.button(f"💾 更新【{w_name}】基本資料", key=f"btn_update_info_{idx}"):
                                try:
                                    all_ids = w_df["id"].tolist()
                                    for rid in all_ids:
                                        supabase.table("worker_service_schedules").update({
                                            "worker_name": edit_w_name.strip(),
                                            "employer_name": edit_e_name.strip(),
                                            "start_date": str(edit_s_date)
                                        }).eq("id", rid).execute()
                                    st.success(f"✅ 已成功更新【{edit_w_name}】所有期數的基本資料！")
                                    st.rerun()
                                except Exception as err:
                                    st.error(f"更新失敗：{err}")

                    # ==========================================
                    # 老闆專用：刪除整組合約排程
                    # ==========================================
                    if current_role == "老闆":
                        with btn_c2:
                            if st.button(f"🗑️ 刪除【{w_name}】整份合約排程", key=f"btn_delete_group_{idx}"):
                                try:
                                    all_ids = w_df["id"].tolist()
                                    for rid in all_ids:
                                        supabase.table("worker_service_schedules").delete().eq("id", rid).execute()
                                    st.success(f"✅ 已徹底刪除【{w_name}】共 {len(all_ids)} 筆排程！")
                                    st.rerun()
                                except Exception as err:
                                    st.error(f"刪除失敗：{err}")
        else:
            st.info("目前尚無移工服務排程紀錄。")

    # ==========================================
    # 核心：自動批次推算移工整份合約雙月訪視日曆
    # ==========================================
    if tab_sched_add:
        with tab_sched_add:
            st.markdown("#### ⚡ 自動批次推算移工雙月服務週期（行政 / 老闆權限）")
            st.info("💡 輸入基本資料與起算日，系統將按照勞動部評鑑日曆天數規則，精確每 2 個月推算一期，自動生成所有期數並寫入資料庫，絕不超期！")
            
            with st.form("auto_generate_schedules_form"):
                col_in1, col_in2 = st.columns(2)
                with col_in1:
                    worker_name_in = st.text_input("移工姓名*", placeholder="例如：SUTRISNO 或 阮文勇")
                    employer_name_in = st.text_input("雇主 / 廠區名稱*", placeholder="例如：台塑企業 或 大立光電")
                with col_in2:
                    start_date_in = st.date_input("合約起始基準日 (入境日/承接日)*", value=date.today())
                    total_periods_choice = st.selectbox(
                        "產生總期數 (每 2 個月一次)：",
                        [18, 36, 12, 6],
                        index=0,
                        help="18期 = 36個月(3年合約)；36期 = 72個月(6年長約)"
                    )
                
                submitted_auto = st.form_submit_button("⚡ 立即批次自動產生全期數排程")
                
                if submitted_auto:
                    if not worker_name_in or not employer_name_in:
                        st.warning("請填寫移工姓名與雇主名稱！")
                    else:
                        batch_rows = []
                        for p in range(1, total_periods_choice + 1):
                            target_d = start_date_in + relativedelta(months=2 * p)
                            batch_rows.append({
                                "worker_name": worker_name_in.strip(),
                                "employer_name": employer_name_in.strip(),
                                "start_date": str(start_date_in),
                                "period_number": p,
                                "target_date": str(target_d),
                                "status": "待訪視"
                            })
                        
                        try:
                            supabase.table("worker_service_schedules").insert(batch_rows).execute()
                            st.success(f"🎉 成功！已為【{worker_name_in}】一次產生共 {total_periods_choice} 期（每 2 個月一次）的法定雙月訪視排程！")
                            st.rerun()
                        except Exception as e:
                            st.error(f"批次建立失敗：{e}")


# ==========================================
# 5. 模組二：突發案件與處置知識庫 (cases)
# ==========================================
elif menu == "📖 突發案件與處置知識庫":
    st.markdown(f"""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.7rem; font-weight: 700; color: #f8fafc;">📖 突發案件處置知識庫</h2>
            <p style="margin: 0.35rem 0 0 0; color: #94a3b8; font-size: 0.9rem;">
                點選案例條目展開詳細處置 SOP。身分：<span style="color:#38bdf8; font-weight:600;">{current_role}</span>。
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
    
    existing_cats = set([str(c.get("category", "")).strip() for c in cases_data if c.get("category")])
    all_cat_options = DEFAULT_CATEGORIES.copy()
    for c_val in existing_cats:
        if c_val and c_val not in all_cat_options:
            all_cat_options.append(c_val)

    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">收錄案例總數</div>
            <div class="kpi-value">{total_cases} <span style="font-size: 0.9rem; color: #64748b; font-weight: 400;">筆</span></div>
            <span class="kpi-badge badge-blue">處置 SOP 資料庫</span>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">涵蓋類別</div>
            <div class="kpi-value">{len(existing_cats)} <span style="font-size: 0.9rem; color: #64748b; font-weight: 400;">大類</span></div>
            <span class="kpi-badge badge-green">完整分類歸檔</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if current_role in ["行政", "老闆"]:
        tabs = st.tabs(["🔍 案例知識庫清單", "➕ 建立新案例紀錄"])
        tab_case_list = tabs[0]
        tab_case_add = tabs[1]
    else:
        tab_case_list = st.container()
        tab_case_add = None

    with tab_case_list:
        col_search, col_cat = st.columns([3, 1])
        with col_search:
            search_query = st.text_input("輸入關鍵字查詢 (如：健檢不合格、失聯、急診、證件補發...)", placeholder="輸入搜尋關鍵字...")
        with col_cat:
            filter_categories = ["全部分類"] + all_cat_options
            selected_cat = st.selectbox("分類篩選", filter_categories)
        
        filtered_cases = cases_data
        
        if selected_cat != "全部分類":
            filtered_cases = [c for c in filtered_cases if str(c.get("category", "")).strip() == selected_cat]
            
        if search_query:
            filtered_cases = [
                c for c in filtered_cases 
                if search_query.lower() in str(c.get("title", "")).lower() 
                or search_query.lower() in str(c.get("problem", "")).lower()
                or search_query.lower() in str(c.get("solution", "")).lower()
                or search_query.lower() in str(c.get("result", "")).lower()
                or search_query.lower() in str(c.get("created_by", "")).lower()
            ]
        
        st.markdown(f"<div style='margin-bottom: 1rem; color: #94a3b8; font-size: 0.85rem;'>共找到 <b>{len(filtered_cases)}</b> 筆案例</div>", unsafe_allow_html=True)
        
        if filtered_cases:
            for item in filtered_cases:
                case_id = item.get("id")
                title = item.get("title") or item.get("problem") or "未命名案件"
                cat = str(item.get("category", "其他")).strip() or "其他"
                creator = item.get("created_by") or "系統/未註記"
                sol = item.get("solution") or item.get("result") or item.get("description") or ""
                created = str(item.get("created_at", ""))[:10]
                
                expander_title = f"📋 【{cat}】{title} ｜ 建檔人：{creator} ｜ 建檔日期：{created}"
                
                with st.expander(expander_title):
                    if current_role == "外務":
                        st.markdown(f"**類別標籤**：`{cat}` ｜ **建檔人**：`{creator}` ｜ **建檔日期**：`{created}`")
                        st.markdown(f"<div class='sop-view-box'>{sol}</div>", unsafe_allow_html=True)
                    else:
                        edit_col1, edit_col2, edit_col3 = st.columns([2, 1, 1])
                        with edit_col1:
                            new_title_val = st.text_input("案例名稱", value=title, key=f"t_{case_id}")
                        with edit_col2:
                            edit_select_default = cat if cat in DEFAULT_CATEGORIES else "其他"
                            new_cat_sel = st.selectbox("分類標籤", DEFAULT_CATEGORIES, index=DEFAULT_CATEGORIES.index(edit_select_default), key=f"c_sel_{case_id}")
                        with edit_col3:
                            new_creator_val = st.text_input("建檔人", value=creator, key=f"u_{case_id}")
                            
                        custom_cat_val = ""
                        if new_cat_sel == "其他":
                            initial_custom = cat if cat not in DEFAULT_CATEGORIES else ""
                            custom_cat_val = st.text_input("請輸入自訂分類名稱*", value=initial_custom, placeholder="例如：居留證遺失、遣返出境...", key=f"c_custom_{case_id}")

                        new_sol_val = st.text_area("處置 SOP 說明與經驗", value=sol, height=180, key=f"s_{case_id}")
                        
                        btn_col1, btn_col2 = st.columns([1, 5])
                        with btn_col1:
                            save_btn = st.button("💾 儲存修改", key=f"btn_save_case_{case_id}")
                            
                        if save_btn:
                            final_cat = custom_cat_val.strip() if (new_cat_sel == "其他" and custom_cat_val.strip()) else new_cat_sel
                            
                            update_payload = {
                                "title": new_title_val.strip(),
                                "problem": new_title_val.strip(),
                                "solution": new_sol_val.strip(),
                                "result": new_sol_val.strip(),
                                "category": final_cat,
                                "created_by": new_creator_val.strip()
                            }

                            try:
                                supabase.table("cases").update(update_payload).eq("id", case_id).execute()
                                st.success("✅ 案例已更新完成！")
                                st.rerun()
                            except Exception as e:
                                st.error(f"更新失敗：{e}")
                        
                        if current_role == "老闆":
                            st.markdown("---")
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

    if tab_case_add:
        with tab_case_add:
            st.markdown("#### 建立新的突發案例 SOP (行政 / 老闆權限)")
            col_add_t, col_add_c, col_add_u = st.columns([2, 1, 1])
            with col_add_t:
                new_title = st.text_input("案例名稱 / 狀況主旨*", placeholder="例如：印尼籍移工初次健檢異常複檢流程")
            with col_add_c:
                new_category_sel = st.selectbox("分類標籤*", DEFAULT_CATEGORIES, index=0)
            with col_add_u:
                new_creator = st.text_input("建檔人員*", value=f"{current_role}同仁")
            
            custom_category_input = ""
            if new_category_sel == "其他":
                custom_category_input = st.text_input("👉 請輸入自訂分類名稱*", placeholder="例如：居留證遺失、換發護照...")
            
            new_solution = st.text_area("處置 SOP 流程與經驗說明*", placeholder="請詳細條列處理步驟、法規依據、通報對象或配合單位聯絡方式...", height=160)
            
            if st.button("儲存新案例至雲端知識庫", key="btn_add_case_submit"):
                final_category = custom_category_input.strip() if (new_category_sel == "其他" and custom_category_input.strip()) else new_category_sel

                if not new_title or not new_solution:
                    st.warning("請填寫完整的案例名稱與處置說明！")
                elif new_category_sel == "其他" and not custom_category_input.strip():
                    st.warning("選擇「其他」分類時，請在自訂空格中輸入具體分類名稱！")
                else:
                    insert_payload = {
                        "title": new_title.strip(),
                        "problem": new_title.strip(),
                        "solution": new_solution.strip(),
                        "result": new_solution.strip(),
                        "category": final_category,
                        "created_by": new_creator.strip() if new_creator else current_role,
                        "created_at": datetime.now().isoformat()
                    }

                    try:
                        supabase.table("cases").insert(insert_payload).execute()
                        st.success(f"✅ 案例【{final_category}】已成功儲存至知識庫！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"儲存失敗：{e}")
