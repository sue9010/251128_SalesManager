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
        self.full_paths = {} # 파일 경로 저장
        
        super().__init__(parent, data_manager, refresh_callback, popup_title="납품", mgmt_no=self.mgmt_nos[0])

    def _create_widgets(self):
        super()._create_widgets()
        self._create_delivery_specific_widgets()
        self.geometry("900x800")

    def _create_items_frame(self):
        list_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"])
        list_frame.pack(fill="both", expand=True, padx=20, pady=5)

        headers = ["품명", "모델명", "시리얼 번호", "잔여 수량", "출고 수량"]
        widths = [200, 200, 150, 100, 100]
        
        header_frame = ctk.CTkFrame(list_frame, height=30, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x")
        
        for h, w in zip(headers, widths):
            lbl = ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["small"])
            lbl.pack(side="left", padx=2)

        self.scroll_items = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.scroll_items.pack(fill="both", expand=True)

    def _create_delivery_specific_widgets(self):
        # 상단 입력 필드들
        self.lbl_delivery_date = ctk.CTkLabel(self.top_frame, text="출고일", font=FONTS["main_bold"])
        self.entry_delivery_date = ctk.CTkEntry(self.top_frame, width=150)
        self.entry_delivery_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        self.lbl_shipping_method = ctk.CTkLabel(self.top_frame, text="운송 방법", font=FONTS["main_bold"])
        self.entry_shipping_method = ctk.CTkEntry(self.top_frame, width=150)

        self.lbl_invoice_no = ctk.CTkLabel(self.top_frame, text="송장번호", font=FONTS["main_bold"])
        self.entry_invoice_no = ctk.CTkEntry(self.top_frame, width=200)

        # Grid 배치
        self.lbl_id.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_id.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        self.lbl_client.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.entry_client.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        self.lbl_status.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.combo_status.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        self.lbl_project.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_project.grid(row=1, column=1, columnspan=5, padx=5, pady=5, sticky="ew")

        self.lbl_delivery_date.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_delivery_date.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        self.lbl_shipping_method.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.entry_shipping_method.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        
        self.lbl_invoice_no.grid(row=2, column=4, padx=5, pady=5, sticky="w")
        self.entry_invoice_no.grid(row=2, column=5, padx=5, pady=5, sticky="w")

        # 버튼 텍스트 변경 (저장 -> 납품 처리)
        try:
            widgets = self.winfo_children()
            if widgets:
                btn_frame = widgets[-1]
                for child in btn_frame.winfo_children():
                    if isinstance(child, ctk.CTkButton) and child.cget("text") == "저장":
                        child.configure(text="납품 처리")
        except:
            pass

    # 하단 프레임 오버라이드
    def _create_bottom_frame(self):
        super()._create_bottom_frame() # 비고란 생성 (Row 0)
        
        # 파일 업로드 위젯 생성 (Row 1)
        self.lbl_waybill_file = ctk.CTkLabel(self.input_grid, text="운송장:", font=FONTS["main"])
        self.lbl_waybill_file.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        self.entry_waybill_file = ctk.CTkEntry(self.input_grid, width=300)
        self.entry_waybill_file.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # 파일 버튼 프레임
        self.file_btn_frame = ctk.CTkFrame(self.input_grid, fg_color="transparent")
        self.file_btn_frame.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        col_name = "운송장경로"
        ctk.CTkButton(self.file_btn_frame, text="열기", width=50, 
                      command=lambda: self.open_file(self.entry_waybill_file, col_name), 
                      fg_color=COLORS["bg_medium"], text_color=COLORS["text"]).pack(side="left", padx=2)
        
        ctk.CTkButton(self.file_btn_frame, text="삭제", width=50, 
                      command=lambda: self.clear_entry(self.entry_waybill_file, col_name), 
                      fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"]).pack(side="left", padx=2)

        # [Fix] OrderPopup과 동일한 방식의 Hook 설정
        try:
            def hook_dnd():
                if self.entry_waybill_file.winfo_exists():
                    # winfo_id()가 유효한 HWND를 반환하는지 확인
                    hwnd = self.entry_waybill_file.winfo_id()
                    windnd.hook_dropfiles(hwnd, self.on_drop)
            
            # 윈도우가 완전히 그려진 후 훅을 걸도록 지연
            self.after(200, hook_dnd)
        except Exception as e:
            print(f"DnD Setup Error: {e}")

    # 파일 관련 메서드들
    def update_file_entry(self, col_name, full_path):
        if not full_path: return
        self.full_paths[col_name] = full_path
        if col_name == "운송장경로" and self.entry_waybill_file:
            self.entry_waybill_file.delete(0, "end")
            self.entry_waybill_file.insert(0, os.path.basename(full_path))

    def on_drop(self, filenames):
        if filenames:
            try:
                # windnd는 bytes 리스트를 반환하므로 디코딩 필요
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
                if col_name in self.full_paths: del self.full_paths[col_name]
        else:
            entry_widget.delete(0, "end")
            if col_name in self.full_paths: del self.full_paths[col_name]

    def _load_data(self):
        df = self.dm.df_data
        rows = df[df["관리번호"].isin(self.mgmt_nos)].copy()
        
        if rows.empty:
            messagebox.showinfo("정보", "데이터를 찾을 수 없습니다.", parent=self)
            self.after(100, self.destroy)
            return

        # 시리얼 번호 매핑 데이터 가져오기
        serial_map = self.dm.get_serial_number_map()

        first = rows.iloc[0]

        widgets_to_load = [
            (self.entry_client, "업체명"),
            (self.entry_project, "프로젝트명"),
            (self.entry_req, "주문요청사항"),
            (self.entry_note, "비고")
        ]

        self.entry_id.configure(state="normal")
        self.entry_id.delete(0, "end")
        if len(self.mgmt_nos) > 1:
            self.entry_id.insert(0, f"{self.mgmt_nos[0]} 외 {len(self.mgmt_nos)-1}건")
        else:
            self.entry_id.insert(0, str(self.mgmt_nos[0]))
        self.entry_id.configure(state="readonly")

        self.combo_status.set(str(first.get("Status", "")))
        self.combo_status.configure(state="disabled")

        for widget, col in widgets_to_load:
            if widget is None: continue
            val = str(first.get(col, ""))
            if val == "nan": val = ""
            widget.configure(state="normal")
            widget.delete(0, "end")
            widget.insert(0, val)
            widget.configure(state="readonly")
        
        if self.entry_waybill_file:
            path = str(first.get("운송장경로", "")).replace("nan", "")
            if path: self.update_file_entry("운송장경로", path)

        target_rows = rows[~rows["Status"].isin(["납품완료/입금대기", "완료", "취소", "보류"])]
        
        for index, row_data in target_rows.iterrows():
            # 매핑 키 생성
            m_no = str(row_data.get("관리번호", "")).strip()
            model = str(row_data.get("모델명", "")).strip()
            desc = str(row_data.get("Description", "")).strip()
            
            # 맵에서 시리얼 찾기
            serial = serial_map.get((m_no, model, desc), "-")
            
            # 아이템 데이터에 시리얼 추가하여 전달
            item_data_with_serial = row_data.to_dict()
            item_data_with_serial["시리얼번호"] = serial
            
            self._add_delivery_item_row(index, item_data_with_serial)

    def _add_delivery_item_row(self, row_index, item_data):
        row_frame = ctk.CTkFrame(self.scroll_items, fg_color="transparent", height=35)
        row_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(row_frame, text=str(item_data.get("품목명", "")), width=200, anchor="w").pack(side="left", padx=2)
        ctk.CTkLabel(row_frame, text=str(item_data.get("모델명", "")), width=200, anchor="w").pack(side="left", padx=2)
        
        # 시리얼 번호 표시
        serial = str(item_data.get("시리얼번호", "-"))
        ctk.CTkLabel(row_frame, text=serial, width=150, anchor="center", text_color=COLORS["primary"]).pack(side="left", padx=2)
        
        try:
            raw_qty = str(item_data.get("수량", "0")).replace(",", "")
            current_qty = float(raw_qty)
        except ValueError:
            current_qty = 0.0

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

        # 현재 사용자
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

        # 운송장 파일 처리 준비
        waybill_path = ""
        if self.entry_waybill_file:
            waybill_path = self.full_paths.get("운송장경로", "")
            if not waybill_path:
                waybill_path = self.entry_waybill_file.get().strip()

        def update_logic(dfs):
            processed_items = []
            new_delivery_records = []
            final_waybill_path = "" # 실제 저장된 경로

            # 1. 파일 저장 로직 (한 번만 수행)
            client_name = self.entry_client.get().strip()
            # 대표 관리번호 사용 (여러 개일 경우 첫 번째)
            main_mgmt_no = self.mgmt_nos[0]
            
            if waybill_path and os.path.exists(waybill_path):
                target_dir = os.path.join(Config.DEFAULT_ATTACHMENT_ROOT, "운송장")
                if not os.path.exists(target_dir):
                    try: os.makedirs(target_dir)
                    except Exception as e: print(f"Folder Create Error: {e}")
                
                ext = os.path.splitext(waybill_path)[1]
                safe_client = "".join([c for c in client_name if c.isalnum() or c in (' ', '_')]).strip()
                # 파일명: 운송장_업체명_관리번호.ext
                new_filename = f"운송장_{safe_client}_{main_mgmt_no}{ext}"
                target_path = os.path.join(target_dir, new_filename)
                
                # 경로가 다르면 복사
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

                # Delivery 시트에 내역 기록
                new_delivery_records.append({
                    "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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

                # Data 시트 업데이트
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
                    dfs["data"].at[idx, "운송장경로"] = final_waybill_path # 경로 저장
                    
                    total_amt = float(str(row_data.get("합계금액", 0)).replace(",", ""))
                    dfs["data"].at[idx, "미수금액"] = total_amt
                    
                # Case 2: 부분 출고 (행 분할)
                else: 
                    # 원본 행(잔여) 업데이트
                    remain_qty = db_qty - deliver_qty
                    remain_supply = remain_qty * price
                    remain_tax = remain_supply * tax_rate
                    dfs["data"].at[idx, "수량"] = remain_qty
                    dfs["data"].at[idx, "공급가액"] = remain_supply
                    dfs["data"].at[idx, "세액"] = remain_tax
                    dfs["data"].at[idx, "합계금액"] = remain_supply + remain_tax
                    dfs["data"].at[idx, "미수금액"] = remain_supply + remain_tax
                    
                    # 신규 행(출고된 부분) 추가
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
                    new_row["운송장경로"] = final_waybill_path # 경로 저장
                    
                    new_df = pd.DataFrame([new_row])
                    dfs["data"] = pd.concat([dfs["data"], new_df], ignore_index=True)
                
                processed_items.append(f"{row_data.get('품목명','')} ({deliver_qty}개)")

            if not processed_items:
                return False, "처리 가능한 항목이 없거나 데이터가 변경되었습니다."

            # Delivery 시트에 저장
            if new_delivery_records:
                delivery_df_new = pd.DataFrame(new_delivery_records)
                dfs["delivery"] = pd.concat([dfs["delivery"], delivery_df_new], ignore_index=True)

            # 로그 기록
            mgmt_str = self.mgmt_nos[0]
            if len(self.mgmt_nos) > 1:
                mgmt_str += f" 외 {len(self.mgmt_nos)-1}건"
            
            file_log = " / 운송장 첨부" if final_waybill_path else ""
            log_msg = f"번호 [{mgmt_str}] 납품 처리 / {', '.join(processed_items)}{file_log} (Delivery 기록됨)"
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

    def _generate_new_id(self): pass
    def delete(self): pass
    def _add_item_row(self, item_data=None): pass
    def _calculate_totals(self): pass
    def _on_client_select(self, client_name): pass