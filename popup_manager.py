from popups.client_popup import ClientPopup
from popups.delivery_popup import DeliveryPopup
from popups.payment_popup import PaymentPopup
from popups.quote_popup import QuotePopup
from popups.settings_popup import SettingsPopup


class PopupManager:
    def __init__(self, parent, data_manager, refresh_callback):
        self.parent = parent
        self.dm = data_manager
        self.refresh_callback = refresh_callback

    def open_settings(self):
        win = SettingsPopup(self.parent, self.dm, self.refresh_callback)

    def open_client_popup(self, client_name=None):
        win = ClientPopup(self.parent, self.dm, self.refresh_callback, client_name)

    def open_quote_popup(self, mgmt_no=None, default_status="견적"):
        win = QuotePopup(self.parent, self.dm, self.refresh_callback, mgmt_no, default_status)

    def open_delivery_popup(self, row_indices):
        """
        납품 처리 팝업 열기
        - row_indices: 선택된 행의 인덱스 리스트 (int list)
        """
        win = DeliveryPopup(self.parent, self.dm, self.refresh_callback, row_indices)

    def open_payment_popup(self, row_index):
        win = PaymentPopup(self.parent, self.dm, self.refresh_callback, row_index)