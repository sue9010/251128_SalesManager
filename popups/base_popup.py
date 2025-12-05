import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from styles import COLORS, FONT_FAMILY, FONTS


from popups.autocomplete_entry import AutocompleteEntry


class BasePopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, refresh_callback, popup_title="Popup", mgmt_no=None):
        super().__init__(parent)
        self.dm = data_manager
        self.refresh_callback = refresh_callback
        self.mgmt_no = mgmt_no
        self.popup_title = popup_title
        
        if mgmt_no:
            mode_text = f"{popup_title} 상세 정보 수정"
        else:
            mode_text = f"신규 {popup_title} 등록"
            
        self.title(f"{mode_text} - Sales Manager")
        self.geometry("1100x750")
        
        self.item_rows = [] 
        self.all_clients = []
        
        self._create_widgets()
        self._load_clients()
        
        if self.mgmt_no:
            self._load_data()
        else:
            self._generate_new_id()

        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)

    def _create_widgets(self):
        """UI 위젯을 생성하고 배치합니다."""
        self._create_top_frame()
        self._layout_top_frame() # 레이아웃 메서드 호출
        self._create_items_frame()
        self._create_bottom_frame()
        self._create_action_buttons()

    def _create_top_frame(self):
        """상단 정보 위젯들을 '생성'만 합니다."""
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=20, pady=15)

        self.lbl_id = ctk.CTkLabel(self.top_frame, text="관리번호", font=FONTS["main_bold"])
        self.entry_id = ctk.CTkEntry(self.top_frame, width=200, font=FONTS["main"], state="readonly")

        self.lbl_status = ctk.CTkLabel(self.top_frame, text="상태", font=FONTS["main_bold"])
        self.combo_status = ctk.CTkComboBox(self.top_frame, values=["견적", "주문", "생산중", "납품대기", "납품완료/입금대기", "완료", "취소", "보류"], width=200, font=FONTS["main"])
        
        self.lbl_client = ctk.CTkLabel(self.top_frame, text="고객사", font=FONTS["main_bold"])
        self.entry_client = AutocompleteEntry(self.top_frame, width=200, font=FONTS["main"], command=self._on_client_select)

        self.lbl_project = ctk.CTkLabel(self.top_frame, text="프로젝트명", font=FONTS["main_bold"])
        self.entry_project = ctk.CTkEntry(self.top_frame, width=400, font=FONTS["main"])

    def _layout_top_frame(self):
        """상단 정보 위젯들을 '배치'합니다. 하위 클래스에서 오버라이드 할 수 있습니다."""
        self.lbl_id.grid(row=0, column=0, padx=5, sticky="w")
        self.entry_id.grid(row=0, column=1, padx=5, sticky="w")

        self.lbl_status.grid(row=0, column=2, padx=5, sticky="w")
        self.combo_status.grid(row=0, column=3, padx=5, sticky="w")
        
        self.lbl_client.grid(row=1, column=0, padx=5, pady=10, sticky="w")
        self.entry_client.grid(row=1, column=1, columnspan=3, padx=5, pady=10, sticky="w")

        self.lbl_project.grid(row=2, column=0, padx=5, sticky="w")
        self.entry_project.grid(row=2, column=1, columnspan=3, padx=5, sticky="ew")

    def _create_items_frame(self):
        """품목을 표시하는 스크롤 가능한 프레임과 헤더를 생성합니다."""
        list_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"])
        list_frame.pack(fill="both", expand=True, padx=20, pady=5)

        headers = ["품명", "모델명", "Description", "수량", "단가", "공급가액", "세액", "합계금액", "삭제"]
        widths = [150, 150, 200, 60, 100, 100, 80, 100, 50]
        header_frame = ctk.CTkFrame(list_frame, height=30, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x")
        
        for i, (h, w) in enumerate(zip(headers, widths)):
            lbl = ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["small"])
            lbl.pack(side="left", padx=2)

        self.scroll_items = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.scroll_items.pack(fill="both", expand=True)

        btn_add_row = ctk.CTkButton(list_frame, text="+ 품목 추가", command=self._add_item_row, 
                                    fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], text_color=COLORS["text"])
        btn_add_row.pack(fill="x", pady=5)

    def _create_bottom_frame(self):
        """
        [수정] 하단 정보 입력 위젯 생성
        기본적으로 '비고'란만 생성하고, '주문요청사항'은 제거합니다.
        (필요 시 하위 클래스에서 오버라이드하여 추가)
        """
        self.input_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.input_grid.pack(fill="x", padx=20, pady=(10, 10))
        
        # '주문요청사항' 제거하고 '비고'만 남김
        ctk.CTkLabel(self.input_grid, text="비고:", font=FONTS["main"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_note = ctk.CTkEntry(self.input_grid, width=600) # 너비 확장
        self.entry_note.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # entry_req는 기본적으로 None으로 초기화해두어 오류 방지
        self.entry_req = None

        self.input_grid.columnconfigure(1, weight=1)

    def _create_action_buttons(self):
        """저장, 취소 등 액션 버튼을 생성합니다."""
        btn_frame = ctk.CTkFrame(self, fg_color="transparent", height=50)
        btn_frame.pack(fill="x", padx=20, pady=20, side="bottom")

        ctk.CTkButton(btn_frame, text="저장", command=self.save, width=120, height=40,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], font=FONTS["main_bold"]).pack(side="right", padx=5)

        ctk.CTkButton(btn_frame, text="취소", command=self.destroy, width=80, height=40,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], text_color=COLORS["text"]).pack(side="right", padx=5)
        
        if self.mgmt_no:
             ctk.CTkButton(btn_frame, text="삭제", command=self.delete, width=80, height=40,
                          fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"]).pack(side="left")

    def _load_clients(self):
        """DataManager로부터 고객사 목록을 로드하여 자동완성 엔트리에 설정합니다."""
        self.all_clients = self.dm.df_clients["업체명"].unique().tolist()
        self.entry_client.update_values(self.all_clients)

    def _on_client_select(self, client_name):
        """고객사 선택 시 호출될 콜백 함수. 하위 클래스에서 필요에 따라 오버라이드합니다."""
        pass

    def _add_item_row(self, item_data=None):
        """품목 테이블에 새로운 행을 추가합니다."""
        row_frame = ctk.CTkFrame(self.scroll_items, fg_color="transparent", height=35)
        row_frame.pack(fill="x", pady=2)

        # 품목 행에 포함될 위젯들 (하위 클래스에서 이 구조를 사용할 수 있음)
        e_item = ctk.CTkEntry(row_frame, width=150)
        e_item.pack(side="left", padx=2)
        e_model = ctk.CTkEntry(row_frame, width=150)
        e_model.pack(side="left", padx=2)
        e_desc = ctk.CTkEntry(row_frame, width=200)
        e_desc.pack(side="left", padx=2)
        e_qty = ctk.CTkEntry(row_frame, width=60, justify="center")
        e_qty.pack(side="left", padx=2)
        e_price = ctk.CTkEntry(row_frame, width=100, justify="right")
        e_price.pack(side="left", padx=2)
        e_supply = ctk.CTkEntry(row_frame, width=100, justify="right", state="readonly")
        e_supply.pack(side="left", padx=2)
        e_tax = ctk.CTkEntry(row_frame, width=80, justify="right", state="readonly")
        e_tax.pack(side="left", padx=2)
        e_total = ctk.CTkEntry(row_frame, width=100, justify="right", state="readonly")
        e_total.pack(side="left", padx=2)
        
        btn_del = ctk.CTkButton(row_frame, text="X", width=40, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                                command=lambda f=row_frame: self._delete_item_row(f))
        btn_del.pack(side="left", padx=5)

        row_widgets = {
            "frame": row_frame, "item": e_item, "model": e_model, "desc": e_desc,
            "qty": e_qty, "price": e_price, "supply": e_supply, "tax": e_tax, "total": e_total
        }
        self.item_rows.append(row_widgets)

        # 이벤트 바인딩은 하위 클래스에서 구체적인 계산 로직과 함께 구현
        return row_widgets

    def _delete_item_row(self, frame):
        """품목 테이블에서 특정 행을 삭제합니다."""
        for item in self.item_rows:
            if item["frame"] == frame:
                self.item_rows.remove(item)
                break
        frame.destroy()
        self._calculate_totals() # 총계 재계산

    def _calculate_totals(self):
        """총계를 계산합니다. 하위 클래스에서 오버라이드하여 사용합니다."""
        pass

    # --- Abstract Methods (하위 클래스에서 반드시 구현해야 할 메서드) ---

    def _generate_new_id(self):
        """새로운 관리번호를 생성합니다."""
        raise NotImplementedError("This method should be implemented by subclasses.")

    def _load_data(self):
        """기존 데이터를 로드하여 UI에 표시합니다."""
        raise NotImplementedError("This method should be implemented by subclasses.")

    def save(self):
        """입력된 데이터를 저장합니다."""
        raise NotImplementedError("This method should be implemented by subclasses.")

    def delete(self):
        """현재 데이터를 삭제합니다."""
        raise NotImplementedError("This method should be implemented by subclasses.")