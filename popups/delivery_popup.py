import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk
import pandas as pd

from popups.base_popup import BasePopup
from styles import COLORS, FONTS

class DeliveryPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_no):
        if not mgmt_no:
            messagebox.showerror("오류", "납품 처리할 대상(관리번호)이 지정되지 않았습니다.", parent=parent)
            return

        self.item_widgets_map = {} # row_index를 키로 사용하여 위젯을 관리
        super().__init__(parent, data_manager, refresh_callback, popup_title="납품", mgmt_no=mgmt_no)

    def _create_widgets(self):
        super()._create_widgets()
        self._create_delivery_specific_widgets()
        
        # 기본 품목 추가/삭제 버튼 비활성화
        self.scroll_items.master.children['!ctkbutton'].destroy()
        
        # 헤더 수정
        header_frame = self.scroll_items.master.children['!ctkframe']
        for w in header_frame.winfo_children():
            w.destroy()
        
        headers = ["품명", "모델명", "잔여 수량", "출고 수량"]
        widths = [150, 200, 100, 100]
        for h, w in zip(headers, widths):
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["small"]).pack(side="left", padx=2)

        self.geometry("1100x750")

    def _create_delivery_specific_widgets(self):
        # --- 납품 정보 입력 프레임 ---
        delivery_info_frame = ctk.CTkFrame(self, fg_color="transparent")
        delivery_info_frame.pack(fill="x", padx=20, pady=10, before=self.winfo_children()[1])

        ctk.CTkLabel(delivery_info_frame, text="출고일", font=FONTS["main_bold"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_delivery_date = ctk.CTkEntry(delivery_info_frame, width=150)
        self.entry_delivery_date.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.entry_delivery_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ctk.CTkLabel(delivery_info_frame, text="송장번호", font=FONTS["main_bold"]).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.entry_invoice_no = ctk.CTkEntry(delivery_info_frame, width=200)
        self.entry_invoice_no.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(delivery_info_frame, text="운송 방법", font=FONTS["main_bold"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_shipping_method = ctk.CTkEntry(delivery_info_frame, width=150)
        self.entry_shipping_method.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # 버튼 텍스트 변경
        btn_frame = self.winfo_children()[-1]
        btn_frame.children['!ctkbutton'].configure(text="납품 처리") # 저장 버튼

    def _load_data(self):
        df = self.dm.df_data
        rows = df[(df["관리번호"] == self.mgmt_no) & (df["Status"] != "납품완료/입금대기") & (df["Status"] != "완료")].copy()
        if rows.empty:
            messagebox.showinfo("정보", "납품할 품목이 없습니다.", parent=self)
            self.after(100, self.destroy)
            return

        first = rows.iloc[0]

        # BasePopup의 위젯에 정보 로드
        self.entry_id.configure(state="normal"); self.entry_id.insert(0, self.mgmt_no); self.entry_id.configure(state="readonly")
        self.combo_status.set(str(first.get("Status", "")))
        self.entry_client.insert(0, str(first.get("업체명", "")))
        self.entry_project.insert(0, str(first.get("프로젝트명", "")))
        self.entry_req.insert(0, str(first.get("주문요청사항", "")))
        self.entry_note.insert(0, str(first.get("비고", "")))
        
        # 모든 기본 위젯 읽기 전용으로
        for w in [self.entry_client, self.entry_project, self.entry_req, self.entry_note, self.combo_status]:
            w.configure(state="readonly")

        # 납품 대상 품목 리스트 생성
        for index, row_data in rows.iterrows():
            self._add_delivery_item_row(index, row_data)

    def _add_delivery_item_row(self, row_index, item_data):
        row_frame = ctk.CTkFrame(self.scroll_items, fg_color="transparent", height=35)
        row_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(row_frame, text=item_data.get("품목명", ""), width=150, anchor="w").pack(side="left", padx=2)
        ctk.CTkLabel(row_frame, text=item_data.get("모델명", ""), width=200, anchor="w").pack(side="left", padx=2)
        
        current_qty = float(item_data["수량"])
        ctk.CTkLabel(row_frame, text=f"{current_qty:g}", width=100).pack(side="left", padx=2)
        
        entry_deliver_qty = ctk.CTkEntry(row_frame, width=100, justify="center")
        entry_deliver_qty.pack(side="left", padx=2)
        entry_deliver_qty.insert(0, f"{current_qty:g}")

        self.item_widgets_map[row_index] = {
            "current_qty": current_qty,
            "entry": entry_deliver_qty,
            "row_data": item_data
        }

    def save(self):
        delivery_date = self.entry_delivery_date.get()
        invoice_no = self.entry_invoice_no.get()
        shipping_method = self.entry_shipping_method.get()

        if not delivery_date:
            messagebox.showwarning("경고", "출고일을 입력하세요.", parent=self)
            return

        update_requests = []
        for index, item_widget in self.item_widgets_map.items():
            try:
                deliver_qty = float(item_widget["entry"].get())
            except ValueError:
                messagebox.showerror("오류", "출고 수량은 숫자여야 합니다.", parent=self)
                return
            
            if deliver_qty < 0 or deliver_qty > item_widget["current_qty"]:
                messagebox.showerror("오류", f"출고 수량은 0 이상, 현재 수량 이하이어야 합니다.\n(품목: {item_widget['row_data']['품목명']})", parent=self)
                return

            if deliver_qty > 0:
                update_requests.append({
                    "idx": index,
                    "deliver_qty": deliver_qty,
                    "current_qty": item_widget["current_qty"]
                })
        
        if not update_requests:
            messagebox.showinfo("정보", "출고할 품목이 없습니다.", parent=self)
            return

        def update_logic(dfs):
            processed_items = []
            for req in update_requests:
                idx = req["idx"]
                deliver_qty = req["deliver_qty"]

                # 트랜잭션 내에서 최신 데이터 다시 가져오기
                if idx not in dfs["data"].index: continue
                row_data = dfs["data"].loc[idx]
                current_qty = float(row_data["수량"])

                if deliver_qty > current_qty: # 동시성 문제 등으로 데이터 변경됨
                    continue

                if deliver_qty >= current_qty: # 전체 납품
                    dfs["data"].at[idx, "Status"] = "납품완료/입금대기"
                    dfs["data"].at[idx, "출고일"] = delivery_date
                    dfs["data"].at[idx, "송장번호"] = invoice_no
                    dfs["data"].at[idx, "운송방법"] = shipping_method
                else: # 부분 납품 (행 분할)
                    remain_qty = current_qty - deliver_qty
                    price = float(row_data["단가"])
                    tax_rate = float(row_data["세율(%)"]) / 100

                    # 1. 기존 행: 잔여 수량으로 업데이트
                    remain_supply = remain_qty * price
                    remain_tax = remain_supply * tax_rate
                    dfs["data"].at[idx, "수량"] = remain_qty
                    dfs["data"].at[idx, "공급가액"] = remain_supply
                    dfs["data"].at[idx, "세액"] = remain_tax
                    dfs["data"].at[idx, "합계금액"] = remain_supply + remain_tax
                    dfs["data"].at[idx, "미수금액"] = remain_supply + remain_tax
                    
                    # 2. 새 행: 출고된 수량으로 추가
                    new_row = row_data.copy()
                    new_supply = deliver_qty * price
                    new_tax = new_supply * tax_rate
                    
                    new_row["수량"] = deliver_qty
                    new_row["공급가액"] = new_supply
                    new_row["세액"] = new_tax
                    new_row["합계금액"] = new_supply + new_tax
                    new_row["미수금액"] = new_supply + new_tax
                    new_row["Status"] = "납품완료/입금대기"
                    new_row["출고일"] = delivery_date
                    new_row["송장번호"] = invoice_no
                    new_row["운송방법"] = shipping_method
                    
                    new_df = pd.DataFrame([new_row])
                    dfs["data"] = pd.concat([dfs["data"], new_df], ignore_index=True)
                
                processed_items.append(row_data["품목명"])

            log_msg = f"번호 [{self.mgmt_no}] / 처리 품목: {', '.join(processed_items)}"
            new_log = self.dm._create_log_entry("납품 처리", log_msg)
            dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
            return True, ""

        success, msg = self.dm._execute_transaction(update_logic)
        
        if success:
            messagebox.showinfo("성공", "납품 처리가 완료되었습니다.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", f"저장에 실패했습니다: {msg}", parent=self)

    # --- 사용하지 않는 메서드 ---
    def _generate_new_id(self): pass
    def delete(self): pass
    def _add_item_row(self, item_data=None): pass
    def _calculate_totals(self): pass
    def _on_client_select(self, client_name): pass