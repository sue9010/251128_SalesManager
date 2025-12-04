import os
import shutil
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import windnd

import customtkinter as ctk
import pandas as pd

from popups.base_popup import BasePopup
from styles import COLORS, FONTS
from config import Config
from export_manager import ExportManager # Import 추가 확인

class OrderPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_no=None):
        self.full_paths = {}
        self.export_manager = ExportManager() # 인스턴스 생성
        super().__init__(parent, data_manager, refresh_callback, popup_title="주문", mgmt_no=mgmt_no)

        if not mgmt_no:
            self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
            self.combo_status.set("주문")
            if hasattr(self, 'btn_export_order'):
                self.btn_export_order.grid_remove()
    
    def _create_widgets(self):
        self._create_top_frame()
        self._create_items_frame()
        self._create_bottom_frame()
        self._create_action_buttons()
        self._create_additional_frames()
        self._layout_top_frame()
    
    # ... (_create_top_frame, _layout_top_frame 등 기존 코드 유지) ...
    # ... 반드시 기존 코드와 동일하게 유지해야 함 ...

    def _create_top_frame(self):
        super()._create_top_frame()

        self.lbl_date = ctk.CTkLabel(self.top_frame, text="주문일자", font=FONTS["main_bold"])
        self.entry_date = ctk.CTkEntry(self.top_frame, width=200, font=FONTS["main"], placeholder_text="YYYY-MM-DD")

        self.lbl_type = ctk.CTkLabel(self.top_frame, text="구분", font=FONTS["main_bold"])
        self.combo_type = ctk.CTkComboBox(self.top_frame, values=["내수", "수출"], width=200, font=FONTS["main"], command=self.on_type_change)
        self.combo_type.set("내수")

        self.lbl_currency = ctk.CTkLabel(self.top_frame, text="통화", font=FONTS["main_bold"])
        self.combo_currency = ctk.CTkComboBox(self.top_frame, values=["KRW", "USD", "EUR", "CNY", "JPY"], width=200, font=FONTS["main"], command=self.on_currency_change)
        self.combo_currency.set("KRW")

        self.lbl_tax_rate = ctk.CTkLabel(self.top_frame, text="세율(%)", font=FONTS["main_bold"])
        self.entry_tax_rate = ctk.CTkEntry(self.top_frame, width=200, font=FONTS["main"])
        self.entry_tax_rate.insert(0, "10")
        self.entry_tax_rate.bind("<KeyRelease>", lambda e: self._calculate_totals())

        # [신규] 출고요청서 발행 버튼 생성
        self.btn_export_order = ctk.CTkButton(self.top_frame, text="출고요청서", command=self.export_order_request, width=120, height=40,
                                        fg_color=COLORS["success"], hover_color="#26A65B", text_color="white", font=FONTS["main_bold"])

    def _layout_top_frame(self):
        self.lbl_id.grid(row=0, column=0, padx=5, sticky="w")
        self.entry_id.grid(row=0, column=1, padx=5, sticky="w")
        self.lbl_date.grid(row=0, column=2, padx=5, sticky="w")
        self.entry_date.grid(row=0, column=3, padx=5, sticky="w")
        self.lbl_type.grid(row=0, column=4, padx=5, sticky="w")
        self.combo_type.grid(row=0, column=5, padx=5, sticky="w")
        self.lbl_status.grid(row=0, column=6, padx=5, sticky="w")
        self.combo_status.grid(row=0, column=7, padx=5, sticky="w")

        self.lbl_client.grid(row=1, column=0, padx=5, pady=10, sticky="w")
        self.entry_client.grid(row=1, column=1, padx=5, pady=10, sticky="w")
        self.lbl_currency.grid(row=1, column=2, padx=5, pady=10, sticky="w")
        self.combo_currency.grid(row=1, column=3, padx=5, pady=10, sticky="w")
        self.lbl_tax_rate.grid(row=1, column=4, padx=5, pady=10, sticky="w")
        self.entry_tax_rate.grid(row=1, column=5, padx=5, pady=10, sticky="w")

        self.lbl_project.grid(row=2, column=0, padx=5, sticky="w")
        self.entry_project.grid(row=2, column=1, columnspan=5, padx=5, sticky="ew")
        
        # [신규] 버튼 배치
        self.btn_export_order.grid(row=2, column=6, columnspan=2, padx=5, sticky="e")

    # ... (나머지 메서드 생략, 기존과 동일) ...
    # ... (_create_bottom_frame, _create_additional_frames, _on_client_select 등) ...
    def _create_bottom_frame(self):
        self.input_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.input_grid.pack(fill="x", padx=20, pady=(10, 10))
        
        # 주문요청사항 표시
        ctk.CTkLabel(self.input_grid, text="주문요청사항:", font=FONTS["main"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_req = ctk.CTkEntry(self.input_grid, width=300)
        self.entry_req.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 비고
        ctk.CTkLabel(self.input_grid, text="비고:", font=FONTS["main"]).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.entry_note = ctk.CTkEntry(self.input_grid, width=300)
        self.entry_note.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        self.input_grid.columnconfigure(1, weight=1)
        self.input_grid.columnconfigure(3, weight=1)

        # 발주서 등록
        row_idx = 1
        ctk.CTkLabel(self.input_grid, text="발주서:", font=FONTS["main"]).grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        
        self.entry_order_file = ctk.CTkEntry(self.input_grid, width=300)
        self.entry_order_file.grid(row=row_idx, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        
        file_btn_frame = ctk.CTkFrame(self.input_grid, fg_color="transparent")
        file_btn_frame.grid(row=row_idx, column=4, padx=5, pady=5, sticky="w")
        
        col_name = "발주서경로"
        ctk.CTkButton(file_btn_frame, text="열기", width=50, 
                      command=lambda: self.open_file(self.entry_order_file, col_name), 
                      fg_color=COLORS["bg_medium"], text_color=COLORS["text"]).pack(side="left", padx=2)
        
        ctk.CTkButton(file_btn_frame, text="삭제", width=50, 
                      command=lambda: self.clear_entry(self.entry_order_file, col_name), 
                      fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"]).pack(side="left", padx=2)

        try:
            def hook_dnd():
                if self.entry_order_file.winfo_exists():
                    windnd.hook_dropfiles(self.entry_order_file.winfo_id(), self.on_drop)
            self.after(100, hook_dnd)
        except Exception as e:
            print(f"DnD Error: {e}")

    # 파일 관련 메서드
    def update_file_entry(self, col_name, full_path):
        if not full_path: return
        self.full_paths[col_name] = full_path
        if col_name == "발주서경로" and self.entry_order_file:
            self.entry_order_file.delete(0, "end")
            self.entry_order_file.insert(0, os.path.basename(full_path))

    def on_drop(self, filenames):
        if filenames:
            try: file_path = filenames[0].decode('mbcs')
            except: file_path = filenames[0].decode('utf-8', errors='ignore')
            self.update_file_entry("발주서경로", file_path)

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
                    if self.mgmt_no:
                        def update_db_logic(dfs):
                            df = dfs["data"]
                            mask = df["관리번호"] == self.mgmt_no
                            if mask.any(): df.loc[mask, col_name] = ""
                            return True, ""
                        self.dm._execute_transaction(update_db_logic)
                except Exception as e:
                    messagebox.showerror("오류", f"삭제 실패: {e}", parent=self)
                    return
                entry_widget.delete(0, "end")
                if col_name in self.full_paths: del self.full_paths[col_name]
        else:
            entry_widget.delete(0, "end")
            if col_name in self.full_paths: del self.full_paths[col_name]

    def _create_additional_frames(self):
        items_frame = self.winfo_children()[1]
        info_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], height=40)
        info_frame.pack(fill="x", padx=20, pady=(0, 10), before=items_frame)
        ctk.CTkLabel(info_frame, text="업체 특이사항:", font=FONTS["main_bold"], text_color=COLORS["primary"]).pack(side="left", padx=10, pady=5)
        self.lbl_client_note = ctk.CTkLabel(info_frame, text="-", font=FONTS["main"])
        self.lbl_client_note.pack(side="left", padx=5, pady=5)

        items_frame_content = items_frame.winfo_children()
        try:
            add_item_button = next(w for w in items_frame_content if isinstance(w, ctk.CTkButton))
            total_frame = ctk.CTkFrame(items_frame, fg_color="transparent")
            total_frame.pack(fill="x", pady=5, before=add_item_button)
            self.lbl_total_qty = ctk.CTkLabel(total_frame, text="총 수량: 0", font=FONTS["main_bold"])
            self.lbl_total_qty.pack(side="left", padx=10)
            self.lbl_total_amt = ctk.CTkLabel(total_frame, text="총 합계금액: 0", font=FONTS["header"], text_color=COLORS["primary"])
            self.lbl_total_amt.pack(side="left", padx=20)
        except StopIteration: pass

    def _on_client_select(self, client_name):
        df = self.dm.df_clients
        row = df[df["업체명"] == client_name]
        if not row.empty:
            currency = row.iloc[0].get("통화", "KRW")
            if currency and str(currency) != "nan":
                self.combo_currency.set(currency)
                self.on_currency_change(currency)
            note = str(row.iloc[0].get("특이사항", "-"))
            if note == "nan" or not note: note = "-"
            self.lbl_client_note.configure(text=note)

    def on_type_change(self, type_val): self._calculate_totals()

    def on_currency_change(self, currency):
        if currency == "KRW":
            self.entry_tax_rate.delete(0, "end")
            self.entry_tax_rate.insert(0, "10")
            self.combo_type.set("내수")
        else:
            self.entry_tax_rate.delete(0, "end")
            self.entry_tax_rate.insert(0, "0")
            self.combo_type.set("수출")
        self._calculate_totals()

    def _generate_new_id(self):
        # 주문 번호 생성 (O + 날짜)
        today_str = datetime.now().strftime("%y%m%d")
        prefix = f"O{today_str}"
        
        df = self.dm.df_data
        existing_ids = df[df["관리번호"].str.startswith(prefix)]["관리번호"].unique()
        
        if len(existing_ids) == 0: seq = 1
        else:
            max_seq = 0
            for eid in existing_ids:
                try:
                    parts = eid.split("-")
                    if len(parts) > 1:
                        seq_num = int(parts[-1])
                        if seq_num > max_seq: max_seq = seq_num
                except: pass
            seq = max_seq + 1
            
        new_id = f"{prefix}-{seq:03d}"
        self.entry_id.configure(state="normal")
        self.entry_id.delete(0, "end")
        self.entry_id.insert(0, new_id)
        self.entry_id.configure(state="readonly")

    def _add_item_row(self, item_data=None):
        row_widgets = super()._add_item_row()
        row_widgets["qty"].insert(0, "1")
        row_widgets["price"].insert(0, "0")
        row_widgets["qty"].bind("<KeyRelease>", lambda e, rw=row_widgets: self.calculate_row(rw))
        row_widgets["price"].bind("<KeyRelease>", lambda e, w=row_widgets["price"], rw=row_widgets: self.on_price_change(e, w, rw))

        if item_data is not None:
            row_widgets["item"].insert(0, str(item_data.get("품목명", "")))
            row_widgets["model"].insert(0, str(item_data.get("모델명", "")))
            row_widgets["desc"].insert(0, str(item_data.get("Description", "")))
            row_widgets["qty"].delete(0, "end"); row_widgets["qty"].insert(0, str(item_data.get("수량", 0)))
            price_val = float(item_data.get("단가", 0))
            row_widgets["price"].delete(0, "end"); row_widgets["price"].insert(0, f"{int(price_val):,}")
            self.calculate_row(row_widgets)

    def on_price_change(self, event, widget, row_data):
        val = widget.get().replace(",", "")
        if val.isdigit():
            formatted = f"{int(val):,}"
            if widget.get() != formatted:
                widget.delete(0, "end")
                widget.insert(0, formatted)
        self.calculate_row(row_data)

    def calculate_row(self, row_data):
        try:
            qty = float(row_data["qty"].get().strip().replace(",","") or 0)
            price = float(row_data["price"].get().strip().replace(",","") or 0)
            supply = qty * price
            try: tax_rate = float(self.entry_tax_rate.get().strip() or 0)
            except: tax_rate = 0
            tax = supply * (tax_rate / 100)
            total = supply + tax
            
            def update_entry(entry, val):
                entry.configure(state="normal")
                entry.delete(0, "end")
                entry.insert(0, f"{val:,.0f}")
                entry.configure(state="readonly")

            update_entry(row_data["supply"], supply)
            update_entry(row_data["tax"], tax)
            update_entry(row_data["total"], total)
        except ValueError: pass
        self._calculate_totals()

    def _calculate_totals(self):
        total_qty = 0
        total_amt = 0
        for row in self.item_rows:
            try:
                q = float(row["qty"].get().replace(",",""))
                t = float(row["total"].get().replace(",",""))
                total_qty += q
                total_amt += t
            except: pass
        self.lbl_total_qty.configure(text=f"총 수량: {total_qty:,.0f}")
        self.lbl_total_amt.configure(text=f"총 합계금액: {total_amt:,.0f}")

    def _load_data(self):
        df = self.dm.df_data
        rows = df[df["관리번호"] == self.mgmt_no]
        if rows.empty: return
        
        first = rows.iloc[0]
        self.entry_id.configure(state="normal")
        self.entry_id.delete(0, "end")
        self.entry_id.insert(0, str(first["관리번호"]))
        self.entry_id.configure(state="readonly")
        
        date_val = str(first.get("수주일", ""))
        self.entry_date.insert(0, date_val)

        self.combo_type.set(str(first.get("구분", "내수")))
        
        client_name = str(first.get("업체명", ""))
        self.entry_client.delete(0, "end")
        self.entry_client.insert(0, client_name)
        
        self.combo_currency.set(str(first.get("통화", "KRW")))
        
        saved_tax = first.get("세율(%)", "")
        if saved_tax != "" and saved_tax != "-": tax_rate = str(saved_tax)
        else:
            currency = str(first.get("통화", "KRW"))
            tax_rate = "10" if currency == "KRW" else "0"
        self.entry_tax_rate.delete(0, "end")
        self.entry_tax_rate.insert(0, tax_rate)

        self.entry_project.insert(0, str(first.get("프로젝트명", "")))
        
        self.entry_req.insert(0, str(first.get("주문요청사항", "")).replace("nan", ""))
        
        if self.entry_order_file:
            path = str(first.get("발주서경로", "")).replace("nan", "")
            if path: self.update_file_entry("발주서경로", path)
            
        self.entry_note.insert(0, str(first.get("비고", "")))
        
        current_status = str(first.get("Status", "주문"))
        self.combo_status.set(current_status)
        
        # [신규] 상태에 따라 버튼 표시
        if current_status in ["주문", "생산중"]:
            if hasattr(self, 'btn_export_order'): self.btn_export_order.grid()
        else:
            if hasattr(self, 'btn_export_order'): self.btn_export_order.grid_remove()
        
        self._on_client_select(client_name)
        for _, row in rows.iterrows(): self._add_item_row(row)

    def save(self):
        mgmt_no = self.entry_id.get()
        client = self.entry_client.get()
        
        if not client:
            messagebox.showwarning("경고", "고객사를 선택해주세요.", parent=self)
            return
        if not self.item_rows:
            messagebox.showwarning("경고", "최소 1개 이상의 품목을 추가해주세요.", parent=self)
            return

        try: tax_rate_val = float(self.entry_tax_rate.get().strip())
        except: tax_rate_val = 0

        new_rows = []
        req_note_val = self.entry_req.get()
        
        order_file_path = ""
        if self.entry_order_file:
            order_file_path = self.full_paths.get("발주서경로", "")
            if not order_file_path:
                order_file_path = self.entry_order_file.get().strip()

        common_data = {
            "관리번호": mgmt_no,
            "구분": self.combo_type.get(),
            "업체명": client,
            "프로젝트명": self.entry_project.get(),
            "통화": self.combo_currency.get(),
            "환율": 1, 
            "세율(%)": tax_rate_val,
            "주문요청사항": req_note_val,
            "비고": self.entry_note.get(),
            "Status": self.combo_status.get(),
            "발주서경로": order_file_path,
            "수주일": self.entry_date.get()
        }
        
        for item in self.item_rows:
            row_data = common_data.copy()
            row_data.update({
                "품목명": item["item"].get(), "모델명": item["model"].get(), "Description": item["desc"].get(),
                "수량": float(item["qty"].get().replace(",","") or 0),
                "단가": float(item["price"].get().replace(",","") or 0),
                "공급가액": float(item["supply"].get().replace(",","") or 0),
                "세액": float(item["tax"].get().replace(",","") or 0),
                "합계금액": float(item["total"].get().replace(",","") or 0),
                "기수금액": 0, "미수금액": float(item["total"].get().replace(",","") or 0)
            })
            new_rows.append(row_data)

        def update_logic(dfs):
            order_path = common_data.get("발주서경로", "")
            if order_path and os.path.exists(order_path):
                target_dir = os.path.join(Config.DEFAULT_ATTACHMENT_ROOT, "발주서")
                if not os.path.exists(target_dir):
                    try: os.makedirs(target_dir)
                    except Exception as e: print(f"Folder Create Error: {e}")
                
                ext = os.path.splitext(order_path)[1]
                safe_client = "".join([c for c in client if c.isalnum() or c in (' ', '_')]).strip()
                # 관리번호를 사용하여 파일명 생성
                new_filename = f"발주서_{safe_client}_{mgmt_no}{ext}"
                target_path = os.path.join(target_dir, new_filename)
                
                if os.path.abspath(order_path) != os.path.abspath(target_path):
                    try:
                        shutil.copy2(order_path, target_path)
                        common_data["발주서경로"] = target_path
                        for r in new_rows: r["발주서경로"] = target_path
                    except Exception as e:
                        return False, f"파일 복사 실패: {e}"

            if self.mgmt_no:
                mask = dfs["data"]["관리번호"] == self.mgmt_no
                existing_rows = dfs["data"][mask]
                if not existing_rows.empty:
                    first_exist = existing_rows.iloc[0]
                    for row in new_rows:
                        row["견적일"] = first_exist.get("견적일", "-")
                        row["출고예정일"] = first_exist.get("출고예정일", "-")
                        row["출고일"] = first_exist.get("출고일", "-")
                        row["입금완료일"] = first_exist.get("입금완료일", "-")
                
                dfs["data"] = dfs["data"][~mask]
            
            new_df = pd.DataFrame(new_rows)
            dfs["data"] = pd.concat([dfs["data"], new_df], ignore_index=True)
            
            action = "수정" if self.mgmt_no else "등록"
            log_msg = f"주문 {action}: 번호 [{mgmt_no}] / 업체 [{client}]"
            new_log = self.dm._create_log_entry(f"주문 {action}", log_msg)
            dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
            
            return True, ""

        success, msg = self.dm._execute_transaction(update_logic)
        
        if success:
            messagebox.showinfo("완료", "저장되었습니다.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", msg, parent=self)

    def delete(self):
        # (기존 delete 메서드 유지)
        if messagebox.askyesno("삭제 확인", f"정말 이 {self.popup_title} 데이터를 삭제하시겠습니까?", parent=self):
            def update_logic(dfs):
                mask = dfs["data"]["관리번호"] == self.mgmt_no
                if mask.any():
                    dfs["data"] = dfs["data"][~mask]
                    log_msg = f"{self.popup_title} 삭제: 번호 [{self.mgmt_no}]"
                    new_log = self.dm._create_log_entry("삭제", log_msg)
                    dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
                    return True, ""
                return False, "삭제할 데이터를 찾을 수 없습니다."

            success, msg = self.dm._execute_transaction(update_logic)
            if success:
                messagebox.showinfo("삭제 완료", "데이터가 삭제되었습니다.", parent=self)
                self.refresh_callback()
                self.destroy()
            else:
                messagebox.showerror("실패", msg, parent=self)

    # [NEW] 출고요청서 발행 구현
    def export_order_request(self):
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
        
        order_info = {
            "client_name": client_name,
            "mgmt_no": self.entry_id.get(),
            "date": self.entry_date.get(),
            "type": self.combo_type.get(),
            "req_note": self.entry_req.get(),
        }
        
        items = []
        for row in self.item_rows:
            items.append({
                "item": row["item"].get(),
                "model": row["model"].get(),
                "desc": row["desc"].get(),
                "qty": float(row["qty"].get().replace(",", "") or 0),
            })

        success, result = self.export_manager.export_order_request_to_pdf(
            client_row.iloc[0], order_info, items
        )
        
        self.attributes("-topmost", False)
        if success:
            messagebox.showinfo("성공", f"출고요청서가 생성되었습니다.\n{result}", parent=self)
        else:
            messagebox.showerror("실패", result, parent=self)
        self.attributes("-topmost", True)