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
from styles import COLORS, FONTS

class PaymentPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_nos):
        if isinstance(mgmt_nos, list):
            self.mgmt_nos = mgmt_nos
        else:
            self.mgmt_nos = [mgmt_nos]

        if not self.mgmt_nos:
            messagebox.showerror("오류", "수금 처리할 대상이 지정되지 않았습니다.", parent=parent)
            self.destroy()
            return
            
        self.full_paths = {}
        super().__init__(parent, data_manager, refresh_callback, popup_title="수금", mgmt_no=self.mgmt_nos[0])

    def _create_widgets(self):
        super()._create_widgets()
        self._create_payment_specific_widgets()
        
        try:
            for child in self.scroll_items.master.winfo_children():
                if isinstance(child, ctk.CTkButton):
                    child.destroy()
        except:
            pass
            
        self.geometry("1100x850")

    def _create_payment_specific_widgets(self):
        # ... (Summary frame - No changes) ...
        summary_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], corner_radius=10)
        try:
            list_frame = self.scroll_items.master
            summary_frame.pack(fill="x", padx=20, pady=(0, 10), before=list_frame)
        except:
            summary_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.lbl_total_amount = self._add_summary_row(summary_frame, "총 합계금액", "0", 0)
        self.lbl_paid_amount = self._add_summary_row(summary_frame, "기수금액", "0", 1)
        
        line = ctk.CTkFrame(summary_frame, height=2, fg_color=COLORS["border"])
        line.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=5)
        
        ctk.CTkLabel(summary_frame, text="남은 미수금", font=FONTS["header"], text_color=COLORS["danger"]).grid(row=3, column=0, padx=15, pady=(5, 15), sticky="w")
        self.lbl_unpaid_amount = ctk.CTkLabel(summary_frame, text="0", font=FONTS["title"], text_color=COLORS["danger"])
        self.lbl_unpaid_amount.grid(row=3, column=1, padx=15, pady=(5, 15), sticky="e")

        # Form Frame
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        try:
            btn_frame = self.winfo_children()[-1]
            form_frame.pack(fill="x", padx=20, pady=10, before=btn_frame)
        except:
            form_frame.pack(fill="x", padx=20, pady=10)
        
        # Row 0
        ctk.CTkLabel(form_frame, text="입금액", font=FONTS["main_bold"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_payment = ctk.CTkEntry(form_frame, width=200, font=FONTS["header"])
        self.entry_payment.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(form_frame, text="입금일", font=FONTS["main_bold"]).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.entry_pay_date = ctk.CTkEntry(form_frame, width=150)
        self.entry_pay_date.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.entry_pay_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Row 1: Foreign Currency File
        ctk.CTkLabel(form_frame, text="외국환 거래 계산서", font=FONTS["main"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_file_foreign = ctk.CTkEntry(form_frame, width=300)
        self.entry_file_foreign.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        
        btn_frame_1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame_1.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        ctk.CTkButton(btn_frame_1, text="열기", width=50, command=lambda: self.open_file(self.entry_file_foreign, "외화입금증빙경로"), fg_color=COLORS["bg_medium"], text_color=COLORS["text"]).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame_1, text="삭제", width=50, command=lambda: self.clear_entry(self.entry_file_foreign, "외화입금증빙경로"), fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"]).pack(side="left", padx=2)

        # Row 2: Remittance Detail File
        ctk.CTkLabel(form_frame, text="Remittance Detail", font=FONTS["main"]).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_file_remit = ctk.CTkEntry(form_frame, width=300)
        self.entry_file_remit.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        btn_frame_2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame_2.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        ctk.CTkButton(btn_frame_2, text="열기", width=50, command=lambda: self.open_file(self.entry_file_remit, "송금상세경로"), fg_color=COLORS["bg_medium"], text_color=COLORS["text"]).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame_2, text="삭제", width=50, command=lambda: self.clear_entry(self.entry_file_remit, "송금상세경로"), fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"]).pack(side="left", padx=2)

        # [Fix] DND Setup with windnd
        try:
            def hook_dnd():
                if self.entry_file_foreign.winfo_exists():
                    windnd.hook_dropfiles(self.entry_file_foreign.winfo_id(), 
                                          lambda f: self.on_drop(f, "외화입금증빙경로"))
                if self.entry_file_remit.winfo_exists():
                    windnd.hook_dropfiles(self.entry_file_remit.winfo_id(), 
                                          lambda f: self.on_drop(f, "송금상세경로"))
            
            self.after(200, hook_dnd)
        except Exception as e:
            print(f"DnD Error: {e}")

    def on_drop(self, filenames, col_name):
        if filenames:
            try:
                file_path = filenames[0].decode('mbcs')
            except:
                try: file_path = filenames[0].decode('utf-8', errors='ignore')
                except: return
            
            self.update_file_entry(col_name, file_path)

    def update_file_entry(self, col_name, full_path):
        if not full_path: return
        self.full_paths[col_name] = full_path
        
        target_entry = None
        if col_name == "외화입금증빙경로": target_entry = self.entry_file_foreign
        elif col_name == "송금상세경로": target_entry = self.entry_file_remit
        
        if target_entry:
            target_entry.delete(0, "end")
            target_entry.insert(0, os.path.basename(full_path))

    def open_file(self, entry, col_name):
        path = self.full_paths.get(col_name)
        if not path: path = entry.get().strip()
        if path and os.path.exists(path):
            try: os.startfile(path)
            except: messagebox.showerror("오류", "파일을 열 수 없습니다.")
        else:
            messagebox.showwarning("경고", "유효한 파일 경로가 아닙니다.")

    def clear_entry(self, entry, col_name):
        entry.delete(0, "end")
        if col_name in self.full_paths:
            del self.full_paths[col_name]

    def _add_summary_row(self, parent, label_text, value_text, row):
        ctk.CTkLabel(parent, text=label_text, font=FONTS["main"], text_color=COLORS["text_dim"]).grid(row=row, column=0, padx=15, pady=5, sticky="w")
        value_label = ctk.CTkLabel(parent, text=value_text, font=FONTS["main_bold"])
        value_label.grid(row=row, column=1, padx=15, pady=5, sticky="e")
        parent.grid_columnconfigure(1, weight=1)
        return value_label

    def _load_data(self):
        df = self.dm.df_data
        rows = df[df["관리번호"].isin(self.mgmt_nos)].copy()
        
        if rows.empty: return

        first = rows.iloc[0]

        self.entry_id.configure(state="normal")
        self.entry_id.delete(0, "end")
        
        if len(self.mgmt_nos) > 1:
            self.entry_id.insert(0, f"{self.mgmt_nos[0]} 외 {len(self.mgmt_nos)-1}건")
        else:
            self.entry_id.insert(0, str(self.mgmt_nos[0]))
            
        self.entry_id.configure(state="readonly")
        
        self.combo_status.set(str(first.get("Status", "")))
        
        widgets = [
            (self.entry_client, "업체명"),
            (self.entry_project, "프로젝트명"),
            (self.entry_req, "주문요청사항"),
            (self.entry_note, "비고")
        ]
        
        for widget, col in widgets:
            if widget is None: continue
            val = str(first.get(col, ""))
            if val == "nan": val = ""
            widget.configure(state="normal")
            widget.delete(0, "end")
            widget.insert(0, val)
            widget.configure(state="readonly")

        for _, row in rows.iterrows():
            widgets = self._add_item_row(row)
            for w in widgets.values():
                if isinstance(w, ctk.CTkEntry):
                    w.configure(state="readonly")
            
            try:
                for child in widgets["frame"].winfo_children():
                    if isinstance(child, ctk.CTkButton):
                        child.destroy()
            except: pass

        self._calculate_and_display_totals(rows)
        
    def _add_item_row(self, item_data=None):
        row_widgets = super()._add_item_row(item_data)
        if item_data is not None:
            def set_val(key, val, is_num=False):
                if is_num:
                    try: val = f"{float(str(val).replace(',', '')):,.0f}"
                    except: val = "0"
                else:
                    val = str(val)
                    if val == "nan": val = ""
                
                w = row_widgets[key]
                w.delete(0, "end")
                w.insert(0, val)

            set_val("item", item_data.get("품목명", ""))
            set_val("model", item_data.get("모델명", ""))
            set_val("desc", item_data.get("Description", ""))
            set_val("qty", item_data.get("수량", 0), is_num=True)
            set_val("price", item_data.get("단가", 0), is_num=True)
            
            for k in ["supply", "tax", "total"]:
                row_widgets[k].configure(state="normal")
            
            set_val("supply", item_data.get("공급가액", 0), is_num=True)
            set_val("tax", item_data.get("세액", 0), is_num=True)
            set_val("total", item_data.get("합계금액", 0), is_num=True)
            
            for k in ["supply", "tax", "total"]:
                row_widgets[k].configure(state="readonly")
                
        return row_widgets

    def _calculate_and_display_totals(self, df_rows):
        try:
            total_amount = pd.to_numeric(df_rows["합계금액"], errors='coerce').sum()
            paid_amount = pd.to_numeric(df_rows["기수금액"], errors='coerce').sum()
        except:
            total_amount = 0
            paid_amount = 0
            
        unpaid_amount = total_amount - paid_amount

        self.lbl_total_amount.configure(text=f"{total_amount:,.0f}")
        self.lbl_paid_amount.configure(text=f"{paid_amount:,.0f}")
        self.lbl_unpaid_amount.configure(text=f"{unpaid_amount:,.0f}")
        
        self.entry_payment.delete(0, "end")
        self.entry_payment.insert(0, f"{unpaid_amount:.0f}")

    def save(self):
        try:
            payment_amount = float(self.entry_payment.get().replace(",", ""))
        except ValueError:
            messagebox.showerror("오류", "입금액은 숫자여야 합니다.", parent=self)
            return

        if payment_amount <= 0:
            messagebox.showwarning("확인", "입금액이 0보다 커야 합니다.", parent=self)
            return

        payment_date = self.entry_pay_date.get()
        try: current_user = getpass.getuser()
        except: current_user = "Unknown"

        # File Saving Logic
        saved_paths = {}
        target_dir = os.path.join(Config.DEFAULT_ATTACHMENT_ROOT, "입금")
        
        file_inputs = [
            ("외화입금증빙경로", self.entry_file_foreign, "외화 입금"),
            ("송금상세경로", self.entry_file_remit, "Remittance detail")
        ]

        for col, entry, prefix in file_inputs:
            path = self.full_paths.get(col)
            if not path: path = entry.get().strip()
            
            if path and os.path.exists(path):
                if not os.path.exists(target_dir):
                    try: os.makedirs(target_dir)
                    except: pass
                
                try:
                    client_name = self.dm.df_data.loc[self.dm.df_data["관리번호"] == self.mgmt_nos[0], "업체명"].values[0]
                except: client_name = "Unknown"
                
                safe_client = "".join([c for c in str(client_name) if c.isalnum() or c in (' ', '_')]).strip()
                ext = os.path.splitext(path)[1]
                
                new_name = f"{prefix}_{safe_client}_{self.mgmt_nos[0]}{ext}"
                target_path = os.path.join(target_dir, new_name)
                
                if os.path.abspath(path) != os.path.abspath(target_path):
                    try:
                        shutil.copy2(path, target_path)
                        saved_paths[col] = target_path
                    except Exception as e:
                        print(f"File copy error ({col}): {e}")
                else:
                    saved_paths[col] = path
            else:
                saved_paths[col] = "" 

        def update_logic(dfs):
            mask = dfs["data"]["관리번호"].isin(self.mgmt_nos)
            if not mask.any():
                return False, "데이터를 찾을 수 없습니다."

            indices = dfs["data"][mask].index
            
            # 1. 강제 재계산
            for mgmt_no in self.mgmt_nos:
                self.dm.recalc_payment_status(dfs, mgmt_no)

            # 2. 배치 처리용 집계
            batch_summary = {}
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            remaining_payment = payment_amount

            # 3. 미수금 차감 시뮬레이션
            for idx in indices:
                if remaining_payment <= 0: break
                
                mgmt_no = dfs["data"].at[idx, "관리번호"]
                currency = str(dfs["data"].at[idx, "통화"]).upper()
                threshold = 200 if currency != "KRW" else 5000
                
                if mgmt_no not in batch_summary:
                    batch_summary[mgmt_no] = {'deposit': 0, 'fee': 0, 'currency': currency}

                try: unpaid = float(dfs["data"].at[idx, "미수금액"])
                except: unpaid = 0
                
                if unpaid > 0:
                    actual_pay = 0
                    fee_pay = 0
                    
                    if remaining_payment >= unpaid:
                        actual_pay = unpaid
                    else:
                        diff = unpaid - remaining_payment
                        if diff <= threshold:
                            item_name = str(dfs["data"].at[idx, "품목명"])
                            if messagebox.askyesno("수수료 처리 확인", 
                                                   f"[{item_name}] 항목의 잔액이 {diff:,.0f} ({currency}) 남습니다.\n"
                                                   f"이를 수수료로 처리하여 '완납' 하시겠습니까?"):
                                actual_pay = remaining_payment
                                fee_pay = diff
                            else:
                                actual_pay = remaining_payment
                        else:
                            actual_pay = remaining_payment

                    batch_summary[mgmt_no]['deposit'] += actual_pay
                    batch_summary[mgmt_no]['fee'] += fee_pay
                    
                    remaining_payment -= actual_pay

            # 4. Payment 시트에 이력 기록
            new_payment_records = []
            
            for mgmt_no, summary in batch_summary.items():
                if summary['deposit'] > 0:
                    record = {
                        "일시": now_str,
                        "관리번호": mgmt_no,
                        "구분": "입금",
                        "입금액": summary['deposit'],
                        "통화": summary['currency'],
                        "작업자": current_user,
                        "비고": f"일괄 입금 ({payment_date})"
                    }
                    if "외화입금증빙경로" in saved_paths:
                        record["외화입금증빙경로"] = saved_paths["외화입금증빙경로"]
                    if "송금상세경로" in saved_paths:
                        record["송금상세경로"] = saved_paths["송금상세경로"]
                        
                    new_payment_records.append(record)
                
                if summary['fee'] > 0:
                    new_payment_records.append({
                        "일시": now_str,
                        "관리번호": mgmt_no,
                        "구분": "수수료/조정",
                        "입금액": summary['fee'],
                        "통화": summary['currency'],
                        "작업자": current_user,
                        "비고": "잔액 탕감 처리"
                    })

            if new_payment_records:
                payment_df_new = pd.DataFrame(new_payment_records)
                dfs["payment"] = pd.concat([dfs["payment"], payment_df_new], ignore_index=True)

            # 5. 최종 재계산
            for mgmt_no in self.mgmt_nos:
                self.dm.recalc_payment_status(dfs, mgmt_no)

            mgmt_str = self.mgmt_nos[0]
            if len(self.mgmt_nos) > 1: mgmt_str += f" 외 {len(self.mgmt_nos)-1}건"
            
            file_log = ""
            if saved_paths.get("외화입금증빙경로"): file_log += " / 외화증빙"
            if saved_paths.get("송금상세경로"): file_log += " / 송금상세"
            
            log_msg = f"번호 [{mgmt_str}] / 입금액 [{payment_amount:,.0f}] 처리{file_log} (재계산 완료)"
            new_log = self.dm._create_log_entry("수금 처리", log_msg)
            dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)

            return True, ""

        success, msg = self.dm._execute_transaction(update_logic)

        if success:
            messagebox.showinfo("성공", "수금 처리가 완료되었습니다.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", f"저장에 실패했습니다: {msg}", parent=self)
    
    def _generate_new_id(self): pass
    def delete(self): pass
    def _on_client_select(self, client_name): pass 
    def _calculate_totals(self): pass