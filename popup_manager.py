from popups.client_popup import ClientPopup
from popups.delivery_popup import DeliveryPopup
from popups.payment_popup import PaymentPopup
from popups.quote_popup import QuotePopup
from popups.order_popup import OrderPopup # [신규]
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

    def open_quote_popup(self, mgmt_no=None):
        """견적 관리 팝업 열기"""
        win = QuotePopup(self.parent, self.dm, self.refresh_callback, mgmt_no)

    def open_order_popup(self, mgmt_no=None):
        """주문 관리 팝업 열기"""
        win = OrderPopup(self.parent, self.dm, self.refresh_callback, mgmt_no)

    def open_delivery_popup(self, mgmt_no):
        win = DeliveryPopup(self.parent, self.dm, self.refresh_callback, mgmt_no)

    def open_payment_popup(self, mgmt_no):
        win = PaymentPopup(self.parent, self.dm, self.refresh_callback, mgmt_no)