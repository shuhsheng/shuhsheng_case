import streamlit as st
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from supabase import create_client, Client

# 設定網頁標題與排版
st.set_page_config(
    page_title="案件知識庫與移工服務系統",
    page_icon="📋",
    layout="wide"
)

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
# 2. 側邊欄導航 (獨立分頁)
# -------------------------------------------------------------
st.sidebar.title("📌 功能選單")
menu_choice = st.sidebar.radio(
    "請選擇要操作的系統：",
    ["📖 突發案件與處置知識庫", "🗓️ 移工雙月服務週期排程"]
)

# =============================================================
# 功能分頁 A：突發案件與處置知識庫
# =============================================================
if menu_choice == "📖 突發案件與處置知識庫":
    st.title("📖 突發案件與處置經驗庫")
    st.caption("供同仁遇到突發或特殊狀況時快速檢索處理流程，無需重複詢問。")
    
    try:
        res = supabase.table("cases").select("*").order("created_at", desc=True).execute()
        cases = res.data
    except Exception as e:
        st.error(f"讀取資料庫失敗: {e}")
        cases = []

    tab1, tab2 = st.tabs(["🔍 查詢處置經驗與 SOP", "➕ 建立新案例紀錄"])
    
    # ---------------- 1. 查詢處置方式 ----------------
    with tab1:
        st.subheader("案例檢索")
        search_query = st.text_input("🔍 輸入關鍵字查詢（如：健檢不合格、失聯、急診、證件補發...）：")
        
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

        st.write(f"共找到 **{len(filtered_cases)}** 筆相關案例紀錄")

        if filtered_cases:
            for case in filtered_cases:
                cid = case["id"]
                ctitle = case.get("title", "無主旨")
                c_created_by = case.get("created_by") or "未具名"
                c_problem = case.get("problem", "") or ""
                c_solution = case.get("solution", "") or case.get("result", "") or case.get("details", "") or ""
                ctime = case.get("created_at", "")[:16].replace("T", " ") if case.get("created_at") else ""

                with st.expander(f"📌 {ctitle}（建檔人：{c_created_by} ｜ {ctime}）"):
                    if c_problem and c_problem != ctitle:
                        st.markdown("**❓ 遇到問題 / 狀況描述：**")
                        st.write(c_problem)
                    
                    st.markdown("**💡 具體處理方式 / 處置 SOP：**")
                    st.info(c_solution if c_solution else "無記錄處置細節")
                    
                    st.markdown("---")
                    col_act1, col_act2 = st.columns([3, 1])
                    with col_act1:
                        with st.popover("✏️ 修改這筆內容"):
                            with st.form(f"edit_case_{cid}"):
                                edit_title = st.text_input("狀況標題", value=ctitle)
                                edit_created_by = st.text_input("建檔人", value=c_created_by)
                                edit_problem = st.text_area("狀況描述", value=c_problem, height=90)
                                edit_solution = st.text_area("處理方式 / SOP", value=c_solution, height=150)
                                if st.form_submit_button("儲存修改"):
                                    up_data = {
                                        "title": edit_title.strip(),
                                        "created_by": edit_created_by.strip(),
                                        "problem": edit_problem.strip(),
                                        "solution": edit_solution.strip(),
                                        "result": edit_solution.strip(),
                                        "details": edit_solution.strip()
                                    }
                                    supabase.table("cases").update(up_data).eq("id", cid).execute()
                                    st.success("修改已儲存！")
                                    st.rerun()

                    with col_act2:
                        if st.button("🗑️ 刪除此案例", key=f"del_{cid}", type="secondary"):
                            supabase.table("cases").delete().eq("id", cid).execute()
                            st.warning("案例已刪除！")
                            st.rerun()
        else:
            st.info("查無相關案例。如果解決了新狀況，歡迎點上方分頁建立紀錄！")

    # ---------------- 2. 新增案例 ----------------
    with tab2:
        st.subheader("新增案例處置經驗")
        with st.form("new_case_knowledge_form", clear_on_submit=True):
            title = st.text_input("狀況標題 / 發生問題 *", placeholder="例：移工居留證過期如何急件補辦、健檢胸部X光疑似異常處理流程")
            created_by = st.text_input("建檔人 *", placeholder="請填寫您的姓名")
            problem = st.text_area("問題狀況補充說明 (選填)", placeholder="若標題已足夠清楚可留空，或補充案件當下的具體細節...")
            solution = st.text_area("具體處理方式 / 處置 SOP / 注意事項 *", height=180, placeholder="請詳細記錄處理步驟、聯絡窗口、應備文件，方便日後同仁直接照做...")
            
            submitted = st.form_submit_button("確認建立此案例")
            if submitted:
                if not title.strip():
                    st.warning("請填寫狀況標題！")
                elif not created_by.strip():
                    st.warning("請填寫建檔人！")
                elif not solution.strip():
                    st.warning("請填寫具體處理方式！")
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
                        st.success("✅ 案例新增成功！已納入同仁查詢庫。")
                        st.rerun()
                    except Exception as err:
                        st.error(f"新增失敗: {err}")

# =============================================================
# 功能分頁 B：移工雙月服務週期排程（一人一行版）
# =============================================================
elif menu_choice == "🗓️ 移工雙月服務週期排程":
    st.title("🗓️ 移工雙月服務週期排程與追蹤")
    st.caption("一人一行管理模式：一覽移工目前在職動態與最新訪視進度，展開即可勾選紀錄。")

    sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
        "👥 移工服務清單（一人一行）", 
        "⚠️ 移工狀態動態變更 / 隨時恢復",
        "📤 批次匯入移工名單 (Excel/CSV)", 
        "➕ 單筆手動建立"
    ])

    # ---------------- 2-1. 一人一行移工名冊與進度 ----------------
    with sub_tab1:
        st.subheader("移工清單總覽")
        try:
            records = supabase.table("worker_service_schedules").select("*").order("period_number", desc=False).execute().data
        except Exception as e:
            st.error(f"讀取排程發生錯誤: {e}")
            records = []

        if records:
            df = pd.DataFrame(records)
            df["target_date"] = pd.to_datetime(df["target_date"]).dt.date
            if "employment_status" not in df.columns:
                df["employment_status"] = "在職中"
            if "status_reason" not in df.columns:
                df["status_reason"] = ""

            # 依移工分組，聚合出「一人一行」的主表
            summary_list = []
            today = date.today()
            grouped = df.groupby(["worker_name", "employer_name", "worker_id", "start_date", "employment_status", "status_reason"], dropna=False)

            for (w_name, emp, wid, s_date, emp_stat, s_reason), g in grouped:
                total_periods = len(g)
                done_periods = len(g[g["status"] == "已完成"])
                
                # 尋找下一次待訪視的排程
                pending = g[g["status"] == "待訪視"].sort_values("target_date")
                if not pending.empty:
                    next_target = pending.iloc[0]["target_date"]
                    next_period = pending.iloc[0]["period_number"]
                    next_info = f"第 {next_period} 期 ({next_target})"
                    is_overdue = next_target < today
                else:
                    next_target = None
                    next_info = "已無待訪期別"
                    is_overdue = False

                summary_list.append({
                    "移工姓名": w_name,
                    "雇主名稱": emp if emp else "-",
                    "在職狀態": emp_stat if emp_stat else "在職中",
                    "入境/承接日": s_date,
                    "進度": f"{done_periods} / {total_periods}",
                    "下次預定訪視": next_info,
                    "是否逾期": is_overdue,
                    "raw_next_date": next_target,
                    "group_df": g
                })

            summary_df = pd.DataFrame(summary_list)

            # 頂部篩選條件
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1:
                stat_filter = st.multiselect("在職狀態篩選", options=["在職中", "失聯(逃跑)", "已轉出", "提前離境", "解約/終止"], default=["在職中"])
            with c_f2:
                kw = st.text_input("🔍 搜尋移工姓名 / 雇主：")
            with c_f3:
                time_flt = st.selectbox("訪視時程篩選", ["全部", "即日起 30 天內待訪視", "即日起 60 天內待訪視", "已有逾期待訪視"])

            # 執行過濾
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

            # 逐位呈現（一行一個移工）
            for _, item in flt.iterrows():
                w_name = item["移工姓名"]
                emp = item["雇主名稱"]
                emp_stat = item["在職狀態"]
                prog = item["進度"]
                nxt = item["下次預定訪視"]
                is_ov = item["是否逾期"]
                g_df = item["group_df"].sort_values("period_number")

                alert_badge = "🚨 " if is_ov and emp_stat == "在職中" else ""
                card_title = f"{alert_badge}{w_name} ｜ 雇主：{emp} ｜ 狀態：{emp_stat} ｜ 進度：{prog} ｜ 下次訪視：{nxt}"

                with st.expander(card_title):
                    st.markdown(f"#### 📅 【{w_name}】3 年雙月服務期程明細")
                    
                    # 呈現這 18 期的表格
                    display_cols = {
                        "period_number": "期別",
                        "target_date": "預定訪視日",
                        "status": "訪視狀態",
                        "visit_date": "實際訪視日",
                        "notes": "備註說明"
                    }
                    st.dataframe(g_df[list(display_cols.keys())].rename(columns=display_cols), use_container_width=True, hide_index=True)

                    st.markdown("##### ✍️ 勾選 / 變更期別進度")
                    
                    # 提供下拉選期別直接勾選，不需查 ID
                    periods_list = g_df["period_number"].tolist()
                    default_choice = g_df[g_df["status"] == "待訪視"]["period_number"].tolist()
                    selected_period = st.selectbox(
                        f"選擇要更新的期別", 
                        periods_list, 
                        index=periods_list.index(default_choice[0]) if default_choice else 0,
                        key=f"sel_p_{w_name}_{emp}"
                    )

                    target_row = g_df[g_df["period_number"] == selected_period].iloc[0]
                    target_sched_id = target_row["id"]

                    with st.form(f"form_quick_{w_name}_{selected_period}"):
                        cu1, cu2, cu3 = st.columns([1.5, 1.5, 3])
                        with cu1:
                            new_st = st.selectbox("狀態變更", ["已完成", "待訪視", "暫緩", "已終止(免訪視)"], index=0)
                        with cu2:
                            actual_dt = st.date_input("完成日期", value=date.today())
                        with cu3:
                            v_note = st.text_input("訪視備註", value=target_row.get("notes") or "")

                        if st.form_submit_button(f"儲存第 {selected_period} 期紀錄"):
                            payload_up = {
                                "status": new_st,
                                "visit_date": actual_dt.strftime("%Y-%m-%d") if new_st == "已完成" else None,
                                "notes": v_note.strip()
                            }
                            supabase.table("worker_service_schedules").update(payload_up).eq("id", target_sched_id).execute()
                            st.success(f"✅ 第 {selected_period} 期訪視紀錄已儲存！")
                            st.rerun()

        else:
            st.info("目前尚無移工資料，請至「批次匯入」或「單筆手動建立」新增移工！")

    # ---------------- 2-2. 移工動態變更 ----------------
    with sub_tab2:
        st.subheader("⚠️ 移工動態變更（失聯 / 轉出 / 離境 / 隨時恢復在職）")
        st.info("💡 彈性機制：若移工發生狀況，可一鍵將未來尚未訪視的期別改為「已終止(免訪視)」；若狀況解除，可隨時切回「在職中」恢復排程！")

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
            selected_option = st.selectbox("請選擇要調整動態的移工：", worker_options)
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
                        "異動原因說明：",
                        placeholder="例：雇主通報曠職滿 3 日失聯 / 轉出至新雇主"
                    )

                submit_status_change = st.form_submit_button("⚡ 確認更新移工動態")
                if submit_status_change:
                    try:
                        base_update = {
                            "employment_status": "在職中" if "在職中" in new_emp_status else new_emp_status,
                            "status_reason": status_note.strip()
                        }
                        supabase.table("worker_service_schedules").update(base_update).eq("worker_name", target_worker_name).execute()

                        if "在職中" in new_emp_status:
                            supabase.table("worker_service_schedules").update({"status": "待訪視"}).eq("worker_name", target_worker_name).neq("status", "已完成").execute()
                            st.success(f"✅ 已將【{target_worker_name}】恢復為在職中，後續訪視排程已重新上線！")
                        else:
                            supabase.table("worker_service_schedules").update({"status": "已終止(免訪視)"}).eq("worker_name", target_worker_name).neq("status", "已完成").execute()
                            st.warning(f"⚠️ 已將【{target_worker_name}】標記為 {new_emp_status}，後續未訪視排程已暫停。隨時可再切回在職中！")
                        st.rerun()
                    except Exception as err:
                        st.error(f"更新失敗: {err}")
        else:
            st.info("目前尚無移工資料可供變更。")

    # ---------------- 2-3. 批次匯入 ----------------
    with sub_tab3:
        st.subheader("批次匯入移工名單 (Excel / CSV)")
        template_df = pd.DataFrame({
            "移工姓名": ["SITI", "AGUS"],
            "入境日或承接日": ["2026-08-01", "2026-08-15"],
            "雇主名稱": ["富喬工業", "廣達電腦"],
            "工號": ["W001", "W002"]
        })
        csv_template = template_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 下載標準匯入範本 (CSV)",
            data=csv_template,
            file_name="移工服務排程匯入範本.csv",
            mime="text/csv"
        )

        uploaded_file = st.file_uploader("上傳移工名單檔案 (支援 .xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith(".csv"):
                    import_df = pd.read_csv(uploaded_file)
                else:
                    import_df = pd.read_excel(uploaded_file)
                
                st.write("預覽上傳內容：")
                st.dataframe(import_df.head(), use_container_width=True)

                req_cols = ["移工姓名", "入境日或承接日"]
                if not all(col in import_df.columns for col in req_cols):
                    st.error("❌ 檔案缺少必要欄位！請確認含有「移工姓名」及「入境日或承接日」。")
                else:
                    if st.button("🚀 確認匯入並自動推算 3 年（18期）排程"):
                        total_inserted = 0
                        with st.spinner("系統正在自動排程並寫入雲端..."):
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

                        st.success(f"🎉 成功匯入！已為名單移工自動產生共 {total_inserted} 筆雙月訪視排程！")
                        st.rerun()
            except Exception as e:
                st.error(f"檔案解析失敗: {e}")

    # ---------------- 2-4. 單筆手動建立 ----------------
    with sub_tab4:
        st.subheader("手動建立單筆移工排程")
        with st.form("manual_worker_form", clear_on_submit=True):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                manual_name = st.text_input("移工姓名 *")
                manual_id = st.text_input("工號 / 護照號 (選填)")
            with col_m2:
                manual_emp = st.text_input("雇主名稱 (選填)")
                manual_start = st.date_input("入境日或承接日 *", value=date.today())

            manual_submit = st.form_submit_button("建立 3 年（18期）雙月訪視排程")
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
                        st.success(f"✅ 已成功為【{manual_name}】自動推算並建立 18 期排程！")
                    except Exception as err:
                        st.error(f"建立失敗: {err}")
