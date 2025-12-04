import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import getpass

import customtkinter as ctk
import pandas as pd

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
            
        self.geometry("1100x800")

    def _create_payment_specific_widgets(self):
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

        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        try:
            btn_frame = self.winfo_children()[-1]
            form_frame.pack(fill="x", padx=20, pady=10, before=btn_frame)
        except:
            form_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(form_frame, text="입금액", font=FONTS["main_bold"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_payment = ctk.CTkEntry(form_frame, width=200, font=FONTS["header"])
        self.entry_payment.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(form_frame, text="입금일", font=FONTS["main_bold"]).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.entry_pay_date = ctk.CTkEntry(form_frame, width=150)
        self.entry_pay_date.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.entry_pay_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

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

        def update_logic(dfs):
            mask = dfs["data"]["관리번호"].isin(self.mgmt_nos)
            if not mask.any():
                return False, "데이터를 찾을 수 없습니다."

            indices = dfs["data"][mask].index
            
            # [수정] 1. 강제 재계산 (동기화)
            # 입금 로직 시작 전, 현재까지의 Payment 이력 기반으로 Data 시트의 잔액을 '정확하게' 맞춤
            for mgmt_no in self.mgmt_nos:
                self.dm.recalc_payment_status(dfs, mgmt_no)

            # 2. 배치 처리용 집계 딕셔너리
            batch_summary = {}
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            remaining_payment = payment_amount

            # 3. 미수금 차감 시뮬레이션 및 이력 누적
            for idx in indices:
                if remaining_payment <= 0: break
                
                mgmt_no = dfs["data"].at[idx, "관리번호"]
                currency = str(dfs["data"].at[idx, "통화"]).upper()
                threshold = 200 if currency != "KRW" else 5000
                
                if mgmt_no not in batch_summary:
                    batch_summary[mgmt_no] = {'deposit': 0, 'fee': 0, 'currency': currency}

                # 이제 미수금은 recalc 되었으므로 정확함
                try: unpaid = float(dfs["data"].at[idx, "미수금액"])
                except: unpaid = 0
                
                if unpaid > 0:
                    actual_pay = 0
                    fee_pay = 0
                    
                    if remaining_payment >= unpaid:
                        actual_pay = unpaid
                    else:
                        diff = unpaid - remaining_payment
                        # threshold는 잔액이 '아주 조금' 남았을 때 털어버리기 위함
                        # 남은 돈이 threshold 이하일 때만 물어봐야 함
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

                    # 집계에만 반영 (Data 시트 직접 수정 X -> 루프 후 recalc에서 일괄 처리)
                    batch_summary[mgmt_no]['deposit'] += actual_pay
                    batch_summary[mgmt_no]['fee'] += fee_pay
                    
                    remaining_payment -= actual_pay

            # 4. Payment 시트에 이력 기록 (1건으로 통합)
            new_payment_records = []
            
            for mgmt_no, summary in batch_summary.items():
                if summary['deposit'] > 0:
                    new_payment_records.append({
                        "일시": now_str,
                        "관리번호": mgmt_no,
                        "구분": "입금",
                        "입금액": summary['deposit'],
                        "통화": summary['currency'],
                        "작업자": current_user,
                        "비고": f"일괄 입금 ({payment_date})"
                    })
                
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

            # 5. 최종 재계산 (방금 추가한 이력 포함하여 Data 시트 갱신)
            for mgmt_no in self.mgmt_nos:
                self.dm.recalc_payment_status(dfs, mgmt_no)

            mgmt_str = self.mgmt_nos[0]
            if len(self.mgmt_nos) > 1: mgmt_str += f" 외 {len(self.mgmt_nos)-1}건"
            
            log_msg = f"번호 [{mgmt_str}] / 입금액 [{payment_amount:,.0f}] 처리 (재계산 완료)"
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