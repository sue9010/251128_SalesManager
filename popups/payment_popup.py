import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk
import pandas as pd

from config import Config
from styles import COLORS, FONT_FAMILY, FONTS


class PaymentPopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, refresh_callback, row_index):
        super().__init__(parent)
        self.dm = data_manager
        self.refresh_callback = refresh_callback
        self.row_index = row_index
        
        self.target_row = self.dm.df_data.loc[self.row_index]
        self.mgmt_no = self.target_row["관리번호"]
        self.is_export = (self.target_row.get("구분") == "수출")
        
        self.title(f"입금(수금) 처리 - {self.mgmt_no}")
        self.geometry("500x650")
        
        self.create_widgets()
        
        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)

    def create_widgets(self):
        # 1. 상단 금액 정보 (카드 형태)
        card_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], corner_radius=10)
        card_frame.pack(fill="x", padx=20, pady=20)
        
        total = float(self.target_row.get("합계금액", 0) or 0)
        paid = float(self.target_row.get("기수금액", 0) or 0)
        unpaid = float(self.target_row.get("미수금액", 0) or 0)
        
        self._add_amount_row(card_frame, "총 합계금액", total, 0)
        self._add_amount_row(card_frame, "기수금액", paid, 1)
        
        # 미수금 강조
        line = ctk.CTkFrame(card_frame, height=2, fg_color=COLORS["border"])
        line.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=5)
        
        ctk.CTkLabel(card_frame, text="남은 미수금", font=FONTS["header"], text_color=COLORS["danger"]).grid(row=3, column=0, padx=15, pady=(5, 15), sticky="w")
        ctk.CTkLabel(card_frame, text=f"{unpaid:,.0f}", font=FONTS["title"], text_color=COLORS["danger"]).grid(row=3, column=1, padx=15, pady=(5, 15), sticky="e")

        # 2. 입금 입력 폼
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20)
        
        # 입금액
        ctk.CTkLabel(form_frame, text="입금액", font=FONTS["main_bold"]).pack(anchor="w", pady=(10, 5))
        self.entry_pay = ctk.CTkEntry(form_frame, width=200, font=FONTS["header"])
        self.entry_pay.pack(anchor="w")
        self.entry_pay.insert(0, f"{unpaid:.0f}") # 기본값: 전액
        
        # 입금일
        ctk.CTkLabel(form_frame, text="입금일", font=FONTS["main_bold"]).pack(anchor="w", pady=(10, 5))
        self.entry_date = ctk.CTkEntry(form_frame, width=200)
        self.entry_date.pack(anchor="w")
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # 증빙 정보 (내수: 세금계산서 / 수출: 신고번호)
        proof_label = "수출신고번호" if self.is_export else "세금계산서 승인번호"
        date_label = "수출신고일" if self.is_export else "세금계산서 발행일"
        
        ctk.CTkLabel(form_frame, text=f"{proof_label} (선택)", font=FONTS["main_bold"]).pack(anchor="w", pady=(15, 5))
        self.entry_tax_no = ctk.CTkEntry(form_frame, width=300)
        self.entry_tax_no.pack(anchor="w")
        # 기존 값 불러오기
        col_name = "수출신고번호" if self.is_export else "계산서번호"
        self.entry_tax_no.insert(0, str(self.target_row.get(col_name, "")).replace("nan", ""))

        ctk.CTkLabel(form_frame, text=f"{date_label} (선택)", font=FONTS["main_bold"]).pack(anchor="w", pady=(10, 5))
        self.entry_tax_date = ctk.CTkEntry(form_frame, width=200)
        self.entry_tax_date.pack(anchor="w")
        self.entry_tax_date.insert(0, str(self.target_row.get("세금계산서발행일", "")).replace("nan", ""))

        # 3. 버튼
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20, side="bottom")
        
        ctk.CTkButton(btn_frame, text="입금 등록", command=self.save,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], width=120, height=40).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="취소", command=self.destroy,
                      fg_color=COLORS["bg_light"], text_color=COLORS["text"], width=80, height=40).pack(side="right", padx=5)

    def _add_amount_row(self, parent, label, value, r):
        ctk.CTkLabel(parent, text=label, font=FONTS["main"], text_color=COLORS["text_dim"]).grid(row=r, column=0, padx=15, pady=5, sticky="w")
        ctk.CTkLabel(parent, text=f"{value:,.0f}", font=FONTS["main_bold"]).grid(row=r, column=1, padx=15, pady=5, sticky="e")
        parent.grid_columnconfigure(1, weight=1)

    def save(self):
        try:
            pay_amt = float(self.entry_pay.get().replace(",", ""))
        except ValueError:
            messagebox.showerror("오류", "입금액은 숫자여야 합니다.", parent=self)
            return
            
        if pay_amt <= 0:
            messagebox.showerror("오류", "입금액은 0보다 커야 합니다.", parent=self)
            return

        pay_date = self.entry_date.get()
        tax_no = self.entry_tax_no.get()
        tax_date = self.entry_tax_date.get()
        
        # 데이터 업데이트
        current_paid = float(self.target_row.get("기수금액", 0) or 0)
        new_paid = current_paid + pay_amt
        total = float(self.target_row.get("합계금액", 0) or 0)
        new_unpaid = total - new_paid
        
        if abs(new_unpaid) < 1: new_unpaid = 0 # 오차 보정
        
        self.dm.df_data.at[self.row_index, "기수금액"] = new_paid
        self.dm.df_data.at[self.row_index, "미수금액"] = new_unpaid
        
        # 증빙 정보 저장
        col_name = "수출신고번호" if self.is_export else "계산서번호"
        self.dm.df_data.at[self.row_index, col_name] = tax_no
        self.dm.df_data.at[self.row_index, "세금계산서발행일"] = tax_date
        
        msg = f"입금 {pay_amt:,.0f}원 등록 완료."
        
        # 완납 체크
        if new_unpaid <= 0:
            self.dm.df_data.at[self.row_index, "Status"] = "완료"
            self.dm.df_data.at[self.row_index, "입금완료일"] = pay_date
            msg += "\n[완납] 상태가 '완료'로 변경되었습니다."
        
        success, err_msg = self.dm.save_to_excel()
        if success:
            self.dm.add_log("입금 등록", f"번호 [{self.mgmt_no}] 금액: {pay_amt}")
            messagebox.showinfo("성공", msg, parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", err_msg, parent=self)