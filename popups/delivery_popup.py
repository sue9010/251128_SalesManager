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
        
        # 다중 선택 지원을 위해 리스트로 변환
        if not isinstance(row_indices, list):
            self.row_indices = [row_indices]
        else:
            self.row_indices = row_indices
            
        self.target_rows = []
        for idx in self.row_indices:
            self.target_rows.append(self.dm.df_data.loc[idx])
            
        # 대표 정보 (첫 번째 항목 기준)
        self.first_row = self.target_rows[0]
        self.mgmt_no = self.first_row["관리번호"]
        self.client_name = self.first_row["업체명"]
        
        count = len(self.target_rows)
        title_text = f"일괄 납품(출고) 처리 - {self.client_name} 외 {count-1}건" if count > 1 else f"납품(출고) 처리 - {self.mgmt_no}"
        
        self.title(title_text)
        self.geometry("700x600")
        
        self.item_widgets = [] # 각 행의 입력 위젯 저장
        
        self.create_widgets()
        self.load_client_info()
        
        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)

    def create_widgets(self):
        # 1. 상단 공통 정보 (출고일, 송장, 운송)
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=20)
        
        # 출고일 (Release Date)
        ctk.CTkLabel(top_frame, text="출고일 (Factory Out)", font=FONTS["main_bold"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_date = ctk.CTkEntry(top_frame, width=150)
        self.entry_date.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # 송장 번호 (Invoice No)
        ctk.CTkLabel(top_frame, text="송장번호 (Invoice No)", font=FONTS["main_bold"]).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.entry_invoice = ctk.CTkEntry(top_frame, width=200)
        self.entry_invoice.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # 운송 방법
        ctk.CTkLabel(top_frame, text="운송 방법", font=FONTS["main_bold"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_shipping = ctk.CTkEntry(top_frame, width=150)
        self.entry_shipping.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # 선적일 안내
        ctk.CTkLabel(top_frame, text="※ 선적일(On Board)은 추후 별도 관리", font=FONTS["small"], text_color=COLORS["text_dim"]).grid(row=1, column=2, columnspan=2, sticky="w", padx=5)

        # 2. 품목 리스트 (스크롤)
        list_label = ctk.CTkLabel(self, text=f"출고 대상 품목 ({len(self.target_rows)}건)", font=FONTS["header"])
        list_label.pack(anchor="w", padx=20, pady=(10, 5))
        
        # 헤더
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
            
            # 정보 표시
            ctk.CTkLabel(row_frame, text=row["관리번호"], width=150, anchor="w").pack(side="left", padx=2)
            ctk.CTkLabel(row_frame, text=row["모델명"], width=200, anchor="w").pack(side="left", padx=2)
            
            current_qty = float(row["수량"])
            ctk.CTkLabel(row_frame, text=f"{current_qty:g}", width=100).pack(side="left", padx=2)
            
            # 출고 수량 입력 (기본값: 전체)
            e_qty = ctk.CTkEntry(row_frame, width=100, justify="center")
            e_qty.pack(side="left", padx=2)
            e_qty.insert(0, f"{current_qty:g}")
            
            self.item_widgets.append({
                "index": self.row_indices[i], # 원본 데이터 인덱스
                "current_qty": current_qty,
                "entry": e_qty,
                "row_data": row
            })

        # 3. 하단 버튼
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20, side="bottom")
        
        ctk.CTkButton(btn_frame, text="일괄 출고 처리", command=self.save,
                      fg_color=COLORS["success"], hover_color="#26A65B", width=150, height=40).pack(side="right", padx=5)
        
        ctk.CTkButton(btn_frame, text="취소", command=self.destroy,
                      fg_color=COLORS["bg_light"], text_color=COLORS["text"], width=80, height=40).pack(side="right", padx=5)

    def load_client_info(self):
        """고객사의 기본 운송방법 불러오기"""
        df_client = self.dm.df_clients
        client_row = df_client[df_client["업체명"] == self.client_name]
        
        if not client_row.empty:
            shipping_method = str(client_row.iloc[0].get("운송방법", ""))
            if shipping_method and shipping_method != "nan":
                self.entry_shipping.delete(0, "end")
                self.entry_shipping.insert(0, shipping_method)

    def save(self):
        date_str = self.entry_date.get()
        invoice_no = self.entry_invoice.get()
        shipping_method = self.entry_shipping.get()
        
        if not date_str:
            messagebox.showwarning("경고", "출고일을 입력하세요.", parent=self)
            return

        # 일괄 처리 로직
        for item in self.item_widgets:
            idx = item["index"]
            row = item["row_data"]
            current_qty = item["current_qty"]
            
            try:
                deliver_qty = float(item["entry"].get())
            except:
                messagebox.showerror("오류", f"수량은 숫자여야 합니다. ({row['모델명']})", parent=self)
                return
            
            if deliver_qty <= 0 or deliver_qty > current_qty:
                messagebox.showerror("오류", f"수량 범위 오류: {row['모델명']}", parent=self)
                return
            
            # 처리 로직 (전체 vs 부분)
            if deliver_qty == current_qty:
                # 전체 납품
                self.dm.df_data.at[idx, "Status"] = "납품완료/입금대기"
                self.dm.df_data.at[idx, "출고일"] = date_str
                self.dm.df_data.at[idx, "송장번호"] = invoice_no
                self.dm.df_data.at[idx, "운송방법"] = shipping_method
            else:
                # 부분 납품 (행 분할)
                remain_qty = current_qty - deliver_qty
                price = float(row["단가"])
                is_domestic = (row["구분"] == "내수")
                
                # 1. 기존 행 (잔여) 업데이트
                remain_supply = remain_qty * price
                remain_tax = remain_supply * 0.1 if is_domestic else 0
                
                self.dm.df_data.at[idx, "수량"] = remain_qty
                self.dm.df_data.at[idx, "공급가액"] = remain_supply
                self.dm.df_data.at[idx, "세액"] = remain_tax
                self.dm.df_data.at[idx, "합계금액"] = remain_supply + remain_tax
                self.dm.df_data.at[idx, "미수금액"] = remain_supply + remain_tax
                
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
                # 선적일은 비워둠 (추후 관리)
                new_row["선적일"] = "-"
                
                # concat을 사용하여 추가
                new_df = pd.DataFrame([new_row])
                self.dm.df_data = pd.concat([self.dm.df_data, new_df], ignore_index=True)

        # 저장 완료
        success, msg = self.dm.save_to_excel()
        if success:
            self.dm.add_log("일괄 출고", f"{len(self.item_widgets)}건 처리 완료")
            messagebox.showinfo("성공", "출고 처리가 완료되었습니다.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", msg, parent=self)