import os
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import pandas as pd

from popups.base_popup import BasePopup
from styles import COLORS, FONTS
from config import Config

class CompletePopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_no):
        self.full_paths = {}
        # 부모 생성자 호출 (내부적으로 _create_widgets -> _load_clients -> _load_data 순 실행)
        super().__init__(parent, data_manager, refresh_callback, popup_title="완료 주문 상세", mgmt_no=mgmt_no)
        
    def _create_widgets(self):
        # [Grid 레이아웃 설정]
        # 창 전체를 Grid로 나누어 각 영역의 크기 비율을 조정합니다.
        self.grid_columnconfigure(0, weight=1)
        
        # Row 0: 상단 정보 (고정)
        # Row 1: 요약 정보 (고정)
        # Row 2: 품목 리스트 (가변 - 여기가 늘어남)
        # Row 3: 하단 정보 (고정)
        # Row 4: 관련 문서 (고정 - 높이 제한)
        # Row 5: 닫기 버튼 (고정)
        
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1) # [핵심] 품목 리스트 영역만 늘어나도록 설정
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0) # 관련 문서는 고정 높이
        self.grid_rowconfigure(5, weight=0)

        # 1. 상단 정보 (Row 0)
        self.top_container = ctk.CTkFrame(self, fg_color="transparent")
        self.top_container.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
        self._fill_top_frame()

        # 2. 요약 정보 (Row 1)
        self.summary_container = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], corner_radius=10)
        self.summary_container.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        self._fill_summary_frame()

        # 3. 품목 리스트 (Row 2) - [핵심] sticky="nsew"로 상하좌우 꽉 채움
        self.items_container = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"])
        self.items_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=5)
        self._fill_items_frame()

        # 4. 하단 정보 (비고/요청사항) (Row 3)
        self.bottom_container = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_container.grid(row=3, column=0, sticky="ew", padx=20, pady=5)
        self._fill_bottom_frame()

        # 5. 관련 문서 (Row 4)
        self.files_container = ctk.CTkFrame(self, fg_color="transparent")
        self.files_container.grid(row=4, column=0, sticky="ew", padx=20, pady=5)
        self._fill_files_frame()

        # 6. 닫기 버튼 (Row 5)
        self.btn_container = ctk.CTkFrame(self, fg_color="transparent", height=50)
        self.btn_container.grid(row=5, column=0, sticky="ew", padx=20, pady=(10, 20))
        
        ctk.CTkButton(self.btn_container, text="닫기", command=self.destroy, width=100, height=40,
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="right")

        self.geometry("1200x950") # 창 크기를 넉넉하게 설정

    # --- [핵심 수정] 초기화 에러 방지 (필수) ---
    def _load_clients(self):
        pass

    # --- 각 섹션 채우기 메서드 ---

    def _fill_top_frame(self):
        self.lbl_id = ctk.CTkLabel(self.top_container, text="관리번호", font=FONTS["main_bold"])
        self.lbl_id.grid(row=0, column=0, padx=5, sticky="w")
        
        self.entry_id = ctk.CTkEntry(self.top_container, width=200, font=FONTS["main"], state="readonly")
        self.entry_id.grid(row=0, column=1, padx=5, sticky="w")

        self.lbl_status = ctk.CTkLabel(self.top_container, text="상태", font=FONTS["main_bold"])
        self.lbl_status.grid(row=0, column=2, padx=5, sticky="w")
        
        self.combo_status = ctk.CTkComboBox(self.top_container, values=[], width=200, font=FONTS["main"], state="disabled")
        self.combo_status.grid(row=0, column=3, padx=5, sticky="w")
        
        self.lbl_client = ctk.CTkLabel(self.top_container, text="고객사", font=FONTS["main_bold"])
        self.lbl_client.grid(row=1, column=0, padx=5, pady=10, sticky="w")
        
        self.entry_client = ctk.CTkEntry(self.top_container, width=200, font=FONTS["main"], state="readonly")
        self.entry_client.grid(row=1, column=1, columnspan=3, padx=5, pady=10, sticky="w")

        self.lbl_project = ctk.CTkLabel(self.top_container, text="프로젝트명", font=FONTS["main_bold"])
        self.lbl_project.grid(row=2, column=0, padx=5, sticky="w")
        
        self.entry_project = ctk.CTkEntry(self.top_container, width=400, font=FONTS["main"], state="readonly")
        self.entry_project.grid(row=2, column=1, columnspan=3, padx=5, sticky="ew")

    def _fill_summary_frame(self):
        ctk.CTkLabel(self.summary_container, text="📊 진행 요약", font=FONTS["header"], text_color=COLORS["primary"]).pack(anchor="w", padx=20, pady=(15, 10))
        
        grid = ctk.CTkFrame(self.summary_container, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=(0, 20))
        
        self.lbl_date_quote = self._create_info_card(grid, 0, 0, "견적일")
        self.lbl_date_order = self._create_info_card(grid, 0, 1, "수주일")
        
        self.lbl_date_delivery = self._create_info_card(grid, 1, 0, "출고일")
        self.lbl_date_paid = self._create_info_card(grid, 1, 1, "입금완료일")
        
        self.lbl_amt_total = self._create_info_card(grid, 2, 0, "총 합계금액")
        self.lbl_amt_paid = self._create_info_card(grid, 2, 1, "실 입금액")
            
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

    def _create_info_card(self, parent, row, col, title):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_dark"], corner_radius=6)
        frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(frame, text=title, font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left", padx=15, pady=10)
        lbl = ctk.CTkLabel(frame, text="-", font=FONTS["main_bold"])
        lbl.pack(side="right", padx=15, pady=10)
        return lbl

    def _fill_items_frame(self):
        # 헤더 생성
        headers = ["품명", "모델명", "Description", "수량", "단가", "공급가액", "세액", "합계금액"]
        widths = [150, 150, 200, 60, 100, 100, 80, 100]
        
        header_frame = ctk.CTkFrame(self.items_container, height=30, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x")
        
        for h, w in zip(headers, widths):
            lbl = ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["small"])
            lbl.pack(side="left", padx=2)

        # [핵심 수정] 스크롤 영역 높이 강제 설정 (300px) 및 Grid 확장
        # height=300은 최소 높이를 보장하고, sticky="nsew"와 Grid 설정으로 인해 늘어날 수 있습니다.
        self.scroll_items = ctk.CTkScrollableFrame(self.items_container, fg_color="transparent", height=300)
        self.scroll_items.pack(fill="both", expand=True)

    def _fill_bottom_frame(self):
        self.bottom_container.columnconfigure(1, weight=1)
        self.bottom_container.columnconfigure(3, weight=1)
        
        ctk.CTkLabel(self.bottom_container, text="비고:", font=FONTS["main"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_note = ctk.CTkEntry(self.bottom_container)
        self.entry_note.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ctk.CTkLabel(self.bottom_container, text="주문요청사항:", font=FONTS["main"]).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.entry_req = ctk.CTkEntry(self.bottom_container)
        self.entry_req.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

    def _fill_files_frame(self):
        ctk.CTkLabel(self.files_container, text="📁 관련 문서", font=FONTS["header"]).pack(anchor="w", pady=(5, 5))
        # [핵심 수정] 파일 목록 높이를 80px로 고정
        self.files_scroll = ctk.CTkScrollableFrame(self.files_container, height=80, fg_color=COLORS["bg_medium"])
        self.files_scroll.pack(fill="x")

    def _add_file_row(self, title, path):
        if path is None: path = ""
        path = str(path).strip()
        
        if not path or path == "-" or path.lower() == "nan" or path.lower() == "none":
            return False
        
        row = ctk.CTkFrame(self.files_scroll, fg_color="transparent", height=25)
        row.pack(fill="x", pady=1)
        
        ctk.CTkLabel(row, text=title, width=120, anchor="w", font=FONTS["main_bold"]).pack(side="left", padx=10)
        
        filename = os.path.basename(path)
        ctk.CTkLabel(row, text=filename, font=FONTS["main"], text_color=COLORS["text"]).pack(side="left", padx=10)
        
        ctk.CTkButton(row, text="열기", width=50, height=22,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=lambda p=path: self.open_file(p)).pack(side="right", padx=10)
        return True

    def open_file(self, path):
        if path and os.path.exists(path):
            try: os.startfile(path)
            except Exception as e: messagebox.showerror("에러", f"파일을 열 수 없습니다.\n{e}", parent=self)
        else:
            messagebox.showwarning("경고", f"파일 경로가 유효하지 않습니다.\n경로: {path}", parent=self)

    def _load_data(self):
        df = self.dm.df_data
        rows = df[df["관리번호"].astype(str) == str(self.mgmt_no)]
        if rows.empty: return

        first = rows.iloc[0]

        # [안전한 값 설정 함수]
        def safe_set(entry, value):
            try:
                entry.configure(state="normal")
                entry.delete(0, "end")
                entry.insert(0, str(value))
                entry.configure(state="readonly")
            except Exception as e:
                print(f"Error setting value for {entry}: {e}")

        # 기본 정보
        safe_set(self.entry_id, first["관리번호"])
        
        if hasattr(self, 'combo_status'):
            self.combo_status.configure(state="normal")
            self.combo_status.set(str(first.get("Status", "")))
            self.combo_status.configure(state="disabled")
        
        safe_set(self.entry_client, first.get("업체명", ""))
        safe_set(self.entry_project, first.get("프로젝트명", ""))
        safe_set(self.entry_note, first.get("비고", ""))
        safe_set(self.entry_req, first.get("주문요청사항", ""))

        # 요약 정보
        if hasattr(self, 'lbl_date_quote'):
            self.lbl_date_quote.configure(text=str(first.get("견적일", "-")))
            self.lbl_date_order.configure(text=str(first.get("수주일", "-")))
            self.lbl_date_delivery.configure(text=str(first.get("출고일", "-")))
            self.lbl_date_paid.configure(text=str(first.get("입금완료일", "-")))
            
            try: total = pd.to_numeric(rows["합계금액"], errors='coerce').sum()
            except: total = 0
            try: paid = pd.to_numeric(rows["기수금액"], errors='coerce').sum()
            except: paid = 0
            
            self.lbl_amt_total.configure(text=f"{total:,.0f} (미수: {total-paid:,.0f})")
            self.lbl_amt_paid.configure(text=f"{paid:,.0f}")

        # 품목 리스트 (BasePopup의 item_rows 초기화 및 추가)
        self.item_rows = [] 
        for _, row in rows.iterrows():
            self._add_item_row(row)

        # 파일 로드
        has_files = False
        if self._add_file_row("주문서(발주서)", first.get("발주서경로")): has_files = True
        
        client_name = str(first.get("업체명", ""))
        client_row = self.dm.df_clients[self.dm.df_clients["업체명"] == client_name]
        if not client_row.empty:
            if self._add_file_row("사업자등록증", client_row.iloc[0].get("사업자등록증경로")): has_files = True
                
        if not has_files:
            ctk.CTkLabel(self.files_scroll, text="첨부된 파일이 없습니다.", 
                         font=FONTS["main"], text_color=COLORS["text_dim"]).pack(pady=10)

    def _add_item_row(self, item_data=None):
        row_frame = ctk.CTkFrame(self.scroll_items, fg_color="transparent", height=30)
        row_frame.pack(fill="x", pady=2)

        def create_entry(val, width, justify="left", is_num=False):
            if is_num:
                try: val = f"{float(val):,.0f}"
                except: val = "0"
            
            # [중요] text_color를 명시적으로 지정하여 가시성 확보
            entry = ctk.CTkEntry(row_frame, width=width, justify=justify, text_color=COLORS["text"])
            entry.insert(0, str(val))
            # border_width=0, fg_color="transparent"로 텍스트만 보이게 설정
            entry.configure(state="readonly", border_width=0, fg_color="transparent")
            entry.pack(side="left", padx=2)
            return entry

        create_entry(item_data.get("품목명", ""), 150)
        create_entry(item_data.get("모델명", ""), 150)
        create_entry(item_data.get("Description", ""), 200)
        create_entry(item_data.get("수량", 0), 60, "center", True)
        create_entry(item_data.get("단가", 0), 100, "right", True)
        create_entry(item_data.get("공급가액", 0), 100, "right", True)
        create_entry(item_data.get("세액", 0), 80, "right", True)
        create_entry(item_data.get("합계금액", 0), 100, "right", True)

        return {}

    # BasePopup 오버라이드 (사용 안 함 - 빈 함수로 두어 충돌 방지)
    def _create_top_frame(self): pass
    def _create_items_frame(self): pass
    def _create_bottom_frame(self): pass
    def _create_files_frame(self): pass
    def _create_action_buttons(self): pass
    def save(self): pass
    def delete(self): pass
    def _generate_new_id(self): pass