import os
import time
import openpyxl
from config import Config

class ExportManager:
    def __init__(self):
        pass

    def export_quote_to_pdf(self, client_info, quote_info, items):
        """견적서 PDF 변환 (기존 코드 유지)"""
        try:
            import win32com.client
            import pythoncom
        except ImportError:
            return False, "PDF 변환을 위해 pywin32 라이브러리가 필요합니다.\n설치: pip install pywin32"

        temp_xlsx_path = None
        excel = None
        wb_opened = None

        try:
            client_name = quote_info['client_name']
            mgmt_no = quote_info['mgmt_no']
            
            country = str(client_info.get("국가", "Korea")).upper()
            is_kr = any(x in country for x in ["대한민국", "KR", "한국", "KOREA"])
            
            template_filename = "Quotation_KR.xlsx" if is_kr else "Quotation_EN.xlsx"
            template_dir = os.path.join(Config.DEFAULT_ATTACHMENT_ROOT, "forms")
            template_path = os.path.join(template_dir, template_filename)

            if not os.path.exists(template_path):
                return False, f"견적서 양식 파일을 찾을 수 없습니다.\n경로: {template_path}"

            wb = openpyxl.load_workbook(template_path)
            ws = wb.active

            ws["B7"] = client_name
            ws["B8"] = str(client_info.get("담당자", ""))
            ws["B9"] = str(client_info.get("전화번호", ""))
            ws["B10"] = str(client_info.get("주소", ""))

            ws["G10"] = quote_info['date']
            ws["G11"] = mgmt_no

            start_row = 14
            for i, item in enumerate(items):
                if i >= 10: break
                r_idx = start_row + i
                
                ws[f"B{r_idx}"] = item.get('item', '')
                ws[f"C{r_idx}"] = item.get('model', '')
                ws[f"D{r_idx}"] = item.get('desc', '')
                ws[f"E{r_idx}"] = item.get('qty', 0)
                ws[f"F{r_idx}"] = item.get('price', 0)
                ws[f"G{r_idx}"] = item.get('amount', 0)

            ws["B28"] = quote_info.get('note', '')

            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            
            if is_kr:
                pdf_filename = f"견적서_{client_name}_{mgmt_no}.pdf"
            else:
                pdf_filename = f"Quotation_{client_name}_{mgmt_no}.pdf"
            
            temp_xlsx_name = f"temp_{mgmt_no}.xlsx"
            temp_xlsx_path = os.path.join(desktop, temp_xlsx_name)
            pdf_path = os.path.join(desktop, pdf_filename)
            
            wb.save(temp_xlsx_path)
            wb.close()

            pythoncom.CoInitialize()
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False 
            excel.ScreenUpdating = False

            abs_xlsx_path = os.path.abspath(temp_xlsx_path)
            wb_opened = excel.Workbooks.Open(abs_xlsx_path)
            
            try:
                wb_opened.ExportAsFixedFormat(0, pdf_path)
            except Exception as e:
                return False, f"PDF 변환 실패 (엑셀 오류): {e}"
            
            wb_opened.Close(SaveChanges=False)
            wb_opened = None
            
            return True, pdf_path

        except Exception as e:
            return False, f"오류 발생: {str(e)}"
            
        finally:
            if wb_opened:
                try: wb_opened.Close(False)
                except: pass
            if excel:
                try: excel.Quit(); del excel
                except: pass
            if temp_xlsx_path and os.path.exists(temp_xlsx_path):
                try: os.remove(temp_xlsx_path)
                except: pass

    # [NEW] 출고요청서 발행 메서드
    def export_order_request_to_pdf(self, client_info, order_info, items):
        """
        출고요청서 엑셀 폼에 데이터를 채우고 PDF로 변환합니다.
        """
        try:
            import win32com.client
            import pythoncom
        except ImportError:
            return False, "PDF 변환을 위해 pywin32 라이브러리가 필요합니다."

        temp_xlsx_path = None
        excel = None
        wb_opened = None

        try:
            # 1. 템플릿 파일 확인 (Config에 설정된 경로 사용)
            template_path = Config.ORDER_REQUEST_FORM_PATH
            if not os.path.exists(template_path):
                return False, f"출고요청서 양식 파일을 찾을 수 없습니다.\n경로: {template_path}"

            # 2. openpyxl로 데이터 기입
            wb = openpyxl.load_workbook(template_path, keep_vba=True) # 매크로 파일(.xlsm)이므로 keep_vba=True
            ws = wb.active

            # [헤더 정보 매핑]
            ws["C1"] = order_info.get('type', '')       # 구분 (수출/내수)
            ws["C2"] = order_info.get('mgmt_no', '')    # 관리번호
            ws["C3"] = order_info.get('date', '')       # 주문일자
            
            # [고객사 정보 매핑]
            # 주소 (C7)
            ws["C7"] = str(client_info.get("주소", ""))
            
            ws["E1"] = order_info.get('client_name', '') # 고객사명
            ws["E3"] = str(client_info.get("국가", ""))
            ws["E4"] = str(client_info.get("전화번호", ""))
            ws["E5"] = str(client_info.get("운송계정", ""))
            ws["E6"] = str(client_info.get("운송방법", ""))

            # [품목 정보 매핑] (C10~F19) - 최대 10개
            start_row = 10
            for i, item in enumerate(items):
                if i >= 10: break 
                r_idx = start_row + i
                
                ws[f"C{r_idx}"] = item.get('item', '') # 품목명
                ws[f"D{r_idx}"] = item.get('model', '') # 모델명
                ws[f"E{r_idx}"] = item.get('desc', '') # Description
                ws[f"F{r_idx}"] = item.get('qty', 0)   # 수량

            # [하단 정보 매핑]
            ws["B21"] = order_info.get('req_note', '') # 주문요청사항
            ws["B24"] = str(client_info.get("특이사항", "")) # 고객 특이사항

            # 3. 저장 경로 설정
            # 폴더: Config.DEFAULT_ATTACHMENT_ROOT/출고요청서
            # 파일명: 출고요청서_업체명_관리번호.pdf
            
            # 저장 폴더 생성
            target_dir = os.path.join(Config.DEFAULT_ATTACHMENT_ROOT, "출고요청서")
            if not os.path.exists(target_dir):
                try: os.makedirs(target_dir)
                except: pass # 폴더 생성 실패 시 바탕화면으로 가거나 에러 처리 필요

            client_safe = "".join([c for c in order_info['client_name'] if c.isalnum() or c in (' ', '_')]).strip()
            pdf_filename = f"출고요청서_{client_safe}_{order_info['mgmt_no']}.pdf"
            
            # 엑셀 저장용 임시 파일 (바탕화면)
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            temp_xlsx_name = f"temp_req_{order_info['mgmt_no']}.xlsm"
            temp_xlsx_path = os.path.join(desktop, temp_xlsx_name)
            
            # 최종 PDF 경로 (공유 폴더)
            # 만약 공유 폴더 접근 불가하면 바탕화면으로
            if os.path.exists(target_dir):
                pdf_path = os.path.join(target_dir, pdf_filename)
            else:
                pdf_path = os.path.join(desktop, pdf_filename)

            wb.save(temp_xlsx_path)
            wb.close()

            # 4. PDF 변환
            pythoncom.CoInitialize()
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            excel.ScreenUpdating = False

            abs_xlsx_path = os.path.abspath(temp_xlsx_path)
            wb_opened = excel.Workbooks.Open(abs_xlsx_path)
            
            try:
                wb_opened.ExportAsFixedFormat(0, pdf_path)
            except Exception as e:
                return False, f"PDF 변환 실패: {e}"
            
            wb_opened.Close(SaveChanges=False)
            wb_opened = None
            
            return True, pdf_path

        except Exception as e:
            return False, f"오류 발생: {str(e)}"
            
        finally:
            if wb_opened:
                try: wb_opened.Close(False)
                except: pass
            if excel:
                try: excel.Quit(); del excel
                except: pass
            if temp_xlsx_path and os.path.exists(temp_xlsx_path):
                try: os.remove(temp_xlsx_path)
                except: pass