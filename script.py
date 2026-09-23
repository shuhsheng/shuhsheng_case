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

# 注入高清晰、高對比現代科技深色 UI
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
    
    /* 1. 所有欄位標題、Label 與說明文字全面亮化 */
    label, [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] span {
        color: #f8fafc !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    .stMarkdown p {
        color: #cbd5e1;
    }
    
    /* 2. 頁籤 (Tabs) 高亮清晰化：亮藍選中 + 醒目白未選 */
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
    
    /* 3. 輸入框美化 (微透深色質感，文字純白，消除刺眼死白) */
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
    
    /* 4. KPI 統計卡片 */
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
    
    /* 5. 案例 SOP 卡片 */
    .sop-card {
        background: #111827;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.25rem 1.4rem;
        margin-bottom: 1rem;
        border-left: 4px solid #38bdf8;
    }
    .sop-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 0.45rem;
    }
    .sop-category {
        display: inline-block;
        background: #1e293b;
        color: #38bdf8;
        padding: 0.2rem 0.55rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }
    .sop-content {
        color: #cbd5e1;
        font-size: 0.95rem;
        line-height: 1.65;
        white-space: pre-wrap;
    }

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
        padding: 0.5rem 1.25rem !important;
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
                供同仁遇到突發或特殊狀況時快速檢索標準處理作業流程 (SOP)，免去重複詢問。
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # 讀取 cases 資料
    cases_data = []
    if supabase:
        try:
            res = supabase.table("cases").select("*").execute()
            cases_data = res.data or []
        except Exception as e:
            st.error(f"讀取資料庫失敗: {e}")

    # 頂部 KPI 卡片
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

    tab_search, tab_add = st.tabs(["🔍 查詢處置經驗與 SOP", "➕ 建立新案例紀錄"])
    
    with tab_search:
        col_search, col_cat = st.columns([3, 1])
        with col_search:
            search_query = st.text_input("輸入關鍵字查詢 (如：健檢不合格、失聯、急診、證件補發...)", placeholder="輸入搜尋關鍵字...")
        with col_cat:
            all_categories = ["全部分類"] + sorted(list(set([c.get("category", "其他") for c in cases_data if c.get("category")])))
            selected_cat = st.selectbox("分類篩選", all_categories)
        
        # 篩選邏輯
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
        
        st.markdown(f"<div style='margin: 0.5rem 0 1rem 0; color: #94a3b8; font-size: 0.85rem;'>共找到 <b>{len(filtered_cases)}</b> 筆相關案例紀錄</div>", unsafe_allow_html=True)
        
        if filtered_cases:
            for item in filtered_cases:
                title = item.get("title", "未命名案件")
                cat = item.get("category", "其他")
                sol = item.get("solution") or item.get("description") or "尚未提供具體說明"
                created = str(item.get("created_at", ""))[:10]
                
                st.markdown(f"""
                <div class="sop-card">
                    <div class="sop-title">{title}</div>
                    <span class="sop-category">{cat}</span>
                    <span style="font-size: 0.75rem; color: #64748b; margin-left: 0.5rem;">紀錄日期: {created}</span>
                    <div class="sop-content">{sol}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("查無相關案例。如果解決了新狀況，歡迎點擊上方「建立新案例紀錄」頁籤進行建檔！")

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
# 5. 功能二：移工雙月服務週期排程 (worker_service_schedules)
# ==========================================
elif menu == "📅 移工雙月服務週期排程":
    st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.7rem; font-weight: 700; color: #f8fafc;">📅 移工雙月服務週期排程</h2>
            <p style="margin: 0.35rem 0 0 0; color: #94a3b8; font-size: 0.9rem;">
                追蹤每兩個月一次的定期關懷訪視、法規申報與入廠服務排程。
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # 讀取排程資料（使用對應的 target_date）
    schedule_data = []
    if supabase:
        try:
            res = supabase.table("worker_service_schedules").select("*").order("target_date", desc=False).execute()
            schedule_data = res.data or []
        except Exception as e:
            st.error(f"讀取資料庫失敗: {e}")

    # 統計指標計算
    today = date.today()
    urgent_count = 0
    overdue_count = 0
    total_records = len(schedule_data)
    
    for row in schedule_data:
        d_str = row.get("target_date")
        status_val = str(row.get("status", ""))
        
        # 只針對未完成的案件進行預警統計
        if d_str and status_val != "已完成":
            try:
                target_d = datetime.strptime(str(d_str)[:10], "%Y-%m-%d").date()
                days_left = (target_d - today).days
                if days_left < 0:
                    overdue_count += 1
                elif days_left <= 14:
                    urgent_count += 1
            except:
                pass

    # 排程 KPI 卡片
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">排程紀錄總數</div>
            <div class="kpi-value">{total_records} <span style="font-size: 0.9rem; color: #64748b; font-weight: 400;">筆</span></div>
            <span class="kpi-badge badge-blue">服務週期列管</span>
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

    tab_sched_list, tab_sched_add = st.tabs(["📋 服務排程清單", "➕ 新增雙月服務週期"])

    with tab_sched_list:
        if schedule_data:
            df = pd.DataFrame(schedule_data)
            
            # 對齊你的真實欄位名稱
            col_rename = {
                "id": "編號",
                "worker_name": "移工姓名",
                "employer_name": "雇主/單位",
                "period_number": "期數",
                "start_date": "起始日期",
                "target_date": "目標服務日期",
                "status": "狀態"
            }
            display_cols = [c for c in col_rename.keys() if c in df.columns]
            df_display = df[display_cols].rename(columns=col_rename)
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
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
                # 預設自動推算雙月 (+2 個月)
                default_target = start_d + relativedelta(months=2)
                target_d = st.date_input("目標服務日期 (雙月)*", value=default_target)
                status_choice = st.selectbox("初始狀態", ["安排中", "已完成", "待追蹤"])
            
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
