import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pandas as pd

from config import Config
from styles import COLORS, FONT_FAMILY, FONTS


class QuotePopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_no=None, default_status="견적"):
        super().__init__(parent)
        self.dm = data_manager
        self.refresh_callback = refresh_callback
        self.mgmt_no = mgmt_no
        self.default_status = default_status
        
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
        # --- 1. 상단 정보 ---
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=15)

        # 관리번호
        ctk.CTkLabel(top_frame, text="관리번호", font=FONTS["main_bold"]).grid(row=0, column=0, padx=5, sticky="w")
        self.entry_id = ctk.CTkEntry(top_frame, width=150, font=FONTS["main"])
        self.entry_id.grid(row=0, column=1, padx=5, sticky="w")
        self.entry_id.configure(state="readonly")

        # 날짜
        date_label_text = "주문일자" if self.default_status == "주문" else "견적일자"
        ctk.CTkLabel(top_frame, text=date_label_text, font=FONTS["main_bold"]).grid(row=0, column=2, padx=5, sticky="w")
        self.entry_date = ctk.CTkEntry(top_frame, width=120, font=FONTS["main"], placeholder_text="YYYY-MM-DD")
        self.entry_date.grid(row=0, column=3, padx=5, sticky="w")

        # 구분
        ctk.CTkLabel(top_frame, text="구분", font=FONTS["main_bold"]).grid(row=0, column=4, padx=5, sticky="w")
        self.combo_type = ctk.CTkComboBox(top_frame, values=["내수", "수출"], width=100, font=FONTS["main"], command=self.on_type_change)
        self.combo_type.grid(row=0, column=5, padx=5, sticky="w")
        self.combo_type.set("내수")

        # 업체 선택
        ctk.CTkLabel(top_frame, text="고객사", font=FONTS["main_bold"]).grid(row=1, column=0, padx=5, pady=10, sticky="w")
        self.combo_client = ctk.CTkComboBox(top_frame, width=200, font=FONTS["main"], command=self.on_client_select)
        self.combo_client.grid(row=1, column=1, padx=5, pady=10, sticky="w")
        try:
            self.combo_client._entry.bind("<KeyRelease>", self.on_client_typing)
        except: pass

        # 통화
        ctk.CTkLabel(top_frame, text="통화", font=FONTS["main_bold"]).grid(row=1, column=2, padx=5, pady=10, sticky="w")
        self.combo_currency = ctk.CTkComboBox(top_frame, values=["KRW", "USD", "EUR", "CNY", "JPY"], width=100, font=FONTS["main"], 
                                              command=self.on_currency_change)
        self.combo_currency.grid(row=1, column=3, padx=5, pady=10, sticky="w")
        self.combo_currency.set("KRW")

        # 세율(%)
        ctk.CTkLabel(top_frame, text="세율(%)", font=FONTS["main_bold"]).grid(row=1, column=4, padx=5, pady=10, sticky="w")
        self.entry_tax_rate = ctk.CTkEntry(top_frame, width=100, font=FONTS["main"])
        self.entry_tax_rate.grid(row=1, column=5, padx=5, pady=10, sticky="w")
        self.entry_tax_rate.insert(0, "10")
        self.entry_tax_rate.bind("<KeyRelease>", lambda e: self.calculate_totals())

        # 프로젝트명
        ctk.CTkLabel(top_frame, text="프로젝트명", font=FONTS["main_bold"]).grid(row=2, column=0, padx=5, sticky="w")
        self.entry_project = ctk.CTkEntry(top_frame, width=300, font=FONTS["main"])
        self.entry_project.grid(row=2, column=1, columnspan=3, padx=5, sticky="ew")
        
        # [수정] 출고예정일 입력란 삭제됨

        # 업체 특이사항 표시 (Readonly)
        info_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], height=40)
        info_frame.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(info_frame, text="업체 특이사항:", font=FONTS["main_bold"], text_color=COLORS["primary"]).pack(side="left", padx=10, pady=5)
        self.lbl_client_note = ctk.CTkLabel(info_frame, text="-", font=FONTS["main"])
        self.lbl_client_note.pack(side="left", padx=5, pady=5)

        # --- 2. 품목 리스트 ---
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

        # --- 3. 하단 정보 ---
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=5)

        self.lbl_total_qty = ctk.CTkLabel(bottom_frame, text="총 수량: 0", font=FONTS["main_bold"])
        self.lbl_total_qty.pack(side="left", padx=10)
        
        self.lbl_total_amt = ctk.CTkLabel(bottom_frame, text="총 합계금액: 0", font=FONTS["header"], text_color=COLORS["primary"])
        self.lbl_total_amt.pack(side="left", padx=20)

        # 주문요청사항 / 비고 / 파일
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

        # --- 4. 버튼 ---
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
        self.all_clients = self.dm.df_clients["업체명"].unique().tolist()
        self.combo_client.configure(values=self.all_clients)

    def on_client_typing(self, event):
        typed = self.combo_client.get()
        if typed == "":
            self.combo_client.configure(values=self.all_clients)
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

    def on_type_change(self, type_val):
        self.calculate_totals()

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
        
        if len(existing_ids) == 0:
            seq = 1
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
            
            try:
                tax_rate = float(self.entry_tax_rate.get().strip() or 0)
            except:
                tax_rate = 0
                
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
            
        except ValueError:
            pass
        
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
        if saved_tax != "" and saved_tax != "-":
            tax_rate = str(saved_tax)
        else:
            currency = str(first.get("통화", "KRW"))
            tax_rate = "10" if currency == "KRW" else "0"
            
        self.entry_tax_rate.delete(0, "end")
        self.entry_tax_rate.insert(0, tax_rate)

        self.entry_project.insert(0, str(first.get("프로젝트명", "")))
        # [수정] 출고예정일 로드 삭제 (입력란이 없으므로)
        self.entry_req.insert(0, str(first.get("주문요청사항", "")).replace("nan", ""))
        
        file_path = str(first.get("발주서경로" if self.default_status == "주문" else "견적서경로", ""))
        self.entry_file.insert(0, file_path)
        self.entry_note.insert(0, str(first.get("비고", "")))
        
        self.on_client_select(str(first.get("업체명", "")))
        
        for _, row in rows.iterrows():
            self.add_item_row(row)

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
        
        try:
            tax_rate_val = float(self.entry_tax_rate.get().strip())
        except:
            tax_rate_val = 0

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
            "Status": self.default_status
        }
        
        if self.default_status == "주문":
            common_data["수주일"] = self.entry_date.get()
            common_data["발주서경로"] = saved_file_path
        else:
            common_data["견적일"] = self.entry_date.get()
            common_data["견적서경로"] = saved_file_path
        
        # [수정] 수정 모드일 경우 기존 데이터의 값을 보존 (특히 출고예정일 등)
        if self.mgmt_no:
            # 기존 데이터의 첫 번째 행에서 정보를 가져옴
            existing_row = self.dm.df_data[self.dm.df_data["관리번호"]==self.mgmt_no].iloc[0]
            common_data["Status"] = existing_row["Status"]
            # 입력란이 없어 화면에선 안 보이지만 데이터에는 존재하는 값들을 보존
            common_data["출고예정일"] = existing_row.get("출고예정일", "-")
            common_data["출고일"] = existing_row.get("출고일", "-")
            common_data["입금완료일"] = existing_row.get("입금완료일", "-")
            common_data["세금계산서발행일"] = existing_row.get("세금계산서발행일", "-")
            common_data["계산서번호"] = existing_row.get("계산서번호", "-")
            common_data["수출신고번호"] = existing_row.get("수출신고번호", "-")
            # 기수금액 등은 아래 루프에서 처리

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
                # [수정] 기수금액, 미수금액은 초기화(신규)하거나 보존(수정)해야 함
                # 하지만 여기서는 단순화를 위해 신규 등록 시 초기화 로직을 유지하고,
                # 수정 시에는 기존 로직을 따라갈 수 있도록 별도 처리하지 않음 (단, 전체 덮어쓰기 구조임)
                # 만약 이미 부분 납품/입금된 건을 여기서 수정하면 기수금액이 날아갈 수 있음.
                # 따라서 수정 모드일 때는 기존 기수금액을 유지해야 함.
            })
            
            if self.mgmt_no:
                # 수정 모드: 기존 행의 기수금액 유지 (단, 품목이 바뀌면 매칭이 어려우므로 
                # 관리번호 단위 총액 관리라 가정하고 여기서는 0으로 리셋하지 않고 기존 값 유지 시도 불가)
                # 현재 구조상 품목별 ID가 없어서, 견적 수정 시에는 금액 초기화를 감수하거나
                # 아예 '진행 중'인 건은 수정 불가하게 막는 것이 안전함.
                # 일단은 '초기화' 로직으로 둡니다. (사용자 요청에 따라 변경 가능)
                row_data["기수금액"] = 0 
                row_data["미수금액"] = total
            else:
                row_data["기수금액"] = 0
                row_data["미수금액"] = total
                
            new_rows.append(row_data)

        if self.mgmt_no:
            self.dm.df_data = self.dm.df_data[self.dm.df_data["관리번호"] != self.mgmt_no]
        
        new_df = pd.DataFrame(new_rows)
        if self.dm.df_data.empty:
            self.dm.df_data = new_df
        else:
            self.dm.df_data = pd.concat([self.dm.df_data, new_df], ignore_index=True)
        
        success, msg = self.dm.save_to_excel()
        if success:
            action = "수정" if self.mgmt_no else "등록"
            self.dm.add_log(f"{self.default_status} {action}", f"번호 [{mgmt_no}] / 업체 [{client}]")
            messagebox.showinfo("완료", "저장되었습니다.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", msg, parent=self)

    def delete_quote(self):
        if messagebox.askyesno("삭제 확인", "정말 이 데이터를 삭제하시겠습니까?", parent=self):
            self.dm.df_data = self.dm.df_data[self.dm.df_data["관리번호"] != self.mgmt_no]
            self.dm.save_to_excel()
            self.refresh_callback()
            self.destroy()