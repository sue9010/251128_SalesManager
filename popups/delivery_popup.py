import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk
import pandas as pd

from config import Config
from styles import COLORS, FONT_FAMILY, FONTS


class DeliveryPopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, refresh_callback, row_indices):
        super().__init__(parent)
        self.dm = data_manager
        self.refresh_callback = refresh_callback
        
        if not isinstance(row_indices, list):
            self.row_indices = [row_indices]
        else:
            self.row_indices = row_indices
            
        self.target_rows = []
        for idx in self.row_indices:
            self.target_rows.append(self.dm.df_data.loc[idx])
            
        self.first_row = self.target_rows[0]
        self.mgmt_no = self.first_row["관리번호"]
        self.client_name = self.first_row["업체명"]
        
        count = len(self.target_rows)
        title_text = f"일괄 납품(출고) 처리 - {self.client_name} 외 {count-1}건" if count > 1 else f"납품(출고) 처리 - {self.mgmt_no}"
        
        self.title(title_text)
        self.geometry("700x600")
        self.item_widgets = [] 
        
        self.create_widgets()
        self.load_client_info()
        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)

    # ... (create_widgets, load_client_info 생략 - 기존과 동일) ...
    def create_widgets(self):
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(top_frame, text="출고일 (Factory Out)", font=FONTS["main_bold"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_date = ctk.CTkEntry(top_frame, width=150)
        self.entry_date.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        ctk.CTkLabel(top_frame, text="송장번호 (Invoice No)", font=FONTS["main_bold"]).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.entry_invoice = ctk.CTkEntry(top_frame, width=200)
        self.entry_invoice.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(top_frame, text="운송 방법", font=FONTS["main_bold"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_shipping = ctk.CTkEntry(top_frame, width=150)
        self.entry_shipping.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(top_frame, text="※ 선적일(On Board)은 추후 별도 관리", font=FONTS["small"], text_color=COLORS["text_dim"]).grid(row=1, column=2, columnspan=2, sticky="w", padx=5)

        list_label = ctk.CTkLabel(self, text=f"출고 대상 품목 ({len(self.target_rows)}건)", font=FONTS["header"])
        list_label.pack(anchor="w", padx=20, pady=(10, 5))
        
        header_frame = ctk.CTkFrame(self, height=30, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x", padx=20)
        headers = ["관리번호", "모델명", "잔여 수량", "출고 수량"]
        widths = [150, 200, 100, 100]
        for h, w in zip(headers, widths):
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["small"]).pack(side="left", padx=2)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=5)
        
        for i, row in enumerate(self.target_rows):
            row_frame = ctk.CTkFrame(scroll, fg_color="transparent", height=35)
            row_frame.pack(fill="x", pady=2)
            ctk.CTkLabel(row_frame, text=row["관리번호"], width=150, anchor="w").pack(side="left", padx=2)
            ctk.CTkLabel(row_frame, text=row["모델명"], width=200, anchor="w").pack(side="left", padx=2)
            current_qty = float(row["수량"])
            ctk.CTkLabel(row_frame, text=f"{current_qty:g}", width=100).pack(side="left", padx=2)
            e_qty = ctk.CTkEntry(row_frame, width=100, justify="center")
            e_qty.pack(side="left", padx=2)
            e_qty.insert(0, f"{current_qty:g}")
            
            self.item_widgets.append({
                "index": self.row_indices[i], 
                "current_qty": current_qty,
                "entry": e_qty,
                "row_data": row
            })

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20, side="bottom")
        ctk.CTkButton(btn_frame, text="일괄 출고 처리", command=self.save, fg_color=COLORS["success"], hover_color="#26A65B", width=150, height=40).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="취소", command=self.destroy, fg_color=COLORS["bg_light"], text_color=COLORS["text"], width=80, height=40).pack(side="right", padx=5)

    def load_client_info(self):
        df_client = self.dm.df_clients
        client_row = df_client[df_client["업체명"] == self.client_name]
        if not client_row.empty:
            shipping_method = str(client_row.iloc[0].get("운송방법", ""))
            if shipping_method and shipping_method != "nan":
                self.entry_shipping.delete(0, "end")
                self.entry_shipping.insert(0, shipping_method)

    # [수정] 트랜잭션 적용
    def save(self):
        date_str = self.entry_date.get()
        invoice_no = self.entry_invoice.get()
        shipping_method = self.entry_shipping.get()
        
        if not date_str:
            messagebox.showwarning("경고", "출고일을 입력하세요.", parent=self)
            return

        # UI에서 입력값 검증 및 데이터 준비
        update_requests = []
        for item in self.item_widgets:
            idx = item["index"]
            row = item["row_data"]
            current_qty = item["current_qty"]
            
            try: deliver_qty = float(item["entry"].get())
            except:
                messagebox.showerror("오류", f"수량은 숫자여야 합니다. ({row['모델명']})", parent=self)
                return
            
            if deliver_qty <= 0 or deliver_qty > current_qty:
                messagebox.showerror("오류", f"수량 범위 오류: {row['모델명']}", parent=self)
                return
            
            update_requests.append({
                "idx": idx,
                "row": row,
                "current_qty": current_qty,
                "deliver_qty": deliver_qty
            })

        def update_logic(dfs):
            for req in update_requests:
                idx = req["idx"]
                row = dfs["data"].loc[idx] # 파일에서 최신 행 가져오기
                deliver_qty = req["deliver_qty"]
                current_qty = float(row["수량"]) # 파일 상의 현재 수량 확인 (동시성 체크)
                
                # 주의: 만약 파일에서 수량이 이미 변경되어 UI와 다르다면? 
                # 여기선 UI 기준이 아니라 파일 기준 current_qty로 다시 계산하는게 안전하지만, 
                # 사용자가 보고 있던 수량(req['current_qty'])과 다르면 로직이 꼬일 수 있음.
                # 단순화를 위해 파일 값을 신뢰하되, 분할 로직 적용
                
                if deliver_qty >= current_qty: # 전체 납품
                    dfs["data"].at[idx, "Status"] = "납품완료/입금대기"
                    dfs["data"].at[idx, "출고일"] = date_str
                    dfs["data"].at[idx, "송장번호"] = invoice_no
                    dfs["data"].at[idx, "운송방법"] = shipping_method
                else:
                    # 부분 납품 (행 분할)
                    remain_qty = current_qty - deliver_qty
                    try: price = float(row["단가"])
                    except: price = 0
                    is_domestic = (row["구분"] == "내수")
                    
                    # 1. 기존 행 (잔여) 업데이트
                    remain_supply = remain_qty * price
                    remain_tax = remain_supply * 0.1 if is_domestic else 0
                    
                    dfs["data"].at[idx, "수량"] = remain_qty
                    dfs["data"].at[idx, "공급가액"] = remain_supply
                    dfs["data"].at[idx, "세액"] = remain_tax
                    dfs["data"].at[idx, "합계금액"] = remain_supply + remain_tax
                    dfs["data"].at[idx, "미수금액"] = remain_supply + remain_tax
                    
                    # 2. 새 행 (출고된 것) 추가
                    new_row = row.copy()
                    new_supply = deliver_qty * price
                    new_tax = new_supply * 0.1 if is_domestic else 0
                    
                    new_row["수량"] = deliver_qty
                    new_row["공급가액"] = new_supply
                    new_row["세액"] = new_tax
                    new_row["합계금액"] = new_supply + new_tax
                    new_row["미수금액"] = new_supply + new_tax
                    new_row["Status"] = "납품완료/입금대기"
                    new_row["출고일"] = date_str
                    new_row["송장번호"] = invoice_no
                    new_row["운송방법"] = shipping_method
                    new_row["선적일"] = "-"
                    
                    new_df = pd.DataFrame([new_row])
                    dfs["data"] = pd.concat([dfs["data"], new_df], ignore_index=True)
            
            # 로그
            new_log = self.dm._create_log_entry("일괄 출고", f"{len(update_requests)}건 처리 완료")
            dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
            return True, ""

        success, msg = self.dm._execute_transaction(update_logic)
        
        if success:
            messagebox.showinfo("성공", "출고 처리가 완료되었습니다.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", msg, parent=self)