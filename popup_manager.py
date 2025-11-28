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
        """환경 설정"""
        win = SettingsPopup(self.parent, self.dm, self.refresh_callback)
        # grab_set은 내부에서 처리

    def open_client_popup(self, client_name=None):
        """업체 등록/수정"""
        win = ClientPopup(self.parent, self.dm, self.refresh_callback, client_name)

    def open_quote_popup(self, mgmt_no=None):
        """견적/주문 등록/수정"""
        win = QuotePopup(self.parent, self.dm, self.refresh_callback, mgmt_no)

    def open_delivery_popup(self, row_index):
        """납품 처리"""
        win = DeliveryPopup(self.parent, self.dm, self.refresh_callback, row_index)

    def open_payment_popup(self, row_index):
        """입금 처리"""
        win = PaymentPopup(self.parent, self.dm, self.refresh_callback, row_index)