# ==========================================
# 5. 功能二：移工雙月服務週期排程 (精準唯一分組 + 勾選編輯)
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
            # 撈取全部資料
            res = supabase.table("worker_service_schedules").select("*").execute()
            schedule_data = res.data or []
        except Exception as e:
            st.error(f"讀取資料庫失敗: {e}")

    df_raw = pd.DataFrame(schedule_data) if schedule_data else pd.DataFrame()

    if not df_raw.empty:
        # 資料清洗與型態修正
        df_raw["worker_name"] = df_raw["worker_name"].fillna("未命名移工").astype(str).str.strip()
        df_raw["employer_name"] = df_raw["employer_name"].fillna("未指定單位").astype(str).str.strip()
        df_raw["start_date"] = df_raw["start_date"].fillna("").astype(str).str[:10]
        df_raw["target_date"] = df_raw["target_date"].fillna("").astype(str).str[:10]
        df_raw["status"] = df_raw["status"].fillna("待訪視").astype(str).str.strip()
        
        if "period_number" in df_raw.columns:
            df_raw["period_number"] = pd.to_numeric(df_raw["period_number"], errors="coerce").fillna(0).astype(int)
        
        # 關鍵修正：加入每位移工的唯一獨立識別碼 (姓名 + 雇主 + 起始日期)
        # 這樣就算名字相同或空白，不同起始日的移工也絕對不會混在一起！
        df_raw["worker_group_key"] = df_raw["worker_name"] + "___" + df_raw["employer_name"] + "___" + df_raw["start_date"]

    # 頂部 KPI 統計計算
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

    # 計算真正獨立的移工組數
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

            # 依「唯一獨立移工」逐一渲染展開條
            for idx, g in enumerate(filtered_groups):
                g_key = g["worker_group_key"]
                w_name = g["worker_name"]
                e_name = g["employer_name"]
                s_date = g["start_date"]
                
                # 嚴格過濾此位移工的所有期數並依期數從小到大排序
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
                    # 重新組裝乾淨的編輯 DataFrame
                    subset_df = pd.DataFrame()
                    subset_df["完成?"] = (w_df["status"] == "已完成")
                    subset_df["狀態"] = w_df["status"]
                    subset_df["期數"] = w_df["period_number"]
                    subset_df["目標服務日期"] = w_df["target_date"]
                    subset_df["編號"] = w_df["id"]

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
                            "期數": st.column_config.NumberColumn("期數", disabled=True),
                            "目標服務日期": st.column_config.TextColumn("目標服務日期", disabled=True),
                            "編號": st.column_config.NumberColumn("編號", disabled=True),
                        },
                        key=f"editor_worker_{idx}"
                    )
                    
                    # 儲存按鈕
                    if st.button(f"💾 儲存【{w_name}】的排程變更", key=f"btn_save_{idx}"):
                        saved_count = 0
                        for _, row in edited_subset.iterrows():
                            rec_id = int(row["編號"])
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
