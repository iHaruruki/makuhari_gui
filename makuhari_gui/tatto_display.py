#!/usr/bin/env python3
"""
ROS 2 Sensor Display Node using Tkinter
Subscribes to sensor_values topic and displays sensor positions as circles
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import UInt16MultiArray
import tkinter as tk
from tkinter import font
from PIL import Image, ImageDraw
import signal
import sys
import math

class SensorDisplayNode(Node):
    """ROS 2 ノード: sensor_values トピックを購読"""
    
    def __init__(self):
        super().__init__('sensor_display_node')
        self.declare_parameter('image_side', 1000)
        self.image_side_ = self.get_parameter('image_side').as_int()
        
        self.sensor_data = [0] * 9
        self.message_count = 0
        self.has_new_message = False
        
        self.subscription = self.create_subscription(
            UInt16MultiArray,
            'sensor_values',
            self.callback,
            10
        )
        self.get_logger().info(f'Sensor Display Node initialized (image_side={self.image_side_})')
        self.get_logger().info('Subscribing to sensor_values')
    
    def callback(self, msg):
        """トピックコールバック"""
        if len(msg.data) != 9:
            self.get_logger().warn(f'Invalid message size: expected 9, got {len(msg.data)}')
            return
        
        self.sensor_data = list(msg.data)
        self.message_count += 1
        self.has_new_message = True
        
        self.get_logger().debug(f'Sensor data received: {self.sensor_data}')


class SensorDisplayGUI:
    """Tkinter GUI: センサー値を可視化"""
    
    def __init__(self, root, node):
        self.root = root
        self.node = node
        self.is_running = True
        
        # ウィンドウ設定
        self.root.title("ROS 2 Sensor Display")
        self.root.geometry("1200x900")
        self.root.configure(bg='#1e1e1e')
        self.root.resizable(True, True)
        
        # パラメータ
        self.image_side = node.image_side_
        self.LOW = 30
        self.HIGH = 2000
        self.FIXED_MIN = 0.0
        self.SCOR = 1000.0
        self.SC = 0.7071  # sin(45°) * sqrt(2) / 2
        self.AB = self.image_side / 2
        self.image_scale = self.image_side / 500.0
        
        # フォント定義
        self.title_font = font.Font(family="Arial", size=20, weight="bold")
        self.status_font = font.Font(family="Arial", size=12)
        self.info_font = font.Font(family="Arial", size=10)
        
        # センサー位置の計算
        self.positions = self.calculate_positions()
        
        self.setup_ui()
        self.update_loop()
    
    def calculate_positions(self):
        """センサーの位置を計算"""
        ab = self.AB
        s = self.image_scale
        sc = self.SC
        
        positions = [
            (int(-125 * s * sc + ab), int(125 * s * sc + ab)),      # 0
            (int(250 * s), int(125 * s)),                              # 1
            (int(125 * s * sc + ab), int(125 * s * sc + ab)),         # 2
            (int(125 * s), int(250 * s)),                              # 3
            (int(250 * s), int(250 * s)),                              # 4 (center)
            (int(375 * s), int(250 * s)),                              # 5
            (int(-125 * s * sc + ab), int(-125 * s * sc + ab)),       # 6
            (int(250 * s), int(375 * s)),                              # 7
            (int(125 * s * sc + ab), int(-125 * s * sc + ab))         # 8
        ]
        return positions
    
    def normalize_sensor_values(self, sensor_data):
        """センサー値を正規化 [0, 1]"""
        normalized = []
        
        for k in range(9):
            if k == 7:  # ch7の特例
                denom = max(1.0, 250.0 - self.FIXED_MIN)
            else:
                denom = max(1.0, self.SCOR - self.FIXED_MIN)
            
            mh = float(sensor_data[k]) - self.FIXED_MIN
            value = mh / denom
            value = max(0.0, min(1.0, value))
            normalized.append(value)
        
        # ch7は固定値
        normalized[7] = 0.5
        
        # ch0に補正を加える
        normalized[0] += 0.2
        if normalized[0] > 1:
            normalized[0] = 1.0
        
        return normalized
    
    def setup_ui(self):
        """UI レイアウトをセットアップ"""
        
        # メインフレーム
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === タイトル ===
        title_label = tk.Label(
            main_frame,
            text="Sensor Display",
            font=self.title_font,
            bg='#1e1e1e',
            fg='white'
        )
        title_label.pack(pady=(0, 10))
        
        # === キャンバスフレーム ===
        canvas_frame = tk.Frame(main_frame, bg='#2a2a2a', relief=tk.SUNKEN, bd=2)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.image_side,
            height=self.image_side,
            bg='white',
            relief=tk.SUNKEN,
            bd=1
        )
        self.canvas.pack(padx=5, pady=5)
        
        # === ステータス情報フレーム ===
        status_frame = tk.Frame(main_frame, bg='#1e1e1e')
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        # メッセージカウント
        self.count_label = tk.Label(
            status_frame,
            text="Messages received: 0",
            font=self.status_font,
            bg='#1e1e1e',
            fg='#888888'
        )
        self.count_label.pack()
        
        # センサー値表示
        sensor_frame = tk.Frame(main_frame, bg='#2a2a2a', relief=tk.SUNKEN, bd=2)
        sensor_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.sensor_labels = []
        for i in range(9):
            lbl = tk.Label(
                sensor_frame,
                text=f"Sensor {i}: --",
                font=self.info_font,
                bg='#2a2a2a',
                fg='#CCCCCC'
            )
            lbl.pack(side=tk.LEFT, padx=5, pady=5)
            self.sensor_labels.append(lbl)
        
        # 接続状態
        self.status_label = tk.Label(
            main_frame,
            text="Status: Waiting for data...",
            font=self.info_font,
            bg='#1e1e1e',
            fg='#FF8800'
        )
        self.status_label.pack(pady=(10, 0))
        
        # === ボタンフレーム ===
        button_frame = tk.Frame(main_frame, bg='#1e1e1e')
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        exit_button = tk.Button(
            button_frame,
            text="Exit",
            command=self.on_exit,
            font=self.info_font,
            bg='#444444',
            fg='white',
            padx=15,
            pady=8,
            relief=tk.RAISED,
            cursor="hand2",
            activebackground='#555555'
        )
        exit_button.pack(side=tk.RIGHT)
    
    def draw_sensor_display(self, normalized_values):
        """センサー表示を描画"""
        
        # キャンバスをクリア
        self.canvas.delete("all")
        
        # 背景を白で塗りつぶし
        self.canvas.create_rectangle(
            0, 0, self.image_side, self.image_side,
            fill='white', outline='white'
        )
        
        # センサーサークルを描画
        for k in range(9):
            x, y = self.positions[k]
            radius = int(15 * self.image_scale + (65 * self.image_scale * normalized_values[k]))
            self.canvas.create_oval(
                x - radius, y - radius,
                x + radius, y + radius,
                outline='blue', width=2
            )
        
        # 代表点を計算
        sumw = 0.0
        wx = 0.0
        wy = 0.0
        
        for k in range(9):
            wx += normalized_values[k] * self.positions[k][0]
            wy += normalized_values[k] * self.positions[k][1]
            sumw += normalized_values[k]
        
        cx = int(250 * self.image_scale)
        cy = int(250 * self.image_scale)
        
        if sumw > 0.0:
            cx = int(wx / sumw)
            cy = int(wy / sumw)
        
        # 代表点を描画（赤い点）
        ref_x = int((cx - self.AB) * 6 + self.AB)
        ref_y = int((cy - self.AB) * 6 + self.AB)
        ref_radius = 10
        
        self.canvas.create_oval(
            ref_x - ref_radius, ref_y - ref_radius,
            ref_x + ref_radius, ref_y + ref_radius,
            fill='red', outline='red'
        )
    
    def update_loop(self):
        """定期的に UI を更新（50ms ごと）"""
        
        if not self.is_running:
            return
        
        try:
            # ROS 2 スピン
            rclpy.spin_once(self.node, timeout_sec=0.01)
            
            # 新しいメッセージがある場合は UI を更新
            if self.node.has_new_message:
                self.update_sensor_display()
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
    
    def update_sensor_display(self):
        """センサー表示を更新"""
        
        sensor_data = self.node.sensor_data
        
        # 全センサが閾値の範囲内かチェック
        above_border = True
        for k in range(9):
            if sensor_data[k] <= self.LOW or sensor_data[k] > self.HIGH:
                above_border = False
                break
        
        if not above_border:
            self.canvas.delete("all")
            self.canvas.create_rectangle(
                0, 0, self.image_side, self.image_side,
                fill='white', outline='white'
            )
            self.status_label.config(
                text="Status: Out of range",
                fg='#FF0000'
            )
            return
        
        # 値を正規化
        normalized = self.normalize_sensor_values(sensor_data)
        
        # センサー表示を描画
        self.draw_sensor_display(normalized)
        
        # センサー値ラベルを更新
        for i in range(9):
            self.sensor_labels[i].config(
                text=f"S{i}: {sensor_data[i]:4d} ({normalized[i]:.2f})"
            )
        
        # ステータス更新
        self.status_label.config(
            text="Status: Connected",
            fg='#00AA00'
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
    node = SensorDisplayNode()
    
    # Tkinter ウィンドウ作成
    root = tk.Tk()
    gui = SensorDisplayGUI(root, node)
    
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