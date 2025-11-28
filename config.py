import os


class Config:
    # ---------------------------------------------------------
    # [앱 설정] 
    # ---------------------------------------------------------
    USER_HOME = os.path.expanduser("~")
    APP_DIR_NAME = ".SalesManager"
    APP_DIR = os.path.join(USER_HOME, APP_DIR_NAME)
    
    if not os.path.exists(APP_DIR):
        try:
            os.makedirs(APP_DIR)
        except OSError:
            pass

    CONFIG_FILENAME = os.path.join(APP_DIR, "config.json")
    APP_VERSION = "1.0.0"
    DEV_PASSWORD = "admin" 

    # ---------------------------------------------------------
    # [경로 설정]
    # ---------------------------------------------------------
    DEFAULT_EXCEL_PATH = r"\\cox_biz\business\SalesManager\SalesList.xlsx"
    DEFAULT_ATTACHMENT_ROOT = r"\\cox_biz\business\SalesManager"
    
    if not os.path.exists(DEFAULT_ATTACHMENT_ROOT):
        try:
            pass 
        except OSError:
            pass 

    # ---------------------------------------------------------
    # [시트 및 컬럼 설정]
    # ---------------------------------------------------------
    SHEET_CLIENTS = "Customers"
    SHEET_DATA = "Data"
    SHEET_LOG = "Log"
    SHEET_MEMO = "Memos"
    SHEET_MEMO_LOG = "Memo Log"

    # 1. 업체 관리 시트
    CLIENT_COLUMNS = [
        "업체명", "국가", "통화", "주소", "담당자", "전화번호", "이메일", 
        "수출허가구분", "수출허가번호", "수출허가만료일", "운송계정", "운송방법", 
        "특이사항", "사업자등록증경로"
    ]

    # 2. 영업 데이터 시트 (컬럼 추가됨)
    DATA_COLUMNS = [
        # [기본 정보]
        "관리번호", "구분", "업체명", "프로젝트명", "품목명", "모델명", "Description",
        
        # [금액 정보]
        "수량", "단가", "통화", "환율", "세율(%)", "공급가액", "세액", "합계금액", 
        "기수금액", "미수금액", 
        
        # [일정 및 증빙]
        "견적일", "수주일", "출고예정일", "출고일", "선적일", "입금완료일", 
        "세금계산서발행일", "계산서번호", "수출신고번호", "송장번호", "운송방법",
        
        # [관리 정보]
        "Status", "견적서경로", "발주서경로", "주문요청사항", "비고"
    ]

    # 로그/메모
    LOG_COLUMNS = ["일시", "작업자", "구분", "상세내용"]
    MEMO_COLUMNS = ["관리번호", "일시", "작업자", "내용", "확인"]
    MEMO_LOG_COLUMNS = ["일시", "작업자", "구분", "관리번호", "내용"]

    # 화면 표시용
    DISPLAY_COLUMNS = [
        "관리번호", "구분", "업체명", "모델명", 
        "수량", "합계금액", "출고예정일", "Status"
    ]
    
    SEARCH_TARGET_COLS = ["관리번호", "업체명", "프로젝트명", "모델명", "품목명", "계산서번호", "수출신고번호", "송장번호"]