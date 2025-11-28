import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog, ttk

import customtkinter as ctk

from config import Config
from styles import COLORS, FONT_FAMILY, FONTS


class OrderView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        # 주문 관리용 컬럼 (납품 예정일 중요)
        self.display_cols = ["관리번호", "업체명", "모델명", "수량", "합계금액", "수주일", "출고예정일", "Status"]
        
        self.create_widgets()
        self.style_treeview()
        self.refresh_data()

    def create_widgets(self):
        # 1. 상단 툴바
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(toolbar, text="🛒 주문 관리 (수주)", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")

        self.entry_search = ctk.CTkEntry(toolbar, width=250, placeholder_text="관리번호, 업체명...")
        self.entry_search.pack(side="left", padx=(20, 10))
        self.entry_search.bind("<Return>", lambda e: self.refresh_data())

        ctk.CTkButton(toolbar, text="검색", width=60, command=self.refresh_data, 
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="left")

        ctk.CTkButton(toolbar, text="새로고침", width=80, command=self.refresh_data,
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="right", padx=(0, 10))

        # 2. 리스트
        tree_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], corner_radius=10)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        scroll_y = ctk.CTkScrollbar(tree_frame, orientation="vertical")
        scroll_y.pack(side="right", fill="y", padx=(0, 5), pady=5)

        self.tree = ttk.Treeview(tree_frame, columns=self.display_cols, show="headings", yscrollcommand=scroll_y.set)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        scroll_y.configure(command=self.tree.yview)

        for col in self.display_cols:
            self.tree.heading(col, text=col)
            width = 100
            if col == "관리번호": width = 120
            if col == "업체명": width = 150
            if col == "모델명": width = 200
            self.tree.column(col, width=width, anchor="center")

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)
        
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="상세 정보 수정", command=self.on_edit)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📦 생산/준비 시작", command=self.on_start_production)
        self.context_menu.add_command(label="🚚 납품 대기 처리", command=self.on_ready_delivery)

    def style_treeview(self):
        style = ttk.Style()
        style.theme_use("default")
        bg = "#2b2b2b" if self.dm.current_theme == "Dark" else "#F5F5F5"
        fg = "white" if self.dm.current_theme == "Dark" else "black"
        style.configure("Treeview", background=bg, foreground=fg, fieldbackground=bg, rowheight=30, borderwidth=0, font=FONTS["main"])
        style.configure("Treeview.Heading", font=(FONT_FAMILY, 11, "bold"), background="#3a3a3a", foreground="white", relief="flat")
        style.map("Treeview", background=[('selected', COLORS["primary"][1])])

    def refresh_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        df = self.dm.df_data
        if df.empty: return

        keyword = self.entry_search.get().strip().lower()
        
        # '주문' 또는 '생산중' 상태인 항목 표시
        target_status = ["주문", "생산중"]
        target_df = df[df["Status"].isin(target_status)]
        
        if target_df.empty: return

        # 최신 수주일 순
        target_df = target_df.sort_values(by="수주일", ascending=False)

        for _, row in target_df.iterrows():
            if keyword:
                matched = False
                for col in Config.SEARCH_TARGET_COLS:
                    if keyword in str(row.get(col, "")).lower():
                        matched = True
                        break
                if not matched: continue

            try:
                amt = float(str(row.get("합계금액", 0)).replace(",",""))
                fmt_amt = f"{amt:,.0f}"
            except:
                fmt_amt = str(row.get("합계금액", "-"))

            values = [
                row.get("관리번호"),
                row.get("업체명"),
                row.get("모델명"),
                row.get("수량"),
                fmt_amt,
                row.get("수주일"),
                row.get("출고예정일"),
                row.get("Status")
            ]
            self.tree.insert("", "end", values=values)

    def on_double_click(self, event):
        self.on_edit()

    def on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def on_edit(self):
        selected = self.tree.selection()
        if not selected: return
        item = self.tree.item(selected[0])
        mgmt_no = item["values"][0]
        self.pm.open_quote_popup(mgmt_no) # 견적/주문 팝업 재사용

    def on_start_production(self):
        self._update_status("생산중", "생산/준비 단계로 변경되었습니다.")

    def on_ready_delivery(self):
        self._update_status("납품대기", "납품 대기 상태로 변경되었습니다.\n'납품 관리' 메뉴에서 확인 가능합니다.")

    def _update_status(self, new_status, success_msg):
        selected = self.tree.selection()
        if not selected: return
        
        item = self.tree.item(selected[0])
        mgmt_no = item["values"][0]
        model = item["values"][2]
        
        # 특정 행(관리번호+모델명)만 업데이트
        # 주의: 관리번호 내 모든 품목을 업데이트할지, 선택한 품목만 할지 결정 필요
        # 여기서는 관리번호에 해당하는 '모든' 품목을 일괄 변경 (주문 단위 처리)
        if messagebox.askyesno("상태 변경", f"관리번호 [{mgmt_no}]의 상태를 '{new_status}'(으)로 변경하시겠습니까?"):
            df = self.dm.df_data
            mask = df["관리번호"] == mgmt_no
            if mask.any():
                self.dm.df_data.loc[mask, "Status"] = new_status
                
                # 출고예정일 입력 (생산중으로 갈 때)
                if new_status == "생산중":
                    date_str = simpledialog.askstring("일정 입력", "출고예정일을 입력하세요 (YYYY-MM-DD):", parent=self)
                    if date_str:
                        self.dm.df_data.loc[mask, "출고예정일"] = date_str

                self.dm.save_to_excel()
                self.dm.add_log(f"상태변경({new_status})", f"번호 [{mgmt_no}]")
                messagebox.showinfo("완료", success_msg)
                self.refresh_data()