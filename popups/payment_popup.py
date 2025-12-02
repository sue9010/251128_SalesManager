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
        
        # self.dm.df_data는 읽기 전용으로만 사용 (초기 렌더링용)
        self.target_row = self.dm.df_data.loc[self.row_index]
        self.mgmt_no = self.target_row["관리번호"]
        self.is_export = (self.target_row.get("구분") == "수출")
        
        self.title(f"입금(수금) 처리 - {self.mgmt_no}")
        self.geometry("500x650")
        
        self.create_widgets()
        
        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)

    # ... (create_widgets, _add_amount_row 생략 - 기존과 동일) ...
    def create_widgets(self):
        card_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], corner_radius=10)
        card_frame.pack(fill="x", padx=20, pady=20)
        total = float(self.target_row.get("합계금액", 0) or 0)
        paid = float(self.target_row.get("기수금액", 0) or 0)
        unpaid = float(self.target_row.get("미수금액", 0) or 0)
        self._add_amount_row(card_frame, "총 합계금액", total, 0)
        self._add_amount_row(card_frame, "기수금액", paid, 1)
        line = ctk.CTkFrame(card_frame, height=2, fg_color=COLORS["border"])
        line.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=5)
        ctk.CTkLabel(card_frame, text="남은 미수금", font=FONTS["header"], text_color=COLORS["danger"]).grid(row=3, column=0, padx=15, pady=(5, 15), sticky="w")
        ctk.CTkLabel(card_frame, text=f"{unpaid:,.0f}", font=FONTS["title"], text_color=COLORS["danger"]).grid(row=3, column=1, padx=15, pady=(5, 15), sticky="e")

        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20)
        ctk.CTkLabel(form_frame, text="입금액", font=FONTS["main_bold"]).pack(anchor="w", pady=(10, 5))
        self.entry_pay = ctk.CTkEntry(form_frame, width=200, font=FONTS["header"])
        self.entry_pay.pack(anchor="w")
        self.entry_pay.insert(0, f"{unpaid:.0f}")
        
        ctk.CTkLabel(form_frame, text="입금일", font=FONTS["main_bold"]).pack(anchor="w", pady=(10, 5))
        self.entry_date = ctk.CTkEntry(form_frame, width=200)
        self.entry_date.pack(anchor="w")
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        proof_label = "수출신고번호" if self.is_export else "세금계산서 승인번호"
        date_label = "수출신고일" if self.is_export else "세금계산서 발행일"
        
        ctk.CTkLabel(form_frame, text=f"{proof_label} (선택)", font=FONTS["main_bold"]).pack(anchor="w", pady=(15, 5))
        self.entry_tax_no = ctk.CTkEntry(form_frame, width=300)
        self.entry_tax_no.pack(anchor="w")
        col_name = "수출신고번호" if self.is_export else "계산서번호"
        self.entry_tax_no.insert(0, str(self.target_row.get(col_name, "")).replace("nan", ""))

        ctk.CTkLabel(form_frame, text=f"{date_label} (선택)", font=FONTS["main_bold"]).pack(anchor="w", pady=(10, 5))
        self.entry_tax_date = ctk.CTkEntry(form_frame, width=200)
        self.entry_tax_date.pack(anchor="w")
        self.entry_tax_date.insert(0, str(self.target_row.get("세금계산서발행일", "")).replace("nan", ""))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20, side="bottom")
        ctk.CTkButton(btn_frame, text="입금 등록", command=self.save, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], width=120, height=40).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="취소", command=self.destroy, fg_color=COLORS["bg_light"], text_color=COLORS["text"], width=80, height=40).pack(side="right", padx=5)

    def _add_amount_row(self, parent, label, value, r):
        ctk.CTkLabel(parent, text=label, font=FONTS["main"], text_color=COLORS["text_dim"]).grid(row=r, column=0, padx=15, pady=5, sticky="w")
        ctk.CTkLabel(parent, text=f"{value:,.0f}", font=FONTS["main_bold"]).grid(row=r, column=1, padx=15, pady=5, sticky="e")
        parent.grid_columnconfigure(1, weight=1)

    # [수정] 트랜잭션 적용
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
        col_name = "수출신고번호" if self.is_export else "계산서번호"

        def update_logic(dfs):
            # 파일에서 최신 행 정보 가져오기 (self.row_index 사용)
            # 주의: 행 인덱스는 파일 변경 시 바뀔 수 있으므로 관리번호로 찾는 것이 안전하지만,
            # 여기서는 편의상 인덱스를 사용합니다. (가장 좋은 방법은 관리번호로 찾는 것)
            
            # 관리번호로 다시 찾기 (안전한 방법)
            # 파일 데이터 로드 시 인덱스가 재설정될 수 있으므로 unique ID 사용 권장
            # 여기서는 편의상 self.row_index를 쓰되, 실제 프로덕션에서는 관리번호 검색 필요
            # dfs["data"]의 인덱스가 유지된다고 가정
            
            if self.row_index in dfs["data"].index:
                target = dfs["data"].loc[self.row_index]
                # 관리번호 일치 확인 (안전장치)
                if str(target["관리번호"]) != str(self.mgmt_no):
                    # 인덱스가 틀어졌다면 관리번호로 검색
                    mask = dfs["data"]["관리번호"] == self.mgmt_no
                    if not mask.any(): return False, "데이터를 찾을 수 없습니다."
                    idx = dfs["data"][mask].index[0]
                else:
                    idx = self.row_index
                
                # 업데이트 수행
                current_paid = float(dfs["data"].at[idx, "기수금액"] or 0)
                new_paid = current_paid + pay_amt
                total = float(dfs["data"].at[idx, "합계금액"] or 0)
                new_unpaid = total - new_paid
                if abs(new_unpaid) < 1: new_unpaid = 0
                
                dfs["data"].at[idx, "기수금액"] = new_paid
                dfs["data"].at[idx, "미수금액"] = new_unpaid
                dfs["data"].at[idx, col_name] = tax_no
                dfs["data"].at[idx, "세금계산서발행일"] = tax_date
                
                log_msg = f"입금 {pay_amt:,.0f}원 등록"
                if new_unpaid <= 0:
                    dfs["data"].at[idx, "Status"] = "완료"
                    dfs["data"].at[idx, "입금완료일"] = pay_date
                    log_msg += " (완납)"
                
                # 로그
                new_log = self.dm._create_log_entry("입금 등록", f"번호 [{self.mgmt_no}] {log_msg}")
                dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
                
                return True, ""
            else:
                return False, "데이터 인덱스 오류"

        success, err_msg = self.dm._execute_transaction(update_logic)
        if success:
            messagebox.showinfo("성공", f"입금 {pay_amt:,.0f}원 등록 완료.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", err_msg, parent=self)