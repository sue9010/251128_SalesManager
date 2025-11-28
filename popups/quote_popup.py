import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pandas as pd

from config import Config
from styles import COLORS, FONT_FAMILY, FONTS


class QuotePopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_no=None):
        super().__init__(parent)
        self.dm = data_manager
        self.refresh_callback = refresh_callback
        self.mgmt_no = mgmt_no # None이면 신규, 있으면 수정
        
        # 신규 모드인지 수정 모드인지 확인
        mode_text = "견적 수정" if mgmt_no else "신규 견적 등록"
        self.title(f"{mode_text} - Sales Manager")
        self.geometry("1100x800")
        
        self.item_rows = [] # 품목 행 위젯 저장소
        self.deleted_items = [] # 삭제된 행 추적 (수정 모드일 때)
        
        self.create_widgets()
        self.load_clients()
        
        if self.mgmt_no:
            self.load_data()
        else:
            self.generate_new_id()
            # 기본값 설정
            self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)

    def create_widgets(self):
        # --- 1. 상단 정보 (기본 정보) ---
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=15)

        # 관리번호 (ID)
        ctk.CTkLabel(top_frame, text="관리번호", font=FONTS["main_bold"]).grid(row=0, column=0, padx=5, sticky="w")
        self.entry_id = ctk.CTkEntry(top_frame, width=150, font=FONTS["main"])
        self.entry_id.grid(row=0, column=1, padx=5, sticky="w")
        self.entry_id.configure(state="readonly") # 자동 생성

        # 날짜 (견적일)
        ctk.CTkLabel(top_frame, text="견적일자", font=FONTS["main_bold"]).grid(row=0, column=2, padx=5, sticky="w")
        self.entry_date = ctk.CTkEntry(top_frame, width=120, font=FONTS["main"], placeholder_text="YYYY-MM-DD")
        self.entry_date.grid(row=0, column=3, padx=5, sticky="w")

        # 구분 (내수/수출)
        ctk.CTkLabel(top_frame, text="구분", font=FONTS["main_bold"]).grid(row=0, column=4, padx=5, sticky="w")
        self.combo_type = ctk.CTkComboBox(top_frame, values=["내수", "수출"], width=100, font=FONTS["main"], command=self.on_type_change)
        self.combo_type.grid(row=0, column=5, padx=5, sticky="w")
        self.combo_type.set("내수")

        # 업체 선택
        ctk.CTkLabel(top_frame, text="고객사", font=FONTS["main_bold"]).grid(row=1, column=0, padx=5, pady=10, sticky="w")
        self.combo_client = ctk.CTkComboBox(top_frame, width=200, font=FONTS["main"], command=self.on_client_select)
        self.combo_client.grid(row=1, column=1, padx=5, pady=10, sticky="w")

        # 통화 및 환율
        ctk.CTkLabel(top_frame, text="통화", font=FONTS["main_bold"]).grid(row=1, column=2, padx=5, pady=10, sticky="w")
        self.combo_currency = ctk.CTkComboBox(top_frame, values=["KRW", "USD", "EUR", "CNY", "JPY"], width=100, font=FONTS["main"])
        self.combo_currency.grid(row=1, column=3, padx=5, pady=10, sticky="w")
        self.combo_currency.set("KRW")

        ctk.CTkLabel(top_frame, text="환율", font=FONTS["main_bold"]).grid(row=1, column=4, padx=5, pady=10, sticky="w")
        self.entry_rate = ctk.CTkEntry(top_frame, width=100, font=FONTS["main"])
        self.entry_rate.grid(row=1, column=5, padx=5, pady=10, sticky="w")
        self.entry_rate.insert(0, "1") # 기본 환율 1

        # 프로젝트/품명
        ctk.CTkLabel(top_frame, text="프로젝트/품명", font=FONTS["main_bold"]).grid(row=2, column=0, padx=5, sticky="w")
        self.entry_project = ctk.CTkEntry(top_frame, width=300, font=FONTS["main"])
        self.entry_project.grid(row=2, column=1, columnspan=3, padx=5, sticky="ew")

        # --- 2. 품목 리스트 (중앙) ---
        list_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"])
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 헤더
        headers = ["모델명", "Description", "수량", "단가", "공급가액", "세액", "합계금액", "삭제"]
        widths = [150, 200, 60, 100, 100, 80, 100, 50]
        
        header_frame = ctk.CTkFrame(list_frame, height=30, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x")
        
        for i, (h, w) in enumerate(zip(headers, widths)):
            lbl = ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["small"])
            lbl.pack(side="left", padx=2)

        # 스크롤 영역
        self.scroll_items = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.scroll_items.pack(fill="both", expand=True)

        # 품목 추가 버튼
        btn_add_row = ctk.CTkButton(list_frame, text="+ 품목 추가", command=self.add_item_row, 
                                    fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], text_color=COLORS["text"])
        btn_add_row.pack(fill="x", pady=5)

        # --- 3. 하단 정보 (합계 및 파일) ---
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=10)

        # 합계 표시
        self.lbl_total_qty = ctk.CTkLabel(bottom_frame, text="총 수량: 0", font=FONTS["main_bold"])
        self.lbl_total_qty.pack(side="left", padx=10)
        
        self.lbl_total_amt = ctk.CTkLabel(bottom_frame, text="총 합계금액: 0", font=FONTS["header"], text_color=COLORS["primary"])
        self.lbl_total_amt.pack(side="left", padx=20)

        # 파일 첨부
        file_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"])
        file_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(file_frame, text="견적서 파일:", font=FONTS["main"]).pack(side="left", padx=10, pady=10)
        self.entry_file = ctk.CTkEntry(file_frame, width=400)
        self.entry_file.pack(side="left", padx=5)
        ctk.CTkButton(file_frame, text="찾기", width=60, command=self.browse_file, fg_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="left", padx=5)

        # 비고
        note_frame = ctk.CTkFrame(self, fg_color="transparent")
        note_frame.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(note_frame, text="비고:", font=FONTS["main"]).pack(side="left", padx=5)
        self.entry_note = ctk.CTkEntry(note_frame)
        self.entry_note.pack(side="left", fill="x", expand=True, padx=5)

        # --- 4. 저장/취소 버튼 ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent", height=50)
        btn_frame.pack(fill="x", padx=20, pady=20, side="bottom")

        ctk.CTkButton(btn_frame, text="저장", command=self.save, width=120, height=40,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], font=FONTS["main_bold"]).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="취소", command=self.destroy, width=80, height=40,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], text_color=COLORS["text"]).pack(side="right", padx=5)
        
        if self.mgmt_no:
             ctk.CTkButton(btn_frame, text="삭제", command=self.delete_quote, width=80, height=40,
                          fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"]).pack(side="left")

    def load_clients(self):
        """업체 목록 로드 및 콤보박스 설정"""
        clients = self.dm.df_clients["업체명"].unique().tolist()
        self.combo_client.configure(values=clients)

    def on_client_select(self, client_name):
        """업체 선택 시 통화 정보 등 자동 입력"""
        df = self.dm.df_clients
        row = df[df["업체명"] == client_name]
        if not row.empty:
            currency = row.iloc[0].get("통화", "KRW")
            if currency and str(currency) != "nan":
                self.combo_currency.set(currency)
            # 여기에 담당자 정보 등을 추가로 불러올 수 있음

    def on_type_change(self, type_val):
        """내수/수출 변경 시 세액 재계산 트리거"""
        self.calculate_totals()

    def generate_new_id(self):
        """새 관리번호 생성 (QYYMMDD-XXX)"""
        today_str = datetime.now().strftime("%y%m%d")
        prefix = f"Q{today_str}"
        
        # 기존 데이터에서 같은 날짜의 번호 찾기
        df = self.dm.df_data
        existing_ids = df[df["관리번호"].str.startswith(prefix)]["관리번호"].unique()
        
        if len(existing_ids) == 0:
            seq = 1
        else:
            # 뒷자리 숫자만 추출해서 최대값 찾기
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

    def add_item_row(self, item_data=None):
        """품목 입력 행 추가"""
        row_idx = len(self.item_rows)
        row_frame = ctk.CTkFrame(self.scroll_items, fg_color="transparent", height=35)
        row_frame.pack(fill="x", pady=2)

        # 위젯 생성
        # 1. 모델명
        e_model = ctk.CTkEntry(row_frame, width=150)
        e_model.pack(side="left", padx=2)
        
        # 2. Description
        e_desc = ctk.CTkEntry(row_frame, width=200)
        e_desc.pack(side="left", padx=2)
        
        # 3. 수량 (숫자만)
        e_qty = ctk.CTkEntry(row_frame, width=60, justify="center")
        e_qty.pack(side="left", padx=2)
        e_qty.insert(0, "1")
        
        # 4. 단가
        e_price = ctk.CTkEntry(row_frame, width=100, justify="right")
        e_price.pack(side="left", padx=2)
        e_price.insert(0, "0")
        
        # 5. 공급가액 (Readonly)
        e_supply = ctk.CTkEntry(row_frame, width=100, justify="right", fg_color=COLORS["bg_light"])
        e_supply.pack(side="left", padx=2)
        e_supply.configure(state="readonly")
        
        # 6. 세액 (Readonly)
        e_tax = ctk.CTkEntry(row_frame, width=80, justify="right", fg_color=COLORS["bg_light"])
        e_tax.pack(side="left", padx=2)
        e_tax.configure(state="readonly")
        
        # 7. 합계 (Readonly)
        e_total = ctk.CTkEntry(row_frame, width=100, justify="right", fg_color=COLORS["bg_light"], text_color=COLORS["primary"])
        e_total.pack(side="left", padx=2)
        e_total.configure(state="readonly")
        
        # 8. 삭제 버튼
        btn_del = ctk.CTkButton(row_frame, text="X", width=40, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                                command=lambda f=row_frame: self.delete_item_row(f))
        btn_del.pack(side="left", padx=5)

        # 데이터 바인딩 (계산용)
        row_data = {
            "frame": row_frame,
            "model": e_model, "desc": e_desc, "qty": e_qty, 
            "price": e_price, "supply": e_supply, "tax": e_tax, "total": e_total
        }
        
        self.item_rows.append(row_data)

        # 이벤트 연결 (값 변경 시 자동 계산)
        e_qty.bind("<KeyRelease>", lambda e: self.calculate_row(row_data))
        e_price.bind("<KeyRelease>", lambda e: self.calculate_row(row_data))

        # 데이터 채우기 (수정 모드)
        if item_data:
            e_model.insert(0, str(item_data.get("모델명", "")))
            e_desc.insert(0, str(item_data.get("Description", "")))
            e_qty.delete(0, "end"); e_qty.insert(0, str(item_data.get("수량", 0)))
            e_price.delete(0, "end"); e_price.insert(0, str(item_data.get("단가", 0)))
            self.calculate_row(row_data) # 초기 계산

    def delete_item_row(self, frame):
        """행 삭제"""
        for item in self.item_rows:
            if item["frame"] == frame:
                self.item_rows.remove(item)
                break
        frame.destroy()
        self.calculate_totals()

    def calculate_row(self, row_data):
        """개별 행 계산"""
        try:
            qty = float(row_data["qty"].get().strip() or 0)
            price = float(row_data["price"].get().strip() or 0)
            
            supply = qty * price
            
            # 세액 계산 (내수: 10%, 수출: 0%)
            is_domestic = (self.combo_type.get() == "내수")
            tax = supply * 0.1 if is_domestic else 0
            
            total = supply + tax
            
            # UI 업데이트
            row_data["supply"].configure(state="normal")
            row_data["supply"].delete(0, "end")
            row_data["supply"].insert(0, f"{supply:,.0f}")
            row_data["supply"].configure(state="readonly")
            
            row_data["tax"].configure(state="normal")
            row_data["tax"].delete(0, "end")
            row_data["tax"].insert(0, f"{tax:,.0f}")
            row_data["tax"].configure(state="readonly")
            
            row_data["total"].configure(state="normal")
            row_data["total"].delete(0, "end")
            row_data["total"].insert(0, f"{total:,.0f}")
            row_data["total"].configure(state="readonly")
            
        except ValueError:
            pass # 숫자 아님
        
        self.calculate_totals()

    def calculate_totals(self):
        """전체 합계 계산"""
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
        self.lbl_total_amt.configure(text=f"총 합계금액: {total_amt:,.0f}")

    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.entry_file.delete(0, "end")
            self.entry_file.insert(0, path)

    def load_data(self):
        """수정 모드: 기존 데이터 불러오기"""
        df = self.dm.df_data
        rows = df[df["관리번호"] == self.mgmt_no]
        if rows.empty: return
        
        # 공통 정보 (첫 번째 행 기준)
        first = rows.iloc[0]
        self.entry_id.configure(state="normal")
        self.entry_id.insert(0, str(first["관리번호"]))
        self.entry_id.configure(state="readonly")
        
        self.entry_date.insert(0, str(first.get("견적일", "")))
        self.combo_type.set(str(first.get("구분", "내수")))
        self.combo_client.set(str(first.get("업체명", "")))
        self.combo_currency.set(str(first.get("통화", "KRW")))
        self.entry_rate.delete(0, "end"); self.entry_rate.insert(0, str(first.get("환율", "1")))
        self.entry_project.insert(0, str(first.get("품목명", "")))
        self.entry_file.insert(0, str(first.get("견적서경로", "")))
        self.entry_note.insert(0, str(first.get("비고", "")))
        
        # 품목 리스트
        for _, row in rows.iterrows():
            self.add_item_row(row)

    def save(self):
        """저장 로직"""
        # 1. 필수값 체크
        mgmt_no = self.entry_id.get()
        client = self.combo_client.get()
        if not client:
            messagebox.showwarning("경고", "고객사를 선택해주세요.")
            return
        if not self.item_rows:
            messagebox.showwarning("경고", "최소 1개 이상의 품목을 추가해주세요.")
            return

        # 2. 파일 저장 (필요 시)
        file_path = self.entry_file.get()
        saved_file_path = file_path
        if file_path and "SalesManager" not in file_path: # 이미 저장된 경로가 아니면
            # 파일 복사 및 경로 업데이트 로직 (DataManager 위임)
            new_path, err = self.dm.save_attachment(file_path, client, "견적서")
            if new_path: saved_file_path = new_path
        
        # 3. 데이터 수집
        new_rows = []
        common_data = {
            "관리번호": mgmt_no,
            "구분": self.combo_type.get(),
            "업체명": client,
            "품목명": self.entry_project.get(),
            "통화": self.combo_currency.get(),
            "환율": self.entry_rate.get(),
            "견적일": self.entry_date.get(),
            "견적서경로": saved_file_path,
            "비고": self.entry_note.get(),
            "Status": "견적" # 기본 상태
        }
        
        # 수정 모드라면 기존 Status 유지 (주문 상태일 수도 있으므로)
        if self.mgmt_no:
            original_status = self.dm.df_data[self.dm.df_data["관리번호"]==self.mgmt_no].iloc[0]["Status"]
            common_data["Status"] = original_status

        for item in self.item_rows:
            # 콤마 제거 후 숫자 변환
            qty = float(item["qty"].get().replace(",","") or 0)
            price = float(item["price"].get().replace(",","") or 0)
            supply = float(item["supply"].get().replace(",","") or 0)
            tax = float(item["tax"].get().replace(",","") or 0)
            total = float(item["total"].get().replace(",","") or 0)
            
            row_data = common_data.copy()
            row_data.update({
                "모델명": item["model"].get(),
                "Description": item["desc"].get(),
                "수량": qty,
                "단가": price,
                "공급가액": supply,
                "세액": tax,
                "합계금액": total,
                "미수금액": total # 초기 미수금은 합계금액과 동일
            })
            new_rows.append(row_data)

        # 4. DataManager 업데이트
        # 기존 데이터 삭제 (수정 모드일 경우)
        if self.mgmt_no:
            self.dm.df_data = self.dm.df_data[self.dm.df_data["관리번호"] != self.mgmt_no]
        
        # 신규 데이터 추가
        new_df = pd.DataFrame(new_rows)
        self.dm.df_data = pd.concat([self.dm.df_data, new_df], ignore_index=True)
        
        # 5. 엑셀 저장
        success, msg = self.dm.save_to_excel()
        if success:
            action = "수정" if self.mgmt_no else "등록"
            self.dm.add_log(f"견적 {action}", f"번호 [{mgmt_no}] / 업체 [{client}]")
            messagebox.showinfo("완료", "저장되었습니다.")
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", msg)

    def delete_quote(self):
        if messagebox.askyesno("삭제 확인", "정말 이 견적 건을 삭제하시겠습니까?"):
            self.dm.df_data = self.dm.df_data[self.dm.df_data["관리번호"] != self.mgmt_no]
            self.dm.save_to_excel()
            self.refresh_callback()
            self.destroy()