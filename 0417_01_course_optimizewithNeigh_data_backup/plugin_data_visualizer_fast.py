import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from mpl_toolkits.mplot3d import Axes3D
import os
import glob
import argparse
from matplotlib.widgets import Slider, Button, CheckButtons, RadioButtons
import matplotlib
from collections import defaultdict
import time

# 使用不依赖中文字体的配置
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

class PluginDataVisualizer:
    def __init__(self, task_id=101, data_dir="plugin_data"):
        self.task_id = task_id
        self.data_dir = data_dir
        self.current_timestamp = None
        self.current_time_idx = 0
        
        # 颜色映射
        self.colors = {
            101: 'blue',
            102: 'green',
            103: 'red',
            1801: 'purple',  # 球体轨迹
            9999: 'orange'   # 其他平台ID
        }
        
        # 数据缓存
        self.data_cache = {}
        self.timestamp_cache = {}
        
        # 查找所有任务ID
        self.available_tasks = self.find_available_tasks()
        print(f"Available tasks: {self.available_tasks}")
        
        # 初始化文件映射
        self.initialize_file_mapping()
        
        # 加载时间戳数据
        self.load_timestamps()
        
        # 选择初始时间戳
        if len(self.all_timestamps) > 0:
            self.current_time_idx = 0
            self.current_timestamp = self.all_timestamps[0]
        else:
            print("No timestamps found!")
            return
        
        # 创建绘图界面
        self.create_plot()
    
    def find_available_tasks(self):
        """查找可用的任务ID"""
        tasks = set()
        pattern = os.path.join(self.data_dir, "task_*_*.csv")
        files = glob.glob(pattern)
        
        for file in files:
            filename = os.path.basename(file)
            # 提取任务ID
            parts = filename.split('_')
            if len(parts) > 1 and parts[0] == 'task' and parts[1].isdigit():
                tasks.add(int(parts[1]))
        
        return sorted(list(tasks))
    
    def initialize_file_mapping(self):
        """初始化文件映射"""
        self.file_mapping = {}
        for task_id in self.available_tasks:
            pattern = os.path.join(self.data_dir, f"task_{task_id}_*.csv")
            files = glob.glob(pattern)
            
            task_files = {
                'position': None,
                'risk': None,
                'ball': None,
                'neighbor': None,
                'simulation': None
            }
            
            for file in files:
                filename = os.path.basename(file)
                if 'CA_get_next_position_data' in filename:
                    task_files['position'] = file
                elif 'CRisk_info_data' in filename:
                    task_files['risk'] = file
                elif 'ballTraj_data_file' in filename:
                    task_files['ball'] = file
                elif 'neiborUAV_next_position_data_file' in filename:
                    task_files['neighbor'] = file
                elif 'CA_plugin_simulation_data' in filename:
                    task_files['simulation'] = file
            
            self.file_mapping[task_id] = task_files
    
    def load_timestamps(self):
        """只加载时间戳数据以提高性能"""
        if self.task_id in self.timestamp_cache:
            self.all_timestamps = self.timestamp_cache[self.task_id]
            print(f"Using cached timestamps for task {self.task_id}, found {len(self.all_timestamps)} timestamps")
            return
        
        print(f"Loading timestamps for task {self.task_id}...")
        
        # 优先使用较小的文件来获取时间戳
        timestamps = set()
        files_to_check = []
        
        # 首先尝试使用simulation文件（通常较小）
        if self.file_mapping[self.task_id]['simulation']:
            files_to_check.append(self.file_mapping[self.task_id]['simulation'])
        
        # 如果没有simulation文件，尝试使用position文件
        if not files_to_check and self.file_mapping[self.task_id]['position']:
            files_to_check.append(self.file_mapping[self.task_id]['position'])
        
        for file in files_to_check:
            try:
                # 只读取time列以提高速度
                df = pd.read_csv(file, usecols=['time'])
                timestamps.update(df['time'].unique())
            except Exception as e:
                print(f"Error reading timestamps from {os.path.basename(file)}: {e}")
        
        self.all_timestamps = sorted(list(timestamps))
        self.timestamp_cache[self.task_id] = self.all_timestamps
        print(f"Found {len(self.all_timestamps)} timestamps")
    
    def load_data_for_timestamp(self, timestamp):
        """按需加载特定时间戳的数据"""
        # 缓存键
        cache_key = (self.task_id, timestamp)
        
        # 如果数据已缓存，直接返回
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        
        data = {
            'platforms': {},
            'risk': None,
            'ball': None
        }
        
        # 加载平台位置数据
        if self.file_mapping[self.task_id]['position']:
            try:
                # 使用更高效的方式读取CSV
                with open(self.file_mapping[self.task_id]['position'], 'r') as f:
                    # 读取标题行
                    header = f.readline().strip().split(',')
                    # 找到必要的列索引
                    time_idx = header.index('time')
                    platform_idx = header.index('platformId')
                    x_idx = header.index('x')
                    y_idx = header.index('y')
                    z_idx = header.index('z')
                    
                    # 只处理与当前时间戳匹配的行
                    for line in f:
                        cols = line.strip().split(',')
                        if float(cols[time_idx]) == timestamp:
                            platform_id = int(float(cols[platform_idx]))
                            data['platforms'][platform_id] = {
                                'x': float(cols[x_idx]),
                                'y': float(cols[y_idx]),
                                'z': float(cols[z_idx])
                            }
            except Exception as e:
                print(f"Error loading position data: {e}")
        
        # 加载风险数据
        if self.file_mapping[self.task_id]['risk']:
            try:
                risk_df = pd.read_csv(self.file_mapping[self.task_id]['risk'], 
                                    usecols=['time', 'risk_type', 'pos_0', 'pos_1', 'pos_2', 'distanceToObst'])
                risk_data = risk_df[risk_df['time'] == timestamp]
                if not risk_data.empty:
                    data['risk'] = risk_data
            except Exception as e:
                print(f"Error loading risk data: {e}")
        
        # 加载球体轨迹数据
        if self.file_mapping[self.task_id]['ball']:
            try:
                ball_df = pd.read_csv(self.file_mapping[self.task_id]['ball'], 
                                    usecols=['time', 'platformId', 'x', 'y', 'z'])
                ball_data = ball_df[ball_df['time'] == timestamp]
                if not ball_data.empty:
                    data['ball'] = ball_data
            except Exception as e:
                print(f"Error loading ball trajectory data: {e}")
        
        # 存入缓存（只保留最近10个时间戳的数据以控制内存使用）
        if len(self.data_cache) > 10:
            # 删除最旧的缓存条目
            oldest_key = next(iter(self.data_cache))
            del self.data_cache[oldest_key]
        
        self.data_cache[cache_key] = data
        return data
    
    def create_plot(self):
        """创建主绘图界面"""
        # 创建主窗口
        self.fig = plt.figure(figsize=(16, 10), dpi=100)
        
        # 布局设置
        gs_main = GridSpec(3, 2, height_ratios=[5, 1, 5], figure=self.fig)
        
        # 3D视图
        self.ax3d = self.fig.add_subplot(gs_main[0, 0], projection='3d')
        self.ax3d.set_title(f"3D View - Task {self.task_id}")
        self.ax3d.set_xlabel("X (m)")
        self.ax3d.set_ylabel("Y (m)")
        self.ax3d.set_zlabel("Z (m)")
        
        # 2D俯视图
        self.ax2d_top = self.fig.add_subplot(gs_main[0, 1])
        self.ax2d_top.set_title("2D Top View")
        self.ax2d_top.set_xlabel("X (m)")
        self.ax2d_top.set_ylabel("Y (m)")
        self.ax2d_top.set_aspect('equal')
        
        # 添加时间戳滑动条
        self.ax_slider = self.fig.add_subplot(gs_main[1, :])
        self.time_slider = Slider(
            self.ax_slider, 'Timestamp Index', 
            0, len(self.all_timestamps) - 1,
            valinit=0, valstep=1
        )
        self.time_slider.on_changed(self.update_timestamp)
        
        # 风险信息显示
        self.ax_risk = self.fig.add_subplot(gs_main[2, 0])
        self.ax_risk.set_title("Risk Information")
        self.ax_risk.set_xlabel("Time")
        self.ax_risk.set_ylabel("Risk Distance (m)")
        
        # 轨迹历史显示
        self.ax_history = self.fig.add_subplot(gs_main[2, 1])
        self.ax_history.set_title("Trajectory History")
        self.ax_history.set_xlabel("X (m)")
        self.ax_history.set_ylabel("Y (m)")
        self.ax_history.set_aspect('equal')
        
        # 控制面板区域
        plt.subplots_adjust(bottom=0.25, left=0.1, right=0.9, top=0.95)
        
        # 导航按钮
        self.ax_prev = plt.axes([0.15, 0.1, 0.1, 0.05])
        self.ax_next = plt.axes([0.3, 0.1, 0.1, 0.05])
        self.btn_prev = Button(self.ax_prev, 'Previous')
        self.btn_next = Button(self.ax_next, 'Next')
        self.btn_prev.on_clicked(self.prev_timestamp)
        self.btn_next.on_clicked(self.next_timestamp)
        
        # 任务选择按钮
        if len(self.available_tasks) > 1:
            self.ax_task = plt.axes([0.5, 0.05, 0.15, 0.15])
            task_labels = [f"Task {task}" for task in self.available_tasks]
            self.task_radio = RadioButtons(
                self.ax_task, task_labels, 
                active=self.available_tasks.index(self.task_id) if self.task_id in self.available_tasks else 0
            )
            self.task_radio.on_clicked(self.change_task)
        
        # 显示选项复选框
        self.ax_check = plt.axes([0.7, 0.05, 0.2, 0.15])
        self.check_labels = ['Show Risk', 'Show Ball Trajectory', 'Show History']
        self.check_status = [True, True, True]
        self.check_buttons = CheckButtons(self.ax_check, self.check_labels, self.check_status)
        self.check_buttons.on_clicked(self.update_display_options)
        
        # 状态文本
        self.status_text = plt.figtext(0.5, 0.01, "Ready", ha="center", fontsize=10)
        
        # 更新初始显示
        self.update_plot()
        
        # 使用合适的布局
        plt.subplots_adjust(left=0.05, right=0.98, top=0.95, bottom=0.25, wspace=0.15, hspace=0.25)
        plt.show()
    
    def change_task(self, label):
        """改变当前任务"""
        # 从按钮标签中提取任务ID
        task_id = int(label.split()[1])
        if task_id != self.task_id:
            self.task_id = task_id
            # 更新状态
            self.status_text.set_text(f"Switching to Task {task_id}...")
            self.fig.canvas.draw_idle()
            
            # 重新加载时间戳
            self.load_timestamps()
            
            if len(self.all_timestamps) > 0:
                self.current_time_idx = 0
                self.current_timestamp = self.all_timestamps[0]
                # 更新滑动条
                self.time_slider.valmax = len(self.all_timestamps) - 1
                self.time_slider.ax.set_xlim(0, len(self.all_timestamps) - 1)
                self.time_slider.set_val(0)
                # 更新绘图
                self.update_plot()
    
    def update_timestamp(self, val):
        """时间戳滑动条回调函数"""
        idx = int(self.time_slider.val)
        if 0 <= idx < len(self.all_timestamps):
            self.current_time_idx = idx
            self.current_timestamp = self.all_timestamps[idx]
            self.update_plot()
    
    def prev_timestamp(self, event):
        """显示上一个时间戳"""
        if self.current_time_idx > 0:
            self.current_time_idx -= 1
            self.current_timestamp = self.all_timestamps[self.current_time_idx]
            self.time_slider.set_val(self.current_time_idx)
    
    def next_timestamp(self, event):
        """显示下一个时间戳"""
        if self.current_time_idx < len(self.all_timestamps) - 1:
            self.current_time_idx += 1
            self.current_timestamp = self.all_timestamps[self.current_time_idx]
            self.time_slider.set_val(self.current_time_idx)
    
    def update_display_options(self, label):
        """更新显示选项"""
        idx = self.check_labels.index(label)
        self.check_status[idx] = not self.check_status[idx]
        self.update_plot()
    
    def update_plot(self):
        """更新所有图表"""
        start_time = time.time()
        
        # 更新状态
        self.status_text.set_text("Loading data...")
        self.fig.canvas.draw_idle()
        
        # 清除现有图表
        self.ax3d.clear()
        self.ax2d_top.clear()
        self.ax_risk.clear()
        self.ax_history.clear()
        
        # 重新设置标题和标签
        self.ax3d.set_title(f"3D View - Task {self.task_id} - Timestamp: {self.current_timestamp}")
        self.ax3d.set_xlabel("X (m)")
        self.ax3d.set_ylabel("Y (m)")
        self.ax3d.set_zlabel("Z (m)")
        
        self.ax2d_top.set_title("2D Top View")
        self.ax2d_top.set_xlabel("X (m)")
        self.ax2d_top.set_ylabel("Y (m)")
        
        self.ax_risk.set_title("Risk Information")
        self.ax_risk.set_xlabel("Time")
        self.ax_risk.set_ylabel("Risk Distance (m)")
        
        self.ax_history.set_title("Trajectory History")
        self.ax_history.set_xlabel("X (m)")
        self.ax_history.set_ylabel("Y (m)")
        
        # 加载当前时间戳的数据
        data = self.load_data_for_timestamp(self.current_timestamp)
        
        # 绘制平台位置
        for platform_id, pos in data['platforms'].items():
            color = self.colors.get(platform_id, self.colors[9999])
            label = f"Platform {platform_id}"
            
            # 3D视图
            self.ax3d.scatter(pos['x'], pos['y'], pos['z'], color=color, s=100, label=label)
            
            # 2D俯视图
            self.ax2d_top.scatter(pos['x'], pos['y'], color=color, s=100, label=label)
        
        # 绘制风险数据
        if self.check_status[0] and data['risk'] is not None:
            for _, row in data['risk'].iterrows():
                if pd.notna(row['risk_type']) and pd.notna(row['pos_0']) and pd.notna(row['pos_1']) and pd.notna(row['pos_2']):
                    risk_type = row['risk_type']
                    pos_x = row['pos_0']
                    pos_y = row['pos_1']
                    pos_z = row['pos_2']
                    
                    if risk_type == 1:  # 风险区域
                        # 绘制风险区域（球体）
                        u = np.linspace(0, 2 * np.pi, 20)
                        v = np.linspace(0, np.pi, 20)
                        radius = 300  # 默认半径
                        
                        x = pos_x + radius * np.outer(np.cos(u), np.sin(v))
                        y = pos_y + radius * np.outer(np.sin(u), np.sin(v))
                        z = pos_z + radius * np.outer(np.ones(np.size(u)), np.cos(v))
                        
                        self.ax3d.plot_surface(x, y, z, color='red', alpha=0.3)
                        
                        # 2D表示
                        circle = plt.Circle((pos_x, pos_y), radius, color='red', fill=False, linestyle='--')
                        self.ax2d_top.add_patch(circle)
                    
                    elif risk_type == 0 or risk_type == 2:  # 风险点
                        risk_color = 'purple' if risk_type == 0 else 'cyan'
                        self.ax3d.scatter(pos_x, pos_y, pos_z, color=risk_color, s=100, marker='*')
                        self.ax2d_top.scatter(pos_x, pos_y, color=risk_color, s=100, marker='*')
        
        # 绘制球体轨迹
        if self.check_status[1] and data['ball'] is not None:
            for _, row in data['ball'].iterrows():
                if pd.notna(row['x']) and pd.notna(row['y']) and pd.notna(row['z']):
                    ball_x = row['x']
                    ball_y = row['y']
                    ball_z = row['z']
                    
                    self.ax3d.scatter(ball_x, ball_y, ball_z, color='purple', s=150, marker='o', alpha=0.7)
                    self.ax2d_top.scatter(ball_x, ball_y, color='purple', s=150, marker='o', alpha=0.7)
        
        # 添加图例（去除重复）
        handles, labels = self.ax2d_top.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        self.ax2d_top.legend(by_label.values(), by_label.keys())
        
        # 绘制风险距离趋势
        if self.check_status[0] and data['risk'] is not None and 'distanceToObst' in data['risk'].columns:
            # 获取前N个时间戳的风险距离数据
            time_indices = range(max(0, self.current_time_idx - 50), self.current_time_idx + 1)
            times = []
            distances = []
            
            for idx in time_indices:
                timestamp = self.all_timestamps[idx]
                idx_data = self.load_data_for_timestamp(timestamp)
                if idx_data['risk'] is not None and 'distanceToObst' in idx_data['risk'].columns:
                    times.append(idx)
                    distances.append(idx_data['risk']['distanceToObst'].iloc[0])
            
            if times and distances:
                self.ax_risk.plot(times, distances, 'b-')
                self.ax_risk.scatter([self.current_time_idx], [distances[-1]], color='red', s=100)
                self.ax_risk.text(self.current_time_idx, distances[-1], f"{distances[-1]:.1f}m", 
                                 fontsize=12, ha='right')
                
                # 设置合适的Y轴范围
                if len(distances) > 1:
                    min_dist = min(distances)
                    max_dist = max(distances)
                    padding = (max_dist - min_dist) * 0.1 if max_dist > min_dist else min_dist * 0.1
                    self.ax_risk.set_ylim(max(0, min_dist - padding), max_dist + padding)
                else:
                    dist = distances[0]
                    self.ax_risk.set_ylim(max(0, dist * 0.9), dist * 1.1)
        
        # 绘制轨迹历史
        if self.check_status[2]:
            self.plot_history_data()
        
        # 计算并显示更新时间
        update_time = time.time() - start_time
        self.status_text.set_text(f"Update time: {update_time:.2f}s - Task {self.task_id} - Index {self.current_time_idx}")
        
        # 更新图表
        self.fig.canvas.draw_idle()
    
    def plot_history_data(self):
        """绘制历史轨迹数据"""
        # 为减少数据加载，只显示部分历史点
        history_end_idx = self.current_time_idx
        history_start_idx = max(0, history_end_idx - 50)  # 显示50个时间点的历史
        
        # 跳过部分点以提高性能
        step = max(1, (history_end_idx - history_start_idx) // 20)
        selected_indices = range(history_start_idx, history_end_idx + 1, step)
        
        # 按平台ID收集轨迹数据
        trajectories = defaultdict(lambda: {'x': [], 'y': []})
        
        for idx in selected_indices:
            timestamp = self.all_timestamps[idx]
            data = self.load_data_for_timestamp(timestamp)
            
            for platform_id, pos in data['platforms'].items():
                trajectories[platform_id]['x'].append(pos['x'])
                trajectories[platform_id]['y'].append(pos['y'])
        
        # 绘制轨迹线
        for platform_id, traj in trajectories.items():
            if len(traj['x']) > 1:  # 至少需要两个点才能画线
                color = self.colors.get(platform_id, self.colors[9999])
                self.ax_history.plot(traj['x'], traj['y'], '-', color=color, 
                                   label=f"Platform {platform_id}")
                
                # 标记当前位置
                if platform_id in self.load_data_for_timestamp(self.current_timestamp)['platforms']:
                    current_pos = self.load_data_for_timestamp(self.current_timestamp)['platforms'][platform_id]
                    self.ax_history.scatter(current_pos['x'], current_pos['y'], color=color, s=100)
        
        # 添加图例（去除重复）
        handles, labels = self.ax_history.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        self.ax_history.legend(by_label.values(), by_label.keys())


def main():
    parser = argparse.ArgumentParser(description='Fast Plugin Data Visualizer')
    parser.add_argument('--task', type=int, default=101, help='Task ID (default: 101)')
    parser.add_argument('--data-dir', type=str, default='plugin_data', help='Data directory (default: plugin_data)')
    args = parser.parse_args()
    
    visualizer = PluginDataVisualizer(task_id=args.task, data_dir=args.data_dir)

if __name__ == "__main__":
    main() 