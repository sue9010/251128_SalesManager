import os
import time
import openpyxl
from config import Config

class ExportManager:
    def __init__(self):
        pass

    def export_quote_to_pdf(self, client_info, quote_info, items):
        """
        견적서 데이터를 받아 엑셀 템플릿에 채우고 PDF로 변환합니다.
        
        Process:
        1. 템플릿 선택 (KR/EN)
        2. openpyxl로 데이터 기입 (엑셀 실행 X, 빠름)
        3. win32com으로 엑셀을 '백그라운드'에서 열어 PDF 내보내기 (엑셀 실행 O)
        """
        try:
            import win32com.client
            import pythoncom
        except ImportError:
            return False, "PDF 변환을 위해 pywin32 라이브러리가 필요합니다.\n설치: pip install pywin32"

        temp_xlsx_path = None
        excel = None
        wb_opened = None

        try:
            # --- 1. 템플릿 파일 결정 ---
            client_name = quote_info['client_name']
            mgmt_no = quote_info['mgmt_no']
            
            # 국가 정보 확인 (한국/KR 등이 포함되면 국문, 아니면 영문)
            country = str(client_info.get("국가", "Korea")).upper()
            is_kr = any(x in country for x in ["대한민국", "KR", "한국", "KOREA"])
            
            template_filename = "Quotation_KR.xlsx" if is_kr else "Quotation_EN.xlsx"
            # forms 폴더 경로 (config.py의 DEFAULT_ATTACHMENT_ROOT 하위)
            template_dir = os.path.join(Config.DEFAULT_ATTACHMENT_ROOT, "forms")
            template_path = os.path.join(template_dir, template_filename)

            if not os.path.exists(template_path):
                # 파일이 없을 경우 기본 경로 등 예외 처리 (테스트용)
                return False, f"견적서 양식 파일을 찾을 수 없습니다.\n경로: {template_path}"

            # --- 2. 엑셀 내용 작성 (openpyxl 사용 - 엑셀 프로세스 없이 빠름) ---
            wb = openpyxl.load_workbook(template_path)
            ws = wb.active # 첫 번째 시트 사용

            # [고객 정보 매핑]
            ws["B7"] = client_name
            ws["B8"] = str(client_info.get("담당자", ""))
            ws["B9"] = str(client_info.get("전화번호", ""))
            ws["B10"] = str(client_info.get("주소", ""))

            # [견적 정보 매핑]
            ws["G10"] = quote_info['date']
            ws["G11"] = mgmt_no

            # [품목 정보 매핑] (B14행부터 시작, 최대 10개 가정)
            start_row = 14
            for i, item in enumerate(items):
                if i >= 10: break # 양식 한계상 10개까지만 (필요 시 양식 수정 필요)
                r_idx = start_row + i
                
                ws[f"B{r_idx}"] = item.get('item', '')
                ws[f"C{r_idx}"] = item.get('model', '')
                ws[f"D{r_idx}"] = item.get('desc', '')
                ws[f"E{r_idx}"] = item.get('qty', 0)
                ws[f"F{r_idx}"] = item.get('price', 0)
                # 수식 대신 계산된 값 입력 (또는 엑셀 수식 유지하려면 문자열 "=..." 사용)
                ws[f"G{r_idx}"] = item.get('amount', 0)

            # [주문요청사항]
            ws["B28"] = quote_info.get('req_note', '')

            # 임시 파일 저장 경로 (바탕화면)
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            
            # 최종 PDF 파일명 결정
            if is_kr:
                pdf_filename = f"견적서_{client_name}_{mgmt_no}.pdf"
            else:
                pdf_filename = f"Quotation_{client_name}_{mgmt_no}.pdf"
            
            # 임시 엑셀 파일명 (충돌 방지 위해 타임스탬프 등 사용 권장하나 여기선 관리번호 사용)
            temp_xlsx_name = f"temp_{mgmt_no}.xlsx"
            temp_xlsx_path = os.path.join(desktop, temp_xlsx_name)
            pdf_path = os.path.join(desktop, pdf_filename)
            
            wb.save(temp_xlsx_path)
            wb.close() # openpyxl 객체 닫기

            # --- 3. PDF 변환 (win32com 사용 - 엑셀 백그라운드 실행) ---
            # 스레드 초기화 (Tkinter와 충돌 방지)
            pythoncom.CoInitialize()
            
            excel = win32com.client.Dispatch("Excel.Application")
            
            # [중요] 엑셀 창 숨기기 및 알림 끄기
            excel.Visible = False
            excel.DisplayAlerts = False 
            excel.ScreenUpdating = False # 화면 갱신 중지 (속도 향상 및 깜빡임 방지)

            # 임시 엑셀 파일 열기 (반드시 절대 경로여야 함)
            abs_xlsx_path = os.path.abspath(temp_xlsx_path)
            wb_opened = excel.Workbooks.Open(abs_xlsx_path)
            
            # PDF 내보내기 (TypePDF = 0, QualityStandard = 0)
            try:
                wb_opened.ExportAsFixedFormat(0, pdf_path)
            except Exception as e:
                return False, f"PDF 변환 실패 (엑셀 오류): {e}"
            
            # 정상 종료 처리
            wb_opened.Close(SaveChanges=False)
            wb_opened = None
            
            return True, pdf_path

        except Exception as e:
            return False, f"오류 발생: {str(e)}"
            
        finally:
            # 자원 정리 (매우 중요)
            if wb_opened:
                try: wb_opened.Close(False)
                except: pass
            
            if excel:
                try: 
                    excel.Quit()
                    # COM 객체 해제
                    del excel
                except: pass
            
            # 임시 엑셀 파일 삭제
            if temp_xlsx_path and os.path.exists(temp_xlsx_path):
                try:
                    os.remove(temp_xlsx_path)
                except: pass # 삭제 실패해도 치명적이지 않음