import os
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import windnd

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
        
        # Compact Size
        self.geometry("900x620")
        self.configure(fg_color=COLORS["bg_dark"])
        
        self.entries = {}
        self.full_paths = {}
        
        self._create_widgets()
        
        if self.client_name:
            self._load_data()

        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)

    def _create_widgets(self):
        # Main Container (No Scroll)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 1. Header
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_text = "NEW CLIENT" if not self.client_name else "EDIT CLIENT"
        ctk.CTkLabel(header_frame, text=title_text, font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")
        
        # 2. Content Area (2 Columns)
        content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        
        # Left Column
        left_col = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Right Column
        right_col = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # --- Left Column Content (Basic + Contact) ---
        
        # Group 1: Basic Info
        self._create_group_header(left_col, "기본 정보")
        basic_frame = ctk.CTkFrame(left_col, fg_color=COLORS["bg_medium"], corner_radius=6)
        basic_frame.pack(fill="x", pady=(0, 15))
        
        self._add_input_row(basic_frame, "업체명", "업체명")
        self._add_input_row(basic_frame, "국가", "국가")
        self._add_combo_row(basic_frame, "통화", "통화", ["KRW", "USD", "EUR", "CNY", "JPY"])
        self._add_input_row(basic_frame, "주소", "주소")

        # Group 2: Contact Info
        self._create_group_header(left_col, "담당자 정보")
        contact_frame = ctk.CTkFrame(left_col, fg_color=COLORS["bg_medium"], corner_radius=6)
        contact_frame.pack(fill="x", pady=(0, 15))
        
        self._add_input_row(contact_frame, "담당자", "담당자")
        self._add_input_row(contact_frame, "전화번호", "전화번호")
        self._add_input_row(contact_frame, "이메일", "이메일")

        # --- Right Column Content (Logistics + Docs) ---
        
        # Group 3: Logistics Info
        self._create_group_header(right_col, "수출/물류 정보")
        logistics_frame = ctk.CTkFrame(right_col, fg_color=COLORS["bg_medium"], corner_radius=6)
        logistics_frame.pack(fill="x", pady=(0, 15))
        
        self._add_input_row(logistics_frame, "수출허가구분", "수출허가구분")
        self._add_input_row(logistics_frame, "수출허가번호", "수출허가번호")
        self._add_input_row(logistics_frame, "만료일", "수출허가만료일", placeholder="YYYY-MM-DD")
        self._add_input_row(logistics_frame, "운송계정", "운송계정")
        self._add_input_row(logistics_frame, "운송방법", "운송방법")
        
        # Group 4: Documents
        self._create_group_header(right_col, "증빙 서류")
        doc_frame = ctk.CTkFrame(right_col, fg_color=COLORS["bg_medium"], corner_radius=6)
        doc_frame.pack(fill="x", pady=(0, 15))
        
        # [수정] height 파라미터 전달 (기본 28, 여기선 50으로 설정하여 드래그 영역 확보)
        self._add_file_row(doc_frame, "사업자등록증", "사업자등록증경로", height=65)

        # --- Bottom Section (Notes) ---
        bottom_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(10, 0))
        
        self._create_group_header(bottom_frame, "기타 특이사항")
        note_frame = ctk.CTkFrame(bottom_frame, fg_color=COLORS["bg_medium"], corner_radius=6)
        note_frame.pack(fill="x")
        
        self.entry_note = ctk.CTkEntry(note_frame, height=60) # Multiline simulation
        self.entry_note.pack(fill="x", padx=10, pady=10)
        self.entries["특이사항"] = self.entry_note

        # 3. Footer (Action Buttons)
        footer_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(20, 0), side="bottom")
        
        if self.client_name:
            ctk.CTkButton(footer_frame, text="삭제", command=self.delete, width=100, height=40,
                          fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"]).pack(side="left")

        ctk.CTkButton(footer_frame, text="저장", command=self.save, width=150, height=40,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], 
                      font=FONTS["main_bold"]).pack(side="right")
                      
        ctk.CTkButton(footer_frame, text="취소", command=self.destroy, width=100, height=40,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], 
                      text_color=COLORS["text"]).pack(side="right", padx=10)

    # --- Helper Methods for UI Construction ---
    
    def _create_group_header(self, parent, text, **kwargs):
        # [수정] kwargs 지원 (height 등)
        ctk.CTkLabel(parent, text=text, font=FONTS["header"], text_color=COLORS["primary"], **kwargs).pack(anchor="w", pady=(0, 5))

    def _add_input_row(self, parent, label, key, placeholder=""):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(frame, text=label, width=90, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        entry = ctk.CTkEntry(frame, height=28, placeholder_text=placeholder, font=FONTS["main"])
        entry.pack(side="left", fill="x", expand=True)
        
        self.entries[key] = entry
        return entry

    def _add_combo_row(self, parent, label, key, values):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(frame, text=label, width=90, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        combo = ctk.CTkComboBox(frame, values=values, height=28, font=FONTS["main"])
        combo.pack(side="left", fill="x", expand=True)
        
        self.entries[key] = combo
        return combo

    def _add_file_row(self, parent, label, key, height=28):
        # [수정] height 파라미터 추가
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(frame, text=label, width=90, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        
        entry = ctk.CTkEntry(frame, height=height, placeholder_text="파일 드래그", font=FONTS["main"])
        entry.pack(side="left", fill="x", expand=True)
        self.entries[key] = entry
        
        # Buttons
        ctk.CTkButton(frame, text="열기", width=40, height=height, command=lambda: self.open_file(entry, key),
                      fg_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="left", padx=(5, 0))
        ctk.CTkButton(frame, text="삭제", width=40, height=height, command=lambda: self.clear_entry(entry, key),
                      fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"]).pack(side="left", padx=(5, 0))

        # DnD Setup
        try:
            def hook_dnd():
                if entry.winfo_exists():
                    windnd.hook_dropfiles(entry.winfo_id(), lambda f: self.on_drop(f, key))
            self.after(200, hook_dnd)
        except Exception as e:
            print(f"DnD Setup Error: {e}")

    # --- Logic Methods ---

    def _load_data(self):
        df = self.dm.df_clients
        row = df[df["업체명"] == self.client_name].iloc[0]
        
        for key, widget in self.entries.items():
            val = str(row.get(key, ""))
            if val == "nan": val = ""
            
            if key == "사업자등록증경로" and val:
                self.update_file_entry(key, val)
            else:
                if isinstance(widget, ctk.CTkComboBox):
                    widget.set(val)
                else:
                    widget.delete(0, "end")
                    widget.insert(0, val)
                    
        # 업체명 수정 불가
        if "업체명" in self.entries:
            self.entries["업체명"].configure(state="disabled")

    def on_drop(self, filenames, key):
        if filenames:
            try: file_path = filenames[0].decode('mbcs')
            except: 
                try: file_path = filenames[0].decode('utf-8', errors='ignore')
                except: return
            self.update_file_entry(key, file_path)

    def update_file_entry(self, key, full_path):
        if not full_path: return
        self.full_paths[key] = full_path
        
        if key in self.entries:
            entry = self.entries[key]
            entry.delete(0, "end")
            entry.insert(0, os.path.basename(full_path))

    def open_file(self, entry, key):
        path = self.full_paths.get(key)
        if not path: path = entry.get().strip()
        
        if path and os.path.exists(path):
            try: os.startfile(path)
            except Exception as e: messagebox.showerror("에러", f"파일 열기 실패: {e}", parent=self)
        else:
            messagebox.showwarning("경고", "유효한 파일 경로가 아닙니다.", parent=self)

    def clear_entry(self, entry, key):
        path = self.full_paths.get(key)
        if not path: path = entry.get().strip()
        
        if not path: return

        # 관리되는 파일인지 확인
        is_managed = False
        try:
            if os.path.abspath(path).startswith(os.path.abspath(Config.DEFAULT_ATTACHMENT_ROOT)):
                is_managed = True
        except: pass

        if is_managed:
            if messagebox.askyesno("파일 삭제", "정말 파일을 삭제하시겠습니까?\n(영구 삭제)", parent=self):
                try:
                    if os.path.exists(path): os.remove(path)
                    if self.client_name:
                         def update_db(dfs):
                            df = dfs["clients"]
                            idx = df[df["업체명"] == self.client_name].index
                            if len(idx) > 0: df.at[idx[0], key] = ""
                            return True, ""
                         self.dm._execute_transaction(update_db)
                except Exception as e:
                    messagebox.showerror("오류", f"삭제 실패: {e}", parent=self)
                    return
                
                entry.delete(0, "end")
                if key in self.full_paths: del self.full_paths[key]
        else:
            entry.delete(0, "end")
            if key in self.full_paths: del self.full_paths[key]

    def save(self):
        data = {}
        for key, widget in self.entries.items():
            if key == "사업자등록증경로":
                data[key] = self.full_paths.get(key, "").strip()
            else:
                data[key] = widget.get().strip()
            
        if not data.get("업체명"):
            messagebox.showwarning("경고", "업체명은 필수입니다.", parent=self)
            return

        def update_logic(dfs):
            # File Save Logic
            biz_path = data.get("사업자등록증경로", "")
            if biz_path and os.path.exists(biz_path):
                target_dir = os.path.join(Config.DEFAULT_ATTACHMENT_ROOT, "사업자등록증")
                if not os.path.exists(target_dir):
                    try: os.makedirs(target_dir)
                    except: pass
                
                ext = os.path.splitext(biz_path)[1]
                today_str = datetime.now().strftime("%y%m%d")
                new_name = f"사업자등록증_{data['업체명']}_{today_str}{ext}"
                target_path = os.path.join(target_dir, new_name)
                
                if os.path.abspath(biz_path) != os.path.abspath(target_path):
                    try:
                        shutil.copy2(biz_path, target_path)
                        data["사업자등록증경로"] = target_path
                    except Exception as e:
                        return False, f"파일 복사 실패: {e}"

            df = dfs["clients"]
            if self.client_name: # Edit
                idx = df[df["업체명"] == self.client_name].index
                if len(idx) > 0:
                    for k, v in data.items(): df.at[idx[0], k] = v
            else: # New
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