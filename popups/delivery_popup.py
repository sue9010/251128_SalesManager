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
            self.destroy()
            return

        self.item_widgets_map = {} # row_index를 키로 사용하여 위젯을 관리
        super().__init__(parent, data_manager, refresh_callback, popup_title="납품", mgmt_no=mgmt_no)

    def _create_widgets(self):
        # BasePopup의 기본 위젯 생성 (상단, 하단, 버튼 등)
        # 단, _create_items_frame은 아래에서 오버라이드된 버전이 호출됨
        super()._create_widgets()
        
        # 납품 전용 위젯 생성 및 상단 레이아웃 재구성
        self._create_delivery_specific_widgets()
        
        # [수정] 팝업 전체 너비 축소 (1100 -> 900)
        self.geometry("900x750")

    # [수정] BasePopup의 메서드를 오버라이드하여 납품 전용 헤더 생성
    def _create_items_frame(self):
        """품목을 표시하는 스크롤 가능한 프레임과 헤더를 생성합니다. (납품 전용)"""
        list_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"])
        list_frame.pack(fill="both", expand=True, padx=20, pady=5)

        # [수정] 납품 팝업 전용 헤더 및 너비 설정 (총합 750px)
        # 품명(250) + 모델명(300) + 잔여(100) + 출고(100)
        headers = ["품명", "모델명", "잔여 수량", "출고 수량"]
        widths = [250, 300, 100, 100]
        
        header_frame = ctk.CTkFrame(list_frame, height=30, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x")
        
        for h, w in zip(headers, widths):
            lbl = ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["small"])
            lbl.pack(side="left", padx=2)

        self.scroll_items = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.scroll_items.pack(fill="both", expand=True)

        # 납품 팝업에서는 '품목 추가' 버튼이 필요 없으므로 생성하지 않음

    def _create_delivery_specific_widgets(self):
        # --- 납품 정보 위젯 생성 ---
        
        # 1. 새 위젯 생성 (출고일, 운송방법, 송장번호) -> self.top_frame에 배치
        self.lbl_delivery_date = ctk.CTkLabel(self.top_frame, text="출고일", font=FONTS["main_bold"])
        self.entry_delivery_date = ctk.CTkEntry(self.top_frame, width=150)
        self.entry_delivery_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        self.lbl_shipping_method = ctk.CTkLabel(self.top_frame, text="운송 방법", font=FONTS["main_bold"])
        self.entry_shipping_method = ctk.CTkEntry(self.top_frame, width=150)

        self.lbl_invoice_no = ctk.CTkLabel(self.top_frame, text="송장번호", font=FONTS["main_bold"])
        self.entry_invoice_no = ctk.CTkEntry(self.top_frame, width=200)

        # 2. 레이아웃 재구성 (3행 구조)
        # BasePopup에서 이미 grid로 배치된 위젯들을 포함하여 재배치
        
        # 1행: 관리번호 | 고객사 | 상태
        self.lbl_id.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_id.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        self.lbl_client.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.entry_client.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        self.lbl_status.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.combo_status.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        # 2행: 프로젝트명 (가로 확장)
        self.lbl_project.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_project.grid(row=1, column=1, columnspan=5, padx=5, pady=5, sticky="ew")

        # 3행: 출고일 | 운송방법 | 송장번호
        self.lbl_delivery_date.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_delivery_date.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        self.lbl_shipping_method.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.entry_shipping_method.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        
        self.lbl_invoice_no.grid(row=2, column=4, padx=5, pady=5, sticky="w")
        self.entry_invoice_no.grid(row=2, column=5, padx=5, pady=5, sticky="w")

        # 버튼 텍스트 변경 (저장 -> 납품 처리)
        try:
            # BasePopup의 구조에 따라 버튼 프레임 위치 찾기 (마지막 위젯일 확률 높음)
            widgets = self.winfo_children()
            if widgets:
                btn_frame = widgets[-1]
                for child in btn_frame.winfo_children():
                    if isinstance(child, ctk.CTkButton) and child.cget("text") == "저장":
                        child.configure(text="납품 처리")
        except:
            pass

    def _load_data(self):
        """데이터 로드 및 UI 반영"""
        df = self.dm.df_data
        
        # 납품 가능한 항목만 필터링
        rows = df[df["관리번호"] == self.mgmt_no].copy()
        
        if rows.empty:
            messagebox.showinfo("정보", "데이터를 찾을 수 없습니다.", parent=self)
            self.after(100, self.destroy)
            return

        first = rows.iloc[0]

        # 1. 기본 정보 위젯 리스트
        widgets_to_load = [
            (self.entry_client, "업체명"),
            (self.entry_project, "프로젝트명"),
            (self.entry_req, "주문요청사항"),
            (self.entry_note, "비고")
        ]

        # 2. 관리번호 설정
        self.entry_id.configure(state="normal")
        self.entry_id.delete(0, "end")
        self.entry_id.insert(0, str(self.mgmt_no))
        self.entry_id.configure(state="readonly")

        # 3. 상태 설정
        self.combo_status.set(str(first.get("Status", "")))
        self.combo_status.configure(state="disabled")

        # 4. 각 텍스트 위젯에 데이터 로드
        for widget, col in widgets_to_load:
            val = str(first.get(col, ""))
            if val == "nan": val = ""
            
            widget.configure(state="normal")
            widget.delete(0, "end")
            widget.insert(0, val)
            widget.configure(state="readonly")

        # 5. 납품 대상 품목 리스트 생성
        # 완료, 취소, 보류 및 이미 납품 완료된 건 제외
        target_rows = rows[~rows["Status"].isin(["납품완료/입금대기", "완료", "취소", "보류"])]
        
        for index, row_data in target_rows.iterrows():
            self._add_delivery_item_row(index, row_data)

    def _add_delivery_item_row(self, row_index, item_data):
        row_frame = ctk.CTkFrame(self.scroll_items, fg_color="transparent", height=35)
        row_frame.pack(fill="x", pady=2)

        # [수정] 각 위젯 너비 조정 (헤더와 동기화: 250, 300, 100, 100)
        
        # 품명 (250)
        ctk.CTkLabel(row_frame, text=str(item_data.get("품목명", "")), width=250, anchor="w").pack(side="left", padx=2)
        # 모델명 (300)
        ctk.CTkLabel(row_frame, text=str(item_data.get("모델명", "")), width=300, anchor="w").pack(side="left", padx=2)
        
        # 잔여 수량 (안전한 변환)
        try:
            raw_qty = str(item_data.get("수량", "0")).replace(",", "")
            current_qty = float(raw_qty)
        except ValueError:
            current_qty = 0.0

        # 잔여 수량 (100)
        ctk.CTkLabel(row_frame, text=f"{current_qty:g}", width=100).pack(side="left", padx=2)
        
        # 출고 수량 입력창 (100) - 기본값: 잔여 수량
        entry_deliver_qty = ctk.CTkEntry(row_frame, width=100, justify="center")
        entry_deliver_qty.pack(side="left", padx=2)
        entry_deliver_qty.insert(0, f"{current_qty:g}")

        # 위젯 관리 맵에 저장
        self.item_widgets_map[row_index] = {
            "current_qty": current_qty,
            "entry": entry_deliver_qty,
            "row_data": item_data
        }

    def save(self):
        """납품 처리 로직"""
        delivery_date = self.entry_delivery_date.get()
        invoice_no = self.entry_invoice_no.get()
        shipping_method = self.entry_shipping_method.get()

        if not delivery_date:
            messagebox.showwarning("경고", "출고일을 입력하세요.", parent=self)
            return

        update_requests = []
        
        # 입력된 출고 수량 검증 및 요청 목록 생성
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
            
            # 0이면 처리하지 않음 (건너뜀)
            if deliver_qty == 0:
                continue

            if deliver_qty > item_widget["current_qty"]:
                messagebox.showerror("오류", f"출고 수량이 잔여 수량을 초과했습니다.\n(품목: {item_widget['row_data'].get('품목명','')})", parent=self)
                return

            update_requests.append({
                "idx": index,
                "deliver_qty": deliver_qty,
                "current_qty": item_widget["current_qty"]
            })
        
        if not update_requests:
            messagebox.showinfo("정보", "처리할 품목(수량 > 0)이 없습니다.", parent=self)
            return

        def update_logic(dfs):
            processed_items = []
            for req in update_requests:
                idx = req["idx"]
                deliver_qty = req["deliver_qty"]

                if idx not in dfs["data"].index: 
                    continue 
                
                row_data = dfs["data"].loc[idx]
                
                try:
                    db_qty = float(str(row_data["수량"]).replace(",", ""))
                except:
                    db_qty = 0

                if deliver_qty > db_qty:
                    deliver_qty = db_qty
                    if deliver_qty <= 0: continue

                try: price = float(str(row_data.get("단가", 0)).replace(",", ""))
                except: price = 0
                
                try: tax_rate = float(str(row_data.get("세율(%)", 0)).replace(",", "")) / 100
                except: tax_rate = 0

                # [수정] 상태 결정 로직 추가
                current_status = str(row_data.get("Status", ""))
                if current_status == "납품대기/입금완료":
                    new_status = "완료"
                else:
                    new_status = "납품완료/입금대기"

                # Case 1: 전량 출고
                if abs(deliver_qty - db_qty) < 0.000001:
                    dfs["data"].at[idx, "Status"] = new_status
                    dfs["data"].at[idx, "출고일"] = delivery_date
                    dfs["data"].at[idx, "송장번호"] = invoice_no
                    dfs["data"].at[idx, "운송방법"] = shipping_method
                    total_amt = float(str(row_data.get("합계금액", 0)).replace(",", ""))
                    dfs["data"].at[idx, "미수금액"] = total_amt
                    
                # Case 2: 부분 출고
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
                    
                    new_df = pd.DataFrame([new_row])
                    dfs["data"] = pd.concat([dfs["data"], new_df], ignore_index=True)
                
                processed_items.append(f"{row_data.get('품목명','')} ({deliver_qty}개)")

            if not processed_items:
                return False, "처리 가능한 항목이 없거나 데이터가 변경되었습니다."

            log_msg = f"번호 [{self.mgmt_no}] 납품 처리 / {', '.join(processed_items)}"
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