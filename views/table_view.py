import tkinter as tk
from tkinter import ttk
from datetime import datetime
import customtkinter as ctk
import pandas as pd

from styles import COLORS, FONT_FAMILY, FONTS

class MultiSelectDropdown(ctk.CTkFrame):
    def __init__(self, parent, values, default_values=None, command=None, width=200):
        super().__init__(parent, fg_color="transparent")
        self.values = values
        self.command = command
        self.vars = {}
        self.dropdown_window = None
        
        # 기본값 설정
        if default_values is None:
            default_values = values
        
        for val in values:
            self.vars[val] = ctk.BooleanVar(value=(val in default_values))
            
        # 메인 버튼
        self.btn_text = ctk.StringVar(value=self._get_button_text())
        self.button = ctk.CTkButton(self, textvariable=self.btn_text, command=self.toggle_dropdown, 
                                    width=width, fg_color=COLORS["bg_light"], text_color=COLORS["text"],
                                    hover_color=COLORS["bg_light_hover"], font=FONTS["main"])
        self.button.pack(fill="both", expand=True)
        
    def _get_button_text(self):
        selected_count = sum([v.get() for v in self.vars.values()])
        if selected_count == len(self.values):
            return "모든 상태 (All)"
        elif selected_count == 0:
            return "선택 안함"
        else:
            return f"{selected_count}개 상태 선택됨"

    def toggle_dropdown(self):
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            self.dropdown_window.destroy()
            self.dropdown_window = None
            return
            
        # 드롭다운 윈도우 생성 (Toplevel)
        self.dropdown_window = ctk.CTkToplevel(self)
        self.dropdown_window.wm_overrideredirect(True)
        self.dropdown_window.attributes("-topmost", True)
        self.dropdown_window.attributes("-alpha", 0.95)
        
        # 위치 계산
        x = self.button.winfo_rootx()
        y = self.button.winfo_rooty() + self.button.winfo_height() + 5
        self.dropdown_window.geometry(f"+{x}+{y}")
        
        # 프레임
        frame = ctk.CTkFrame(self.dropdown_window, fg_color=COLORS["bg_medium"], border_width=1, border_color=COLORS["border"])
        frame.pack(fill="both", expand=True)
        
        # 체크박스 리스트
        scroll = ctk.CTkScrollableFrame(frame, width=200, height=250, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        for val in self.values:
            chk = ctk.CTkCheckBox(scroll, text=val, variable=self.vars[val], command=self.on_change,
                                  font=FONTS["main"], text_color=COLORS["text"])
            chk.pack(anchor="w", pady=2)
            
        # 닫기 버튼 (또는 포커스 아웃 시 닫기 구현 가능하나 간단히 버튼으로)
        ctk.CTkButton(frame, text="닫기", command=self.close_dropdown, height=25, 
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]).pack(fill="x", padx=5, pady=5)
                      
        # 포커스 아웃 시 닫기 (선택적)
        self.dropdown_window.bind("<FocusOut>", lambda e: self.close_dropdown() if str(e.widget) == str(self.dropdown_window) else None)

    def on_change(self):
        self.btn_text.set(self._get_button_text())
        if self.command:
            self.command()

    def close_dropdown(self):
        if self.dropdown_window:
            self.dropdown_window.destroy()
            self.dropdown_window = None
            
    def get_selected(self):
        return [val for val, var in self.vars.items() if var.get()]


class TableView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager
        
        # 상태 목록 정의
        self.all_statuses = [
            "견적", "주문", "생산중", "납품대기", 
            "납품완료/입금대기", "납품대기/입금완료", 
            "완료", "취소", "보류"
        ]
        
        # 기본 선택: 완료 제외
        self.default_statuses = [s for s in self.all_statuses if s != "완료"]
        
        self.create_widgets()
        self.refresh_data()

    def create_widgets(self):
        # 1. 헤더 (필터링)
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="상태 필터:", font=FONTS["main_bold"], text_color=COLORS["text"]).pack(side="left", padx=(0, 10))
        
        # 다중 선택 드롭다운
        self.status_filter = MultiSelectDropdown(
            header_frame, 
            values=self.all_statuses, 
            default_values=self.default_statuses,
            command=self.refresh_data,
            width=200
        )
        self.status_filter.pack(side="left", padx=5)
        
        # 새로고침 버튼
        ctk.CTkButton(header_frame, text="새로고침", command=self.refresh_data, width=80, 
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"], font=FONTS["main"]).pack(side="right")

        # 2. 테이블 (Treeview)
        # Treeview 스타일링
        style = ttk.Style()
        style.theme_use("default") # 기본 테마 사용 후 커스텀
        
        # Treeview 색상 설정 (다크 모드 대응)
        mode = ctk.get_appearance_mode()
        bg_color = COLORS["bg_dark"][1] if mode == "Dark" else COLORS["bg_dark"][0]
        text_color = COLORS["text"][1] if mode == "Dark" else COLORS["text"][0]
        header_bg = COLORS["bg_medium"][1] if mode == "Dark" else COLORS["bg_medium"][0]
        
        style.configure("Treeview", 
                        background=bg_color, 
                        foreground=text_color, 
                        fieldbackground=bg_color,
                        rowheight=30,
                        font=(FONT_FAMILY, 11))
        
        style.configure("Treeview.Heading", 
                        background=header_bg, 
                        foreground=text_color, 
                        font=(FONT_FAMILY, 11, "bold"))
        
        style.map("Treeview", background=[("selected", COLORS["primary"][1] if mode == "Dark" else COLORS["primary"][0])], 
                  foreground=[("selected", "white")])
        
        # 테이블 프레임
        table_frame = ctk.CTkFrame(self, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        columns = ("관리번호", "업체명", "모델명", "수량", "출고예정일", "Status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        # 컬럼 설정
        col_widths = {"관리번호": 100, "업체명": 150, "모델명": 200, "수량": 80, "출고예정일": 100, "Status": 120}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100), anchor="center" if col in ["관리번호", "수량", "출고예정일", "Status"] else "w")
            
        # 스크롤바
        scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 더블클릭 이벤트 (상세 보기 등)
        self.tree.bind("<Double-1>", self.on_double_click)

    def refresh_data(self):
        # 기존 데이터 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        df = self.dm.df_data
        if df.empty: return
        
        # 선택된 상태 가져오기
        selected_statuses = self.status_filter.get_selected()
        
        # 필터링 로직
        filtered_rows = []
        for _, row in df.iterrows():
            status = str(row.get("Status", "")).strip()
            
            # 상태 필터링
            # 부분 일치 허용? 아니면 정확 일치? -> 정확 일치 권장하지만, 복합 상태(납품완료/입금대기 등) 고려
            # 여기서는 리스트에 있는 값과 정확히 일치하거나, 포함되는지 확인
            # 사용자 요청: "status가 몇 종류지... 그것들을 다 넣어줘" -> 정확 일치로 처리
            
            if status in selected_statuses:
                filtered_rows.append(row)
            else:
                # 예외 케이스: 데이터의 status가 리스트에 없는 새로운 값일 경우?
                # 일단은 선택된 것만 보여줌.
                pass
        
        # 정렬: 출고예정일 기준 (날짜 없는 경우 뒤로)
        def sort_key(x):
            date_str = str(x.get("출고예정일", "")).strip()
            if not date_str or date_str == "-":
                return "9999-99-99" # 날짜 없음 -> 맨 뒤
            return date_str
            
        filtered_rows.sort(key=sort_key)
        
        # 데이터 삽입
        for row in filtered_rows:
            values = (
                row["관리번호"],
                row["업체명"],
                row["모델명"],
                row["수량"],
                row["출고예정일"],
                row["Status"]
            )
            self.tree.insert("", "end", values=values)

    def on_double_click(self, event):
        item = self.tree.selection()
        if not item: return
        
        values = self.tree.item(item[0], "values")
        mgmt_no = values[0]
        
        # 견적 팝업 열기 (기존 로직 활용)
        self.pm.open_quote_popup(mgmt_no)
