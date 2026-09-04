import streamlit as st
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from supabase import create_client, Client

# 設定網頁標題與寬版排版
st.set_page_config(
    page_title="業務管理與服務追蹤系統",
    page_icon="📋",
    layout="wide"
)

# -------------------------------------------------------------
# 專業企業風 CSS 與 全域標楷體設定
# -------------------------------------------------------------
st.markdown("""
<style>
    /* 全站字體強制統一為標楷體 */
    html, body, [class*="css"], .stMarkdown, .stText, .stButton, .stTextInput, .stSelectbox, .stTextArea, .stDataFrame, div, span, p, h1, h2, h3, h4, h5, h6, input, button, select {
        font-family: "DFKai-SB", "BiauKai", "標楷體", "Kaiti TC", "KaiTi", serif !important;
    }

    /* 頂部與背景精緻化 */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* 標題樣式優化 */
    h1 {
        color: #1E293B !important;
        font-weight: bold;
        border-bottom: 2px solid #2563EB;
        padding-bottom: 8px;
        margin-bottom: 20px !important;
    }
    h2, h3 {
        color: #334155 !important;
        font-weight: 600;
    }

    /* 側邊欄專業配色 */
    [data-testid="stSidebar"] {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    [data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 1.05rem;
        padding: 6px 0;
    }

    /* 卡片與展開容器 (Expander) 風格 */
    .streamlit-expanderHeader {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        padding: 12px 18px !important;
        font-size: 1.08rem !important;
        font-weight: 600 !important;
        color: #1E293B !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .streamlit-expanderContent {
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-top: none;
        border-bottom-left-radius: 8px;
        border-bottom-right-radius: 8px;
        padding: 18px !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }

    /* 專業按鈕樣式 */
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* 提示訊息框美化 */
    .stAlert {
        border-radius: 6px;
        border-left: 5px solid #2563EB;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. 資料庫連線 (Supabase)
# -------------------------------------------------------------
@st.cache_resource
def get_supabase_client() -> Client:
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    return create_client(supabase_url, supabase_key)

try:
    supabase = get_supabase_client()
except Exception as e:
    st.error(f"資料庫連線失敗，請檢查 Streamlit Secrets 設定: {e}")
    st.stop()

# -------------------------------------------------------------
# 2. 側邊欄導航 (獨立模組)
# -------------------------------------------------------------
st.sidebar.markdown("### 🏢 管理系統導航")
menu_choice = st.sidebar.radio(
    "請選取作業模組：",
    ["📖 突發案件與處置知識庫", "🗓️ 移工雙月服務週期排程"]
)

# =============================================================
# 功能分頁 A：突發案件與處置知識庫
# =============================================================
if menu_choice == "📖 突發案件與處置知識庫":
    st.title("📖 突發案件處置與知識庫系統")
    st.caption("匯整內部突發事件應對處置指引，提供同仁迅速檢索標準作業程序。")
    
    try:
        res = supabase.table("cases").select("*").order("created_at", desc=True).execute()
        cases = res.data
    except Exception as e:
        st.error(f"資料庫讀取異常: {e}")
        cases = []

    tab1, tab2 = st.tabs(["🔍 處置知識檢索", "➕ 建立新處置案例"])
    
    # ---------------- 1. 檢索知識庫 ----------------
    with tab1:
        st.subheader("案例查詢")
        search_query = st.text_input("🔍 請輸入檢索關鍵字（例如：急診、健檢異常、證件逾期、失聯申報）：")
        
        filtered_cases = cases
        if search_query.strip():
            q = search_query.strip().lower()
            filtered_cases = [
                c for c in filtered_cases 
                if q in str(c.get("title", "")).lower() 
                or q in str(c.get("problem", "")).lower()
                or q in str(c.get("solution", "")).lower()
                or q in str(c.get("result", "")).lower()
                or q in str(c.get("details", "")).lower()
                or q in str(c.get("created_by", "")).lower()
            ]

        st.write(f"檢索結果：共 **{len(filtered_cases)}** 筆處置紀錄")

        if filtered_cases:
            for case in filtered_cases:
                cid = case["id"]
                ctitle = case.get("title", "無主旨")
                c_created_by = case.get("created_by") or "未具名"
                c_problem = case.get("problem", "") or ""
                c_solution = case.get("solution", "") or case.get("result", "") or case.get("details", "") or ""
                ctime = case.get("created_at", "")[:16].replace("T", " ") if case.get("created_at") else ""

                with st.expander(f"📌 {ctitle}（建檔人員：{c_created_by} ｜ 登記時間：{ctime}）"):
                    if c_problem and c_problem != ctitle:
                        st.markdown("**【狀況描述】**")
                        st.write(c_problem)
                    
                    st.markdown("**【標準處置流程 / 應對方式】**")
                    st.info(c_solution if c_solution else "尚無詳細處置備註。")
                    
                    st.markdown("---")
                    col_act1, col_act2 = st.columns([3, 1])
                    with col_act1:
                        with st.popover("✏️ 編輯本筆案例"):
                            with st.form(f"edit_case_{cid}"):
                                edit_title = st.text_input("狀況標題", value=ctitle)
                                edit_created_by = st.text_input("建檔人員", value=c_created_by)
                                edit_problem = st.text_area("狀況描述", value=c_problem, height=90)
                                edit_solution = st.text_area("處置流程與注意事項", value=c_solution, height=150)
                                if st.form_submit_button("儲存修改內容"):
                                    up_data = {
                                        "title": edit_title.strip(),
                                        "created_by": edit_created_by.strip(),
                                        "problem": edit_problem.strip(),
                                        "solution": edit_solution.strip(),
                                        "result": edit_solution.strip(),
                                        "details": edit_solution.strip()
                                    }
                                    supabase.table("cases").update(up_data).eq("id", cid).execute()
                                    st.success("案例內容已順利更新！")
                                    st.rerun()

                    with col_act2:
                        if st.button("🗑️ 刪除此案例", key=f"del_{cid}", type="secondary"):
                            supabase.table("cases").delete().eq("id", cid).execute()
                            st.warning("該筆紀錄已移除。")
                            st.rerun()
        else:
            st.info("目前無相符案例。若已妥善解決突發案件，請透過「建立新處置案例」分頁建檔分享。")

    # ---------------- 2. 建立新案例 ----------------
    with tab2:
        st.subheader("新增處置流程與指引")
        with st.form("new_case_knowledge_form", clear_on_submit=True):
            title = st.text_input("狀況主旨 / 案件名稱 *", placeholder="請簡述問題核心，例如：居留證逾期補發流程")
            created_by = st.text_input("建檔人員 *", placeholder="請填寫同仁姓名")
            problem = st.text_area("問題細節補充說明 (選填)", placeholder="若標題已足夠明確可留空，或補述現場特殊狀況...")
            solution = st.text_area("標準處置流程 / 應備文件 / 聯繫窗口 *", height=180, placeholder="請詳列處置步驟，方便後續同仁直接遵循辦理...")
            
            submitted = st.form_submit_button("確認建立此案例")
            if submitted:
                if not title.strip():
                    st.warning("請填寫狀況主旨！")
                elif not created_by.strip():
                    st.warning("請填寫建檔人員！")
                elif not solution.strip():
                    st.warning("請填寫處置流程！")
                else:
                    try:
                        valid_problem = problem.strip() if problem.strip() else title.strip()
                        now_str = datetime.now().isoformat()
                        
                        payload = {
                            "title": title.strip(),
                            "problem": valid_problem,
                            "solution": solution.strip(),
                            "result": solution.strip(),
                            "details": solution.strip(),
                            "created_by": created_by.strip(),
                            "created_at": now_str
                        }
                        supabase.table("cases").insert(payload).execute()
                        st.success("✅ 案例已成功收錄至內部知識庫！")
                        st.rerun()
                    except Exception as err:
                        st.error(f"存檔異常: {err}")

# =============================================================
# 功能分頁 B：移工雙月服務週期排程（一人一行版）
# =============================================================
elif menu_choice == "🗓️ 移工雙月服務週期排程":
    st.title("🗓️ 移工雙月服務週期排程管理系統")
    st.caption("依入境或承接日起算 3 年（18 期）訪視期程，支援直覺勾選及狀態隨時動態變更。")

    sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
        "👥 移工服務名冊與訪視勾選", 
        "⚠️ 移工狀態動態管理",
        "📤 批次匯入移工資料", 
        "➕ 單筆手動建檔"
    ])

    # ---------------- 2-1. 一人一行 + 點選打勾 ----------------
    with sub_tab1:
        st.subheader("服務名冊總覽")
        try:
            records = supabase.table("worker_service_schedules").select("*").order("period_number", desc=False).execute().data
        except Exception as e:
            st.error(f"讀取期程異常: {e}")
            records = []

        if records:
            df = pd.DataFrame(records)
            df["target_date"] = pd.to_datetime(df["target_date"]).dt.date
            if "employment_status" not in df.columns:
                df["employment_status"] = "在職中"
            if "status_reason" not in df.columns:
                df["status_reason"] = ""
            if "notes" not in df.columns:
                df["notes"] = ""
            if "visit_date" not in df.columns:
                df["visit_date"] = None

            # 彙總一人一行結構
            today = date.today()
            grouped = df.groupby(["worker_name", "employer_name", "worker_id", "start_date", "employment_status", "status_reason"], dropna=False)

            summary_list = []
            for (w_name, emp, wid, s_date, emp_stat, s_reason), g in grouped:
                total_p = len(g)
                done_p = len(g[g["status"] == "已完成"])
                
                pending = g[g["status"] == "待訪視"].sort_values("target_date")
                if not pending.empty:
                    next_target = pending.iloc[0]["target_date"]
                    next_period = pending.iloc[0]["period_number"]
                    next_info = f"第 {next_period} 期 ({next_target})"
                    is_overdue = next_target < today
                else:
                    next_target = None
                    next_info = "所有期別皆已訪視"
                    is_overdue = False

                summary_list.append({
                    "移工姓名": w_name,
                    "雇主名稱": emp if emp else "-",
                    "在職狀態": emp_stat if emp_stat else "在職中",
                    "進度": f"{done_p} / {total_p}",
                    "下次預定訪視": next_info,
                    "是否逾期": is_overdue,
                    "raw_next_date": next_target,
                    "group_df": g
                })

            summary_df = pd.DataFrame(summary_list)

            # 篩選工具列
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1:
                stat_filter = st.multiselect("在職狀態", options=["在職中", "失聯(逃跑)", "已轉出", "提前離境", "解約/終止"], default=["在職中"])
            with c_f2:
                kw = st.text_input("🔍 搜尋姓名 / 雇主：")
            with c_f3:
                time_flt = st.selectbox("訪視時程狀態", ["全部", "即日起 30 天內待訪視", "即日起 60 天內待訪視", "已有逾期待訪視"])

            flt = summary_df.copy()
            if stat_filter:
                flt = flt[flt["在職狀態"].isin(stat_filter)]
            if kw.strip():
                flt = flt[flt["移工姓名"].str.contains(kw, case=False) | flt["雇主名稱"].str.contains(kw, case=False)]
            
            if time_flt == "即日起 30 天內待訪視":
                flt = flt[flt["raw_next_date"].apply(lambda d: d is not None and today <= d <= today + relativedelta(days=30))]
            elif time_flt == "即日起 60 天內待訪視":
                flt = flt[flt["raw_next_date"].apply(lambda d: d is not None and today <= d <= today + relativedelta(days=60))]
            elif time_flt == "已有逾期待訪視":
                flt = flt[flt["是否逾期"] == True]

            st.write(f"移工總數：共 **{len(flt)}** 位")

            # 逐位呈現卡片
            for _, item in flt.iterrows():
                w_name = item["移工姓名"]
                emp = item["雇主名稱"]
                emp_stat = item["在職狀態"]
                prog = item["進度"]
                nxt = item["下次預定訪視"]
                is_ov = item["是否逾期"]
                g_df = item["group_df"].sort_values("period_number").copy()

                alert_badge = "🚨 " if is_ov and emp_stat == "在職中" else ""
                card_title = f"{alert_badge}{w_name} ｜ 雇主：{emp} ｜ 狀態：{emp_stat} ｜ 進度：{prog} ｜ 下次訪視：{nxt}"

                with st.expander(card_title):
                    st.info("💡 **操作指引**：在「是否已完成？」方塊直接點擊打勾，完成後點選下方「儲存訪視勾選變更」按鈕即可即時存檔。")
                    
                    edit_df = pd.DataFrame({
                        "id": g_df["id"],
                        "已完成訪視": g_df["status"] == "已完成",
                        "期別": g_df["period_number"].apply(lambda x: f"第 {x} 期"),
                        "預定訪視日": g_df["target_date"].astype(str),
                        "實際完成日": g_df["visit_date"].fillna(""),
                        "備註說明": g_df["notes"].fillna("")
                    })

                    edited_result = st.data_editor(
                        edit_df,
                        column_config={
                            "id": None,
                            "已完成訪視": st.column_config.CheckboxColumn(
                                "是否已完成？",
                                help="勾選即標記為完成；取消則標記為待訪視",
                                default=False,
                            ),
                            "期別": st.column_config.TextColumn("期別", disabled=True),
                            "預定訪視日": st.column_config.TextColumn("預定訪視日", disabled=True),
                            "實際完成日": st.column_config.TextColumn("實際完成日"),
                            "備註說明": st.column_config.TextColumn("備註說明"),
                        },
                        disabled=["期別", "預定訪視日"],
                        hide_index=True,
                        use_container_width=True,
                        key=f"editor_{w_name}_{emp}"
                    )

                    diff = edited_result["已完成訪視"] != edit_df["已完成訪視"]
                    diff_notes = edited_result["備註說明"] != edit_df["備註說明"]
                    diff_dates = edited_result["實際完成日"] != edit_df["實際完成日"]

                    if diff.any() or diff_notes.any() or diff_dates.any():
                        if st.button("💾 儲存訪視勾選變更", type="primary", key=f"btn_save_{w_name}_{emp}"):
                            with st.spinner("資料同步中..."):
                                for idx, row in edited_result.iterrows():
                                    sched_id = int(row["id"])
                                    is_done = row["已完成訪視"]
                                    note_val = str(row["備註說明"]).strip()
                                    
                                    if is_done:
                                        new_status = "已完成"
                                        cur_date = str(row["實際完成日"]).strip()
                                        visit_dt = cur_date if cur_date else date.today().strftime("%Y-%m-%d")
                                    else:
                                        new_status = "待訪視"
                                        visit_dt = None

                                    supabase.table("worker_service_schedules").update({
                                        "status": new_status,
                                        "visit_date": visit_dt,
                                        "notes": note_val
                                    }).eq("id", sched_id).execute()

                            st.success("✅ 訪視進度變更已儲存！")
                            st.rerun()

        else:
            st.info("目前尚無移工服務排程資料，請透過「批次匯入」或「單筆手動建檔」建立。")

    # ---------------- 2-2. 狀態動態變更 ----------------
    with sub_tab2:
        st.subheader("⚠️ 移工狀態動態管理（失聯 / 轉出 / 離境 / 恢復在職）")
        st.info("💡 **彈性說明**：標記失聯或轉出將暫停後續未完成訪視；若後續尋回投案或取消轉出，隨時可切回「在職中」恢復後續期程，先前已訪視紀錄均完整保存。")

        try:
            worker_list_res = supabase.table("worker_service_schedules").select("worker_name, employer_name, worker_id, employment_status, status_reason").execute().data
            if worker_list_res:
                workers_df = pd.DataFrame(worker_list_res).drop_duplicates(subset=["worker_name", "employer_name"])
            else:
                workers_df = pd.DataFrame()
        except:
            workers_df = pd.DataFrame()

        if not workers_df.empty:
            worker_options = [
                f"{row['worker_name']} ｜ 雇主：{row.get('employer_name', '未填')} ｜ 目前：{row.get('employment_status', '在職中')}"
                for _, row in workers_df.iterrows()
            ]
            selected_option = st.selectbox("請選擇目標移工：", worker_options)
            sel_idx = worker_options.index(selected_option)
            selected_worker_row = workers_df.iloc[sel_idx]
            target_worker_name = selected_worker_row["worker_name"]

            with st.form("worker_status_change_form"):
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    new_emp_status = st.selectbox(
                        "變更狀態為：",
                        ["在職中 (恢復排程)", "失聯(逃跑)", "已轉出", "提前離境", "解約/終止"]
                    )
                with col_s2:
                    status_note = st.text_input(
                        "異動備註說明：",
                        placeholder="例：曠職滿三日失聯通報 / 廢止轉出至新雇主"
                    )

                submit_status_change = st.form_submit_button("⚡ 確認變更動態")
                if submit_status_change:
                    try:
                        base_update = {
                            "employment_status": "在職中" if "在職中" in new_emp_status else new_emp_status,
                            "status_reason": status_note.strip()
                        }
                        supabase.table("worker_service_schedules").update(base_update).eq("worker_name", target_worker_name).execute()

                        if "在職中" in new_emp_status:
                            supabase.table("worker_service_schedules").update({"status": "待訪視"}).eq("worker_name", target_worker_name).neq("status", "已完成").execute()
                            st.success(f"✅ 【{target_worker_name}】已成功恢復為在職中，後續訪視期程已重啟！")
                        else:
                            supabase.table("worker_service_schedules").update({"status": "已終止(免訪視)"}).eq("worker_name", target_worker_name).neq("status", "已完成").execute()
                            st.warning(f"⚠️ 【{target_worker_name}】已標記為 {new_emp_status}，後續訪視已暫停。")
                        st.rerun()
                    except Exception as err:
                        st.error(f"狀態變更失敗: {err}")
        else:
            st.info("目前無移工資料可供變更。")

    # ---------------- 2-3. 批次匯入 ----------------
    with sub_tab3:
        st.subheader("批次匯入名單（自動推算 3 年 18 期）")
        template_df = pd.DataFrame({
            "移工姓名": ["SITI", "AGUS"],
            "入境日或承接日": ["2026-08-01", "2026-08-15"],
            "雇主名稱": ["富喬工業", "廣達電腦"],
            "工號": ["W001", "W002"]
        })
        csv_template = template_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 下載標準範本 (CSV)",
            data=csv_template,
            file_name="移工服務排程匯入範本.csv",
            mime="text/csv"
        )

        uploaded_file = st.file_uploader("上傳檔案 (支援 .xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith(".csv"):
                    import_df = pd.read_csv(uploaded_file)
                else:
                    import_df = pd.read_excel(uploaded_file)
                
                st.write("檔案內容預覽：")
                st.dataframe(import_df.head(), use_container_width=True)

                req_cols = ["移工姓名", "入境日或承接日"]
                if not all(col in import_df.columns for col in req_cols):
                    st.error("❌ 格式不符！請確認具備「移工姓名」及「入境日或承接日」欄位。")
                else:
                    if st.button("🚀 確認匯入並產生 18 期雙月排程"):
                        total_inserted = 0
                        with st.spinner("排程生成與寫入中..."):
                            for _, row in import_df.iterrows():
                                w_name = str(row["移工姓名"]).strip()
                                emp_name = str(row.get("雇主名稱", "")).strip() if pd.notna(row.get("雇主名稱")) else ""
                                w_id = str(row.get("工號", "")).strip() if pd.notna(row.get("工號")) else ""
                                
                                raw_date = row["入境日或承接日"]
                                try:
                                    start_dt = pd.to_datetime(raw_date).date()
                                except:
                                    continue

                                schedules = []
                                for i in range(1, 19):
                                    target_dt = start_dt + relativedelta(months=2 * i)
                                    schedules.append({
                                        "worker_id": w_id,
                                        "worker_name": w_name,
                                        "employer_name": emp_name,
                                        "start_date": start_dt.strftime("%Y-%m-%d"),
                                        "period_number": i,
                                        "target_date": target_dt.strftime("%Y-%m-%d"),
                                        "status": "待訪視",
                                        "employment_status": "在職中"
                                    })
                                
                                if schedules:
                                    supabase.table("worker_service_schedules").insert(schedules).execute()
                                    total_inserted += len(schedules)

                        st.success(f"🎉 匯入完成！已為名單移工建立共 {total_inserted} 筆服務排程！")
                        st.rerun()
            except Exception as e:
                st.error(f"檔案解析異常: {e}")

    # ---------------- 2-4. 單筆手動建立 ----------------
    with sub_tab4:
        st.subheader("手動建立單筆排程")
        with st.form("manual_worker_form", clear_on_submit=True):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                manual_name = st.text_input("移工姓名 *")
                manual_id = st.text_input("工號 / 護照號 (選填)")
            with col_m2:
                manual_emp = st.text_input("雇主名稱 (選填)")
                manual_start = st.date_input("入境日或承接日 *", value=date.today())

            manual_submit = st.form_submit_button("建立 3 年（18 期）服務排程")
            if manual_submit:
                if not manual_name.strip():
                    st.warning("請填寫移工姓名！")
                else:
                    try:
                        schedules = []
                        for i in range(1, 19):
                            t_dt = manual_start + relativedelta(months=2 * i)
                            schedules.append({
                                "worker_id": manual_id.strip(),
                                "worker_name": manual_name.strip(),
                                "employer_name": manual_emp.strip(),
                                "start_date": manual_start.strftime("%Y-%m-%d"),
                                "period_number": i,
                                "target_date": t_dt.strftime("%Y-%m-%d"),
                                "status": "待訪視",
                                "employment_status": "在職中"
                            })
                        supabase.table("worker_service_schedules").insert(schedules).execute()
                        st.success(f"✅ 已成功為【{manual_name}】建立 18 期排程！")
                    except Exception as err:
                        st.error(f"建立失敗: {err}")
