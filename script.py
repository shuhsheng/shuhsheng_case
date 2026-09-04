import streamlit as st
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from supabase import create_client, Client

# 設定網頁標題與排版
st.set_page_config(
    page_title="智慧案件與移工服務管理系統",
    page_icon="📋",
    layout="wide"
)

# -------------------------------------------------------------
# 1. 資料庫安全連線 (Supabase)
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
# 2. 側邊欄選單（分頁切換，互不干擾）
# -------------------------------------------------------------
st.sidebar.title("📌 系統選單")
menu_choice = st.sidebar.radio(
    "請選擇功能模組：",
    ["📂 案件追蹤管理", "🗓️ 移工雙月服務週期排程"]
)

# =============================================================
# 功能一：案件追蹤管理（包含「建檔人」欄位）
# =============================================================
if menu_choice == "📂 案件追蹤管理":
    st.title("📂 案件追蹤管理系統")
    
    try:
        res = supabase.table("cases").select("*").order("created_at", desc=True).execute()
        cases_data = res.data
    except Exception as e:
        cases_data = []

    tab1, tab2 = st.tabs(["📋 案件列表與查詢", "➕ 新增案件紀錄"])
    
    with tab1:
        st.subheader("案件總覽清單")
        if cases_data:
            df_cases = pd.DataFrame(cases_data)
            
            # 美化欄位標題與調整順序
            rename_dict = {
                "id": "編號",
                "title": "案件標題",
                "category": "類別",
                "status": "處理狀態",
                "created_by": "建檔人",
                "handled_by": "承辦人",
                "details": "詳細說明與處置",
                "created_at": "建檔時間"
            }
            cols_to_display = [c for c in ["id", "title", "category", "status", "created_by", "handled_by", "details", "created_at"] if c in df_cases.columns]
            df_show = df_cases[cols_to_display].rename(columns=rename_dict)
            
            search_query = st.text_input("🔍 搜尋案件標題、建檔人、承辦人或關鍵字：")
            if search_query:
                mask = df_show.astype(str).apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
                df_show = df_show[mask]
            st.dataframe(df_show, use_container_width=True)
        else:
            st.info("目前尚無案件紀錄。")
            
    with tab2:
        st.subheader("新增案件")
        with st.form("new_case_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("案件標題 / 摘要 *")
                category = st.selectbox("案件類別", ["日常申報", "突發緊急", "例行健檢", "證件申辦", "轉出承接", "其他"])
                status = st.selectbox("進度狀態", ["進行中", "已完成", "列管追蹤", "已結案"])
            with col2:
                created_by = st.text_input("建檔人 *", placeholder="請輸入填表同仁姓名")
                handled_by = st.text_input("負責承辦人", placeholder="若尚未指派可先空白")
                details = st.text_area("詳細內容 / 處置紀錄", height=110)
            
            submitted = st.form_submit_button("確認新增案件")
            if submitted:
                if not title.strip():
                    st.warning("請填寫案件標題！")
                elif not created_by.strip():
                    st.warning("請填寫建檔人！")
                else:
                    try:
                        payload = {
                            "title": title.strip(),
                            "category": category,
                            "status": status,
                            "created_by": created_by.strip(),
                            "handled_by": handled_by.strip(),
                            "details": details.strip()
                        }
                        supabase.table("cases").insert(payload).execute()
                        st.success("✅ 案件新增成功！")
                        st.rerun()
                    except Exception as err:
                        st.error(f"新增失敗: {err}")

# =============================================================
# 功能二：移工雙月服務週期排程（支援Excel匯入、追蹤、動態變更）
# =============================================================
elif menu_choice == "🗓️ 移工雙月服務週期排程":
    st.title("🗓️ 移工雙月服務週期排程與追蹤")
    st.caption("依據入境日或承接日起算，自動推算 3 年（18 期）訪視排程。支援失聯、轉出動態變更與隨時恢復機制。")

    sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
        "📊 訪視進度追蹤與勾選", 
        "⚠️ 移工狀態動態變更 / 隨時恢復",
        "📤 批次匯入移工名單 (Excel/CSV)", 
        "➕ 單筆手動建立"
    ])

    # ---------------------------------------------------------
    # 2-1. 訪視進度追蹤與主管勾選
    # ---------------------------------------------------------
    with sub_tab1:
        st.subheader("訪視排程總覽")
        try:
            records = supabase.table("worker_service_schedules").select("*").order("target_date", desc=False).execute().data
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

            # 篩選列
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                status_filter = st.multiselect("訪視狀態", options=["待訪視", "已完成", "暫緩", "已終止(免訪視)"], default=["待訪視"])
            with col_f2:
                emp_filter = st.multiselect("在職狀態", options=["在職中", "失聯(逃跑)", "已轉出", "提前離境", "解約/終止"], default=["在職中"])
            with col_f3:
                keyword = st.text_input("搜尋移工姓名 / 雇主 / 工號：")
            with col_f4:
                time_range = st.selectbox("到期篩選", ["全部", "即日起 30 天內待訪視", "即日起 60 天內待訪視", "已逾期待訪視"])

            filtered_df = df.copy()
            if status_filter:
                filtered_df = filtered_df[filtered_df["status"].isin(status_filter)]
            if emp_filter:
                filtered_df = filtered_df[filtered_df["employment_status"].isin(emp_filter)]
            if keyword.strip():
                match_mask = filtered_df[["worker_name", "employer_name", "worker_id"]].fillna("").astype(str).apply(
                    lambda row: row.str.contains(keyword, case=False).any(), axis=1
                )
                filtered_df = filtered_df[match_mask]
                
            today = date.today()
            if time_range == "即日起 30 天內待訪視":
                filtered_df = filtered_df[(filtered_df["target_date"] >= today) & (filtered_df["target_date"] <= today + relativedelta(days=30)) & (filtered_df["status"] == "待訪視")]
            elif time_range == "即日起 60 天內待訪視":
                filtered_df = filtered_df[(filtered_df["target_date"] >= today) & (filtered_df["target_date"] <= today + relativedelta(days=60)) & (filtered_df["status"] == "待訪視")]
            elif time_range == "已逾期待訪視":
                filtered_df = filtered_df[(filtered_df["target_date"] < today) & (filtered_df["status"] == "待訪視")]

            st.write(f"篩選結果：共 **{len(filtered_df)}** 筆排程")
            
            show_cols = {
                "id": "編號",
                "worker_name": "移工姓名",
                "employment_status": "目前狀態",
                "employer_name": "雇主名稱",
                "period_number": "期別",
                "target_date": "預定訪視日",
                "status": "訪視狀態",
                "visit_date": "實際訪視日",
                "notes": "備註說明",
                "status_reason": "異動說明"
            }
            display_df = filtered_df[[c for c in show_cols.keys() if c in filtered_df.columns]].rename(columns=show_cols)
            st.dataframe(display_df, use_container_width=True)

            # 主管快速標記訪視結果
            st.markdown("---")
            st.markdown("#### ✍️ 標記單次訪視結果")
            with st.form("update_visit_form"):
                col_u1, col_u2, col_u3, col_u4 = st.columns([1, 1.5, 1.5, 3])
                with col_u1:
                    update_id = st.number_input("請輸入排程「編號」", min_value=1, step=1)
                with col_u2:
                    new_status = st.selectbox("變更訪視狀態", ["已完成", "待訪視", "暫緩", "已終止(免訪視)"])
                with col_u3:
                    actual_date = st.date_input("實際完成日期", value=date.today())
                with col_u4:
                    visit_notes = st.text_input("訪視重點備註 (選填)")

                save_update = st.form_submit_button("儲存訪視紀錄")
                if save_update:
                    try:
                        update_payload = {
                            "status": new_status,
                            "visit_date": actual_date.strftime("%Y-%m-%d") if new_status == "已完成" else None,
                            "notes": visit_notes.strip()
                        }
                        supabase.table("worker_service_schedules").update(update_payload).eq("id", update_id).execute()
                        st.success(f"✅ 編號 {update_id} 更新成功！")
                        st.rerun()
                    except Exception as err:
                        st.error(f"更新失敗: {err}")
        else:
            st.info("目前尚無排程資料，請至「批次匯入」或「單筆手動建立」新增移工！")

    # ---------------------------------------------------------
    # 2-2. 移工動態變更 / 隨時恢復 (防止同仁白跑，且隨時可復原)
    # ---------------------------------------------------------
    with sub_tab2:
        st.subheader("⚠️ 移工動態變更（失聯 / 轉出 / 離境 / 隨時恢復在職）")
        st.info("💡 彈性機制：若移工發生狀況，可一鍵將未來尚未訪視的期別改為「已終止(免訪視)」；若狀況解除（例如尋回投案、取消轉出），可隨時切回「在職中」恢復排程！過去已經完成的訪視紀錄絕對不會受影響。")

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

    # ---------------------------------------------------------
    # 2-3. 批次匯入名單（自動計算 3 年 18 期）
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # 2-4. 單筆手動建立
    # ---------------------------------------------------------
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
