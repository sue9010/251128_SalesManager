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
        self.geometry("600x750")
        
        self.entries = {}
        # [신규] 전체 파일 경로를 저장할 딕셔너리 (키: 컬럼명, 값: 전체 경로)
        self.full_paths = {}
        
        self.create_widgets()
        
        if self.client_name:
            self.load_data()

        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)

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
                    
                    # [신규] windnd 드래그앤드롭 설정
                    try:
                        # 윈도우 핸들이 생성된 후 훅을 걸어야 함
                        def hook_dnd():
                            if entry.winfo_exists():
                                windnd.hook_dropfiles(entry.winfo_id(), self.on_drop)
                        
                        entry.after(100, hook_dnd)
                    except Exception as e:
                        print(f"DnD Error: {e}")

                    # [수정] 파일찾기 -> 삭제 버튼으로 변경
                    ctk.CTkButton(row, text="삭제", width=50, command=lambda e=entry, c=col: self.clear_entry(e, c), fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"]).pack(side="right")
                    # [신규] 파일 열기 버튼
                    ctk.CTkButton(row, text="열기", width=50, command=lambda e=entry, c=col: self.open_file(e, c), fg_color=COLORS["bg_medium"], text_color=COLORS["text"]).pack(side="right", padx=2)
                    self.entries[col] = entry
                elif col == "통화":
                    entry = ctk.CTkComboBox(row, values=["KRW", "USD", "EUR", "CNY", "JPY"], font=FONTS["main"])
                    entry.pack(side="left", fill="x", expand=True)
                    self.entries[col] = entry
                else:
                    entry = ctk.CTkEntry(row, font=FONTS["main"])
                    entry.pack(side="left", fill="x", expand=True)
                    self.entries[col] = entry

    # [신규] 파일 경로 업데이트 헬퍼 (UI에는 파일명만, 내부는 전체 경로)
    def update_file_entry(self, col_name, full_path):
        if not full_path:
            return
            
        self.full_paths[col_name] = full_path
        
        if col_name in self.entries:
            entry = self.entries[col_name]
            entry.delete(0, "end")
            # 파일명만 표시
            entry.insert(0, os.path.basename(full_path))

    def browse_file(self, entry_widget):
        pass

    # [수정] 입력창 초기화 및 파일 삭제 (안전 삭제 및 DB 동기화)
    def clear_entry(self, entry_widget, col_name):
        path = self.full_paths.get(col_name)
        
        if not path:
            path = entry_widget.get().strip()

        if not path:
            return

        # 1. 관리되는 폴더인지 확인
        is_managed_file = False
        try:
            abs_path = os.path.abspath(path)
            abs_root = os.path.abspath(Config.DEFAULT_ATTACHMENT_ROOT)
            if abs_path.startswith(abs_root):
                is_managed_file = True
        except:
            pass

        if is_managed_file:
            # 관리되는 파일인 경우: 실제 삭제 및 DB 업데이트
            if messagebox.askyesno("파일 삭제", f"정말 파일을 삭제하시겠습니까?\n파일명: {os.path.basename(path)}\n\n(주의: 실제 파일이 영구적으로 삭제됩니다.)", parent=self):
                try:
                    if os.path.exists(path):
                        os.remove(path)
                        messagebox.showinfo("삭제 완료", "파일이 삭제되었습니다.", parent=self)
                    else:
                        messagebox.showwarning("알림", "파일이 존재하지 않아 경로만 삭제합니다.", parent=self)
                    
                    # [중요] DB 업데이트 (기존 업체인 경우)
                    if self.client_name:
                         def update_db_logic(dfs):
                            df = dfs["clients"]
                            idx = df[df["업체명"] == self.client_name].index
                            if len(idx) > 0:
                                df.at[idx[0], col_name] = "" # DB에서 경로 삭제
                            return True, ""
                         
                         self.dm._execute_transaction(update_db_logic)

                except Exception as e:
                    messagebox.showerror("오류", f"파일 삭제 실패: {e}", parent=self)
                    return # 실패 시 경로는 유지

                # UI 및 내부 변수 초기화
                entry_widget.delete(0, "end")
                if col_name in self.full_paths:
                    del self.full_paths[col_name]
        else:
            # 외부 파일인 경우: 그냥 UI만 초기화 (원본 보호)
            entry_widget.delete(0, "end")
            if col_name in self.full_paths:
                del self.full_paths[col_name]

    # [신규] 파일 열기
    def open_file(self, entry_widget, col_name):
        # self.full_paths 우선 사용
        path = self.full_paths.get(col_name)
        
        if not path:
             path = entry_widget.get().strip()

        if path and os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("에러", f"파일을 열 수 없습니다.\n{e}", parent=self)
        else:
            messagebox.showwarning("경고", "파일 경로가 유효하지 않습니다.", parent=self)

    # [신규] windnd 드래그앤드롭 핸들러
    def on_drop(self, filenames):
        if filenames:
            # windnd는 bytes 리스트를 반환하므로 디코딩 필요
            try:
                file_path = filenames[0].decode('mbcs') # Windows 기본 인코딩
            except:
                file_path = filenames[0].decode('utf-8', errors='ignore')

            # 사업자등록증경로 컬럼에 대해 업데이트
            self.update_file_entry("사업자등록증경로", file_path)

    def load_data(self):
        df = self.dm.df_clients
        row = df[df["업체명"] == self.client_name].iloc[0]
        for col, entry in self.entries.items():
            val = str(row.get(col, ""))
            if val == "nan": val = ""
            
            if col == "사업자등록증경로" and val:
                # 파일 경로인 경우 update_file_entry 사용
                self.update_file_entry(col, val)
            else:
                if isinstance(entry, ctk.CTkComboBox): entry.set(val)
                else:
                    entry.delete(0, "end")
                    entry.insert(0, val)
        self.entries["업체명"].configure(state="disabled")

    # [수정] 트랜잭션 적용
    def save(self):
        data = {}
        for col, entry in self.entries.items():
            # 파일 경로 컬럼은 self.full_paths에서 가져옴
            if col == "사업자등록증경로":
                data[col] = self.full_paths.get(col, "").strip()
            else:
                data[col] = entry.get().strip()
            
        if not data["업체명"]:
            messagebox.showwarning("경고", "업체명은 필수입니다.", parent=self)
            return

        def update_logic(dfs):
            # [신규] 사업자등록증 파일 처리
            biz_license_path = data.get("사업자등록증경로", "")
            if biz_license_path and os.path.exists(biz_license_path):
                # 저장 폴더 생성
                target_dir = os.path.join(Config.DEFAULT_ATTACHMENT_ROOT, "사업자등록증")
                if not os.path.exists(target_dir):
                    try:
                        os.makedirs(target_dir)
                    except Exception as e:
                        print(f"Folder Create Error: {e}")
                
                # 파일명 생성: 사업자등록증_업체명_YYMMDD.ext
                ext = os.path.splitext(biz_license_path)[1]
                today_str = datetime.now().strftime("%y%m%d")
                new_filename = f"사업자등록증_{data['업체명']}_{today_str}{ext}"
                target_path = os.path.join(target_dir, new_filename)
                
                # 경로가 다르면 복사
                if os.path.abspath(biz_license_path) != os.path.abspath(target_path):
                    try:
                        shutil.copy2(biz_license_path, target_path)
                        data["사업자등록증경로"] = target_path # 데이터 업데이트
                    except Exception as e:
                        return False, f"파일 복사 실패: {e}"

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