import os
import shutil
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import getpass
import windnd

import customtkinter as ctk
import pandas as pd

from config import Config
from popups.base_popup import BasePopup
from popups.packing_list_popup import PackingListPopup 
from styles import COLORS, FONTS
from export_manager import ExportManager 

class DeliveryPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_nos):
        if isinstance(mgmt_nos, list):
            self.mgmt_nos = mgmt_nos
        else:
            self.mgmt_nos = [mgmt_nos]

        if not self.mgmt_nos:
            messagebox.showerror("오류", "납품 처리할 대상이 지정되지 않았습니다.", parent=parent)
            self.destroy()
            return

        self.item_widgets_map = {}
        self.full_paths = {} 
        self.export_manager = ExportManager() 
        
        self.current_delivery_no = ""
        
        super().__init__(parent, data_manager, refresh_callback, popup_title="납품 처리", mgmt_no=self.mgmt_nos[0])

    def _create_widgets(self):
        self.configure(fg_color=COLORS["bg_dark"])
        self.geometry("1100x850") # 넓은 화면 사용
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # 1. 헤더 (Compact)
        self._create_header(self.main_container)
        
        # 2. 메인 콘텐츠 (Split View)
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, pady=10)
        
        # 좌측: 배송 정보 및 액션 (Fixed 400px)
        self.shipping_panel = ctk.CTkFrame(self.content_frame, fg_color=COLORS["bg_medium"], corner_radius=10, width=400)
        self.shipping_panel.pack(side="left", fill="y", padx=(0, 10))
        self.shipping_panel.pack_propagate(False)

        # 우측: 품목 리스트 (Flexible)
        self.items_panel = ctk.CTkFrame(self.content_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        self.items_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self.items_panel.pack_propagate(False)
        
        self._setup_shipping_panel(self.shipping_panel)
        self._setup_items_panel(self.items_panel)
        
        # 3. 하단 액션 바
        self._create_footer(self.main_container)

    def _create_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        # 상단: ID 및 상태
        top_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        top_row.pack(fill="x", anchor="w")
        
        self.lbl_id = ctk.CTkLabel(top_row, text="MGMT-000000", font=FONTS["main"], text_color=COLORS["text_dim"])
        self.lbl_id.pack(side="left")
        
        self.status_badge = ctk.CTkLabel(top_row, text="납품 대기", font=FONTS["small"], 
                                       fg_color=COLORS["primary"], text_color="white", corner_radius=10, width=80)
        self.status_badge.pack(side="left", padx=10)
        
        # 프로젝트명 및 고객사
        info_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        info_row.pack(fill="x", pady=(5, 0))
        
        self.lbl_project = ctk.CTkLabel(info_row, text="Project Name", font=FONTS["title"], anchor="w")
        self.lbl_project.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(info_row, text="|", font=FONTS["header"], text_color=COLORS["text_dim"]).pack(side="left", padx=10)
        
        self.lbl_client = ctk.CTkLabel(info_row, text="Client Name", font=FONTS["header"], text_color=COLORS["text_dim"], anchor="w")
        self.lbl_client.pack(side="left", padx=10)

        # [NEW] 추가 정보 (특이사항, 주문요청사항)
        note_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        note_row.pack(fill="x", pady=(5, 0))
        
        self.lbl_client_note = ctk.CTkLabel(note_row, text="업체 특이사항: -", font=FONTS["main"], text_color=COLORS["danger"], anchor="w")
        self.lbl_client_note.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(note_row, text="|", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left", padx=10)

        self.lbl_order_note = ctk.CTkLabel(note_row, text="주문 요청사항: -", font=FONTS["main"], text_color=COLORS["text"], anchor="w")
        self.lbl_order_note.pack(side="left", padx=10)
        
        # 숨겨진 필드들 (로직 호환성 유지)
        self.entry_client = ctk.CTkEntry(self, width=0) 
        self.entry_project = ctk.CTkEntry(self, width=0) 

    def _setup_items_panel(self, parent):
        # 타이틀
        ctk.CTkLabel(parent, text="납품 품목 리스트", font=FONTS["header"]).pack(anchor="w", padx=15, pady=15)
        
        # 헤더 - Width 조정 (150, 150, 100, 50, 70)
        headers = ["품명", "모델명", "시리얼", "잔여", "출고"]
        widths = [150, 150, 100, 50, 70]
        
        header_frame = ctk.CTkFrame(parent, height=35, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x", padx=15)
        
        for h, w in zip(headers, widths):
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["main_bold"]).pack(side="left", padx=2)
            
        self.scroll_items = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_items.pack(fill="both", expand=True, padx=10, pady=5)

    def _setup_shipping_panel(self, parent):
        # 스크롤 가능하게 변경 (내용이 많을 수 있음)
        scroll_container = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 1. 배송 정보 섹션
        ctk.CTkLabel(scroll_container, text="배송 정보", font=FONTS["header"]).pack(anchor="w", padx=10, pady=(10, 5))
        
        input_frame = ctk.CTkFrame(scroll_container, fg_color="transparent")
        input_frame.pack(fill="x", padx=10)
        
        def create_input(p, label, var_name):
            f = ctk.CTkFrame(p, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=label, width=80, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
            entry = ctk.CTkEntry(f, height=30)
            entry.pack(side="left", fill="x", expand=True)
            setattr(self, var_name, entry)
            return entry

        create_input(input_frame, "출고번호", "entry_delivery_no").configure(state="readonly")
        
        date_entry = create_input(input_frame, "출고일", "entry_delivery_date")
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        create_input(input_frame, "송장번호", "entry_invoice_no")
        create_input(input_frame, "운송방법", "entry_shipping_method")
        create_input(input_frame, "운송계정", "entry_shipping_account")
        
        ctk.CTkFrame(scroll_container, height=2, fg_color=COLORS["border"]).pack(fill="x", padx=10, pady=15)

        # 2. 서류 발행 섹션
        ctk.CTkLabel(scroll_container, text="서류 발행", font=FONTS["header"]).pack(anchor="w", padx=10, pady=(0, 5))
        
        doc_frame = ctk.CTkFrame(scroll_container, fg_color="transparent")
        doc_frame.pack(fill="x", padx=10)
        
        def create_doc_btn(text, cmd, color=COLORS["bg_light"]):
            ctk.CTkButton(doc_frame, text=text, command=cmd, height=35,
                          fg_color=color, hover_color=COLORS["primary_hover"], 
                          text_color=COLORS["text"], font=FONTS["main_bold"]).pack(fill="x", pady=3)

        create_doc_btn("📄 PI (Proforma Invoice)", self.export_pi)
        create_doc_btn("📄 CI (Commercial Invoice)", self.export_ci)
        create_doc_btn("📄 PL (Packing List)", self.export_pl)
        
        ctk.CTkFrame(scroll_container, height=2, fg_color=COLORS["border"]).pack(fill="x", padx=10, pady=15)

        # 3. 운송장 첨부 섹션
        ctk.CTkLabel(scroll_container, text="운송장 파일", font=FONTS["header"]).pack(anchor="w", padx=10, pady=(0, 5))
        
        self.drop_frame = ctk.CTkFrame(scroll_container, fg_color=COLORS["bg_dark"], border_width=1, border_color=COLORS["border"])
        self.drop_frame.pack(fill="x", padx=10, pady=5, ipady=10)
        
        self.lbl_drop = ctk.CTkLabel(self.drop_frame, text="파일을 여기에 드래그하세요", text_color=COLORS["text_dim"])
        self.lbl_drop.pack(pady=5)
        
        self.entry_waybill_file = ctk.CTkEntry(self.drop_frame, placeholder_text="파일 경로")
        self.entry_waybill_file.pack(fill="x", padx=10, pady=5)
        
        btn_file_frame = ctk.CTkFrame(self.drop_frame, fg_color="transparent")
        btn_file_frame.pack(fill="x", padx=10)
        
        ctk.CTkButton(btn_file_frame, text="열기", width=60, height=25,
                      command=lambda: self.open_file(self.entry_waybill_file, "운송장경로"),
                      fg_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="left", padx=2)
                      
        ctk.CTkButton(btn_file_frame, text="삭제", width=60, height=25,
                      command=lambda: self.clear_entry(self.entry_waybill_file, "운송장경로"),
                      fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"]).pack(side="right", padx=2)

        # DnD 설정
        try:
            def hook_dnd():
                if self.drop_frame.winfo_exists():
                    hwnd = self.drop_frame.winfo_id()
                    windnd.hook_dropfiles(hwnd, self.on_drop)
            self.after(200, hook_dnd)
        except Exception as e:
            print(f"DnD Setup Error: {e}")

    def _create_footer(self, parent):
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(footer_frame, text="닫기", command=self.destroy, width=100, height=45,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], 
                      text_color=COLORS["text"]).pack(side="left")
                      
        ctk.CTkButton(footer_frame, text="납품 처리 (저장)", command=self.save, width=200, height=45,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], 
                      font=FONTS["header"]).pack(side="right")

    def _load_data(self):
        df = self.dm.df_data
        rows = df[df["관리번호"].isin(self.mgmt_nos)].copy()
        
        if rows.empty:
            messagebox.showinfo("정보", "데이터를 찾을 수 없습니다.", parent=self)
            self.after(100, self.destroy)
            return

        serial_map = self.dm.get_serial_number_map()
        first = rows.iloc[0]

        # 헤더 정보 설정
        mgmt_str = str(self.mgmt_nos[0])
        if len(self.mgmt_nos) > 1:
            mgmt_str += f" 외 {len(self.mgmt_nos)-1}건"
        self.lbl_id.configure(text=f"No. {mgmt_str}")
        
        self.lbl_project.configure(text=first.get("프로젝트명", ""))
        self.lbl_client.configure(text=first.get("업체명", ""))
        
        # [NEW] 특이사항 및 주문요청사항 로드
        client_note = "-"
        client_row = self.dm.df_clients[self.dm.df_clients["업체명"] == str(first.get("업체명", ""))]
        if not client_row.empty:
             val = client_row.iloc[0].get("특이사항", "-")
             if str(val) != "nan" and val: client_note = str(val)
        
        order_note = str(first.get("주문요청사항", "-"))
        if order_note == "nan" or not order_note: order_note = "-"
        
        self.lbl_client_note.configure(text=f"업체 특이사항: {client_note}")
        self.lbl_order_note.configure(text=f"주문 요청사항: {order_note}")

        # 더미 엔트리에 값 설정
        self.entry_client.delete(0, "end")
        self.entry_client.insert(0, str(first.get("업체명", "")))
        self.entry_project.delete(0, "end")
        self.entry_project.insert(0, str(first.get("프로젝트명", "")))

        # 배송 정보 로드
        client_name = str(first.get("업체명", ""))
        default_shipping = self.dm.get_client_shipping_method(client_name)
        if default_shipping:
            self.entry_shipping_method.delete(0, "end")
            self.entry_shipping_method.insert(0, default_shipping)

        default_account = self.dm.get_client_shipping_account(client_name)
        if default_account:
            self.entry_shipping_account.delete(0, "end")
            self.entry_shipping_account.insert(0, default_account)

        # 운송장 파일
        if self.entry_waybill_file:
            path = str(first.get("운송장경로", "")).replace("nan", "")
            if path: self.update_file_entry("운송장경로", path)

        # 출고번호 생성 또는 로드
        d_rows = self.dm.df_delivery[self.dm.df_delivery["관리번호"].isin(self.mgmt_nos)]
        existing_no = ""
        if not d_rows.empty:
            last_row = d_rows.sort_values("일시", ascending=False).iloc[0]
            existing_no = last_row.get("출고번호", "")
        
        if existing_no and existing_no != "-":
            self.current_delivery_no = existing_no
        else:
            self.current_delivery_no = self.dm.generate_delivery_no()
            
        self.entry_delivery_no.configure(state="normal")
        self.entry_delivery_no.delete(0, "end")
        self.entry_delivery_no.insert(0, self.current_delivery_no)
        self.entry_delivery_no.configure(state="readonly")

        # 품목 리스트 로드
        target_rows = rows[~rows["Status"].isin(["납품완료/입금대기", "완료", "취소", "보류"])]
        
        for index, row_data in target_rows.iterrows():
            m_no = str(row_data.get("관리번호", "")).strip()
            model = str(row_data.get("모델명", "")).strip()
            desc = str(row_data.get("Description", "")).strip()
            
            serial = serial_map.get((m_no, model, desc), "-")
            
            item_data_with_serial = row_data.to_dict()
            item_data_with_serial["시리얼번호"] = serial
            
            self._add_delivery_item_row(index, item_data_with_serial)

    def _add_delivery_item_row(self, row_index, item_data):
        row_frame = ctk.CTkFrame(self.scroll_items, fg_color="transparent", height=40)
        row_frame.pack(fill="x", pady=2)

        # 품명 - Width 조정 (150)
        ctk.CTkLabel(row_frame, text=str(item_data.get("품목명", "")), width=150, anchor="w").pack(side="left", padx=2)
        # 모델명 - Width 조정 (150)
        ctk.CTkLabel(row_frame, text=str(item_data.get("모델명", "")), width=150, anchor="w").pack(side="left", padx=2)
        
        # 시리얼 - Width 조정 (100)
        serial = str(item_data.get("시리얼번호", "-"))
        ctk.CTkLabel(row_frame, text=serial, width=100, anchor="center", text_color=COLORS["primary"]).pack(side="left", padx=2)
        
        # 잔여 수량 - Width 조정 (50)
        try:
            raw_qty = str(item_data.get("수량", "0")).replace(",", "")
            current_qty = float(raw_qty)
        except ValueError:
            current_qty = 0.0
        ctk.CTkLabel(row_frame, text=f"{current_qty:g}", width=50).pack(side="left", padx=2)
        
        # 출고 수량 입력 (강조) - Width 조정 (70)
        entry_deliver_qty = ctk.CTkEntry(row_frame, width=70, justify="center", 
                                       fg_color=COLORS["bg_light"], border_color=COLORS["primary"])
        entry_deliver_qty.pack(side="left", padx=2)
        entry_deliver_qty.insert(0, f"{current_qty:g}")

        self.item_widgets_map[row_index] = {
            "current_qty": current_qty,
            "entry": entry_deliver_qty,
            "row_data": item_data
        }

    # ==========================================================================
    # 파일 및 DnD 관련 메서드
    # ==========================================================================
    def update_file_entry(self, col_name, full_path):
        if not full_path: return
        self.full_paths[col_name] = full_path
        if col_name == "운송장경로" and self.entry_waybill_file:
            self.entry_waybill_file.delete(0, "end")
            self.entry_waybill_file.insert(0, os.path.basename(full_path))
            self.lbl_drop.configure(text=os.path.basename(full_path), text_color=COLORS["primary"])

    def on_drop(self, filenames):
        if filenames:
            try:
                file_path = filenames[0].decode('mbcs')
            except:
                try: file_path = filenames[0].decode('utf-8', errors='ignore')
                except: return
            
            self.update_file_entry("운송장경로", file_path)

    def open_file(self, entry_widget, col_name):
        path = self.full_paths.get(col_name)
        if not path: path = entry_widget.get().strip()
        
        if path and os.path.exists(path):
            try: os.startfile(path)
            except Exception as e: messagebox.showerror("에러", f"파일을 열 수 없습니다.\n{e}", parent=self)
        else:
            messagebox.showwarning("경고", "파일 경로가 유효하지 않습니다.", parent=self)

    def clear_entry(self, entry_widget, col_name):
        path = self.full_paths.get(col_name)
        if not path: path = entry_widget.get().strip()
        if not path: return

        is_managed = False
        try:
            abs_path = os.path.abspath(path)
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
                self.lbl_drop.configure(text="파일을 여기에 드래그하세요", text_color=COLORS["text_dim"])
                if col_name in self.full_paths: del self.full_paths[col_name]
        else:
            entry_widget.delete(0, "end")
            self.lbl_drop.configure(text="파일을 여기에 드래그하세요", text_color=COLORS["text_dim"])
            if col_name in self.full_paths: del self.full_paths[col_name]

    # ==========================================================================
    # Export 메서드
    # ==========================================================================
    def export_pi(self):
        client_name = self.entry_client.get()
        if not client_name:
            self.attributes("-topmost", False)
            messagebox.showwarning("경고", "고객사를 선택해주세요.", parent=self)
            self.attributes("-topmost", True)
            return

        client_row = self.dm.df_clients[self.dm.df_clients["업체명"] == client_name]
        if client_row.empty:
            self.attributes("-topmost", False)
            messagebox.showerror("오류", "고객 정보를 찾을 수 없습니다.", parent=self)
            self.attributes("-topmost", True)
            return
        
        main_mgmt_no = self.mgmt_nos[0]
        rows = self.dm.df_data[self.dm.df_data["관리번호"] == main_mgmt_no]
        if rows.empty: return
        first = rows.iloc[0]

        order_info = {
            "client_name": client_name,
            "mgmt_no": main_mgmt_no,
            "date": first.get("수주일", ""), 
            "po_no": first.get("발주서번호", ""), 
        }
        
        items = []
        for _, row in rows.iterrows():
            items.append({
                "item": row.get("품목명", ""),
                "model": row.get("모델명", ""),
                "desc": row.get("Description", ""),
                "qty": float(str(row.get("수량", 0)).replace(",", "") or 0),
                "price": float(str(row.get("단가", 0)).replace(",", "") or 0),
                "amount": float(str(row.get("공급가액", 0)).replace(",", "") or 0)
            })

        success, result = self.export_manager.export_pi_to_pdf(
            client_row.iloc[0], order_info, items
        )
        
        self.attributes("-topmost", False)
        if success:
            messagebox.showinfo("성공", f"PI가 생성되었습니다.\n{result}", parent=self)
        else:
            messagebox.showerror("실패", result, parent=self)
        self.attributes("-topmost", True)

    def export_ci(self):
        client_name = self.entry_client.get()
        if not client_name:
            self.attributes("-topmost", False)
            messagebox.showwarning("경고", "고객사를 선택해주세요.", parent=self)
            self.attributes("-topmost", True)
            return

        client_row = self.dm.df_clients[self.dm.df_clients["업체명"] == client_name]
        if client_row.empty:
            self.attributes("-topmost", False)
            messagebox.showerror("오류", "고객 정보를 찾을 수 없습니다.", parent=self)
            self.attributes("-topmost", True)
            return
        
        main_mgmt_no = self.mgmt_nos[0]
        rows = self.dm.df_data[self.dm.df_data["관리번호"].isin(self.mgmt_nos)]
        if rows.empty: return
        first = rows.iloc[0]

        order_info = {
            "client_name": client_name,
            "mgmt_no": self.current_delivery_no, 
            "date": self.entry_delivery_date.get(), 
            "po_no": first.get("발주서번호", ""), 
        }
        
        items = []
        for index, item_info in self.item_widgets_map.items():
            entry_widget = item_info["entry"]
            row_data = item_info["row_data"]
            
            try:
                deliver_qty = float(entry_widget.get().replace(",", ""))
            except:
                deliver_qty = 0
            
            if deliver_qty <= 0: continue
                
            try: price = float(str(row_data.get("단가", 0)).replace(",", ""))
            except: price = 0
                
            amount = deliver_qty * price
            
            items.append({
                "model": row_data.get("모델명", ""),
                "desc": row_data.get("Description", ""),
                "qty": deliver_qty, 
                "currency": row_data.get("통화", ""),
                "price": price,
                "amount": amount, 
                "po_no": row_data.get("발주서번호", ""),
                "serial": str(row_data.get("시리얼번호", "-"))
            })

        if not items:
            self.attributes("-topmost", False)
            messagebox.showwarning("경고", "출고 수량이 입력된 항목이 없습니다.", parent=self)
            self.attributes("-topmost", True)
            return

        success, result = self.export_manager.export_ci_to_pdf(
            client_row.iloc[0], order_info, items
        )
        
        self.attributes("-topmost", False)
        if success:
            messagebox.showinfo("성공", f"CI가 생성되었습니다.\n{result}", parent=self)
        else:
            messagebox.showerror("실패", result, parent=self)
        self.attributes("-topmost", True)

    def export_pl(self):
        client_name = self.entry_client.get()
        if not client_name:
            self.attributes("-topmost", False)
            messagebox.showwarning("경고", "고객사를 선택해주세요.", parent=self)
            self.attributes("-topmost", True)
            return

        client_row = self.dm.df_clients[self.dm.df_clients["업체명"] == client_name]
        if client_row.empty:
            self.attributes("-topmost", False)
            messagebox.showerror("오류", "고객 정보를 찾을 수 없습니다.", parent=self)
            self.attributes("-topmost", True)
            return
        
        items = []
        for index, item_info in self.item_widgets_map.items():
            entry_widget = item_info["entry"]
            row_data = item_info["row_data"]
            
            try:
                deliver_qty = float(entry_widget.get().replace(",", ""))
            except:
                deliver_qty = 0
            
            if deliver_qty <= 0: continue
            
            items.append({
                "model": row_data.get("모델명", ""),
                "desc": row_data.get("Description", ""),
                "qty": deliver_qty,
                "po_no": row_data.get("발주서번호", ""),
                "serial": str(row_data.get("시리얼번호", "-"))
            })

        if not items:
            self.attributes("-topmost", False)
            messagebox.showwarning("경고", "출고 수량이 입력된 항목이 없습니다.", parent=self)
            self.attributes("-topmost", True)
            return

        initial_data = {
            "client_name": client_name,
            "mgmt_no": self.current_delivery_no,
            "date": self.entry_delivery_date.get(),
            "items": items
        }

        def on_pl_confirm(pl_items, notes):
            first_po = items[0].get("po_no", "") if items else ""
            
            order_info = {
                "client_name": client_name,
                "mgmt_no": self.current_delivery_no,
                "date": self.entry_delivery_date.get(),
                "po_no": first_po,
                "notes": notes
            }
            
            success, result = self.export_manager.export_pl_to_pdf(
                client_row.iloc[0], order_info, pl_items
            )
            return success, result 

        self.attributes("-topmost", False)
        PackingListPopup(self, self.dm, on_pl_confirm, initial_data)

    # ==========================================================================
    # 저장 (납품 처리) 메서드
    # ==========================================================================
    def save(self):
        delivery_date = self.entry_delivery_date.get()
        invoice_no = self.entry_invoice_no.get()
        shipping_method = self.entry_shipping_method.get()

        if not delivery_date:
            messagebox.showwarning("경고", "출고일을 입력하세요.", parent=self)
            return

        try: current_user = getpass.getuser()
        except: current_user = "Unknown"

        update_requests = []
        
        for index, item_widget in self.item_widgets_map.items():
            try:
                val = item_widget["entry"].get().replace(",", "")
                deliver_qty = float(val)
            except ValueError:
                messagebox.showerror("오류", "출고 수량은 숫자여야 합니다.", parent=self)
                return
            
            if deliver_qty < 0:
                messagebox.showerror("오류", "출고 수량은 0보다 작을 수 없습니다.", parent=self)
                return
            
            if deliver_qty == 0:
                continue

            if deliver_qty > item_widget["current_qty"]:
                messagebox.showerror("오류", f"출고 수량이 잔여 수량을 초과했습니다.\n(품목: {item_widget['row_data'].get('품목명','')})", parent=self)
                return

            serial_no = str(item_widget["row_data"].get("시리얼번호", "-"))
            
            update_requests.append({
                "idx": index,
                "deliver_qty": deliver_qty,
                "current_qty": item_widget["current_qty"],
                "serial_no": serial_no
            })
        
        if not update_requests:
            messagebox.showinfo("정보", "처리할 품목(수량 > 0)이 없습니다.", parent=self)
            return

        waybill_path = ""
        if self.entry_waybill_file:
            waybill_path = self.full_paths.get("운송장경로", "")
            if not waybill_path:
                waybill_path = self.entry_waybill_file.get().strip()

        def update_logic(dfs):
            processed_items = []
            new_delivery_records = []
            final_waybill_path = "" 

            client_name = self.entry_client.get().strip()
            main_mgmt_no = self.mgmt_nos[0]
            
            final_delivery_no = self.current_delivery_no

            if waybill_path and os.path.exists(waybill_path):
                target_dir = os.path.join(Config.DEFAULT_ATTACHMENT_ROOT, "운송장")
                if not os.path.exists(target_dir):
                    try: os.makedirs(target_dir)
                    except Exception as e: print(f"Folder Create Error: {e}")
                
                ext = os.path.splitext(waybill_path)[1]
                safe_client = "".join([c for c in client_name if c.isalnum() or c in (' ', '_')]).strip()
                new_filename = f"운송장_{safe_client}_{main_mgmt_no}{ext}"
                target_path = os.path.join(target_dir, new_filename)
                
                if os.path.abspath(waybill_path) != os.path.abspath(target_path):
                    try:
                        shutil.copy2(waybill_path, target_path)
                        final_waybill_path = target_path
                    except Exception as e:
                        return False, f"운송장 파일 복사 실패: {e}"
                else:
                    final_waybill_path = waybill_path
            elif waybill_path:
                 final_waybill_path = ""

            for req in update_requests:
                idx = req["idx"]
                deliver_qty = req["deliver_qty"]
                serial_no = req["serial_no"]

                if idx not in dfs["data"].index: 
                    continue 
                
                row_data = dfs["data"].loc[idx]
                
                try: db_qty = float(str(row_data["수량"]).replace(",", ""))
                except: db_qty = 0

                if deliver_qty > db_qty:
                    deliver_qty = db_qty
                    if deliver_qty <= 0: continue

                try: price = float(str(row_data.get("단가", 0)).replace(",", ""))
                except: price = 0
                
                try: tax_rate = float(str(row_data.get("세율(%)", 0)).replace(",", "")) / 100
                except: tax_rate = 0

                new_delivery_records.append({
                    "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "출고번호": final_delivery_no, 
                    "출고일": delivery_date,
                    "관리번호": row_data.get("관리번호", ""),
                    "품목명": row_data.get("품목명", ""),
                    "시리얼번호": serial_no,
                    "출고수량": deliver_qty,
                    "송장번호": invoice_no,
                    "운송방법": shipping_method,
                    "작업자": current_user,
                    "비고": "일괄 납품 처리"
                })

                current_status = str(row_data.get("Status", ""))
                if current_status == "납품대기/입금완료":
                    new_status = "완료"
                else:
                    new_status = "납품완료/입금대기"

                if abs(deliver_qty - db_qty) < 0.000001:
                    dfs["data"].at[idx, "Status"] = new_status
                    dfs["data"].at[idx, "출고일"] = delivery_date
                    dfs["data"].at[idx, "송장번호"] = invoice_no
                    dfs["data"].at[idx, "운송방법"] = shipping_method
                    dfs["data"].at[idx, "운송장경로"] = final_waybill_path
                    
                    total_amt = float(str(row_data.get("합계금액", 0)).replace(",", ""))
                    dfs["data"].at[idx, "미수금액"] = total_amt
                    
                else: 
                    remain_qty = db_qty - deliver_qty
                    remain_supply = remain_qty * price
                    remain_tax = remain_supply * tax_rate
                    dfs["data"].at[idx, "수량"] = remain_qty
                    dfs["data"].at[idx, "공급가액"] = remain_supply
                    dfs["data"].at[idx, "세액"] = remain_tax
                    dfs["data"].at[idx, "합계금액"] = remain_supply + remain_tax
                    dfs["data"].at[idx, "미수금액"] = remain_supply + remain_tax
                    
                    new_row = row_data.copy()
                    new_supply = deliver_qty * price
                    new_tax = new_supply * tax_rate
                    
                    new_row["수량"] = deliver_qty
                    new_row["공급가액"] = new_supply
                    new_row["세액"] = new_tax
                    new_row["합계금액"] = new_supply + new_tax
                    new_row["미수금액"] = new_supply + new_tax
                    new_row["Status"] = new_status
                    new_row["출고일"] = delivery_date
                    new_row["송장번호"] = invoice_no
                    new_row["운송방법"] = shipping_method
                    new_row["운송장경로"] = final_waybill_path 
                    
                    new_df = pd.DataFrame([new_row])
                    dfs["data"] = pd.concat([dfs["data"], new_df], ignore_index=True)
                
                processed_items.append(f"{row_data.get('품목명','')} ({deliver_qty}개)")

            if not processed_items:
                return False, "처리 가능한 항목이 없거나 데이터가 변경되었습니다."

            if new_delivery_records:
                delivery_df_new = pd.DataFrame(new_delivery_records)
                dfs["delivery"] = pd.concat([dfs["delivery"], delivery_df_new], ignore_index=True)

            mgmt_str = self.mgmt_nos[0]
            if len(self.mgmt_nos) > 1:
                mgmt_str += f" 외 {len(self.mgmt_nos)-1}건"
            
            file_log = " / 운송장 첨부" if final_waybill_path else ""
            log_msg = f"번호 [{mgmt_str}] 납품 처리(출고번호: {final_delivery_no}) / {', '.join(processed_items)}{file_log}"
            new_log = self.dm._create_log_entry("납품 처리", log_msg)
            dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
            return True, ""

        success, msg = self.dm._execute_transaction(update_logic)
        
        if success:
            messagebox.showinfo("성공", "납품 처리가 완료되었습니다.\n(CI/PL 발행 가능)", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", f"저장에 실패했습니다: {msg}", parent=self)

    # BasePopup 추상 메서드 구현 (사용 안함)
    def _create_top_frame(self): pass
    def _create_items_frame(self): pass
    def _create_bottom_frame(self): pass
    def _create_files_frame(self): pass
    def _create_action_buttons(self): pass
    def delete(self): pass
    def _generate_new_id(self): pass
    def _add_item_row(self, item_data=None): pass
    def _calculate_totals(self): pass
    def _on_client_select(self, client_name): pass
    def _load_clients(self): pass