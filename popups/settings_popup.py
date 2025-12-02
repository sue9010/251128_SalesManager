import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

import customtkinter as ctk

from config import Config
from styles import COLORS, FONT_FAMILY, FONTS


class SettingsPopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, refresh_callback):
        super().__init__(parent)
        self.dm = data_manager
        self.refresh_callback = refresh_callback
        
        self.title("환경 설정")
        self.geometry("500x750") # 높이 조정
        
        # 화면 중앙 배치
        self.center_window(500, 750)
        
        self.create_widgets()
        
        # 팝업 설정
        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

    def create_widgets(self):
        # 컨텐츠 영역
        parent = ctk.CTkFrame(self, fg_color="transparent")
        parent.pack(fill="both", expand=True, padx=20, pady=20)

        # 1. 테마 설정 섹션
        ctk.CTkLabel(parent, text="테마 설정 (Appearance)", font=FONTS["header"]).pack(pady=(10, 10), anchor="w")
        
        theme_frame = ctk.CTkFrame(parent, fg_color="transparent")
        theme_frame.pack(fill="x")
        
        self.theme_var = ctk.StringVar(value=self.dm.current_theme)
        
        self.theme_switch = ctk.CTkSegmentedButton(
            theme_frame, 
            values=["Light", "Dark"], 
            variable=self.theme_var,
            command=self.change_theme,
            font=(FONT_FAMILY, 12, "bold"),
            selected_color=COLORS["primary"],
            selected_hover_color=COLORS["primary_hover"]
        )
        self.theme_switch.pack(fill="x")

        # 구분선
        ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=20)

        # 2. 엑셀 파일 경로 설정 섹션
        ctk.CTkLabel(parent, text="영업 데이터 파일 경로 (SalesList)", font=FONTS["header"]).pack(pady=(0, 10), anchor="w")

        path_frame = ctk.CTkFrame(parent, fg_color="transparent")
        path_frame.pack(fill="x")

        self.path_entry = ctk.CTkEntry(path_frame, font=FONTS["main"])
        self.path_entry.insert(0, self.dm.current_excel_path)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(path_frame, text="찾기", width=60, command=self.browse_excel, 
                      fg_color=COLORS["bg_medium"], text_color=COLORS["text"]).pack(side="right")
        
        # 3. 첨부 파일 저장 경로 설정 섹션
        ctk.CTkLabel(parent, text="첨부 파일 저장 폴더 (Root)", font=FONTS["header"]).pack(pady=(20, 10), anchor="w")

        attach_frame = ctk.CTkFrame(parent, fg_color="transparent")
        attach_frame.pack(fill="x")

        self.attach_path_entry = ctk.CTkEntry(attach_frame, font=FONTS["main"])
        self.attach_path_entry.insert(0, self.dm.attachment_root)
        self.attach_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(attach_frame, text="폴더선택", width=80, command=self.browse_folder, 
                      fg_color=COLORS["bg_medium"], text_color=COLORS["text"]).pack(side="right")

        # 구분선
        ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=20)

        # [NEW] 4. 생산 요청 파일 경로 설정 (추가)
        ctk.CTkLabel(parent, text="생산 요청 파일 경로 (출고관리)", font=FONTS["header"]).pack(pady=(0, 10), anchor="w")

        prod_frame = ctk.CTkFrame(parent, fg_color="transparent")
        prod_frame.pack(fill="x")

        self.prod_path_entry = ctk.CTkEntry(prod_frame, font=FONTS["main"])
        self.prod_path_entry.insert(0, self.dm.production_request_path)
        self.prod_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(prod_frame, text="찾기", width=60, command=self.browse_production_file, 
                      fg_color=COLORS["bg_medium"], text_color=COLORS["text"]).pack(side="right")

        # 구분선
        ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=20)

        # 5. 개발자 모드 설정
        dev_frame = ctk.CTkFrame(parent, fg_color="transparent")
        dev_frame.pack(fill="x")
        
        self.dev_var = ctk.BooleanVar(value=self.dm.is_dev_mode)
        
        ctk.CTkSwitch(
            dev_frame, 
            text="관리자/개발자 모드 활성화", 
            variable=self.dev_var,
            command=self.toggle_dev_mode,
            font=FONTS["main_bold"],
            progress_color=COLORS["danger"]
        ).pack(side="left")

        # 개발자 도구 버튼들 (개발자 모드일 때만 보임)
        self.dev_tools_frame = ctk.CTkFrame(parent, fg_color="transparent")
        if self.dm.is_dev_mode:
            self.show_dev_tools()

        # 6. 하단 저장 버튼
        ctk.CTkButton(self, text="설정 저장 및 닫기", command=self.save, height=40,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], font=FONTS["header"]).pack(side="bottom", fill="x", padx=20, pady=20)

    def show_dev_tools(self):
        self.dev_tools_frame.pack(fill="x", pady=(10, 0))
        for widget in self.dev_tools_frame.winfo_children(): widget.destroy()
        
        ctk.CTkButton(self.dev_tools_frame, text="💾 데이터 백업 생성", height=30,
                      fg_color=COLORS["success"], hover_color="#26A65B", command=self.do_backup).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(self.dev_tools_frame, text="🧹 오래된 로그 정리", height=30,
                      fg_color=COLORS["warning"], hover_color="#D35400", command=self.do_clean_logs).pack(side="right", fill="x", expand=True, padx=(5, 0))

    def change_theme(self, new_theme):
        """테마 즉시 변경"""
        ctk.set_appearance_mode(new_theme)

    def browse_excel(self):
        self.attributes("-topmost", False)
        file_path = filedialog.askopenfilename(parent=self, filetypes=[("Excel files", "*.xlsx;*.xls;*.xlsm")])
        self.attributes("-topmost", True)
        if file_path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, file_path)

    # [NEW] 생산 요청 파일 브라우즈
    def browse_production_file(self):
        self.attributes("-topmost", False)
        file_path = filedialog.askopenfilename(parent=self, filetypes=[("Excel files", "*.xlsx;*.xls;*.xlsm")])
        self.attributes("-topmost", True)
        if file_path:
            self.prod_path_entry.delete(0, "end")
            self.prod_path_entry.insert(0, file_path)

    def browse_folder(self):
        self.attributes("-topmost", False)
        folder_path = filedialog.askdirectory(parent=self)
        self.attributes("-topmost", True)
        if folder_path:
            self.attach_path_entry.delete(0, "end")
            self.attach_path_entry.insert(0, folder_path)

    def toggle_dev_mode(self):
        if self.dev_var.get():
            # 켜려고 할 때: 비밀번호 확인
            self.attributes("-topmost", False)
            pwd = simpledialog.askstring("관리자 인증", "관리자 비밀번호를 입력하세요:", show="*", parent=self)
            self.attributes("-topmost", True)
            
            if pwd == Config.DEV_PASSWORD:
                self.dm.set_dev_mode(True)
                messagebox.showinfo("인증 성공", "관리자 모드가 활성화되었습니다.", parent=self)
                self.show_dev_tools()
            else:
                self.dev_var.set(False)
                messagebox.showerror("인증 실패", "비밀번호가 올바르지 않습니다.", parent=self)
        else:
            # 끌 때는 그냥 끔
            self.dm.set_dev_mode(False)
            self.dev_tools_frame.pack_forget()

    def do_backup(self):
        self.attributes("-topmost", False)
        if messagebox.askyesno("백업", "현재 데이터 파일의 백업본을 생성하시겠습니까?", parent=self):
            success, msg = self.dm.create_backup()
            if success:
                messagebox.showinfo("성공", msg, parent=self)
            else:
                messagebox.showerror("실패", msg, parent=self)
        self.attributes("-topmost", True)

    def do_clean_logs(self):
        self.attributes("-topmost", False)
        if messagebox.askyesno("로그 정리", "오래된 로그 데이터를 정리하시겠습니까?", parent=self):
            success, msg = self.dm.clean_old_logs()
            messagebox.showinfo("완료", msg, parent=self)
        self.attributes("-topmost", True)

    def save(self):
        new_path = self.path_entry.get()
        new_theme = self.theme_var.get()
        new_attach = self.attach_path_entry.get()
        # [NEW] 생산 요청 경로 가져오기
        new_prod_path = self.prod_path_entry.get()
        
        if new_path:
            self.dm.save_config(
                new_path=new_path, 
                new_theme=new_theme, 
                new_attachment_dir=new_attach,
                new_prod_path=new_prod_path # [NEW] 저장 함수로 전달
            )
            
            self.attributes("-topmost", False)
            messagebox.showinfo("설정 저장", "설정이 저장되었습니다.", parent=self)
            self.destroy()
            
            # 메인 UI 갱신 (테마 변경 등 반영)
            if self.refresh_callback:
                self.refresh_callback()
        else:
            messagebox.showwarning("경고", "엑셀 파일 경로를 입력해주세요.", parent=self)