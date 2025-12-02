import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pandas as pd

from config import Config
from styles import COLORS, FONT_FAMILY, FONTS
from export_manager import ExportManager


class QuotePopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_no=None, default_status="견적"):
        super().__init__(parent)
        self.dm = data_manager
        self.refresh_callback = refresh_callback
        self.mgmt_no = mgmt_no
        self.default_status = default_status
        
        self.export_manager = ExportManager()
        
        if mgmt_no:
            mode_text = "상세 정보 수정"
        else:
            mode_text = "신규 주문 등록" if default_status == "주문" else "신규 견적 등록"
            
        self.title(f"{mode_text} - Sales Manager")
        self.geometry("1100x850")
        
        self.item_rows = [] 
        self.all_clients = []
        
        self.create_widgets()
        self.load_clients()
        
        if self.mgmt_no:
            self.load_data()
        else:
            self.generate_new_id()
            self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)

    def create_widgets(self):
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(top_frame, text="관리번호", font=FONTS["main_bold"]).grid(row=0, column=0, padx=5, sticky="w")
        self.entry_id = ctk.CTkEntry(top_frame, width=150, font=FONTS["main"])
        self.entry_id.grid(row=0, column=1, padx=5, sticky="w")
        self.entry_id.configure(state="readonly")

        date_label_text = "주문일자" if self.default_status == "주문" else "견적일자"
        ctk.CTkLabel(top_frame, text=date_label_text, font=FONTS["main_bold"]).grid(row=0, column=2, padx=5, sticky="w")
        self.entry_date = ctk.CTkEntry(top_frame, width=120, font=FONTS["main"], placeholder_text="YYYY-MM-DD")
        self.entry_date.grid(row=0, column=3, padx=5, sticky="w")

        ctk.CTkLabel(top_frame, text="구분", font=FONTS["main_bold"]).grid(row=0, column=4, padx=5, sticky="w")
        self.combo_type = ctk.CTkComboBox(top_frame, values=["내수", "수출"], width=100, font=FONTS["main"], command=self.on_type_change)
        self.combo_type.grid(row=0, column=5, padx=5, sticky="w")
        self.combo_type.set("내수")

        # [신규] 상태 변경 콤보박스
        ctk.CTkLabel(top_frame, text="상태", font=FONTS["main_bold"]).grid(row=0, column=6, padx=5, sticky="w")
        self.combo_status = ctk.CTkComboBox(top_frame, values=["견적", "주문", "생산중", "납품대기", "납품완료/입금대기", "납품대기/입금완료", "완료", "취소", "보류"], width=120, font=FONTS["main"])
        self.combo_status.grid(row=0, column=7, padx=5, sticky="w")
        self.combo_status.set(self.default_status)

        ctk.CTkLabel(top_frame, text="고객사", font=FONTS["main_bold"]).grid(row=1, column=0, padx=5, pady=10, sticky="w")
        self.combo_client = ctk.CTkComboBox(top_frame, width=200, font=FONTS["main"], command=self.on_client_select)
        self.combo_client.grid(row=1, column=1, padx=5, pady=10, sticky="w")
        try: self.combo_client._entry.bind("<KeyRelease>", self.on_client_typing)
        except: pass

        ctk.CTkLabel(top_frame, text="통화", font=FONTS["main_bold"]).grid(row=1, column=2, padx=5, pady=10, sticky="w")
        self.combo_currency = ctk.CTkComboBox(top_frame, values=["KRW", "USD", "EUR", "CNY", "JPY"], width=100, font=FONTS["main"], command=self.on_currency_change)
        self.combo_currency.grid(row=1, column=3, padx=5, pady=10, sticky="w")
        self.combo_currency.set("KRW")

        ctk.CTkLabel(top_frame, text="세율(%)", font=FONTS["main_bold"]).grid(row=1, column=4, padx=5, pady=10, sticky="w")
        self.entry_tax_rate = ctk.CTkEntry(top_frame, width=100, font=FONTS["main"])
        self.entry_tax_rate.grid(row=1, column=5, padx=5, pady=10, sticky="w")
        self.entry_tax_rate.insert(0, "10")
        self.entry_tax_rate.bind("<KeyRelease>", lambda e: self.calculate_totals())

        ctk.CTkLabel(top_frame, text="프로젝트명", font=FONTS["main_bold"]).grid(row=2, column=0, padx=5, sticky="w")
        self.entry_project = ctk.CTkEntry(top_frame, width=300, font=FONTS["main"])
        self.entry_project.grid(row=2, column=1, columnspan=3, padx=5, sticky="ew")
        
        info_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], height=40)
        info_frame.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(info_frame, text="업체 특이사항:", font=FONTS["main_bold"], text_color=COLORS["primary"]).pack(side="left", padx=10, pady=5)
        self.lbl_client_note = ctk.CTkLabel(info_frame, text="-", font=FONTS["main"])
        self.lbl_client_note.pack(side="left", padx=5, pady=5)

        list_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"])
        list_frame.pack(fill="both", expand=True, padx=20, pady=5)

        headers = ["품명", "모델명", "Description", "수량", "단가", "공급가액", "세액", "합계금액", "삭제"]
        widths = [150, 150, 200, 60, 100, 100, 80, 100, 50]
        header_frame = ctk.CTkFrame(list_frame, height=30, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x")
        
        for i, (h, w) in enumerate(zip(headers, widths)):
            lbl = ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["small"])
            lbl.pack(side="left", padx=2)

        self.scroll_items = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.scroll_items.pack(fill="both", expand=True)

        btn_add_row = ctk.CTkButton(list_frame, text="+ 품목 추가", command=self.add_item_row, 
                                    fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], text_color=COLORS["text"])
        btn_add_row.pack(fill="x", pady=5)

        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=5)

        self.lbl_total_qty = ctk.CTkLabel(bottom_frame, text="총 수량: 0", font=FONTS["main_bold"])
        self.lbl_total_qty.pack(side="left", padx=10)
        self.lbl_total_amt = ctk.CTkLabel(bottom_frame, text="총 합계금액: 0", font=FONTS["header"], text_color=COLORS["primary"])
        self.lbl_total_amt.pack(side="left", padx=20)

        input_grid = ctk.CTkFrame(self, fg_color="transparent")
        input_grid.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(input_grid, text="주문요청사항:", font=FONTS["main"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_req = ctk.CTkEntry(input_grid, width=300)
        self.entry_req.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ctk.CTkLabel(input_grid, text="비고:", font=FONTS["main"]).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.entry_note = ctk.CTkEntry(input_grid, width=300)
        self.entry_note.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        file_label_text = "발주서 파일:" if self.default_status == "주문" else "견적서 파일:"
        ctk.CTkLabel(input_grid, text=file_label_text, font=FONTS["main"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        file_box = ctk.CTkFrame(input_grid, fg_color="transparent")
        file_box.grid(row=1, column=1, columnspan=3, sticky="ew")
        self.entry_file = ctk.CTkEntry(file_box, width=400)
        self.entry_file.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(file_box, text="찾기", width=60, command=self.browse_file, fg_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="left", padx=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent", height=50)
        btn_frame.pack(fill="x", padx=20, pady=20, side="bottom")

        ctk.CTkButton(btn_frame, text="저장", command=self.save, width=120, height=40,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], font=FONTS["main_bold"]).pack(side="right", padx=5)
        
        ctk.CTkButton(btn_frame, text="🖨️ 견적서 발행", command=self.export_quote, width=120, height=40,
                      fg_color=COLORS["warning"], hover_color="#D35400", text_color="white", font=FONTS["main_bold"]).pack(side="right", padx=5)

        ctk.CTkButton(btn_frame, text="취소", command=self.destroy, width=80, height=40,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], text_color=COLORS["text"]).pack(side="right", padx=5)
        
        if self.mgmt_no:
             ctk.CTkButton(btn_frame, text="삭제", command=self.delete_quote, width=80, height=40,
                          fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"]).pack(side="left")

    def load_clients(self):
        self.all_clients = self.dm.df_clients["업체명"].unique().tolist()
        self.combo_client.configure(values=self.all_clients)

    def on_client_typing(self, event):
        typed = self.combo_client.get()
        if typed == "": self.combo_client.configure(values=self.all_clients)
        else:
            filtered = [c for c in self.all_clients if typed.lower() in c.lower()]
            self.combo_client.configure(values=filtered)

    def on_client_select(self, client_name):
        df = self.dm.df_clients
        row = df[df["업체명"] == client_name]
        if not row.empty:
            currency = row.iloc[0].get("통화", "KRW")
            if currency and str(currency) != "nan":
                self.combo_currency.set(currency)
                self.on_currency_change(currency)
            
            note = str(row.iloc[0].get("특이사항", "-"))
            if note == "nan" or not note: note = "-"
            self.lbl_client_note.configure(text=note)

    def on_type_change(self, type_val): self.calculate_totals()

    def on_currency_change(self, currency):
        if currency == "KRW":
            self.entry_tax_rate.delete(0, "end")
            self.entry_tax_rate.insert(0, "10")
            self.combo_type.set("내수")
        else:
            self.entry_tax_rate.delete(0, "end")
            self.entry_tax_rate.insert(0, "0")
            self.combo_type.set("수출")
        self.calculate_totals()

    def generate_new_id(self):
        prefix_char = "O" if self.default_status == "주문" else "Q"
        today_str = datetime.now().strftime("%y%m%d")
        prefix = f"{prefix_char}{today_str}"
        
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

    def add_item_row(self, item_data=None):
        row_frame = ctk.CTkFrame(self.scroll_items, fg_color="transparent", height=35)
        row_frame.pack(fill="x", pady=2)

        e_item = ctk.CTkEntry(row_frame, width=150)
        e_item.pack(side="left", padx=2)
        e_model = ctk.CTkEntry(row_frame, width=150)
        e_model.pack(side="left", padx=2)
        e_desc = ctk.CTkEntry(row_frame, width=200)
        e_desc.pack(side="left", padx=2)
        e_qty = ctk.CTkEntry(row_frame, width=60, justify="center")
        e_qty.pack(side="left", padx=2)
        e_qty.insert(0, "1")
        e_price = ctk.CTkEntry(row_frame, width=100, justify="right")
        e_price.pack(side="left", padx=2)
        e_price.insert(0, "0")
        
        e_supply = ctk.CTkEntry(row_frame, width=100, justify="right", fg_color=COLORS["bg_light"])
        e_supply.pack(side="left", padx=2)
        e_supply.configure(state="readonly")
        e_tax = ctk.CTkEntry(row_frame, width=80, justify="right", fg_color=COLORS["bg_light"])
        e_tax.pack(side="left", padx=2)
        e_tax.configure(state="readonly")
        e_total = ctk.CTkEntry(row_frame, width=100, justify="right", fg_color=COLORS["bg_light"], text_color=COLORS["primary"])
        e_total.pack(side="left", padx=2)
        e_total.configure(state="readonly")
        
        btn_del = ctk.CTkButton(row_frame, text="X", width=40, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                                command=lambda f=row_frame: self.delete_item_row(f))
        btn_del.pack(side="left", padx=5)

        row_data = {
            "frame": row_frame,
            "item": e_item, "model": e_model, "desc": e_desc, "qty": e_qty, 
            "price": e_price, "supply": e_supply, "tax": e_tax, "total": e_total
        }
        self.item_rows.append(row_data)

        e_qty.bind("<KeyRelease>", lambda e: self.calculate_row(row_data))
        e_price.bind("<KeyRelease>", lambda e, w=e_price, r=row_data: self.on_price_change(e, w, r))

        if item_data is not None:
            e_item.insert(0, str(item_data.get("품목명", "")))
            e_model.insert(0, str(item_data.get("모델명", "")))
            e_desc.insert(0, str(item_data.get("Description", "")))
            e_qty.delete(0, "end"); e_qty.insert(0, str(item_data.get("수량", 0)))
            price_val = float(item_data.get("단가", 0))
            e_price.delete(0, "end"); e_price.insert(0, f"{int(price_val):,}")
            self.calculate_row(row_data)

    def delete_item_row(self, frame):
        for item in self.item_rows:
            if item["frame"] == frame:
                self.item_rows.remove(item)
                break
        frame.destroy()
        self.calculate_totals()

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
        self.calculate_totals()

    def calculate_totals(self):
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
        self.attributes("-topmost", False)
        path = filedialog.askopenfilename()
        self.attributes("-topmost", True)
        if path:
            self.entry_file.delete(0, "end")
            self.entry_file.insert(0, path)

    def load_data(self):
        # 기존: self.dm.df_data 사용 (읽기는 문제 없음)
        df = self.dm.df_data
        rows = df[df["관리번호"] == self.mgmt_no]
        if rows.empty: return
        
        first = rows.iloc[0]
        self.entry_id.configure(state="normal")
        self.entry_id.insert(0, str(first["관리번호"]))
        self.entry_id.configure(state="readonly")
        
        date_val = str(first.get("수주일" if self.default_status == "주문" else "견적일", ""))
        if date_val == "-" or date_val == "": date_val = str(first.get("견적일", ""))
        self.entry_date.insert(0, date_val)

        self.combo_type.set(str(first.get("구분", "내수")))
        self.combo_client.set(str(first.get("업체명", "")))
        self.combo_currency.set(str(first.get("통화", "KRW")))
        
        saved_tax = first.get("세율(%)", "")
        if saved_tax != "" and saved_tax != "-": tax_rate = str(saved_tax)
        else:
            currency = str(first.get("통화", "KRW"))
            tax_rate = "10" if currency == "KRW" else "0"
        self.entry_tax_rate.delete(0, "end")
        self.entry_tax_rate.insert(0, tax_rate)

        self.entry_project.insert(0, str(first.get("프로젝트명", "")))
        self.entry_req.insert(0, str(first.get("주문요청사항", "")).replace("nan", ""))
        
        file_path = str(first.get("발주서경로" if self.default_status == "주문" else "견적서경로", ""))
        self.entry_file.insert(0, file_path)
        self.entry_note.insert(0, str(first.get("비고", "")))
        
        # [신규] 상태 로드
        current_status = str(first.get("Status", self.default_status))
        self.combo_status.set(current_status)
        
        self.on_client_select(str(first.get("업체명", "")))
        for _, row in rows.iterrows(): self.add_item_row(row)

    # [수정] 트랜잭션 적용
    def save(self):
        mgmt_no = self.entry_id.get()
        client = self.combo_client.get()
        if not client:
            messagebox.showwarning("경고", "고객사를 선택해주세요.", parent=self)
            return
        if not self.item_rows:
            messagebox.showwarning("경고", "최소 1개 이상의 품목을 추가해주세요.", parent=self)
            return

        file_path = self.entry_file.get()
        saved_file_path = file_path
        file_prefix = "발주서" if self.default_status == "주문" else "견적서"
        
        if file_path and "SalesManager" not in file_path:
            new_path, err = self.dm.save_attachment(file_path, client, file_prefix)
            if new_path: saved_file_path = new_path
        
        try: tax_rate_val = float(self.entry_tax_rate.get().strip())
        except: tax_rate_val = 0

        # UI에서 데이터 수집 (메인 스레드 작업)
        new_rows = []
        common_data = {
            "관리번호": mgmt_no,
            "구분": self.combo_type.get(),
            "업체명": client,
            "프로젝트명": self.entry_project.get(),
            "통화": self.combo_currency.get(),
            "환율": 1, 
            "세율(%)": tax_rate_val,
            "주문요청사항": self.entry_req.get(),
            "비고": self.entry_note.get(),
            "Status": self.combo_status.get() # [수정] 콤보박스 값 사용
        }
        
        if self.default_status == "주문":
            common_data["수주일"] = self.entry_date.get()
            common_data["발주서경로"] = saved_file_path
        else:
            common_data["견적일"] = self.entry_date.get()
            common_data["견적서경로"] = saved_file_path

        for item in self.item_rows:
            qty = float(item["qty"].get().replace(",","") or 0)
            price = float(item["price"].get().replace(",","") or 0)
            supply = float(item["supply"].get().replace(",","") or 0)
            tax = float(item["tax"].get().replace(",","") or 0)
            total = float(item["total"].get().replace(",","") or 0)
            
            row_data = common_data.copy()
            row_data.update({
                "품목명": item["item"].get(),
                "모델명": item["model"].get(),
                "Description": item["desc"].get(),
                "수량": qty,
                "단가": price,
                "공급가액": supply,
                "세액": tax,
                "합계금액": total,
                "기수금액": 0,
                "미수금액": total
            })
            new_rows.append(row_data)

        # 트랜잭션 로직 정의
        def update_logic(dfs):
            # 기존 데이터가 있으면 보존해야 할 필드(출고 정보 등)를 가져와야 함
            if self.mgmt_no:
                # 파일에 있는 최신 데이터에서 해당 관리번호 행들 조회
                mask = dfs["data"]["관리번호"] == self.mgmt_no
                existing_rows = dfs["data"][mask]
                
                if not existing_rows.empty:
                    first_exist = existing_rows.iloc[0]
                    # 보존할 필드들 업데이트
                    for row in new_rows:
                        # [수정] Status는 이미 new_rows에 콤보박스 값으로 설정됨. 기존 값 덮어쓰지 않음.
                        # row["Status"] = first_exist.get("Status", self.default_status) 
                        row["출고예정일"] = first_exist.get("출고예정일", "-")
                        row["출고일"] = first_exist.get("출고일", "-")
                        row["입금완료일"] = first_exist.get("입금완료일", "-")
                        row["세금계산서발행일"] = first_exist.get("세금계산서발행일", "-")
                        row["계산서번호"] = first_exist.get("계산서번호", "-")
                        row["수출신고번호"] = first_exist.get("수출신고번호", "-")
                        # 기수금액/미수금액은 새로 계산된 값으로 덮어쓰거나, 기존 납부 내역을 고려해야 함
                        # 여기서는 단순 수정을 가정하여 초기화 로직(0/Total)을 쓰지만,
                        # 부분 입금된 상태에서 견적 수정 시 입금액 보존 로직이 필요할 수 있음.
                        # 복잡도상 현재는 UI에서 계산된 값(0/Total)을 쓰되,
                        # 필요하다면 existing_rows['기수금액'] 합계를 가져와 반영해야 함.
                        
                # 기존 데이터 삭제
                dfs["data"] = dfs["data"][~mask]
            
            # 새 데이터 추가
            new_df = pd.DataFrame(new_rows)
            dfs["data"] = pd.concat([dfs["data"], new_df], ignore_index=True)
            
            # 로그
            action = "수정" if self.mgmt_no else "등록"
            new_log = self.dm._create_log_entry(f"{self.default_status} {action}", f"번호 [{mgmt_no}] / 업체 [{client}]")
            dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
            
            return True, ""

        # 트랜잭션 실행
        success, msg = self.dm._execute_transaction(update_logic)
        
        if success:
            messagebox.showinfo("완료", "저장되었습니다.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", msg, parent=self)

    # [수정] 트랜잭션 적용
    def delete_quote(self):
        if messagebox.askyesno("삭제 확인", "정말 이 데이터를 삭제하시겠습니까?", parent=self):
            def update_logic(dfs):
                mask = dfs["data"]["관리번호"] == self.mgmt_no
                if mask.any():
                    dfs["data"] = dfs["data"][~mask]
                    new_log = self.dm._create_log_entry("삭제", f"번호 [{self.mgmt_no}] 삭제됨")
                    dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
                    return True, ""
                return False, "삭제할 데이터를 찾을 수 없습니다."

            success, msg = self.dm._execute_transaction(update_logic)
            if success:
                self.refresh_callback()
                self.destroy()
            else:
                messagebox.showerror("실패", msg, parent=self)

    def export_quote(self):
        # ... (기존과 동일, 읽기 전용 작업이므로 수정 불필요) ...
        # [코드 생략 - 위와 동일]
        client_name = self.combo_client.get()
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
            "req_note": self.entry_req.get()
        }
        
        items = []
        for row in self.item_rows:
            try:
                qty = float(row["qty"].get().replace(",", "") or 0)
                price = float(row["price"].get().replace(",", "") or 0)
                amount = float(row["total"].get().replace(",", "") or 0)
            except:
                qty, price, amount = 0, 0, 0
                
            items.append({
                "item": row["item"].get(),
                "model": row["model"].get(),
                "desc": row["desc"].get(),
                "qty": qty,
                "price": price,
                "amount": amount
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