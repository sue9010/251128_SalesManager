import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

from config import Config
from styles import COLORS, FONT_FAMILY, FONTS


class QuoteView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        self.display_cols = ["관리번호", "업체명", "모델명", "수량", "합계금액", "견적일", "Status"]
        
        self.create_widgets()
        self.style_treeview()
        self.refresh_data()

    def create_widgets(self):
        # 1. 상단 툴바
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(toolbar, text="📄 견적 관리", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")

        self.entry_search = ctk.CTkEntry(toolbar, width=250, placeholder_text="관리번호, 업체명, 모델명...")
        self.entry_search.pack(side="left", padx=(20, 10))
        self.entry_search.bind("<Return>", lambda e: self.refresh_data())

        ctk.CTkButton(toolbar, text="검색", width=60, command=self.refresh_data, 
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="left")

        # [수정] 팝업 연결 완료
        ctk.CTkButton(toolbar, text="+ 신규 견적", width=100, command=self.open_add_popup,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]).pack(side="right")
        
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
        self.context_menu.add_command(label="상세 보기 / 수정", command=self.on_context_edit)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🛒 주문 확정 처리", command=self.on_context_order)

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
        
        # 기본적으로 '견적' 상태인 것만 표시 (검색 시 전체)
        if not keyword:
            target_df = df[df["Status"] == "견적"]
        else:
            target_df = df

        # 관리번호 기준으로 중복 제거 (대표 1개 행만 표시)
        # 품목이 여러 개여도 리스트에는 1줄만 나와야 깔끔함
        if not target_df.empty:
            # 관리번호별로 그룹화하여 첫 번째 행만 가져오되, 수량과 금액은 합산
            grouped = target_df.groupby("관리번호", as_index=False).agg({
                "업체명": "first",
                "모델명": "first", # "외 N건" 처리 로직 추가 가능
                "수량": "sum",
                "합계금액": "sum",
                "견적일": "first",
                "Status": "first"
            })
            # 날짜순 정렬
            grouped = grouped.sort_values(by="견적일", ascending=False)
            
            for _, row in grouped.iterrows():
                if keyword:
                    # 검색 필터 로직 (생략 가능 또는 상세 구현)
                    pass

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
                    row.get("견적일"),
                    row.get("Status")
                ]
                self.tree.insert("", "end", values=values)

    def open_add_popup(self):
        # [수정] 실제 팝업 호출
        self.pm.open_quote_popup(None)

    def on_double_click(self, event):
        self.on_context_edit()

    def on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def on_context_edit(self):
        selected = self.tree.selection()
        if not selected: return
        item = self.tree.item(selected[0])
        mgmt_no = item["values"][0]
        # [수정] 실제 팝업 호출
        self.pm.open_quote_popup(mgmt_no)

    def on_context_order(self):
        selected = self.tree.selection()
        if not selected: return
        
        item = self.tree.item(selected[0])
        mgmt_no = item["values"][0]
        
        if messagebox.askyesno("주문 확정", f"견적 번호 [{mgmt_no}]를 '주문' 상태로 변경하시겠습니까?\n이 작업 후에는 '주문 관리' 메뉴에서 확인 가능합니다."):
            success = self.update_status_to_order(mgmt_no)
            if success:
                messagebox.showinfo("완료", "주문 확정 처리되었습니다.")
                self.refresh_data()
            else:
                messagebox.showerror("실패", "상태 변경에 실패했습니다.")

    def update_status_to_order(self, mgmt_no):
        # DataManager를 통해 상태 업데이트
        df = self.dm.df_data
        mask = df["관리번호"] == mgmt_no
        if mask.any():
            from datetime import datetime

            # 해당 번호를 가진 모든 행(품목)의 상태를 업데이트
            self.dm.df_data.loc[mask, "Status"] = "주문"
            self.dm.df_data.loc[mask, "수주일"] = datetime.now().strftime("%Y-%m-%d")
            return self.dm.save_to_excel()
        return False
