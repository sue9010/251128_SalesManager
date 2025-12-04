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
        super().__init__(parent, data_manager, refresh_callback, popup_title="완료 주문 상세", mgmt_no=mgmt_no)
        
    def _create_widgets(self):
        # [레이아웃 전략]
        # 전체를 아우르는 메인 프레임 안에 섹션별로 카드를 배치합니다.
        # 윈도우 배경색 설정
        self.configure(fg_color=COLORS["bg_dark"])
        
        # 메인 컨테이너 (패딩을 주어 윈도우 테두리와 간격 확보)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 1. 헤더 섹션 (프로젝트명, 관리번호, 상태, 고객사)
        self._create_header(self.main_container)
        
        # 2. 요약 대시보드 (카드 형태)
        self._create_summary_cards(self.main_container)
        
        # 3. 품목 리스트 (데이터 그리드)
        self._create_items_table(self.main_container)
        
        # 4. 하단 섹션 (비고, 요청사항, 파일)
        self._create_footer(self.main_container)
        
        # 5. 닫기 버튼
        self._create_action_buttons_custom(self.main_container)

        self.geometry("1200x850")

    def _create_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        # 상단: 관리번호 & 상태 배지
        top_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        top_row.pack(fill="x", anchor="w")
        
        self.lbl_id = ctk.CTkLabel(top_row, text="MGMT-000000", font=FONTS["main"], text_color=COLORS["text_dim"])
        self.lbl_id.pack(side="left")
        
        self.status_badge = ctk.CTkLabel(top_row, text="Status", font=FONTS["small"], 
                                       fg_color=COLORS["primary"], text_color="white", corner_radius=10, width=80)
        self.status_badge.pack(side="left", padx=10)
        
        # 중단: 프로젝트명
        self.lbl_project = ctk.CTkLabel(header_frame, text="Project Name", font=FONTS["title"], anchor="w")
        self.lbl_project.pack(fill="x", pady=(5, 0))
        
        # 하단: 고객사
        self.lbl_client = ctk.CTkLabel(header_frame, text="Client Name", font=FONTS["header"], text_color=COLORS["text_dim"], anchor="w")
        self.lbl_client.pack(fill="x")

    def _create_summary_cards(self, parent):
        card_frame = ctk.CTkFrame(parent, fg_color="transparent")
        card_frame.pack(fill="x", pady=(0, 20))
        
        # 그리드 설정 (4열)
        card_frame.columnconfigure(0, weight=1)
        card_frame.columnconfigure(1, weight=1)
        card_frame.columnconfigure(2, weight=1)
        card_frame.columnconfigure(3, weight=1)
        
        # 카드 생성 헬퍼
        def create_card(col, title, value_id, color=COLORS["bg_medium"], title_color=COLORS["text_dim"], value_color=COLORS["text"]):
            card = ctk.CTkFrame(card_frame, fg_color=color, corner_radius=10)
            card.grid(row=0, column=col, sticky="ew", padx=5)
            
            ctk.CTkLabel(card, text=title, font=FONTS["small"], text_color=title_color).pack(anchor="w", padx=15, pady=(10, 0))
            lbl_val = ctk.CTkLabel(card, text="-", font=FONTS["header"], text_color=value_color)
            lbl_val.pack(anchor="w", padx=15, pady=(0, 10))
            setattr(self, value_id, lbl_val)
            
        # 1. 총 합계금액
        create_card(0, "총 합계금액", "lbl_amt_total", color=COLORS["bg_light"], value_color=COLORS["primary"])
        # 2. 실 입금액
        create_card(1, "실 입금액", "lbl_amt_paid", color=COLORS["bg_light"], value_color=COLORS["success"])
        # 3. 주요 날짜 (견적/수주)
        create_card(2, "견적일 / 수주일", "lbl_date_qs")
        # 4. 주요 날짜 (출고/입금)
        create_card(3, "출고일 / 입금완료일", "lbl_date_dp")

    def _create_items_table(self, parent):
        # 컨테이너
        table_container = ctk.CTkFrame(parent, fg_color=COLORS["bg_medium"], corner_radius=10)
        table_container.pack(fill="both", expand=True, pady=(0, 20))
        
        # 타이틀
        ctk.CTkLabel(table_container, text="품목 리스트", font=FONTS["header"]).pack(anchor="w", padx=20, pady=15)
        
        # 헤더
        headers = ["품명", "모델명", "Description", "수량", "단가", "공급가액", "세액", "합계금액"]
        widths = [150, 150, 200, 60, 100, 100, 80, 100]
        
        header_frame = ctk.CTkFrame(table_container, height=35, fg_color=COLORS["bg_light"])
        header_frame.pack(fill="x", padx=20)
        
        for h, w in zip(headers, widths):
            lbl = ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["main_bold"], text_color=COLORS["text"])
            lbl.pack(side="left", padx=2)
            
        # 리스트 (스크롤)
        self.scroll_items = ctk.CTkScrollableFrame(table_container, fg_color="transparent", height=250)
        self.scroll_items.pack(fill="both", expand=True, padx=10, pady=10)

    def _create_footer(self, parent):
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(0, 10))
        
        footer_frame.columnconfigure(0, weight=3) # 비고/요청사항
        footer_frame.columnconfigure(1, weight=2) # 파일
        
        # 왼쪽: 텍스트 정보
        left_col = ctk.CTkFrame(footer_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(left_col, text="비고", font=FONTS["main_bold"]).pack(anchor="w", padx=15, pady=(15, 5))
        self.entry_note = ctk.CTkEntry(left_col, fg_color=COLORS["bg_dark"], border_width=0, height=35)
        self.entry_note.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(left_col, text="주문요청사항", font=FONTS["main_bold"]).pack(anchor="w", padx=15, pady=(5, 5))
        self.entry_req = ctk.CTkEntry(left_col, fg_color=COLORS["bg_dark"], border_width=0, height=35)
        self.entry_req.pack(fill="x", padx=15, pady=(0, 15))
        
        # 오른쪽: 파일 리스트
        right_col = ctk.CTkFrame(footer_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        right_col.grid(row=0, column=1, sticky="nsew")
        
        ctk.CTkLabel(right_col, text="관련 문서", font=FONTS["main_bold"]).pack(anchor="w", padx=15, pady=15)
        self.files_scroll = ctk.CTkScrollableFrame(right_col, fg_color="transparent", height=100)
        self.files_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 10))

    def _create_action_buttons_custom(self, parent):
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(btn_frame, text="닫기", command=self.destroy, width=120, height=40,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], 
                      text_color=COLORS["text"]).pack(side="right")

    def _load_data(self):
        df = self.dm.df_data
        rows = df[df["관리번호"].astype(str) == str(self.mgmt_no)]
        if rows.empty: return

        first = rows.iloc[0]

        # 헤더 정보
        self.lbl_id.configure(text=f"No. {first['관리번호']}")
        self.lbl_project.configure(text=first.get("프로젝트명", ""))
        self.lbl_client.configure(text=first.get("업체명", ""))
        self.status_badge.configure(text=first.get("Status", "Unknown"))
        
        # 상태별 배지 색상 (예시)
        status = str(first.get("Status", ""))
        if "완료" in status: self.status_badge.configure(fg_color=COLORS["success"])
        elif "취소" in status: self.status_badge.configure(fg_color=COLORS["danger"])
        else: self.status_badge.configure(fg_color=COLORS["primary"])

        # 요약 정보
        try: total = pd.to_numeric(rows["합계금액"], errors='coerce').sum()
        except: total = 0
        try: paid = pd.to_numeric(rows["기수금액"], errors='coerce').sum()
        except: paid = 0
        
        self.lbl_amt_total.configure(text=f"₩ {total:,.0f}")
        self.lbl_amt_paid.configure(text=f"₩ {paid:,.0f}")
        
        q_date = str(first.get("견적일", "-"))
        s_date = str(first.get("수주일", "-"))
        d_date = str(first.get("출고일", "-"))
        p_date = str(first.get("입금완료일", "-"))
        
        self.lbl_date_qs.configure(text=f"{q_date} / {s_date}")
        self.lbl_date_dp.configure(text=f"{d_date} / {p_date}")

        # 텍스트 필드
        self.entry_note.configure(state="normal")
        self.entry_note.delete(0, "end")
        self.entry_note.insert(0, str(first.get("비고", "")))
        self.entry_note.configure(state="readonly")
        
        self.entry_req.configure(state="normal")
        self.entry_req.delete(0, "end")
        self.entry_req.insert(0, str(first.get("주문요청사항", "")))
        self.entry_req.configure(state="readonly")

        # 품목 리스트
        for widget in self.scroll_items.winfo_children(): widget.destroy()
        for _, row in rows.iterrows():
            self._add_item_row(row)

        # 파일 리스트
        for widget in self.files_scroll.winfo_children(): widget.destroy()
        
        has_files = False
        if self._add_file_row("주문서(발주서)", first.get("발주서경로")): has_files = True
        
        client_name = str(first.get("업체명", ""))
        client_row = self.dm.df_clients[self.dm.df_clients["업체명"] == client_name]
        if not client_row.empty:
            if self._add_file_row("사업자등록증", client_row.iloc[0].get("사업자등록증경로")): has_files = True
                
        if not has_files:
            ctk.CTkLabel(self.files_scroll, text="첨부 파일 없음", font=FONTS["small"], text_color=COLORS["text_dim"]).pack(pady=20)

    def _add_item_row(self, item_data):
        row_frame = ctk.CTkFrame(self.scroll_items, fg_color="transparent", height=35)
        row_frame.pack(fill="x", pady=2)
        
        # 마우스 오버 효과를 위한 프레임 (선택 사항)
        
        def create_cell(val, width, justify="left", is_num=False, is_bold=False):
            if is_num:
                try: val = f"{float(val):,.0f}"
                except: val = "0"
            
            font = FONTS["main_bold"] if is_bold else FONTS["main"]
            lbl = ctk.CTkLabel(row_frame, text=str(val), width=width, font=font, anchor="e" if justify=="right" else "w" if justify=="left" else "center")
            lbl.pack(side="left", padx=2)
            
        create_cell(item_data.get("품목명", ""), 150, is_bold=True)
        create_cell(item_data.get("모델명", ""), 150)
        create_cell(item_data.get("Description", ""), 200)
        create_cell(item_data.get("수량", 0), 60, "center", True)
        create_cell(item_data.get("단가", 0), 100, "right", True)
        create_cell(item_data.get("공급가액", 0), 100, "right", True)
        create_cell(item_data.get("세액", 0), 80, "right", True)
        create_cell(item_data.get("합계금액", 0), 100, "right", True)

    def _add_file_row(self, title, path):
        if path is None: path = ""
        path = str(path).strip()
        if not path or path == "-" or path.lower() == "nan" or path.lower() == "none":
            return False
            
        row = ctk.CTkFrame(self.files_scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        ctk.CTkLabel(row, text="📄", font=FONTS["main"]).pack(side="left", padx=(10, 5))
        ctk.CTkLabel(row, text=title, font=FONTS["main_bold"], width=100, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=os.path.basename(path), font=FONTS["small"], text_color=COLORS["text_dim"]).pack(side="left", padx=10)
        
        ctk.CTkButton(row, text="열기", width=50, height=24,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=lambda p=path: self.open_file(p)).pack(side="right", padx=10)
        return True

    def open_file(self, path):
        if path and os.path.exists(path):
            try: os.startfile(path)
            except Exception as e: messagebox.showerror("에러", f"파일을 열 수 없습니다.\n{e}", parent=self)
        else:
            messagebox.showwarning("경고", f"파일 경로가 유효하지 않습니다.\n경로: {path}", parent=self)

    # BasePopup 추상 메서드 구현 (사용하지 않음)
    def _create_top_frame(self): pass
    def _create_items_frame(self): pass
    def _create_bottom_frame(self): pass
    def _create_files_frame(self): pass
    def _create_action_buttons(self): pass
    def save(self): pass
    def delete(self): pass
    def _generate_new_id(self): pass
    def _load_clients(self): pass