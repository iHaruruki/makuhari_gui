#!/usr/bin/env python3
"""
ROS 2 Vital Signs Display GUI using Tkinter
Subscribes to /lucia/vital/ave topic and displays vital signs (HR, SpO2, SYS, DIA)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import tkinter as tk
from tkinter import font
import signal
import sys

class VitalDisplayNode(Node):
    """ROS 2 ノード: /lucia/vital/ave トピックを購読"""
    
    def __init__(self):
        super().__init__('vital_display_node')
        self.vital_data = {
            'hr': -1.0,
            'spo2': -1.0,
            'sys_bp': -1.0,
            'dia_bp': -1.0
        }
        self.message_count = 0
        self.has_new_message = False
        
        self.subscription = self.create_subscription(
            Float64MultiArray,
            '/lucia/vital/ave',
            self.callback,
            10
        )
        self.get_logger().info('Vital Display Node initialized')
        self.get_logger().info('Subscribing to /lucia/vital/ave')
        self.get_logger().info('Initial vital data: HR=-1, SpO2=-1, SYS=-1, DIA=-1')
    
    def callback(self, msg):
        """トピックコールバック"""
        if len(msg.data) >= 4:
            self.vital_data['hr'] = msg.data[0]
            self.vital_data['spo2'] = msg.data[1]
            self.vital_data['sys_bp'] = msg.data[2]
            self.vital_data['dia_bp'] = msg.data[3]
            self.message_count += 1
            self.has_new_message = True
            
            self.get_logger().info(
                f'Vital data received: HR={self.vital_data["hr"]:.1f}, '
                f'SpO2={self.vital_data["spo2"]:.1f}, '
                f'SYS={self.vital_data["sys_bp"]:.1f}, '
                f'DIA={self.vital_data["dia_bp"]:.1f}'
            )
        else:
            self.get_logger().warn(f'Invalid message format: expected 4 elements, got {len(msg.data)}')

class VitalDisplayGUI:
    """Tkinter GUI: バイタルサイン表示"""
    
    def __init__(self, root, node):
        self.root = root
        self.node = node
        self.is_running = True
        
        # ウィンドウ設定
        self.root.title("ROS 2 Vital Signs Display")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1e1e1e')
        self.root.resizable(True, True)
        
        # フォント定義
        self.title_font = font.Font(family="Arial", size=28, weight="bold")
        self.vital_label_font = font.Font(family="Arial", size=16, weight="bold")
        self.vital_value_font = font.Font(family="Arial", size=56, weight="bold")
        self.status_font = font.Font(family="Arial", size=14)
        self.info_font = font.Font(family="Arial", size=12)
        
        # バイタルサインの色
        self.valid_color = '#00AA00'  # 緑
        self.invalid_color = '#666666'  # グレー
        self.warning_color = '#FF8800'  # オレンジ
        
        self.setup_ui()
        self.update_loop()
    
    def setup_ui(self):
        """UI レイアウトをセットアップ"""
        
        # メインフレーム
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # === タイトル ===
        title_label = tk.Label(
            main_frame,
            text="Vital Signs Display",
            font=self.title_font,
            bg='#1e1e1e',
            fg='white'
        )
        title_label.pack(pady=(0, 30))
        
        # === バイタルサイン表示フレーム ===
        vital_frame = tk.Frame(
            main_frame,
            bg='#2a2a2a',
            relief=tk.RAISED,
            bd=3
        )
        vital_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # グリッドレイアウト用の内部フレーム
        grid_frame = tk.Frame(vital_frame, bg='#2a2a2a')
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # HR (Heart Rate)
        hr_frame = self.create_vital_frame(
            grid_frame,
            "Heart Rate",
            "HR",
            "bpm",
            0, 0
        )
        self.hr_value_label = hr_frame['value_label']
        
        # SpO2 (Oxygen Saturation)
        spo2_frame = self.create_vital_frame(
            grid_frame,
            "Blood oxygen level",
            "SpO2",
            "%",
            0, 1
        )
        self.spo2_value_label = spo2_frame['value_label']
        
        # SYS BP (Systolic Blood Pressure)
        sys_frame = self.create_vital_frame(
            grid_frame,
            "Systolic Blood Pressure",
            "SBP",
            "mmHg",
            1, 0
        )
        self.sys_value_label = sys_frame['value_label']
        
        # DIA BP (Diastolic Blood Pressure)
        dia_frame = self.create_vital_frame(
            grid_frame,
            "Diastolic Blood Pressure",
            "DBP",
            "mmHg",
            1, 1
        )
        self.dia_value_label = dia_frame['value_label']
        
        # === ステータス情報フレーム ===
        status_frame = tk.Frame(main_frame, bg='#1e1e1e')
        status_frame.pack(fill=tk.X, pady=(20, 0))
        
        # メッセージカウント
        self.count_label = tk.Label(
            status_frame,
            text="Messages received: 0",
            font=self.status_font,
            bg='#1e1e1e',
            fg='#888888'
        )
        self.count_label.pack()
        
        # トピック情報
        topic_label = tk.Label(
            status_frame,
            text="Topic: /lucia/vital/ave (Combined average of A/B/C channels)",
            font=self.info_font,
            bg='#1e1e1e',
            fg='#999999'
        )
        topic_label.pack()
        
        # 接続状態
        self.status_label = tk.Label(
            status_frame,
            text="Status: Waiting for data...",
            font=self.info_font,
            bg='#1e1e1e',
            fg='#FF8800'
        )
        self.status_label.pack()
        
        # === ボタンフレーム ===
        button_frame = tk.Frame(main_frame, bg='#1e1e1e')
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        exit_button = tk.Button(
            button_frame,
            text="Exit",
            command=self.on_exit,
            font=self.info_font,
            bg='#444444',
            fg='white',
            padx=20,
            pady=10,
            relief=tk.RAISED,
            cursor="hand2",
            activebackground='#555555'
        )
        exit_button.pack(side=tk.RIGHT)
    
    def create_vital_frame(self, parent, label_text, short_label, unit, row, col):
        """バイタルサイン表示フレームを作成"""
        
        vital_box = tk.Frame(
            parent,
            bg='#333333',
            relief=tk.SUNKEN,
            bd=2
        )
        vital_box.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
        
        # 行と列の重みを設定
        parent.grid_rowconfigure(row, weight=1)
        parent.grid_columnconfigure(col, weight=1)
        
        # ラベル
        label = tk.Label(
            vital_box,
            text=label_text,
            font=self.vital_label_font,
            bg='#333333',
            fg='#CCCCCC',
            pady=10
        )
        label.pack()
        
        # 値表示
        value_label = tk.Label(
            vital_box,
            text="--",
            font=self.vital_value_font,
            bg='#333333',
            fg=self.invalid_color,
            pady=20
        )
        value_label.pack()
        
        # ユニット
        unit_label = tk.Label(
            vital_box,
            text=unit,
            font=self.vital_label_font,
            bg='#333333',
            fg='#AAAAAA',
            pady=10
        )
        unit_label.pack()
        
        return {
            'frame': vital_box,
            'value_label': value_label,
            'short_label': short_label
        }
    
    def get_value_color(self, vital_type, value):
        """バイタルサインの値に基づいて色を決定"""
        
        if value < 0:
            return self.invalid_color
        
        # 正常範囲チェック
        if vital_type == 'hr':
            if 60 <= value <= 100:
                return self.valid_color
            else:
                return self.warning_color
        elif vital_type == 'spo2':
            if 95 <= value <= 100:
                return self.valid_color
            elif value >= 90:
                return self.warning_color
            else:
                return '#FF0000'  # 赤
        elif vital_type == 'sys_bp':
            if 100 <= value <= 140:
                return self.valid_color
            else:
                return self.warning_color
        elif vital_type == 'dia_bp':
            if 60 <= value <= 90:
                return self.valid_color
            else:
                return self.warning_color
        
        return self.valid_color
    
    def update_loop(self):
        """定期的に UI を更新（50ms ごと）"""
        
        if not self.is_running:
            return
        
        try:
            # ROS 2 スピン
            rclpy.spin_once(self.node, timeout_sec=0.01)
            
            # 新しいメッセージがある場合は UI を更新
            if self.node.has_new_message:
                self.update_vital_display()
                self.node.has_new_message = False
            
            # メッセージカウント更新
            self.count_label.config(
                text=f"Messages received: {self.node.message_count}"
            )
            
        except Exception as e:
            self.node.get_logger().error(f"Update error: {e}")
        
        # 50ms ごとに次の更新をスケジュール
        if self.is_running:
            self.root.after(50, self.update_loop)
    
    def update_vital_display(self):
        """バイタルサイン表示を更新"""
        
        # HR
        hr_value = self.node.vital_data['hr']
        if hr_value >= 0:
            self.hr_value_label.config(
                text=f"{hr_value:.0f}",
                fg=self.get_value_color('hr', hr_value)
            )
        else:
            self.hr_value_label.config(text="--", fg=self.invalid_color)
        
        # SpO2
        spo2_value = self.node.vital_data['spo2']
        if spo2_value >= 0:
            self.spo2_value_label.config(
                text=f"{spo2_value:.1f}",
                fg=self.get_value_color('spo2', spo2_value)
            )
        else:
            self.spo2_value_label.config(text="--", fg=self.invalid_color)
        
        # SYS
        sys_value = self.node.vital_data['sys_bp']
        if sys_value >= 0:
            self.sys_value_label.config(
                text=f"{sys_value:.0f}",
                fg=self.get_value_color('sys_bp', sys_value)
            )
        else:
            self.sys_value_label.config(text="--", fg=self.invalid_color)
        
        # DIA
        dia_value = self.node.vital_data['dia_bp']
        if dia_value >= 0:
            self.dia_value_label.config(
                text=f"{dia_value:.0f}",
                fg=self.get_value_color('dia_bp', dia_value)
            )
        else:
            self.dia_value_label.config(text="--", fg=self.invalid_color)
        
        # ステータス更新
        self.status_label.config(
            text="Status: Connected",
            fg=self.valid_color
        )
    
    def on_exit(self):
        """終了ボタン処理"""
        self.is_running = False
        self.root.quit()

def signal_handler(sig, frame):
    """Ctrl+C シグナルハンドラー"""
    print('\n\nInterrupted by user (Ctrl+C)')
    sys.exit(0)

def main():
    """メイン関数"""
    
    # Ctrl+C シグナルハンドラーを登録
    signal.signal(signal.SIGINT, signal_handler)
    
    # ROS 2 初期化
    rclpy.init()
    node = VitalDisplayNode()
    
    # Tkinter ウィンドウ作成
    root = tk.Tk()
    gui = VitalDisplayGUI(root, node)
    
    # ウィンドウを閉じるときの処理
    def on_closing():
        gui.is_running = False
        node.get_logger().info('Shutting down...')
        root.quit()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        node.get_logger().info('Interrupted by user')
    finally:
        gui.is_running = False
        rclpy.shutdown()
        print('Shutdown complete')

if __name__ == '__main__':
    main()