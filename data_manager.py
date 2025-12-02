import getpass
import json
import os
import shutil
from datetime import datetime

import pandas as pd
import openpyxl

from config import Config


class DataManager:
    def __init__(self):
        self.df_clients = pd.DataFrame(columns=Config.CLIENT_COLUMNS)
        self.df_data = pd.DataFrame(columns=Config.DATA_COLUMNS)
        self.df_log = pd.DataFrame(columns=Config.LOG_COLUMNS)
        self.df_memo = pd.DataFrame(columns=Config.MEMO_COLUMNS)
        self.df_memo_log = pd.DataFrame(columns=Config.MEMO_LOG_COLUMNS)
        
        self.current_excel_path = Config.DEFAULT_EXCEL_PATH
        self.attachment_root = Config.DEFAULT_ATTACHMENT_ROOT
        self.production_request_path = Config.DEFAULT_PRODUCTION_REQUEST_PATH
        
        self.current_theme = "Dark"
        self.is_dev_mode = False
        
        self.load_config()

    def load_config(self):
        if os.path.exists(Config.CONFIG_FILENAME):
            try:
                with open(Config.CONFIG_FILENAME, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.current_excel_path = data.get("excel_path", Config.DEFAULT_EXCEL_PATH)
                    self.current_theme = data.get("theme", "Dark")
                    self.attachment_root = data.get("attachment_root", Config.DEFAULT_ATTACHMENT_ROOT)
                    self.production_request_path = data.get("production_request_path", Config.DEFAULT_PRODUCTION_REQUEST_PATH)
            except: pass

    def save_config(self, new_path=None, new_theme=None, new_attachment_dir=None, new_prod_path=None):
        if new_path: self.current_excel_path = new_path
        if new_theme: self.current_theme = new_theme
        if new_attachment_dir: self.attachment_root = new_attachment_dir
        if new_prod_path: self.production_request_path = new_prod_path
        
        data = {
            "excel_path": self.current_excel_path,
            "theme": self.current_theme,
            "attachment_root": self.attachment_root,
            "production_request_path": self.production_request_path
        }
        try:
            with open(Config.CONFIG_FILENAME, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"설정 저장 실패: {e}")

    def load_data(self):
        if not os.path.exists(self.current_excel_path):
            return False, "파일이 존재하지 않습니다. 새 파일을 생성합니다."

        try:
            with pd.ExcelFile(self.current_excel_path) as xls:
                if Config.SHEET_CLIENTS in xls.sheet_names:
                    self.df_clients = pd.read_excel(xls, Config.SHEET_CLIENTS)
                    self.df_clients.columns = self.df_clients.columns.str.strip()
                
                if Config.SHEET_DATA in xls.sheet_names:
                    self.df_data = pd.read_excel(xls, Config.SHEET_DATA)
                    self.df_data.columns = self.df_data.columns.str.strip()
                
                if Config.SHEET_LOG in xls.sheet_names:
                    self.df_log = pd.read_excel(xls, Config.SHEET_LOG)
                if Config.SHEET_MEMO in xls.sheet_names:
                    self.df_memo = pd.read_excel(xls, Config.SHEET_MEMO)
                if Config.SHEET_MEMO_LOG in xls.sheet_names:
                    self.df_memo_log = pd.read_excel(xls, Config.SHEET_MEMO_LOG)

            self._preprocess_data()
            return True, "데이터 로드 완료"
        except Exception as e:
            return False, f"오류 발생: {e}"

    def _preprocess_data(self):
        for col in Config.DATA_COLUMNS:
            if col not in self.df_data.columns:
                self.df_data[col] = "-"
        
        self.df_data = self.df_data.fillna("-")
        self.df_clients = self.df_clients.fillna("-")
        
        num_cols = ["수량", "단가", "환율", "세율(%)", "공급가액", "세액", "합계금액", "기수금액", "미수금액"]
        for col in num_cols:
            if col in self.df_data.columns:
                self.df_data[col] = pd.to_numeric(self.df_data[col], errors='coerce').fillna(0)

        date_cols = ["견적일", "수주일", "출고예정일", "출고일", "선적일", "입금완료일", "세금계산서발행일"]
        for col in date_cols:
            if col in self.df_data.columns:
                self.df_data[col] = pd.to_datetime(self.df_data[col], errors='coerce', format='mixed').dt.strftime("%Y-%m-%d")
                self.df_data[col] = self.df_data[col].fillna("-")

    def save_to_excel(self):
        try:
            with pd.ExcelWriter(self.current_excel_path, engine="openpyxl") as writer:
                self.df_clients.to_excel(writer, sheet_name=Config.SHEET_CLIENTS, index=False)
                self.df_data.to_excel(writer, sheet_name=Config.SHEET_DATA, index=False)
                self.df_log.to_excel(writer, sheet_name=Config.SHEET_LOG, index=False)
                self.df_memo.to_excel(writer, sheet_name=Config.SHEET_MEMO, index=False)
                self.df_memo_log.to_excel(writer, sheet_name=Config.SHEET_MEMO_LOG, index=False)
            return True, "저장 완료"
        except PermissionError:
            return False, "엑셀 파일이 열려있습니다. 파일을 닫고 다시 시도해주세요."
        except Exception as e:
            return False, f"저장 실패: {e}"

    def save_attachment(self, source_path, company_name, file_prefix):
        if not os.path.exists(source_path): return None, "파일 없음"
        try:
            current_year = datetime.now().strftime("%Y")
            year_dir = os.path.join(self.attachment_root, current_year)
            if not os.path.exists(year_dir): os.makedirs(year_dir)

            safe_name = "".join([c for c in str(company_name) if c.isalnum() or c in (' ', '_', '-')]).strip()
            comp_dir = os.path.join(year_dir, safe_name)
            if not os.path.exists(comp_dir): os.makedirs(comp_dir)

            fname = os.path.basename(source_path)
            name, ext = os.path.splitext(fname)
            today = datetime.now().strftime("%Y%m%d")
            new_name = f"{file_prefix}_{today}_{name}{ext}"
            
            dest_path = os.path.join(comp_dir, new_name)
            shutil.copy2(source_path, dest_path)
            return dest_path, None
        except Exception as e:
            return None, str(e)

    def add_log(self, action, details):
        try: user = getpass.getuser()
        except: user = "Unknown"
        new = {"일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "작업자": user, "구분": action, "상세내용": details}
        new_df = pd.DataFrame([new])
        if self.df_log.empty: self.df_log = new_df
        else: self.df_log = pd.concat([self.df_log, new_df], ignore_index=True)
    
    def get_status_by_req_no(self, req_no):
        if self.df_data.empty: return None
        rows = self.df_data[self.df_data["관리번호"] == req_no]
        return rows.iloc[0]["Status"] if not rows.empty else None

    def get_filtered_data(self, status_list=None, keyword=""):
        df = self.df_data
        if df.empty: return df
        if status_list: df = df[df["Status"].isin(status_list)]
        if keyword:
            mask = pd.Series(False, index=df.index)
            for col in Config.SEARCH_TARGET_COLS:
                if col in df.columns:
                    mask |= df[col].astype(str).str.contains(keyword, case=False)
            df = df[mask]
        return df

    def set_dev_mode(self, enabled): self.is_dev_mode = enabled
    
    def create_backup(self):
        if not os.path.exists(self.current_excel_path): return False, "파일 없음"
        try:
            folder = os.path.dirname(self.current_excel_path)
            backup_folder = os.path.join(folder, "backup")
            if not os.path.exists(backup_folder): os.makedirs(backup_folder)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = os.path.basename(self.current_excel_path)
            shutil.copy2(self.current_excel_path, os.path.join(backup_folder, f"{fname}_{timestamp}.bak"))
            return True, "백업 완료"
        except Exception as e: return False, str(e)

    def clean_old_logs(self): return True, "로그 정리 완료"

    def export_to_production_request(self, rows_data):
        """
        SalesList의 특정 행 데이터들(List of Series/Dict)을 생산요청.xlsx 파일의 Data 시트에 추가합니다.
        동일한 관리번호(번호)와 모델명, 상세가 있는 행이 이미 있다면 업데이트(덮어쓰기)하고,
        없다면 새로 추가합니다.
        """
        prod_path = self.production_request_path
        if not os.path.exists(prod_path):
            return False, f"생산 요청 파일을 찾을 수 없습니다.\n경로: {prod_path}"

        try:
            wb = openpyxl.load_workbook(prod_path)
            if "Data" not in wb.sheetnames:
                return False, "'Data' 시트가 존재하지 않습니다."
            ws = wb["Data"]

            # 2. 업데이트/추가 카운트
            added_count = 0
            updated_count = 0

            # 3. 각 행별 처리
            for row_data in rows_data:
                # 업체 특이사항 조회
                client_name = row_data.get("업체명", "")
                client_note = "-"
                if not self.df_clients.empty:
                    c_row = self.df_clients[self.df_clients["업체명"] == client_name]
                    if not c_row.empty:
                        val = c_row.iloc[0].get("특이사항", "-")
                        if str(val) != "nan" and val:
                            client_note = str(val)

                mgmt_no = str(row_data.get("관리번호", ""))
                model_name = str(row_data.get("모델명", ""))
                desc = str(row_data.get("Description", ""))

                # 매핑 데이터 준비 (16개 컬럼)
                mapping_values = [
                    mgmt_no,                                # A: 번호
                    client_name,                            # B: 업체명
                    model_name,                             # C: 모델명
                    desc,                                   # D: 상세
                    row_data.get("수량", 0),                # E: 수량
                    row_data.get("주문요청사항", ""),       # F: 기타요청사항
                    client_note,                            # G: 업체별 특이사항
                    row_data.get("수주일", ""),             # H: 출고요청일
                    "-",                                    # I: 출고예정일 (초기값 '-')
                    "-",                                    # J: 출고일
                    "-",                                    # K: 시리얼번호
                    "-",                                    # L: 렌즈업체
                    "-",                                    # M: 생산팀 메모
                    "생산 접수",                            # N: Status
                    row_data.get("발주서경로", ""),         # O: 파일경로
                    "-"                                     # P: 대기사유
                ]

                # 중복 체크 (번호, 모델명, 상세 내용이 모두 일치하는 행 찾기)
                target_row_idx = None
                
                # 헤더 제외하고 2행부터 검색
                # [성능 고려] 데이터가 많을 경우 전체 스캔이 느릴 수 있으나, 현재 구조상 불가피함.
                for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                    # A열(번호), C열(모델명), D열(상세) 비교
                    curr_mgmt = str(row[0]) if row[0] else ""
                    curr_model = str(row[2]) if row[2] else ""
                    curr_desc = str(row[3]) if row[3] else ""
                    
                    if curr_mgmt == mgmt_no and curr_model == model_name and curr_desc == desc:
                        target_row_idx = i
                        break
                
                if target_row_idx:
                    # 업데이트
                    for col_idx, val in enumerate(mapping_values, start=1):
                        # I열(9번째, 출고예정일) 이후의 값들은 생산팀이 수정했을 수 있으므로
                        # '생산 접수' 상태로 초기화할지, 값을 보존할지 결정해야 함.
                        # 사용자 요구사항: "초기값 - 로 입력해줘" -> 리셋 로직 적용
                        ws.cell(row=target_row_idx, column=col_idx, value=val)
                    updated_count += 1
                else:
                    # 신규 추가
                    ws.append(mapping_values)
                    added_count += 1

            wb.save(prod_path)
            wb.close()
            
            return True, f"신규: {added_count}건, 업데이트: {updated_count}건 처리되었습니다."

        except PermissionError:
            return False, "생산 요청 파일이 열려있습니다. 파일을 닫고 다시 시도해주세요."
        except Exception as e:
            return False, f"생산 요청 내보내기 실패: {e}"