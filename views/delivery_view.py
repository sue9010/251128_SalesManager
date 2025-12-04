import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk
import pandas as pd

from config import Config
from styles import COLORS, FONT_FAMILY, FONTS


class DeliveryView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        self.display_cols = ["관리번호", "업체명", "모델명", "수량", "단가", "출고예정일", "Status"]
        
        self.create_widgets()
        self.style_treeview()
        self.refresh_data()

    def create_widgets(self):
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(toolbar, text="🚚 납품 관리 (출고)", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")

        self.entry_search = ctk.CTkEntry(toolbar, width=250, placeholder_text="관리번호, 업체명, 모델명...")
        self.entry_search.pack(side="left", padx=(20, 10))
        self.entry_search.bind("<Return>", lambda e: self.refresh_data())

        ctk.CTkButton(toolbar, text="검색", width=60, command=self.refresh_data, 
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="left")

        # 다중 선택 후 일괄 처리 버튼
        ctk.CTkButton(toolbar, text="📦 선택 항목 일괄 출고", width=150, command=self.on_process_delivery,
                      fg_color=COLORS["success"], hover_color="#26A65B").pack(side="right", padx=(0, 10))
        
        ctk.CTkButton(toolbar, text="새로고침", width=80, command=self.refresh_data,
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="right")

        tree_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], corner_radius=10)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        scroll_y = ctk.CTkScrollbar(tree_frame, orientation="vertical")
        scroll_y.pack(side="right", fill="y", padx=(0, 5), pady=5)

        self.tree = ttk.Treeview(tree_frame, columns=self.display_cols, show="headings", yscrollcommand=scroll_y.set, selectmode="extended")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        scroll_y.configure(command=self.tree.yview)

        for col in self.display_cols:
            self.tree.heading(col, text=col)
            width = 100
            if col == "관리번호": width = 120
            if col == "업체명": width = 150
            if col == "모델명": width = 200
            self.tree.column(col, width=width, anchor="center")

        self.tree.bind("<Double-1>", lambda e: self.on_process_delivery())

    def style_treeview(self):
        style = ttk.Style()
        style.theme_use("default")
        
        bg_color = "#2b2b2b" if self.dm.current_theme == "Dark" else "#F5F5F5"
        fg_color = "white" if self.dm.current_theme == "Dark" else "black"
        header_bg = "#3a3a3a" if self.dm.current_theme == "Dark" else "#E0E0E0"
        header_fg = "white" if self.dm.current_theme == "Dark" else "black"
        
        style.configure("Treeview", 
                        background=bg_color, 
                        foreground=fg_color, 
                        fieldbackground=bg_color, 
                        rowheight=30, 
                        borderwidth=0, 
                        font=FONTS["main"])
        
        style.configure("Treeview.Heading", 
                        font=(FONT_FAMILY, 11, "bold"), 
                        background=header_bg, 
                        foreground=header_fg, 
                        relief="flat")
        
        style.map("Treeview", background=[('selected', COLORS["success"][1])])

    def refresh_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        df = self.dm.df_data
        if df.empty: return

        keyword = self.entry_search.get().strip().lower()
        target_status = ["생산중", "납품대기", "납품대기/입금완료"]
        target_df = df[df["Status"].astype(str).isin(target_status)]
        
        if target_df.empty: return
        target_df = target_df.sort_values(by="출고예정일")

        for idx, row in target_df.iterrows():
            if keyword:
                matched = False
                for col in Config.SEARCH_TARGET_COLS:
                    if keyword in str(row.get(col, "")).lower():
                        matched = True
                        break
                if not matched: continue

            try:
                price = float(row.get("단가", 0))
                fmt_price = f"{price:,.0f}"
            except:
                fmt_price = str(row.get("단가", 0))

            values = [
                row.get("관리번호"),
                row.get("업체명"),
                row.get("모델명"),
                row.get("수량"),
                fmt_price,
                row.get("출고예정일"),
                row.get("Status")
            ]
            self.tree.insert("", "end", iid=idx, values=values)

    def on_process_delivery(self):
        """[수정] 납품 처리 팝업 호출 (동일 업체명 일괄 처리 가능)"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("경고", "출고 처리할 항목을 하나 이상 선택해주세요.")
            return
        
        # 첫 번째 선택 항목 정보 가져오기
        first_item_idx = int(selected_items[0])
        first_client = self.dm.df_data.loc[first_item_idx, "업체명"]
        
        target_mgmt_nos = set() # 중복 제거를 위해 set 사용

        # 모든 선택된 항목이 동일한 업체명을 가졌는지 확인
        for item in selected_items:
            item_idx = int(item)
            client = self.dm.df_data.loc[item_idx, "업체명"]
            mgmt_no = self.dm.df_data.loc[item_idx, "관리번호"]
            
            if client != first_client:
                messagebox.showwarning("주의", "동일한 업체의 항목들만 일괄 출고 처리가 가능합니다.")
                return
            
            target_mgmt_nos.add(mgmt_no)

        # 팝업 호출 (관리번호 리스트 전달)
        self.pm.open_delivery_popup(list(target_mgmt_nos))