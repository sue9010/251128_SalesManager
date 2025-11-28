import os
import sys
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

try:
    from tkinterdnd2 import TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

from config import Config
from data_manager import DataManager
from popup_manager import PopupManager
from styles import COLORS, FONT_FAMILY, FONTS
from views.calendar_view import CalendarView
from views.client_view import ClientView
# Views Import
from views.dashboard import DashboardView
from views.delivery_view import DeliveryView
from views.gantt_view import GanttView
from views.kanban_view import KanbanView
from views.order_view import OrderView
from views.payment_view import PaymentView
from views.quote_view import QuoteView

if DND_AVAILABLE:
    class BaseApp(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)
else:
    class BaseApp(ctk.CTk):
        pass

class SalesManagerApp(BaseApp):
    def __init__(self):
        super().__init__()

        self.dm = DataManager()
        self.title(f"Sales Manager - v{Config.APP_VERSION}")
        self.geometry("1650x900")
        
        ctk.set_appearance_mode(self.dm.current_theme)
        ctk.set_default_color_theme("dark-blue")
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.pm = PopupManager(self, self.dm, self.refresh_ui)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_view = None
        self.nav_buttons = {}

        self.create_sidebar()
        self.create_content_area()
        
        # 데이터 로드 시도
        success, msg = self.dm.load_data()
        if not success:
            # 파일이 없어서 생성했거나 에러가 났을 경우 알림
            pass 
            
        self.show_dashboard()

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=COLORS["bg_dark"])
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Sales Manager", 
            font=("Emoji", 26, "bold"), 
            text_color=COLORS["primary"]
        )
        self.logo_label.pack(pady=(30, 20), padx=20, anchor="w")
        self.logo_label.bind("<Button-1>", lambda e: self.show_dashboard())
        self.logo_label.bind("<Enter>", lambda e: self.logo_label.configure(cursor="hand2"))
        self.logo_label.bind("<Leave>", lambda e: self.logo_label.configure(cursor=""))

        menu_groups = [
            ("관리", [
                ("🏢 업체 관리", self.show_client_view),
                ("📄 견적 관리", self.show_quote_view),
                ("🛒 주문 관리", self.show_order_view),
                ("🚚 납품 관리", self.show_delivery_view),
                ("💰 입금 관리", self.show_payment_view),
            ]),
            ("일정", [
                ("📅 캘린더 뷰", self.show_calendar_view),
                ("📋 칸반 보드", self.show_kanban_view),
                ("📈 간트 차트", self.show_gantt_view),
            ])
        ]

        for group_name, items in menu_groups:
            ctk.CTkLabel(self.sidebar_frame, text=group_name, font=FONTS["main_bold"], text_color=COLORS["text_dim"]).pack(anchor="w", padx=20, pady=(20, 5))
            
            for text, command in items:
                btn = ctk.CTkButton(
                    self.sidebar_frame, 
                    text=text, 
                    command=command,
                    height=40, 
                    anchor="w", 
                    fg_color="transparent", 
                    text_color=COLORS["text"], 
                    hover_color=COLORS["bg_medium"], 
                    font=FONTS["main"]
                )
                btn.pack(fill="x", padx=10, pady=2)
                self.nav_buttons[text] = btn

        ctk.CTkFrame(self.sidebar_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=20, padx=10, side="bottom")
        
        ctk.CTkButton(self.sidebar_frame, text="⚙️  설정", command=self.pm.open_settings, 
                      height=40, anchor="w", fg_color="transparent", text_color=COLORS["text_dim"], 
                      hover_color=COLORS["bg_medium"], font=FONTS["main"]).pack(fill="x", padx=10, pady=5, side="bottom")
        
        ctk.CTkButton(self.sidebar_frame, text="🔄  데이터 로드", command=self.reload_all_data, 
                      height=40, anchor="w", fg_color=COLORS["bg_medium"], text_color=COLORS["text"], 
                      hover_color=COLORS["bg_light"], font=FONTS["main"]).pack(fill="x", padx=10, pady=10, side="bottom")

    def create_content_area(self):
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        
        # 뷰 인스턴스 생성
        self.view_dashboard = DashboardView(self.content_frame, self.dm, self.pm)
        self.view_client = ClientView(self.content_frame, self.dm, self.pm)
        self.view_quote = QuoteView(self.content_frame, self.dm, self.pm)
        self.view_order = OrderView(self.content_frame, self.dm, self.pm)
        self.view_delivery = DeliveryView(self.content_frame, self.dm, self.pm)
        self.view_payment = PaymentView(self.content_frame, self.dm, self.pm)
        self.view_calendar = CalendarView(self.content_frame, self.dm, self.pm)
        self.view_kanban = KanbanView(self.content_frame, self.dm, self.pm)
        self.view_gantt = GanttView(self.content_frame, self.dm, self.pm)

    def switch_view(self, view_name_key, view_instance):
        for text, btn in self.nav_buttons.items():
            if text == view_name_key:
                btn.configure(fg_color=COLORS["bg_light"], text_color=COLORS["primary"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text"])
        
        for child in self.content_frame.winfo_children():
            child.pack_forget()
        
        view_instance.pack(fill="both", expand=True)
        self.current_view = view_instance
        
        if hasattr(view_instance, "refresh_data"):
            view_instance.refresh_data()

    def show_dashboard(self): self.switch_view(None, self.view_dashboard)
    def show_client_view(self): self.switch_view("🏢 업체 관리", self.view_client)
    def show_quote_view(self): self.switch_view("📄 견적 관리", self.view_quote)
    def show_order_view(self): self.switch_view("🛒 주문 관리", self.view_order)
    def show_delivery_view(self): self.switch_view("🚚 납품 관리", self.view_delivery)
    def show_payment_view(self): self.switch_view("💰 입금 관리", self.view_payment)
    def show_calendar_view(self): self.switch_view("📅 캘린더 뷰", self.view_calendar)
    def show_kanban_view(self): self.switch_view("📋 칸반 보드", self.view_kanban)
    def show_gantt_view(self): self.switch_view("📈 간트 차트", self.view_gantt)

    def reload_all_data(self):
        success, msg = self.dm.load_data()
        if success:
            messagebox.showinfo("완료", "데이터를 새로고침했습니다.")
            self.refresh_ui()
        else:
            messagebox.showerror("오류", msg)

    def refresh_ui(self):
        if self.dm.is_dev_mode:
            self.sidebar_frame.configure(fg_color="#4a1e1e")
            self.logo_label.configure(text="[DEV MODE]", text_color=COLORS["danger"])
        else:
            self.sidebar_frame.configure(fg_color=COLORS["bg_dark"])
            self.logo_label.configure(text="Sales Manager", text_color=COLORS["primary"])
            
        if self.current_view and hasattr(self.current_view, "refresh_data"):
            self.current_view.refresh_data()

    def on_closing(self):
        self.quit()
        self.destroy()

if __name__ == "__main__":
    app = SalesManagerApp()
    app.mainloop()