import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk
import pandas as pd

from popups.base_popup import BasePopup
from styles import COLORS, FONTS

class PaymentPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_nos):
        # [수정] 관리번호 리스트 처리
        if isinstance(mgmt_nos, list):
            self.mgmt_nos = mgmt_nos
        else:
            self.mgmt_nos = [mgmt_nos]

        if not self.mgmt_nos:
            messagebox.showerror("오류", "수금 처리할 대상이 지정되지 않았습니다.", parent=parent)
            self.destroy()
            return
            
        # BasePopup에는 대표 번호 하나만 넘김
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
        
        # [수정] 여러 관리번호에 해당하는 데이터 로드
        rows = df[df["관리번호"].isin(self.mgmt_nos)].copy()
        
        if rows.empty: return

        first = rows.iloc[0]

        # 기본 정보 로드
        self.entry_id.configure(state="normal")
        self.entry_id.delete(0, "end")
        
        # [수정] 관리번호 표시 (다중일 경우)
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

        # 품목 정보 로드
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

        def update_logic(dfs):
            # [수정] 다중 관리번호 처리
            # 모든 대상 행을 찾음 (isin 사용)
            mask = dfs["data"]["관리번호"].isin(self.mgmt_nos)
            if not mask.any():
                return False, "데이터를 찾을 수 없습니다."

            # 대상 행들의 인덱스를 가져옴 (순서 보장을 위해 정렬 권장)
            # 여기서는 출고일이나 관리번호 순 등으로 정렬하여 처리할 수도 있음
            # 기본적으로 데이터프레임 순서(등록순)대로 처리
            indices = dfs["data"][mask].index
            
            # 미수금액이 있는 항목들에 입금액 분배 (순차적 차감)
            remaining_payment = payment_amount
            processed_mgmts = set()

            for idx in indices:
                if remaining_payment <= 0: break
                
                try: unpaid = float(dfs["data"].at[idx, "미수금액"])
                except: unpaid = 0
                
                if unpaid > 0:
                    pay_for_item = min(remaining_payment, unpaid)
                    
                    try: current_paid = float(dfs["data"].at[idx, "기수금액"])
                    except: current_paid = 0
                    
                    dfs["data"].at[idx, "기수금액"] = current_paid + pay_for_item
                    dfs["data"].at[idx, "미수금액"] = unpaid - pay_for_item
                    remaining_payment -= pay_for_item
                    
                    processed_mgmts.add(dfs["data"].at[idx, "관리번호"])

            # 상태 업데이트 (각 행별로 재계산)
            # 주의: 분배 로직 루프 밖에서 다시 모든 대상 행을 순회하며 상태 결정
            for idx in indices:
                try: 
                    row_unpaid = float(dfs["data"].at[idx, "미수금액"])
                    row_status = str(dfs["data"].at[idx, "Status"])
                except: continue

                if row_unpaid < 1:
                    # 완납 시
                    if row_status == "납품완료/입금대기":
                        new_status = "완료"
                    else:
                        new_status = "납품대기/입금완료"
                    
                    dfs["data"].at[idx, "입금완료일"] = payment_date
                else:
                    # 미납 시 (상태 유지)
                    new_status = row_status
                
                dfs["data"].at[idx, "Status"] = new_status

            # 로그 기록
            mgmt_str = self.mgmt_nos[0]
            if len(self.mgmt_nos) > 1: mgmt_str += f" 외 {len(self.mgmt_nos)-1}건"
            
            log_msg = f"번호 [{mgmt_str}] / 총 입금액 [{payment_amount:,.0f}]"
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
    
    # --- 사용하지 않는 메서드 ---
    def _generate_new_id(self): pass
    def delete(self): pass
    def _on_client_select(self, client_name): pass 
    def _calculate_totals(self): pass