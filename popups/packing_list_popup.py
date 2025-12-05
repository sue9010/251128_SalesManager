import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from styles import COLORS, FONTS

class PackingListPopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, export_callback, initial_data):
        super().__init__(parent)
        self.dm = data_manager
        self.export_callback = export_callback
        self.initial_data = initial_data # {client, mgmt_no, date, items: [...]}
        
        self.title("Packing List 입력 - Sales Manager")
        self.geometry("1100x600")
        self.configure(fg_color=COLORS["bg_dark"])
        self.attributes("-topmost", True)
        
        self.item_entries = []
        self._create_ui()

    def _create_ui(self):
        # 1. 상단 정보
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(top_frame, text="출고번호:", font=FONTS["main_bold"]).pack(side="left", padx=5)
        ctk.CTkLabel(top_frame, text=self.initial_data.get("mgmt_no", ""), font=FONTS["main"], text_color=COLORS["primary"]).pack(side="left", padx=5)
        
        ctk.CTkLabel(top_frame, text="업체명:", font=FONTS["main_bold"]).pack(side="left", padx=(20, 5))
        ctk.CTkLabel(top_frame, text=self.initial_data.get("client_name", ""), font=FONTS["main"]).pack(side="left", padx=5)

        ctk.CTkLabel(top_frame, text="출고일:", font=FONTS["main_bold"]).pack(side="left", padx=(20, 5))
        ctk.CTkLabel(top_frame, text=self.initial_data.get("date", ""), font=FONTS["main"]).pack(side="left", padx=5)

        # 2. 품목 리스트 (테이블 헤더)
        list_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"])
        list_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        headers = ["C/No.", "Description", "Qty", "Unit", "N.W(kg)", "G.W(kg)", "L(cm)", "W(cm)", "H(cm)"]
        widths = [60, 250, 50, 60, 80, 80, 60, 60, 60]
        
        header_frame = ctk.CTkFrame(list_frame, height=30, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x")
        
        for h, w in zip(headers, widths):
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["small"]).pack(side="left", padx=2)

        # 스크롤 영역
        self.scroll_frame = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)

        # 아이템 로우 생성
        for item in self.initial_data.get("items", []):
            self._add_item_row(item)

        # 3. 하단 (Notes, 버튼)
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(bottom_frame, text="Notes:", font=FONTS["main_bold"]).pack(anchor="w")
        self.entry_notes = ctk.CTkEntry(bottom_frame, width=600)
        self.entry_notes.pack(fill="x", pady=5)
        
        btn_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(btn_frame, text="발행", command=self.on_export, 
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      width=100, height=40, font=FONTS["header"]).pack(side="right", padx=5)
        
        ctk.CTkButton(btn_frame, text="취소", command=self.destroy,
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"],
                      width=80, height=40, font=FONTS["main"]).pack(side="right", padx=5)

    def _add_item_row(self, item_data):
        row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", height=35)
        row.pack(fill="x", pady=2)
        
        entries = {}
        
        # C/No.
        ent_cno = ctk.CTkEntry(row, width=60)
        ent_cno.pack(side="left", padx=2)
        ent_cno.insert(0, "1") # Default 1
        entries["c_no"] = ent_cno
        
        # Description (Readonly)
        desc_text = item_data.get("desc", "")
        # 만약 desc가 비어있으면 모델명이나 품목명 사용
        if not desc_text: desc_text = item_data.get("model", "")
        
        lbl_desc = ctk.CTkLabel(row, text=desc_text, width=250, anchor="w")
        lbl_desc.pack(side="left", padx=2)
        
        # Qty (Readonly or Editable? -> Readonly recommended as it comes from delivery popup)
        qty_val = item_data.get("qty", 0)
        lbl_qty = ctk.CTkLabel(row, text=f"{qty_val:g}", width=50)
        lbl_qty.pack(side="left", padx=2)
        
        # Unit
        ent_unit = ctk.CTkEntry(row, width=60)
        ent_unit.pack(side="left", padx=2)
        ent_unit.insert(0, "SET")
        entries["unit"] = ent_unit
        
        # N.W
        ent_nw = ctk.CTkEntry(row, width=80)
        ent_nw.pack(side="left", padx=2)
        entries["net_weight"] = ent_nw
        
        # G.W
        ent_gw = ctk.CTkEntry(row, width=80)
        ent_gw.pack(side="left", padx=2)
        entries["gross_weight"] = ent_gw
        
        # Size L, W, H
        ent_l = ctk.CTkEntry(row, width=60)
        ent_l.pack(side="left", padx=2)
        entries["size_l"] = ent_l
        
        ent_w = ctk.CTkEntry(row, width=60)
        ent_w.pack(side="left", padx=2)
        entries["size_w"] = ent_w
        
        ent_h = ctk.CTkEntry(row, width=60)
        ent_h.pack(side="left", padx=2)
        entries["size_h"] = ent_h
        
        self.item_entries.append({
            "widgets": entries,
            "data": item_data
        })

    def on_export(self):
        # 데이터 수집
        pl_items = []
        for row in self.item_entries:
            w = row["widgets"]
            d = row["data"]
            
            pl_items.append({
                "c_no": w["c_no"].get(),
                "desc": d.get("desc", "") if d.get("desc") else d.get("model", ""),
                "qty": d.get("qty", 0),
                "unit": w["unit"].get(),
                "net_weight": w["net_weight"].get(),
                "gross_weight": w["gross_weight"].get(),
                "size_l": w["size_l"].get(),
                "size_w": w["size_w"].get(),
                "size_h": w["size_h"].get(),
                "po_no": d.get("po_no", ""),
                "serial": d.get("serial", "")
            })
            
        notes = self.entry_notes.get()
        
        self.export_callback(pl_items, notes)
        self.destroy()