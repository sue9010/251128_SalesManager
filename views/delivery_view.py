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

        # 리스트에 표시할 컬럼 (납품 관리에 필요한 항목 위주)
        self.display_cols = ["관리번호", "업체명", "모델명", "수량", "단가", "출고예정일", "Status"]
        
        self.create_widgets()
        self.style_treeview()
        self.refresh_data()

    def create_widgets(self):
        # 1. 상단 툴바 영역
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(20, 10))

        # 타이틀
        ctk.CTkLabel(toolbar, text="🚚 납품 관리 (출고)", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")

        # 검색 입력창
        self.entry_search = ctk.CTkEntry(toolbar, width=250, placeholder_text="관리번호, 업체명, 모델명...")
        self.entry_search.pack(side="left", padx=(20, 10))
        self.entry_search.bind("<Return>", lambda e: self.refresh_data())

        # 검색 버튼
        ctk.CTkButton(toolbar, text="검색", width=60, command=self.refresh_data, 
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="left")

        # 기능 버튼 (우측 정렬)
        # 납품 처리 버튼 (핵심 기능)
        ctk.CTkButton(toolbar, text="📦 납품 처리 (출고)", width=120, command=self.on_process_delivery,
                      fg_color=COLORS["success"], hover_color="#26A65B").pack(side="right", padx=(0, 10))
        
        # 새로고침 버튼
        ctk.CTkButton(toolbar, text="새로고침", width=80, command=self.refresh_data,
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="right")

        # 2. 리스트 영역 (Treeview)
        tree_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], corner_radius=10)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # 스크롤바
        scroll_y = ctk.CTkScrollbar(tree_frame, orientation="vertical")
        scroll_y.pack(side="right", fill="y", padx=(0, 5), pady=5)

        # 트리뷰 설정
        self.tree = ttk.Treeview(tree_frame, columns=self.display_cols, show="headings", yscrollcommand=scroll_y.set)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        scroll_y.configure(command=self.tree.yview)

        # 컬럼 헤더 설정
        for col in self.display_cols:
            self.tree.heading(col, text=col)
            # 컬럼별 너비 조정
            width = 100
            if col == "관리번호": width = 120
            if col == "업체명": width = 150
            if col == "모델명": width = 200
            self.tree.column(col, width=width, anchor="center")

        # 이벤트 바인딩 (더블클릭 시 납품 처리)
        self.tree.bind("<Double-1>", lambda e: self.on_process_delivery())

    def style_treeview(self):
        """트리뷰 스타일 설정 (다크/라이트 모드 대응)"""
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
        
        style.map("Treeview", background=[('selected', COLORS["success"][1])]) # 선택 시 녹색 계열

    def refresh_data(self):
        """데이터 로드 및 리스트 갱신"""
        # 기존 항목 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)

        df = self.dm.df_data
        if df.empty: return

        keyword = self.entry_search.get().strip().lower()
        
        # 납품 가능한 상태 필터링: 주문, 생산중, 납품대기
        # (이미 완료된 건이나 취소된 건은 제외)
        target_status = ["주문", "생산중", "납품대기"]
        
        # 상태 필터링 적용
        # df["Status"] 컬럼이 문자열이 아닐 경우를 대비해 astype(str) 사용
        target_df = df[df["Status"].astype(str).isin(target_status)]
        
        if target_df.empty: return
        
        # 출고예정일 순으로 정렬
        target_df = target_df.sort_values(by="출고예정일")

        for idx, row in target_df.iterrows():
            # 검색 키워드 필터링
            if keyword:
                matched = False
                for col in Config.SEARCH_TARGET_COLS:
                    if keyword in str(row.get(col, "")).lower():
                        matched = True
                        break
                if not matched: continue

            # 금액 천단위 콤마 포맷팅
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
            
            # Treeview의 iid를 DataFrame의 index(idx)로 설정하여 추후 데이터 참조 용이하게 함
            self.tree.insert("", "end", iid=idx, values=values)

    def on_process_delivery(self):
        """납품 처리 팝업 호출"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("경고", "납품할 항목을 선택해주세요.")
            return
        
        # 선택된 항목의 iid (DataFrame Index) 가져오기
        idx = int(selected[0])
        
        # 팝업 매니저를 통해 납품 팝업 열기
        self.pm.open_delivery_popup(idx)