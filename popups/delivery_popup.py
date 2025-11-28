import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pandas as pd

from config import Config
from styles import COLORS, FONT_FAMILY, FONTS


class DeliveryPopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, refresh_callback, row_index):
        super().__init__(parent)
        self.dm = data_manager
        self.refresh_callback = refresh_callback
        self.row_index = row_index
        
        # 대상 데이터 로드
        self.target_row = self.dm.df_data.loc[self.row_index]
        self.mgmt_no = self.target_row["관리번호"]
        
        self.title(f"납품(출고) 처리 - {self.mgmt_no}")
        self.geometry("500x550")
        
        self.create_widgets()
        
        # 팝업 설정
        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)

    def create_widgets(self):
        # 1. 정보 표시
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=20)
        
        info_items = [
            ("업체명", self.target_row["업체명"]),
            ("모델명", self.target_row["모델명"]),
            ("현재 수량", f"{self.target_row['수량']} 개"),
            ("출고예정일", self.target_row["출고예정일"])
        ]
        
        for i, (k, v) in enumerate(info_items):
            ctk.CTkLabel(info_frame, text=k, font=FONTS["main_bold"], width=80, anchor="w").grid(row=i, column=0, pady=5)
            ctk.CTkLabel(info_frame, text=str(v), font=FONTS["main"], anchor="w").grid(row=i, column=1, pady=5, sticky="w")

        # 2. 입력 폼
        form_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"])
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # 출고일
        ctk.CTkLabel(form_frame, text="출고일 (선적일)", font=FONTS["main_bold"]).pack(anchor="w", padx=15, pady=(15, 5))
        self.entry_date = ctk.CTkEntry(form_frame, width=200)
        self.entry_date.pack(anchor="w", padx=15)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # 납품 수량
        ctk.CTkLabel(form_frame, text="납품 수량", font=FONTS["main_bold"]).pack(anchor="w", padx=15, pady=(15, 5))
        self.entry_qty = ctk.CTkEntry(form_frame, width=200)
        self.entry_qty.pack(anchor="w", padx=15)
        self.entry_qty.insert(0, str(self.target_row["수량"])) # 기본값: 전체 수량
        
        # 파일 첨부
        ctk.CTkLabel(form_frame, text="거래명세서 / 송장", font=FONTS["main_bold"]).pack(anchor="w", padx=15, pady=(15, 5))
        
        file_box = ctk.CTkFrame(form_frame, fg_color="transparent")
        file_box.pack(fill="x", padx=15)
        
        self.entry_file = ctk.CTkEntry(file_box)
        self.entry_file.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(file_box, text="찾기", width=60, command=self.browse_file,
                      fg_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="right")

        # 3. 버튼
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20, side="bottom")
        
        ctk.CTkButton(btn_frame, text="납품 처리", command=self.save,
                      fg_color=COLORS["success"], hover_color="#26A65B", width=120, height=40).pack(side="right", padx=5)
        
        ctk.CTkButton(btn_frame, text="취소", command=self.destroy,
                      fg_color=COLORS["bg_light"], text_color=COLORS["text"], width=80, height=40).pack(side="right", padx=5)

    def browse_file(self):
        self.attributes("-topmost", False)
        path = filedialog.askopenfilename()
        self.attributes("-topmost", True)
        if path:
            self.entry_file.delete(0, "end")
            self.entry_file.insert(0, path)

    def save(self):
        # 1. 유효성 검사
        try:
            deliver_qty = float(self.entry_qty.get())
            current_qty = float(self.target_row["수량"])
        except ValueError:
            messagebox.showerror("오류", "수량은 숫자여야 합니다.", parent=self)
            return
            
        if deliver_qty <= 0 or deliver_qty > current_qty:
            messagebox.showerror("오류", f"수량은 0보다 크고 {current_qty}보다 작거나 같아야 합니다.", parent=self)
            return
            
        date_str = self.entry_date.get()
        if not date_str:
            messagebox.showwarning("경고", "출고일을 입력하세요.", parent=self)
            return

        # 2. 파일 저장 로직 (필요시)
        file_path = self.entry_file.get()
        saved_path = file_path
        if file_path:
            new_path, err = self.dm.save_attachment(file_path, self.target_row["업체명"], "거래명세서")
            if new_path: saved_path = new_path

        # 3. 데이터 업데이트 (전체 vs 부분)
        # 중요: 원본 데이터프레임의 인덱스를 사용하여 수정해야 함
        
        if deliver_qty == current_qty:
            # 전체 납품
            self.dm.df_data.at[self.row_index, "Status"] = "납품완료/입금대기"
            self.dm.df_data.at[self.row_index, "출고일"] = date_str
            self.dm.df_data.at[self.row_index, "발주서경로"] = saved_path # 컬럼 재활용하거나 비고에 넣음
            action = "전체 납품"
        else:
            # 부분 납품 -> 행 분할
            remain_qty = current_qty - deliver_qty
            price = float(self.target_row["단가"])
            
            # 남은 수량 계산
            remain_supply = remain_qty * price
            is_domestic = (self.target_row["구분"] == "내수")
            remain_tax = remain_supply * 0.1 if is_domestic else 0
            
            # 3-1. 기존 행 수정 (남은 것)
            self.dm.df_data.at[self.row_index, "수량"] = remain_qty
            self.dm.df_data.at[self.row_index, "공급가액"] = remain_supply
            self.dm.df_data.at[self.row_index, "세액"] = remain_tax
            self.dm.df_data.at[self.row_index, "합계금액"] = remain_supply + remain_tax
            self.dm.df_data.at[self.row_index, "미수금액"] = remain_supply + remain_tax
            
            # 3-2. 새 행 추가 (납품된 것)
            new_row = self.target_row.copy()
            new_supply = deliver_qty * price
            new_tax = new_supply * 0.1 if is_domestic else 0
            
            new_row["수량"] = deliver_qty
            new_row["공급가액"] = new_supply
            new_row["세액"] = new_tax
            new_row["합계금액"] = new_supply + new_tax
            new_row["미수금액"] = new_supply + new_tax # 아직 입금 안됨
            new_row["Status"] = "납품완료/입금대기"
            new_row["출고일"] = date_str
            new_row["발주서경로"] = saved_path
            
            self.dm.df_data = pd.concat([self.dm.df_data, pd.DataFrame([new_row])], ignore_index=True)
            action = f"부분 납품 ({deliver_qty}개)"

        # 저장
        success, msg = self.dm.save_to_excel()
        if success:
            self.dm.add_log(action, f"번호 [{self.mgmt_no}]")
            messagebox.showinfo("성공", "납품 처리가 완료되었습니다.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", msg, parent=self)