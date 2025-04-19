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
# 使用不依赖中文字体的配置
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'WenQuanYi Micro Hei', 'Microsoft YaHei', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

class PluginDataVisualizer:
    def __init__(self, task_id=101, data_dir="plugin_data"):
        self.task_id = task_id
        self.data_dir = data_dir
        
        # 颜色映射
        self.colors = {
            101: 'blue',
            102: 'green',
            103: 'red',
            1801: 'purple',  # 球体轨迹
            9999: 'orange'   # 其他平台ID
        }
        
        # 查找所有任务ID
        self.available_tasks = self.find_available_tasks()
        print(f"Available tasks: {self.available_tasks}")
        
        # 加载数据
        self.load_data()
        
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
    
    def load_data(self):
        """加载所有相关数据文件"""
        print(f"Loading data for task {self.task_id}...")
        
        # 查找所有相关文件
        pattern = os.path.join(self.data_dir, f"task_{self.task_id}_*.csv")
        files = glob.glob(pattern)
        
        self.data = {}
        self.all_timestamps = set()
        
        for file in files:
            filename = os.path.basename(file)
            print(f"Loading file: {filename}")
            
            try:
                # 仅读取前几行获取列名
                header_df = pd.read_csv(file, nrows=1)
                col_names = header_df.columns.tolist()
                
                # 只读取必要的列以节省内存
                usecols = ['time']
                
                if 'platformId' in col_names:
                    usecols.append('platformId')
                
                if 'x' in col_names and 'y' in col_names and 'z' in col_names:
                    usecols.extend(['x', 'y', 'z'])
                
                if 'UAV_NED_x' in col_names and 'UAV_NED_y' in col_names and 'UAV_NED_z' in col_names:
                    usecols.extend(['UAV_NED_x', 'UAV_NED_y', 'UAV_NED_z'])
                
                if 'pos_0' in col_names and 'pos_1' in col_names and 'pos_2' in col_names:
                    usecols.extend(['pos_0', 'pos_1', 'pos_2'])
                
                if 'risk_type' in col_names:
                    usecols.append('risk_type')
                
                if 'distanceToObst' in col_names:
                    usecols.append('distanceToObst')
                
                # 读取数据
                df = pd.read_csv(file, usecols=usecols)
                
                # 提取所有时间戳
                self.all_timestamps.update(df['time'].unique())
                
                # 保存数据
                self.data[filename] = df
                
            except Exception as e:
                print(f"Error loading file {filename}: {e}")
        
        # 将时间戳排序
        self.all_timestamps = sorted(list(self.all_timestamps))
        print(f"Found {len(self.all_timestamps)} timestamps")
    
    def create_plot(self):
        """创建主绘图界面"""
        # 创建主窗口
        self.fig = plt.figure(figsize=(16, 10), dpi=100)
        
        # 布局设置 - 使用GridSpec
        # 主体布局(3行, 2列)
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
        
        # 更新初始显示
        self.update_plot()
        
        # 使用合适的布局，避免使用tight_layout
        plt.subplots_adjust(left=0.05, right=0.98, top=0.95, bottom=0.25, wspace=0.15, hspace=0.25)
        plt.show()
    
    def change_task(self, label):
        """改变当前任务"""
        # 从按钮标签中提取任务ID
        task_id = int(label.split()[1])
        if task_id != self.task_id:
            self.task_id = task_id
            # 重新加载数据
            self.load_data()
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
            self.update_plot()
    
    def next_timestamp(self, event):
        """显示下一个时间戳"""
        if self.current_time_idx < len(self.all_timestamps) - 1:
            self.current_time_idx += 1
            self.current_timestamp = self.all_timestamps[self.current_time_idx]
            self.time_slider.set_val(self.current_time_idx)
            self.update_plot()
    
    def update_display_options(self, label):
        """更新显示选项"""
        idx = self.check_labels.index(label)
        self.check_status[idx] = not self.check_status[idx]
        self.update_plot()
    
    def update_plot(self):
        """更新所有图表"""
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
        
        # 获取当前时间戳的数据
        self.plot_current_data()
        
        # 如果启用了历史轨迹，则绘制历史数据
        if self.check_status[2]:  # 显示历史轨迹
            self.plot_history_data()
        
        # 更新图表
        self.fig.canvas.draw_idle()
    
    def plot_current_data(self):
        """绘制当前时间戳的数据"""
        # 查找所有与当前时间戳匹配的数据
        platforms_data = {}
        risk_data = None
        ball_data = None
        
        for filename, df in self.data.items():
            # 找到当前时间戳的数据
            current_data = df[df['time'] == self.current_timestamp]
            
            if current_data.empty:
                continue
            
            if 'CA_get_next_position_data' in filename:
                # 处理平台位置数据
                for _, row in current_data.iterrows():
                    platform_id = int(row['platformId'])
                    platforms_data[platform_id] = {
                        'x': row['x'],
                        'y': row['y'],
                        'z': row['z']
                    }
            
            elif 'CRisk_info_data' in filename and self.check_status[0]:  # 显示风险
                # 处理风险数据
                risk_data = current_data
            
            elif 'ballTraj_data_file' in filename and self.check_status[1]:  # 显示球体轨迹
                # 处理球体轨迹数据
                ball_data = current_data
        
        # 绘制平台位置
        for platform_id, pos in platforms_data.items():
            color = self.colors.get(platform_id, self.colors[9999])
            label = f"Platform {platform_id}"
            
            # 3D视图
            self.ax3d.scatter(pos['x'], pos['y'], pos['z'], color=color, s=100, label=label)
            
            # 2D俯视图
            self.ax2d_top.scatter(pos['x'], pos['y'], color=color, s=100, label=label)
        
        # 绘制风险数据
        if risk_data is not None and not risk_data.empty:
            for _, row in risk_data.iterrows():
                if 'risk_type' in row and 'pos_0' in row and 'pos_1' in row and 'pos_2' in row:
                    risk_type = row['risk_type']
                    pos_x = row['pos_0']
                    pos_y = row['pos_1']
                    pos_z = row['pos_2']
                    
                    if risk_type == 1:  # 风险区域
                        # 绘制风险区域（球体）
                        u = np.linspace(0, 2 * np.pi, 20)
                        v = np.linspace(0, np.pi, 20)
                        radius = 300  # 默认半径，可根据实际数据调整
                        
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
        if ball_data is not None and not ball_data.empty:
            for _, row in ball_data.iterrows():
                if 'x' in row and 'y' in row and 'z' in row:
                    ball_x = row['x']
                    ball_y = row['y']
                    ball_z = row['z']
                    
                    self.ax3d.scatter(ball_x, ball_y, ball_z, color='purple', s=150, marker='o', alpha=0.7)
                    self.ax2d_top.scatter(ball_x, ball_y, color='purple', s=150, marker='o', alpha=0.7)
        
        # 添加图例（去除重复）
        handles, labels = self.ax2d_top.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        self.ax2d_top.legend(by_label.values(), by_label.keys())
        
        # 如果有风险距离数据，在风险图表中显示
        if risk_data is not None and 'distanceToObst' in risk_data.columns:
            # 获取前N个时间戳以显示趋势
            time_indices = range(max(0, self.current_time_idx - 50), self.current_time_idx + 1)
            times = []
            distances = []
            
            for idx in time_indices:
                timestamp = self.all_timestamps[idx]
                time_risk_data = None
                for filename, df in self.data.items():
                    if 'CRisk_info_data' in filename:
                        tmp_data = df[df['time'] == timestamp]
                        if not tmp_data.empty and 'distanceToObst' in tmp_data.columns:
                            time_risk_data = tmp_data
                            break
                
                if time_risk_data is not None:
                    times.append(idx)
                    distances.append(time_risk_data['distanceToObst'].iloc[0])
            
            if times and distances:
                self.ax_risk.plot(times, distances, 'b-')
                self.ax_risk.scatter([self.current_time_idx], [distances[-1]], color='red', s=100)
                self.ax_risk.text(self.current_time_idx, distances[-1], f"{distances[-1]:.1f}m", 
                                 fontsize=12, ha='right')
                
                # 设置合适的Y轴范围
                if len(distances) > 1:  # 确保有多个点才进行范围计算
                    min_dist = min(distances)
                    max_dist = max(distances)
                    padding = (max_dist - min_dist) * 0.1 if max_dist > min_dist else min_dist * 0.1
                    self.ax_risk.set_ylim(max(0, min_dist - padding), max_dist + padding)
                else:
                    # 单点情况下设置一个合理的范围
                    dist = distances[0]
                    self.ax_risk.set_ylim(max(0, dist * 0.9), dist * 1.1)
    
    def plot_history_data(self):
        """绘制历史轨迹数据"""
        # 为主要平台绘制历史轨迹
        for filename, df in self.data.items():
            if 'CA_get_next_position_data' in filename:
                # 只显示截至当前时间戳的历史数据
                history_end_idx = self.all_timestamps.index(self.current_timestamp)
                history_start_idx = max(0, history_end_idx - 100)  # 显示100个时间点的历史
                
                history_timestamps = self.all_timestamps[history_start_idx:history_end_idx+1]
                history_data = df[df['time'].isin(history_timestamps)]
                
                # 按平台ID分组
                for platform_id, group in history_data.groupby('platformId'):
                    color = self.colors.get(int(platform_id), self.colors[9999])
                    
                    # 按时间戳排序
                    group = group.sort_values('time')
                    
                    # 绘制轨迹线
                    self.ax_history.plot(group['x'], group['y'], '-', color=color, 
                                       label=f"Platform {platform_id}")
                    
                    # 标记当前位置
                    current_pos = group[group['time'] == self.current_timestamp]
                    if not current_pos.empty:
                        self.ax_history.scatter(current_pos['x'].iloc[0], current_pos['y'].iloc[0], 
                                              color=color, s=100)
        
        # 添加图例（去除重复）
        handles, labels = self.ax_history.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        self.ax_history.legend(by_label.values(), by_label.keys())


def main():
    parser = argparse.ArgumentParser(description='Plugin Data Visualizer')
    parser.add_argument('--task', type=int, default=101, help='Task ID (default: 101)')
    parser.add_argument('--data-dir', type=str, default='plugin_data', help='Data directory (default: plugin_data)')
    args = parser.parse_args()
    
    visualizer = PluginDataVisualizer(task_id=args.task, data_dir=args.data_dir)

if __name__ == "__main__":
    main() 