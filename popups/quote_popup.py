import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk
import pandas as pd

from popups.base_popup import BasePopup
from styles import COLORS, FONTS
from export_manager import ExportManager

class QuotePopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_no=None, copy_mode=False):
        self.export_manager = ExportManager()
        self.copy_mode = copy_mode
        self.copy_src_no = mgmt_no if copy_mode else None
        
        # [수정] 복사 모드일 경우, 부모 클래스에는 mgmt_no를 None(신규)으로 전달하여 새 번호를 따게 함
        real_mgmt_no = None if copy_mode else mgmt_no
        
        super().__init__(parent, data_manager, refresh_callback, popup_title="견적", mgmt_no=real_mgmt_no)

        # 신규 등록(또는 복사)일 때 기본값 설정
        if not real_mgmt_no:
            # self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d")) # _setup_info_panel에서 처리하거나 여기서 처리 (중복 방지)
            self.combo_status.set("견적")
            
        # [신규] 복사 모드라면 원본 데이터 로드하여 필드 채우기
        if self.copy_mode and self.copy_src_no:
            self._load_copied_data()
    
    def _create_widgets(self):
        self.configure(fg_color=COLORS["bg_dark"])
        self.geometry("1350x850") # OrderPopup과 동일한 크기
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 1. 헤더
        self._create_header(self.main_container)
        
        # 2. 메인 콘텐츠 (Split View)
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, pady=10)
        
        # 좌측: 견적 정보 (Fixed 400px)
        self.info_panel = ctk.CTkFrame(self.content_frame, fg_color=COLORS["bg_medium"], corner_radius=10, width=400)
        self.info_panel.pack(side="left", fill="y", padx=(0, 10))
        self.info_panel.pack_propagate(False)
        
        # 우측: 품목 리스트 (Flexible)
        self.items_panel = ctk.CTkFrame(self.content_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        self.items_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self.items_panel.pack_propagate(False)
        
        self._setup_info_panel(self.info_panel)
        self._setup_items_panel(self.items_panel)
        
        # 3. 하단 액션 바
        self._create_footer(self.main_container)

    def _create_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        # 상단: ID 및 상태
        top_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        top_row.pack(fill="x", anchor="w")
        
        self.lbl_id = ctk.CTkLabel(top_row, text="NEW QUOTE", font=FONTS["main"], text_color=COLORS["text_dim"])
        self.lbl_id.pack(side="left")
        
        # 상태 콤보박스 (헤더에 배치)
        self.combo_status = ctk.CTkComboBox(top_row, values=["견적", "진행중", "완료", "취소"], width=100, height=24, font=FONTS["small"])
        self.combo_status.pack(side="left", padx=10)
        self.combo_status.set("견적")
        
        # 프로젝트명 및 고객사 (헤더에 표시)
        info_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        info_row.pack(fill="x", pady=(5, 0))
        
        self.lbl_project_header = ctk.CTkLabel(info_row, text="Project Name", font=FONTS["title"], anchor="w")
        self.lbl_project_header.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(info_row, text="|", font=FONTS["header"], text_color=COLORS["text_dim"]).pack(side="left", padx=10)
        
        self.lbl_client_header = ctk.CTkLabel(info_row, text="Client Name", font=FONTS["header"], text_color=COLORS["text_dim"], anchor="w")
        self.lbl_client_header.pack(side="left", padx=10)
        
        # 숨겨진 필드 (로직 호환성)
        self.entry_id = ctk.CTkEntry(self, width=0) # _generate_new_id 등에서 사용
        
    def _setup_info_panel(self, parent):
        # 스크롤 없이 고정된 패널 사용
        
        # 1. 기본 정보 섹션
        ctk.CTkLabel(parent, text="기본 정보", font=FONTS["header"]).pack(anchor="w", padx=10, pady=(10, 5))
        
        input_frame = ctk.CTkFrame(parent, fg_color="transparent")
        input_frame.pack(fill="x", padx=10)
        
        # Grid 설정
        info_grid = ctk.CTkFrame(input_frame, fg_color="transparent")
        info_grid.pack(fill="x", pady=5)
        info_grid.columnconfigure(0, weight=1)
        info_grid.columnconfigure(1, weight=1)

        def create_grid_input(parent, row, col, label, var_name, placeholder="", colspan=1):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=row, column=col, columnspan=colspan, sticky="ew", padx=2, pady=2)
            
            ctk.CTkLabel(f, text=label, width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
            entry = ctk.CTkEntry(f, height=28, placeholder_text=placeholder, font=FONTS["main"])
            entry.pack(side="left", fill="x", expand=True)
            setattr(self, var_name, entry)
            return entry

        # Row 0: 고객사 (Autocomplete)
        f_client = ctk.CTkFrame(info_grid, fg_color="transparent")
        f_client.grid(row=0, column=0, columnspan=2, sticky="ew", padx=2, pady=2)
        ctk.CTkLabel(f_client, text="고객사", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        from popups.autocomplete_entry import AutocompleteEntry
        self.entry_client = AutocompleteEntry(f_client, font=FONTS["main"], height=28,
                                            completevalues=self.dm.df_clients["업체명"].unique().tolist(),
                                            command=self._on_client_select)
        self.entry_client.pack(side="left", fill="x", expand=True)
        self.entry_client.set_completion_list(self.dm.df_clients["업체명"].unique().tolist())
        
        # 직접 입력 후 포커스 아웃/엔터 시에도 업데이트
        self.entry_client.bind("<FocusOut>", lambda e: self._on_client_select(self.entry_client.get()))
        self.entry_client.bind("<Return>", lambda e: self._on_client_select(self.entry_client.get()))
        
        # Row 1: 프로젝트
        create_grid_input(info_grid, 1, 0, "프로젝트", "entry_project", colspan=2)
        
        # Row 2: 견적일자 | 구분
        date_entry = create_grid_input(info_grid, 2, 0, "견적일자", "entry_date")
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # 구분 (ComboBox)
        f_type = ctk.CTkFrame(info_grid, fg_color="transparent")
        f_type.grid(row=2, column=1, sticky="ew", padx=2, pady=2)
        ctk.CTkLabel(f_type, text="구분", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        self.combo_type = ctk.CTkComboBox(f_type, values=["내수", "수출"], height=28, font=FONTS["main"], command=self.on_type_change)
        self.combo_type.pack(side="left", fill="x", expand=True)
        self.combo_type.set("내수")

        # Row 3: 통화 | 세율
        # 통화 (ComboBox)
        f_curr = ctk.CTkFrame(info_grid, fg_color="transparent")
        f_curr.grid(row=3, column=0, sticky="ew", padx=2, pady=2)
        ctk.CTkLabel(f_curr, text="통화", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        self.combo_currency = ctk.CTkComboBox(f_curr, values=["KRW", "USD", "EUR", "CNY", "JPY"], height=28, font=FONTS["main"], command=self.on_currency_change)
        self.combo_currency.pack(side="left", fill="x", expand=True)
        self.combo_currency.set("KRW")
        
        # 세율
        tax_entry = create_grid_input(info_grid, 3, 1, "세율(%)", "entry_tax_rate")
        tax_entry.insert(0, "10")
        tax_entry.bind("<KeyRelease>", lambda e: self._calculate_totals())

        ctk.CTkFrame(parent, height=2, fg_color=COLORS["border"]).pack(fill="x", padx=10, pady=10)

        # 2. 추가 정보 (특이사항, 비고)
        ctk.CTkLabel(parent, text="추가 정보", font=FONTS["header"]).pack(anchor="w", padx=10, pady=(0, 5))
        
        # 업체 특이사항
        self.lbl_client_note = ctk.CTkLabel(parent, text="업체 특이사항: -", font=FONTS["main"], text_color=COLORS["danger"], anchor="w", wraplength=380)
        self.lbl_client_note.pack(fill="x", padx=15, pady=(0, 5))
        
        # 견적 비고
        ctk.CTkLabel(parent, text="견적 비고", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(anchor="w", padx=15, pady=(5, 0))
        self.entry_note = ctk.CTkEntry(parent, height=60) # Multiline 느낌을 위해 높이 키움 (실제론 Entry)
        self.entry_note.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkFrame(parent, height=2, fg_color=COLORS["border"]).pack(fill="x", padx=10, pady=10)

        # 3. 문서 발행
        ctk.CTkLabel(parent, text="문서 발행", font=FONTS["header"]).pack(anchor="w", padx=10, pady=(0, 5))
        
        self.btn_export = ctk.CTkButton(parent, text="📄 견적서 발행 (PDF)", command=self.export_quote, height=35,
                                      fg_color=COLORS["warning"], hover_color="#D35400", 
                                      text_color="white", font=FONTS["main_bold"])
        self.btn_export.pack(fill="x", padx=10, pady=5)

    def _setup_items_panel(self, parent):
        # 타이틀 및 요약
        top_frame = ctk.CTkFrame(parent, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(top_frame, text="견적 품목 리스트", font=FONTS["header"]).pack(side="left")
        
        # 총계 표시
        summary_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        summary_frame.pack(side="right")
        
        self.lbl_total_qty = ctk.CTkLabel(summary_frame, text="총 수량: 0", font=FONTS["main_bold"])
        self.lbl_total_qty.pack(side="left", padx=10)
        
        self.lbl_total_amt = ctk.CTkLabel(summary_frame, text="총 합계: 0", font=FONTS["header"], text_color=COLORS["primary"])
        self.lbl_total_amt.pack(side="left", padx=10)

        # 헤더
        headers = ["품명", "모델명", "Description", "수량", "단가", "공급가액", "세액", "합계"]
        widths = [120, 120, 150, 50, 80, 80, 60, 80]
        
        header_frame = ctk.CTkFrame(parent, height=35, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x", padx=15)
        
        for h, w in zip(headers, widths):
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["main_bold"]).pack(side="left", padx=2)
            
        # 스크롤 리스트
        self.scroll_items = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_items.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 품목 추가 버튼
        ctk.CTkButton(parent, text="+ 품목 추가", command=self._add_item_row, height=35,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], 
                      text_color=COLORS["text"]).pack(fill="x", padx=15, pady=10)

    def _create_footer(self, parent):
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(footer_frame, text="닫기", command=self.destroy, width=100, height=45,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], 
                      text_color=COLORS["text"]).pack(side="left")
                      
        if self.copy_mode:
            btn_text = "복사 등록 (저장)"
        else:
            btn_text = "견적 저장" if not self.mgmt_no else "견적 수정 (저장)"
            
        ctk.CTkButton(footer_frame, text=btn_text, command=self.save, width=200, height=45,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], 
                      font=FONTS["header"]).pack(side="right")
        
        if self.mgmt_no and not self.copy_mode:
            ctk.CTkButton(footer_frame, text="삭제", command=self.delete, width=100, height=45,
                          fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"], 
                          text_color="white").pack(side="right", padx=10)

    # ==========================================================================
    # 로직 메서드 (기존 유지 및 UI 연동)
    # ==========================================================================
    def _on_client_select(self, client_name):
        # 헤더 업데이트
        self.lbl_client_header.configure(text=client_name)
        
        df = self.dm.df_clients
        row = df[df["업체명"] == client_name]
        if not row.empty:
            currency = row.iloc[0].get("통화", "KRW")
            if currency and str(currency) != "nan":
                self.combo_currency.set(currency)
                self.on_currency_change(currency)
            
            note = str(row.iloc[0].get("특이사항", "-"))
            if note == "nan" or not note: note = "-"
            self.lbl_client_note.configure(text=f"업체 특이사항: {note}")

    def on_type_change(self, type_val): self._calculate_totals()

    def on_currency_change(self, currency):
        if currency == "KRW":
            self.entry_tax_rate.delete(0, "end")
            self.entry_tax_rate.insert(0, "10")
            self.combo_type.set("내수")
        else:
            self.entry_tax_rate.delete(0, "end")
            self.entry_tax_rate.insert(0, "0")
            self.combo_type.set("수출")
        self._calculate_totals()

    def _generate_new_id(self):
        # 견적 번호 생성 (Q + 날짜)
        today_str = datetime.now().strftime("%y%m%d")
        prefix = f"Q{today_str}"
        
        df = self.dm.df_data
        existing_ids = df[df["관리번호"].str.startswith(prefix)]["관리번호"].unique()
        
        if len(existing_ids) == 0: seq = 1
        else:
            max_seq = 0
            for eid in existing_ids:
                try:
                    parts = eid.split("-")
                    if len(parts) > 1:
                        seq_num = int(parts[-1])
                        if seq_num > max_seq: max_seq = seq_num
                except: pass
            seq = max_seq + 1
            
        new_id = f"{prefix}-{seq:03d}"
        self.entry_id.configure(state="normal")
        self.entry_id.delete(0, "end")
        self.entry_id.insert(0, new_id)
        self.entry_id.configure(state="readonly")
        
        # 헤더 라벨 업데이트
        self.lbl_id.configure(text=new_id)

    def _add_item_row(self, item_data=None):
        # BasePopup._add_item_row 호출 (self.scroll_items에 추가됨)
        # 하지만 BasePopup은 self.scroll_items가 있다고 가정함.
        # 여기서는 self.scroll_items가 _setup_items_panel에서 생성됨.
        
        row_widgets = super()._add_item_row()

        row_widgets["qty"].insert(0, "1")
        row_widgets["price"].insert(0, "0")

        row_widgets["qty"].bind("<KeyRelease>", lambda e, rw=row_widgets: self.calculate_row(rw))
        row_widgets["price"].bind("<KeyRelease>", lambda e, w=row_widgets["price"], rw=row_widgets: self.on_price_change(e, w, rw))

        if item_data is not None:
            row_widgets["item"].insert(0, str(item_data.get("품목명", "")))
            row_widgets["model"].insert(0, str(item_data.get("모델명", "")))
            row_widgets["desc"].insert(0, str(item_data.get("Description", "")))
            row_widgets["qty"].delete(0, "end"); row_widgets["qty"].insert(0, str(item_data.get("수량", 0)))
            price_val = float(item_data.get("단가", 0))
            row_widgets["price"].delete(0, "end"); row_widgets["price"].insert(0, f"{int(price_val):,}")
            self.calculate_row(row_widgets)

    def on_price_change(self, event, widget, row_data):
        val = widget.get().replace(",", "")
        if val.isdigit():
            formatted = f"{int(val):,}"
            if widget.get() != formatted:
                widget.delete(0, "end")
                widget.insert(0, formatted)
        self.calculate_row(row_data)

    def calculate_row(self, row_data):
        try:
            qty = float(row_data["qty"].get().strip().replace(",","") or 0)
            price = float(row_data["price"].get().strip().replace(",","") or 0)
            supply = qty * price
            try: tax_rate = float(self.entry_tax_rate.get().strip() or 0)
            except: tax_rate = 0
            tax = supply * (tax_rate / 100)
            total = supply + tax
            
            def update_entry(entry, val):
                entry.configure(state="normal")
                entry.delete(0, "end")
                entry.insert(0, f"{val:,.0f}")
                entry.configure(state="readonly")

            update_entry(row_data["supply"], supply)
            update_entry(row_data["tax"], tax)
            update_entry(row_data["total"], total)
        except ValueError: pass
        self._calculate_totals()

    def _calculate_totals(self):
        total_qty = 0
        total_amt = 0
        for row in self.item_rows:
            try:
                q = float(row["qty"].get().replace(",",""))
                t = float(row["total"].get().replace(",",""))
                total_qty += q
                total_amt += t
            except: pass
        self.lbl_total_qty.configure(text=f"총 수량: {total_qty:,.0f}")
        self.lbl_total_amt.configure(text=f"총 합계: {total_amt:,.0f}")

    def _load_data(self):
        df = self.dm.df_data
        rows = df[df["관리번호"] == self.mgmt_no]
        if rows.empty: return
        
        first = rows.iloc[0]
        self.entry_id.configure(state="normal")
        self.entry_id.delete(0, "end")
        self.entry_id.insert(0, str(first["관리번호"]))
        self.entry_id.configure(state="readonly")
        
        self.lbl_id.configure(text=str(first["관리번호"]))
        
        date_val = str(first.get("견적일", ""))
        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, date_val)

        self.combo_type.set(str(first.get("구분", "내수")))
        
        client_name = str(first.get("업체명", ""))
        self.entry_client.delete(0, "end")
        self.entry_client.insert(0, client_name)
        
        self.combo_currency.set(str(first.get("통화", "KRW")))
        
        saved_tax = first.get("세율(%)", "")
        if saved_tax != "" and saved_tax != "-": tax_rate = str(saved_tax)
        else:
            currency = str(first.get("통화", "KRW"))
            tax_rate = "10" if currency == "KRW" else "0"
        self.entry_tax_rate.delete(0, "end")
        self.entry_tax_rate.insert(0, tax_rate)

        self.entry_project.delete(0, "end")
        self.entry_project.insert(0, str(first.get("프로젝트명", "")))
        self.lbl_project_header.configure(text=str(first.get("프로젝트명", "")))
        
        self.entry_note.delete(0, "end")
        self.entry_note.insert(0, str(first.get("비고", "")))
        
        current_status = str(first.get("Status", "견적"))
        self.combo_status.set(current_status)
        
        self._on_client_select(client_name)
        for _, row in rows.iterrows(): self._add_item_row(row)

    # [신규] 복사된 데이터 로드 메서드
    def _load_copied_data(self):
        df = self.dm.df_data
        # 원본(copy_src_no) 데이터를 찾음
        rows = df[df["관리번호"] == self.copy_src_no]
        if rows.empty: return
        
        first = rows.iloc[0]
        
        # ID는 _generate_new_id()에 의해 이미 신규로 생성되어 있으므로 건드리지 않음
        # 날짜는 오늘 날짜로 유지 (이미 __init__에서 설정됨)
        # 상태는 '견적'으로 유지 (이미 __init__에서 설정됨)

        self.combo_type.set(str(first.get("구분", "내수")))
        
        client_name = str(first.get("업체명", ""))
        self.entry_client.delete(0, "end")
        self.entry_client.insert(0, client_name)
        
        self.combo_currency.set(str(first.get("통화", "KRW")))
        
        saved_tax = first.get("세율(%)", "")
        if saved_tax != "" and saved_tax != "-": tax_rate = str(saved_tax)
        else:
            currency = str(first.get("통화", "KRW"))
            tax_rate = "10" if currency == "KRW" else "0"
        self.entry_tax_rate.delete(0, "end")
        self.entry_tax_rate.insert(0, tax_rate)

        # 프로젝트명 뒤에 (Copy) 붙이기
        original_proj = str(first.get("프로젝트명", ""))
        self.entry_project.insert(0, f"{original_proj} (Copy)")
        self.lbl_project_header.configure(text=f"{original_proj} (Copy)")
        
        self.entry_note.insert(0, str(first.get("비고", "")))
        
        self._on_client_select(client_name)
        
        # 품목 추가
        for _, row in rows.iterrows(): self._add_item_row(row)
        
        # 윈도우 타이틀 업데이트
        self.title(f"견적 복사 등록 (원본: {self.copy_src_no}) - Sales Manager")

    def save(self):
        mgmt_no = self.entry_id.get()
        client = self.entry_client.get()
        
        if not client:
            messagebox.showwarning("경고", "고객사를 선택해주세요.", parent=self)
            return
        if not self.item_rows:
            messagebox.showwarning("경고", "최소 1개 이상의 품목을 추가해주세요.", parent=self)
            return

        try: tax_rate_val = float(self.entry_tax_rate.get().strip())
        except: tax_rate_val = 0

        new_rows = []
        
        common_data = {
            "관리번호": mgmt_no,
            "구분": self.combo_type.get(),
            "업체명": client,
            "프로젝트명": self.entry_project.get(),
            "통화": self.combo_currency.get(),
            "환율": 1, 
            "세율(%)": tax_rate_val,
            "주문요청사항": "",
            "비고": self.entry_note.get(),
            "Status": self.combo_status.get(),
            "견적일": self.entry_date.get()
        }
        
        for item in self.item_rows:
            row_data = common_data.copy()
            row_data.update({
                "품목명": item["item"].get(), "모델명": item["model"].get(), "Description": item["desc"].get(),
                "수량": float(item["qty"].get().replace(",","") or 0),
                "단가": float(item["price"].get().replace(",","") or 0),
                "공급가액": float(item["supply"].get().replace(",","") or 0),
                "세액": float(item["tax"].get().replace(",","") or 0),
                "합계금액": float(item["total"].get().replace(",","") or 0),
                "기수금액": 0, "미수금액": float(item["total"].get().replace(",","") or 0)
            })
            new_rows.append(row_data)

        def update_logic(dfs):
            # [수정] 복사 모드일 때도 mgmt_no는 신규이므로 self.mgmt_no 체크 로직 타지 않음 (self.mgmt_no가 None임)
            # 일반 수정 모드(self.mgmt_no가 있음)일 때만 기존 데이터 삭제 로직 실행
            if self.mgmt_no:
                mask = dfs["data"]["관리번호"] == self.mgmt_no
                existing_rows = dfs["data"][mask]
                if not existing_rows.empty:
                    first_exist = existing_rows.iloc[0]
                    preserve_cols = ["수주일", "출고예정일", "출고일", "입금완료일", 
                                     "세금계산서발행일", "계산서번호", "수출신고번호", "발주서경로"]
                    for row in new_rows:
                        for col in preserve_cols:
                            row[col] = first_exist.get(col, "-")
                        
                dfs["data"] = dfs["data"][~mask]
            
            new_df = pd.DataFrame(new_rows)
            dfs["data"] = pd.concat([dfs["data"], new_df], ignore_index=True)
            
            # 액션 로그 메시지 수정
            if self.copy_mode:
                action = "복사 등록"
                log_msg = f"견적 복사: [{self.copy_src_no}] -> [{mgmt_no}] / 업체 [{client}]"
            else:
                action = "수정" if self.mgmt_no else "등록"
                log_msg = f"견적 {action}: 번호 [{mgmt_no}] / 업체 [{client}]"
                
            new_log = self.dm._create_log_entry(f"견적 {action}", log_msg)
            dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
            
            return True, ""

        success, msg = self.dm._execute_transaction(update_logic)
        
        if success:
            messagebox.showinfo("완료", "저장되었습니다.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", msg, parent=self)

    def delete(self):
        if messagebox.askyesno("삭제 확인", f"정말 이 {self.popup_title} 데이터를 삭제하시겠습니까?", parent=self):
            def update_logic(dfs):
                mask = dfs["data"]["관리번호"] == self.mgmt_no
                if mask.any():
                    dfs["data"] = dfs["data"][~mask]
                    log_msg = f"{self.popup_title} 삭제: 번호 [{self.mgmt_no}]"
                    new_log = self.dm._create_log_entry("삭제", log_msg)
                    dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
                    return True, ""
                return False, "삭제할 데이터를 찾을 수 없습니다."

            success, msg = self.dm._execute_transaction(update_logic)
            if success:
                messagebox.showinfo("삭제 완료", "데이터가 삭제되었습니다.", parent=self)
                self.refresh_callback()
                self.destroy()
            else:
                messagebox.showerror("실패", msg, parent=self)

    def export_quote(self):
        client_name = self.entry_client.get()
        if not client_name:
            self.attributes("-topmost", False)
            messagebox.showwarning("경고", "고객사를 선택해주세요.", parent=self)
            self.attributes("-topmost", True)
            return

        client_row = self.dm.df_clients[self.dm.df_clients["업체명"] == client_name]
        if client_row.empty:
            self.attributes("-topmost", False)
            messagebox.showerror("오류", "고객 정보를 찾을 수 없습니다.", parent=self)
            self.attributes("-topmost", True)
            return
        
        quote_info = {
            "client_name": client_name,
            "mgmt_no": self.entry_id.get(),
            "date": self.entry_date.get(),
            "req_note": "", # 견적엔 주문요청사항 없음
            "note": self.entry_note.get()
        }
        
        items = []
        for row in self.item_rows:
            items.append({
                "item": row["item"].get(),
                "model": row["model"].get(),
                "desc": row["desc"].get(),
                "qty": float(row["qty"].get().replace(",", "") or 0),
                "price": float(row["price"].get().replace(",", "") or 0),
                "amount": float(row["supply"].get().replace(",", "") or 0)
            })

        success, result = self.export_manager.export_quote_to_pdf(
            client_row.iloc[0], quote_info, items
        )
        
        self.attributes("-topmost", False)
        if success:
            messagebox.showinfo("성공", f"견적서가 생성되었습니다.\n{result}", parent=self)
        else:
            messagebox.showerror("실패", result, parent=self)
        self.attributes("-topmost", True)
    
    # BasePopup의 미사용 메서드 오버라이드 (빈 구현)
    def _create_top_frame(self): pass
    def _create_items_frame(self): pass
    def _create_bottom_frame(self): pass
    def _create_action_buttons(self): pass
    def _create_additional_frames(self): pass