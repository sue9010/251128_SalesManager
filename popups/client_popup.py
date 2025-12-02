import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pandas as pd

from config import Config
from styles import COLORS, FONT_FAMILY, FONTS


class ClientPopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, refresh_callback, client_name=None):
        super().__init__(parent)
        self.dm = data_manager
        self.refresh_callback = refresh_callback
        self.client_name = client_name # None이면 신규, 있으면 수정
        
        title = "업체 신규 등록" if client_name is None else f"업체 정보 수정 - {client_name}"
        self.title(title)
        self.geometry("600x750")
        
        self.entries = {}
        
        self.create_widgets()
        
        if self.client_name:
            self.load_data()

        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)

    # ... (create_widgets, browse_file, load_data 생략 - 기존과 동일) ...
    def create_widgets(self):
        footer = ctk.CTkFrame(self, fg_color="transparent", height=60)
        footer.pack(side="bottom", fill="x", padx=20, pady=20)
        ctk.CTkButton(footer, text="저장", command=self.save, width=120, height=40,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], font=FONTS["main_bold"]).pack(side="right", padx=5)
        ctk.CTkButton(footer, text="취소", command=self.destroy, width=80, height=40,
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="right", padx=5)
        if self.client_name:
            ctk.CTkButton(footer, text="삭제", command=self.delete, width=80, height=40,
                          fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"]).pack(side="left")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        groups = {
            "기본 정보": ["업체명", "국가", "통화", "주소"],
            "담당자 정보": ["담당자", "전화번호", "이메일"],
            "수출/물류 정보": ["수출허가구분", "수출허가번호", "수출허가만료일", "운송계정", "운송방법"],
            "기타": ["특이사항", "사업자등록증경로"]
        }

        for group_name, fields in groups.items():
            ctk.CTkLabel(scroll, text=group_name, font=FONTS["header"], text_color=COLORS["primary"]).pack(anchor="w", pady=(15, 5))
            group_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_medium"])
            group_frame.pack(fill="x", pady=5)
            for i, col in enumerate(fields):
                row = ctk.CTkFrame(group_frame, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=5)
                ctk.CTkLabel(row, text=col, width=120, anchor="w", font=FONTS["main"]).pack(side="left")
                if col == "사업자등록증경로":
                    entry = ctk.CTkEntry(row, font=FONTS["main"])
                    entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
                    ctk.CTkButton(row, text="파일찾기", width=70, command=lambda e=entry: self.browse_file(e), fg_color=COLORS["bg_dark"]).pack(side="right")
                    self.entries[col] = entry
                elif col == "통화":
                    entry = ctk.CTkComboBox(row, values=["KRW", "USD", "EUR", "CNY", "JPY"], font=FONTS["main"])
                    entry.pack(side="left", fill="x", expand=True)
                    self.entries[col] = entry
                else:
                    entry = ctk.CTkEntry(row, font=FONTS["main"])
                    entry.pack(side="left", fill="x", expand=True)
                    self.entries[col] = entry

    def browse_file(self, entry_widget):
        self.attributes("-topmost", False)
        path = filedialog.askopenfilename(parent=self)
        self.attributes("-topmost", True)
        if path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, path)

    def load_data(self):
        df = self.dm.df_clients
        row = df[df["업체명"] == self.client_name].iloc[0]
        for col, entry in self.entries.items():
            val = str(row.get(col, ""))
            if val == "nan": val = ""
            if isinstance(entry, ctk.CTkComboBox): entry.set(val)
            else:
                entry.delete(0, "end")
                entry.insert(0, val)
        self.entries["업체명"].configure(state="disabled")

    # [수정] 트랜잭션 적용
    def save(self):
        data = {}
        for col, entry in self.entries.items():
            data[col] = entry.get().strip()
            
        if not data["업체명"]:
            messagebox.showwarning("경고", "업체명은 필수입니다.", parent=self)
            return

        def update_logic(dfs):
            df = dfs["clients"]
            
            if self.client_name: # 수정
                idx = df[df["업체명"] == self.client_name].index
                if len(idx) > 0:
                    for col, val in data.items():
                        df.at[idx[0], col] = val
            else: # 신규
                if data["업체명"] in df["업체명"].values:
                    return False, "이미 존재하는 업체명입니다."
                new_row = pd.DataFrame([data])
                dfs["clients"] = pd.concat([dfs["clients"], new_row], ignore_index=True)
            
            return True, ""

        success, msg = self.dm._execute_transaction(update_logic)
        
        if success:
            messagebox.showinfo("성공", "저장되었습니다.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", msg, parent=self)

    # [수정] 트랜잭션 적용
    def delete(self):
        if messagebox.askyesno("삭제 확인", f"정말 '{self.client_name}' 업체를 삭제하시겠습니까?", parent=self):
            def update_logic(dfs):
                dfs["clients"] = dfs["clients"][dfs["clients"]["업체명"] != self.client_name]
                return True, ""

            success, msg = self.dm._execute_transaction(update_logic)
            if success:
                messagebox.showinfo("삭제", "삭제되었습니다.", parent=self)
                self.refresh_callback()
                self.destroy()
            else:
                messagebox.showerror("실패", msg, parent=self)