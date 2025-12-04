import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk
import pandas as pd

from config import Config
from styles import COLORS, FONT_FAMILY, FONTS


class PaymentView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        # 입금 관리에 필요한 컬럼 (금액 정보 위주)
        self.display_cols = ["관리번호", "업체명", "합계금액", "기수금액", "미수금액", "출고일", "Status"]
        
        self.create_widgets()
        self.style_treeview()
        self.refresh_data()

    def create_widgets(self):
        # 1. 상단 툴바 영역
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(20, 10))

        # 타이틀
        ctk.CTkLabel(toolbar, text="💰 입금 관리 (수금)", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")

        # 기능 버튼 (우측 정렬)
        # 새로고침 버튼
        ctk.CTkButton(toolbar, text="새로고침", width=80, command=self.refresh_data,
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="right", padx=(0, 10))

        # 입금 처리 버튼
        ctk.CTkButton(toolbar, text="💵 입금 등록", width=120, command=self.on_process_payment,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]).pack(side="right", padx=(0, 10))

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
            if "금액" in col: width = 120 # 금액 컬럼은 조금 넓게
            self.tree.column(col, width=width, anchor="center")

        # 태그 설정 (미수금이 있는 행 강조를 위해)
        self.tree.tag_configure("unpaid", foreground="#FF5252") # 붉은색 텍스트

        # 이벤트 바인딩 (더블클릭 시 입금 처리)
        self.tree.bind("<Double-1>", lambda e: self.on_process_payment())

    def style_treeview(self):
        """트리뷰 스타일 설정"""
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
        
        style.map("Treeview", background=[('selected', COLORS["primary"][1])])

    def refresh_data(self):
        """데이터 로드 및 리스트 갱신"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        df = self.dm.df_data
        if df.empty: return

        # 입금 관리 대상 필터링
        # 1. 미수금액이 0보다 큰 건 (아직 돈을 다 못 받은 건)
        # 2. 또는 상태가 '입금대기'가 포함된 건
        try:
            # 미수금액을 숫자로 변환 (에러 시 0)
            df["_unpaid"] = pd.to_numeric(df["미수금액"], errors='coerce').fillna(0)
            
            # 필터 조건: 미수금이 남았거나, 상태 명칭에 입금대기가 있거나
            mask = (df["_unpaid"] > 0) | (df["Status"].astype(str).str.contains("입금대기"))
            target_df = df[mask].copy()
        except Exception:
            # 변환 에러 시 전체 표시 (안전장치)
            target_df = df

        if target_df.empty: return
        
        # 출고일(최신순) 정렬
        target_df = target_df.sort_values(by="출고일", ascending=False)

        for idx, row in target_df.iterrows():
            # 금액 포맷팅
            total = float(row.get("합계금액", 0) or 0)
            paid = float(row.get("기수금액", 0) or 0)
            unpaid = float(row.get("미수금액", 0) or 0)
            
            # 미수금이 있으면 태그 적용
            row_tags = ("unpaid",) if unpaid > 0 else ()

            values = [
                row.get("관리번호"),
                row.get("업체명"),
                f"{total:,.0f}",
                f"{paid:,.0f}",
                f"{unpaid:,.0f}",
                row.get("출고일"),
                row.get("Status")
            ]
            
            # iid를 DataFrame 인덱스로 설정
            self.tree.insert("", "end", iid=idx, values=values, tags=row_tags)

    def on_process_payment(self):
        """입금 처리 팝업 호출"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("경고", "입금 처리할 항목을 선택해주세요.")
            return
        
        # 선택된 항목의 iid(DataFrame 인덱스) 가져오기
        idx = int(selected[0])
        
        # 인덱스를 사용하여 관리번호 조회
        try:
            mgmt_no = self.dm.df_data.loc[idx, "관리번호"]
        except (KeyError, IndexError):
            messagebox.showerror("오류", "선택된 항목의 정보를 찾을 수 없습니다.")
            return

        # 팝업 매니저를 통해 입금 팝업 열기 (관리번호 전달)
        self.pm.open_payment_popup(mgmt_no)