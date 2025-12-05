import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from styles import COLORS, FONT_FAMILY, FONTS





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
        
        self._create_widgets()

        
        if self.mgmt_no:
            self._load_data()
        else:
            self._generate_new_id()

        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)

    def _create_widgets(self):
        """Standard Split View Layout: Header -> Split Content (Info + Items) -> Footer"""
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Main Container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 1. Header
        self._create_header(self.main_container)
        
        # 2. Main Content (Split View)
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, pady=10)
        
        # Left Panel (Info)
        self.info_panel = ctk.CTkFrame(self.content_frame, fg_color=COLORS["bg_medium"], corner_radius=10, width=400)
        self.info_panel.pack(side="left", fill="y", padx=(0, 10))
        self.info_panel.pack_propagate(False)
        self._setup_info_panel(self.info_panel)
        
        # Right Panel (Items)
        self.items_panel = ctk.CTkFrame(self.content_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        self.items_panel.pack(side="right", fill="both", expand=True)
        self._setup_items_panel(self.items_panel)
        
        # 3. Footer
        self._create_footer(self.main_container)

    def _create_header(self, parent):
        """Common Header: ID and Title. Subclasses can override or extend."""
        self.header_frame = ctk.CTkFrame(parent, height=50, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 10))
        
        # Title/ID
        title_text = f"{self.popup_title} #{self.mgmt_no}" if self.mgmt_no else f"새 {self.popup_title}"
        self.lbl_title = ctk.CTkLabel(self.header_frame, text=title_text, font=FONTS["header"])
        self.lbl_title.pack(side="left", padx=10)

    def _setup_info_panel(self, parent):
        """Hook for Left Info Panel content. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _setup_info_panel")

    def _setup_items_panel(self, parent):
        """Hook for Right Items Panel content. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _setup_items_panel")

    def _create_footer(self, parent):
        """Common Footer: Action Buttons (Save, Cancel, Delete)."""
        self.footer_frame = ctk.CTkFrame(parent, height=60, fg_color="transparent")
        self.footer_frame.pack(fill="x", pady=(10, 0), side="bottom")
        
        # Right Side: Save, Cancel
        self.btn_save = ctk.CTkButton(self.footer_frame, text="저장", command=self.save, width=120, height=40,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], font=FONTS["main_bold"])
        self.btn_save.pack(side="right", padx=5)
        
        self.btn_cancel = ctk.CTkButton(self.footer_frame, text="취소", command=self.destroy, width=80, height=40,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], text_color=COLORS["text"])
        self.btn_cancel.pack(side="right", padx=5)
        
    # ==========================================================================
    # File & DnD Helpers
    # ==========================================================================
    def create_file_input_row(self, parent, label, col_name, placeholder="파일을 드래그하거나 열기 버튼을 클릭하세요"):
        """
        Creates a standardized file input row: Label -> Row[Entry, Open, Delete]
        Returns: (entry_widget, btn_open, btn_delete)
        """
        if label:
            ctk.CTkLabel(parent, text=label, font=FONTS["main"], text_color=COLORS["text_dim"]).pack(anchor="w", pady=(5, 0))
        
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(2, 5))
        
        entry = ctk.CTkEntry(row, placeholder_text=placeholder, height=28)
        entry.pack(side="left", fill="x", expand=True)
        
        # Open Button
        btn_open = ctk.CTkButton(row, text="열기", width=50, height=28,
                      command=lambda: self.open_file(entry, col_name),
                      fg_color=COLORS["bg_light"], text_color=COLORS["text"])
        btn_open.pack(side="left", padx=(5, 0))
                      
        # Delete Button
        btn_delete = ctk.CTkButton(row, text="삭제", width=50, height=28,
                      command=lambda: self.clear_entry(entry, col_name),
                      fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])
        btn_delete.pack(side="left", padx=(5, 0))
        
        return entry, btn_open, btn_delete

    def open_file(self, entry_widget, col_name):
        path = self.full_paths.get(col_name) if hasattr(self, "full_paths") else None
        if not path: path = entry_widget.get().strip()
        
        if path and os.path.exists(path):
            try: os.startfile(path)
            except Exception as e: messagebox.showerror("에러", f"파일을 열 수 없습니다.\n{e}", parent=self)
        else:
            messagebox.showwarning("경고", "파일 경로가 유효하지 않습니다.", parent=self)

    def clear_entry(self, entry_widget, col_name):
        path = self.full_paths.get(col_name) if hasattr(self, "full_paths") else None
        if not path: path = entry_widget.get().strip()
        if not path: return

        is_managed = False
        try:
            abs_path = os.path.abspath(path)
            # Config might need import, doing lazy import or assuming it's available if imported at top
            from config import Config
            abs_root = os.path.abspath(Config.DEFAULT_ATTACHMENT_ROOT)
            if abs_path.startswith(abs_root): is_managed = True
        except: pass

        if is_managed:
            if messagebox.askyesno("파일 삭제", f"정말 파일을 삭제하시겠습니까?\n(영구 삭제됨)", parent=self):
                try:
                    if os.path.exists(path): os.remove(path)
                except Exception as e:
                    messagebox.showerror("오류", f"삭제 실패: {e}", parent=self)
                    return
                entry_widget.delete(0, "end")
                if hasattr(self, "full_paths") and col_name in self.full_paths: 
                    del self.full_paths[col_name]
        else:
            entry_widget.delete(0, "end")
            if hasattr(self, "full_paths") and col_name in self.full_paths: 
                del self.full_paths[col_name]

    # ==========================================================================
    # Item List Helpers
    # ==========================================================================
    def _add_item_row(self, item_data=None):
        """품목 테이블에 새로운 행을 추가합니다."""
        # Note: self.scroll_items might not exist in BasePopup if _create_items_frame is not called 
        # (subclasses currently implement _setup_items_panel instead).
        # This methods assumes subclass has created self.scroll_items or it might fail.
        # However, for backward compatibility or future BasePopup logic, we keep it but it might need adjustment 
        # if subclasses don't use 'scroll_items' name. 
        # Looking at Order/Quote/Delivery/Payment, they all seem to have scroll_items.
        
        if not hasattr(self, 'scroll_items'):
             return None

        row_frame = ctk.CTkFrame(self.scroll_items, fg_color="transparent", height=35)
        row_frame.pack(fill="x", pady=2)

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