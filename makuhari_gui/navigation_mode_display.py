#!/usr/bin/env python3
"""
ROS 2 Navigation Mode Display GUI using Tkinter
Subscribes to /reject_nav_vel topic and displays mode (Interactive/Autonomous)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
import tkinter as tk
from tkinter import font
import signal
import sys

class ModeDisplayNode(Node):
    """ROS 2 ノード: /reject_nav_vel トピックを購読"""
    
    def __init__(self):
        super().__init__('mode_display_node')
        self.mode = False
        self.message_count = 0
        self.has_new_message = False
        
        self.subscription = self.create_subscription(
            Bool,
            '/reject_nav_vel',
            self.callback,
            10
        )
        self.get_logger().info('Mode Display Node initialized')
        self.get_logger().info('Subscribing to /reject_nav_vel')
        self.get_logger().info('Initial mode: Autonomous Mode (false)')
    
    def callback(self, msg):
        """トピックコールバック"""
        old_mode = self.mode
        self.mode = msg.data
        self.message_count += 1
        self.has_new_message = True
        
        if old_mode != self.mode:
            if self.mode:
                self.get_logger().warn('Mode changed: INTERACTIVE MODE (true)')
            else:
                self.get_logger().info('Mode changed: AUTONOMOUS MODE (false)')

class ModeDisplayGUI:
    """Tkinter GUI: モード表示"""
    
    def __init__(self, root, node):
        self.root = root
        self.node = node
        self.is_running = True
        
        # ウィンドウ設定
        self.root.title("ROS 2 Navigation Mode Display")
        self.root.geometry("800x600")
        self.root.configure(bg='#1e1e1e')
        self.root.resizable(True, True)
        
        # フォント定義
        self.title_font = font.Font(family="Arial", size=28, weight="bold")
        self.mode_font = font.Font(family="Arial", size=64, weight="bold")
        self.status_font = font.Font(family="Arial", size=14)
        self.info_font = font.Font(family="Arial", size=12)
        
        # 状態管理
        self.current_mode = False
        self.current_color = '#00AA00'  # 緑
        
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
            text="Navigation Mode Display",
            font=self.title_font,
            bg='#1e1e1e',
            fg='white'
        )
        title_label.pack(pady=(0, 30))
        
        # === モード表示フレーム ===
        mode_frame = tk.Frame(
            main_frame,
            bg='#2a2a2a',
            relief=tk.RAISED,
            bd=3,
            height=200
        )
        mode_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        mode_frame.pack_propagate(False)
        
        # モード表示ラベル
        self.mode_label = tk.Label(
            mode_frame,
            text="Autonomous Mode",
            font=self.mode_font,
            bg='#2a2a2a',
            fg='#00AA00',
            padx=20,
            pady=20,
            wraplength=700
        )
        self.mode_label.pack(fill=tk.BOTH, expand=True)
        
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
            text="Topic: /reject_nav_vel",
            font=self.info_font,
            bg='#1e1e1e',
            fg='#999999'
        )
        topic_label.pack()
        
        # 接続状態
        self.status_label = tk.Label(
            status_frame,
            text="Status: Connected",
            font=self.info_font,
            bg='#1e1e1e',
            fg='#00AA00'
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
    
    def update_loop(self):
        """定期的に UI を更新（50ms ごと）"""
        
        if not self.is_running:
            return
        
        try:
            # ROS 2 スピン
            rclpy.spin_once(self.node, timeout_sec=0.01)
            
            # 新しいメッセージがある場合は UI を更新
            if self.node.has_new_message:
                self.update_mode_display()
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
    
    def update_mode_display(self):
        """モード表示と色を更新"""
        
        if self.node.mode:
            # Interactive Mode
            mode_text = "Interactive Mode"
            mode_color = '#FF8800'  # オレンジ
            status_text = "Status: Interactive Mode (true)"
            status_color = '#FF8800'
            self.current_mode = True
        else:
            # Autonomous Mode
            mode_text = "Autonomous Mode"
            mode_color = '#00AA00'  # 緑
            status_text = "Status: Autonomous Mode (false)"
            status_color = '#00AA00'
            self.current_mode = False
        
        # UI更新
        self.mode_label.config(text=mode_text, fg=mode_color)
        self.status_label.config(text=status_text, fg=status_color)
        self.current_color = mode_color
    
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
    node = ModeDisplayNode()
    
    # Tkinter ウィンドウ作成
    root = tk.Tk()
    gui = ModeDisplayGUI(root, node)
    
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