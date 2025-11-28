import tkinter as tk
from datetime import datetime

import customtkinter as ctk
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from styles import COLORS, FONT_FAMILY, FONTS, get_color_str

from config import Config


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        # 그리드 레이아웃 (2행 2열)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)  # 헤더 & 카드
        self.grid_rowconfigure(1, weight=1)  # 차트 & 리스트

        self.create_widgets()
        self.refresh_data()

    def create_widgets(self):
        # 1. 상단 타이틀 및 컨트롤
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkLabel(title_frame, text="📊 영업 현황 대시보드", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")

        ctk.CTkButton(title_frame, text="🔄 새로고침", width=80, height=32,
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"],
                      command=self.refresh_data, font=FONTS["main"]).pack(side="right")

        # 2. 핵심 지표 카드 (KPI)
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 20))

        for i in range(4): self.cards_frame.grid_columnconfigure(i, weight=1)

        self.card_widgets = []
        # 카드 구성: [제목, 색상, 아이콘]
        card_config = [
            ("이번 달 매출 (완료)", COLORS["success"], "💰"),
            ("총 미수금", COLORS["danger"], "⚠️"),
            ("진행 중인 주문", COLORS["primary"], "📦"),
            ("금일 출고 예정", COLORS["warning"], "🚚")
        ]

        for i, (title, color, icon) in enumerate(card_config):
            card = ctk.CTkFrame(self.cards_frame, fg_color=COLORS["bg_medium"], corner_radius=10, 
                                border_width=2, border_color=COLORS["border"])
            card.grid(row=0, column=i, sticky="ew", padx=10, pady=5)

            ctk.CTkLabel(card, text=icon, font=("Emoji", 24)).pack(side="right", anchor="ne", padx=15, pady=10)
            
            # 값 라벨 (나중에 update)
            val_lbl = ctk.CTkLabel(card, text="0", font=(FONT_FAMILY, 24, "bold"), text_color=COLORS["text"])
            val_lbl.pack(anchor="w", padx=15, pady=(15, 0))
            
            title_lbl = ctk.CTkLabel(card, text=title, font=FONTS["main"], text_color=COLORS["text_dim"])
            title_lbl.pack(anchor="w", padx=15, pady=(0, 15))
            
            self.card_widgets.append(val_lbl)

        # 3. 하단 컨텐츠 (차트 + 리스트)
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=20, pady=(0, 20))
        content_frame.grid_columnconfigure(0, weight=3) # 차트 영역을 좀 더 넓게
        content_frame.grid_columnconfigure(1, weight=2)
        content_frame.grid_rowconfigure(0, weight=1)

        # [좌측] 차트 영역
        chart_container = ctk.CTkFrame(content_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        chart_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(chart_container, text="📈 영업 단계별 현황 (Pipeline)", font=FONTS["header"]).pack(anchor="w", padx=20, pady=15)
        
        self.chart_area = ctk.CTkFrame(chart_container, fg_color="transparent")
        self.chart_area.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas = None

        # [우측] 납품 예정 리스트
        list_container = ctk.CTkFrame(content_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        list_container.grid(row=0, column=1, sticky="nsew")
        
        ctk.CTkLabel(list_container, text="📅 납품(출고) 예정 목록", font=FONTS["header"]).pack(anchor="w", padx=20, pady=15)
        
        self.list_scroll = ctk.CTkScrollableFrame(list_container, fg_color="transparent")
        self.list_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def refresh_data(self):
        """데이터 로드 및 UI 갱신"""
        df = self.dm.df_data # 영업 데이터 시트

        if df is None or df.empty:
            self._update_empty_state()
            return

        self._update_kpi_cards(df)
        self._update_pipeline_chart(df)
        self._update_delivery_list(df)

    def _update_empty_state(self):
        for lbl in self.card_widgets:
            lbl.configure(text="-")
        
        # 차트 초기화
        for widget in self.chart_area.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.chart_area, text="데이터가 없습니다.", font=FONTS["main"]).pack(expand=True)

    def _update_kpi_cards(self, df):
        # 1. 이번 달 매출 (완료 상태인 건의 합계금액)
        now = datetime.now()
        # 날짜 변환 (에러 방지)
        df['입금완료일_dt'] = pd.to_datetime(df['입금완료일'], errors='coerce')
        
        # 조건: 이번달 + 완료 상태
        mask_month = (df['입금완료일_dt'].dt.year == now.year) & (df['입금완료일_dt'].dt.month == now.month)
        mask_complete = df['Status'].astype(str).str.contains("완료")
        
        # 금액 계산 (숫자 변환)
        revenue_df = df[mask_month & mask_complete]
        total_revenue = pd.to_numeric(revenue_df['합계금액'], errors='coerce').sum()

        # 2. 총 미수금
        total_unpaid = pd.to_numeric(df['미수금액'], errors='coerce').sum()

        # 3. 진행 중인 주문 (견적, 완료, 취소 제외)
        exclude_status = ['견적', '완료', '보류', '취소']
        active_orders = df[~df['Status'].isin(exclude_status)]
        active_count = len(active_orders)

        # 4. 금일 출고 예정
        today_str = now.strftime("%Y-%m-%d")
        today_delivery = df[df['출고예정일'] == today_str]
        today_count = len(today_delivery)

        # UI 적용 (천단위 콤마)
        kpi_values = [
            f"₩ {total_revenue:,.0f}",
            f"₩ {total_unpaid:,.0f}",
            f"{active_count} 건",
            f"{today_count} 건"
        ]

        for lbl, val in zip(self.card_widgets, kpi_values):
            lbl.configure(text=val)

    def _update_pipeline_chart(self, df):
        # 기존 차트 제거
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        # 상태별 건수 집계 (파이프라인 순서대로 정렬)
        pipeline_order = ['견적', '주문', '생산중', '납품대기', '입금대기', '완료']
        status_counts = df['Status'].value_counts()
        
        # 데이터 정렬 및 매핑
        data = []
        labels = []
        colors = []
        
        # 색상 매핑 (config나 styles에 정의하면 더 좋음)
        color_map = {
            '견적': '#90CAF9', '주문': '#42A5F5', '생산중': '#1E88E5',
            '납품대기': '#FFB74D', '입금대기': '#EF5350', '완료': '#66BB6A'
        }

        for status in pipeline_order:
            # 부분 일치 검색 (예: 납품대기/입금완료 -> 납품대기로 포함)
            # 여기서는 단순화를 위해 정확히 일치하거나 포함되는 건수 합산
            count = 0
            for idx, val in status_counts.items():
                if status in str(idx):
                    count += val
            
            if count > 0:
                data.append(count)
                labels.append(status)
                colors.append(color_map.get(status, '#BDBDBD'))

        if not data:
            return

        # Matplotlib 차트 생성
        bg_color = get_color_str("bg_medium")
        text_color = get_color_str("text")

        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        # 가로 막대 그래프
        y_pos = range(len(labels))
        ax.barh(y_pos, data, color=colors, align='center', height=0.6)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, color=text_color, fontfamily=FONT_FAMILY)
        ax.invert_yaxis()  # 위에서부터 표시
        
        # X축 설정
        ax.tick_params(axis='x', colors=text_color)
        ax.spines['bottom'].set_color(text_color)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)

        # 값 표시
        for i, v in enumerate(data):
            ax.text(v + 0.1, i, str(v), color=text_color, va='center', fontweight='bold')

        plt.tight_layout()

        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_area)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _update_delivery_list(self, df):
        for w in self.list_scroll.winfo_children(): w.destroy()

        # 출고예정일이 있는 데이터만 필터링 (완료 제외)
        mask = (df['출고예정일'] != '-') & (~df['Status'].str.contains('완료')) & (~df['Status'].str.contains('취소'))
        target_df = df[mask].copy()
        
        if target_df.empty:
            ctk.CTkLabel(self.list_scroll, text="예정된 납품이 없습니다.", text_color=COLORS["text_dim"]).pack(pady=20)
            return

        # 날짜순 정렬
        target_df = target_df.sort_values(by='출고예정일')

        for _, row in target_df.head(10).iterrows(): # 상위 10개만
            card = ctk.CTkFrame(self.list_scroll, fg_color=COLORS["bg_dark"], corner_radius=5)
            card.pack(fill="x", pady=5, padx=5)
            
            # 좌측: 날짜 + D-Day
            date_str = str(row['출고예정일'])
            try:
                d_day_dt = datetime.strptime(date_str, "%Y-%m-%d")
                delta = (d_day_dt - datetime.now()).days + 1
                if delta < 0: d_text = f"D+{abs(delta)}" # 지연
                elif delta == 0: d_text = "D-Day"
                else: d_text = f"D-{delta}"
                
                # 지연이면 빨간색
                d_color = COLORS["danger"] if delta < 0 else COLORS["primary"]
            except:
                d_text = "-"
                d_color = COLORS["text_dim"]

            left = ctk.CTkFrame(card, fg_color="transparent", width=80)
            left.pack(side="left", padx=10, pady=10)
            
            ctk.CTkLabel(left, text=d_text, font=(FONT_FAMILY, 14, "bold"), text_color=d_color).pack()
            ctk.CTkLabel(left, text=date_str, font=(FONT_FAMILY, 10), text_color=COLORS["text_dim"]).pack()

            # 중앙: 정보
            center = ctk.CTkFrame(card, fg_color="transparent")
            center.pack(side="left", fill="x", expand=True, padx=10)
            
            title = f"[{row['업체명']}] {row['모델명']}"
            ctk.CTkLabel(center, text=title, font=(FONT_FAMILY, 12, "bold"), anchor="w").pack(fill="x")
            
            info = f"수량: {row['수량']} | 금액: {row['합계금액']:,}원" if str(row['합계금액']).replace(',','').replace('.','').isdigit() else f"수량: {row['수량']}"
            ctk.CTkLabel(center, text=info, font=(FONT_FAMILY, 11), text_color=COLORS["text_dim"], anchor="w").pack(fill="x")

            # 우측: 상태
            ctk.CTkLabel(card, text=row['Status'], font=(FONT_FAMILY, 11), text_color=COLORS["text"]).pack(side="right", padx=15)