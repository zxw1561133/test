import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import os
import glob
import argparse
import matplotlib
from matplotlib.widgets import Slider, Button, RadioButtons
from matplotlib.gridspec import GridSpec
import time

# 使用不依赖中文字体的配置
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

class PluginDataDynamicVisualizer:
    def __init__(self, task_id=101, data_dir="plugin_data"):
        self.task_id = task_id
        self.data_dir = data_dir
        self.cur_frame = 0
        self.is_paused = True
        self.frame_step = 1  # 播放速度，帧数步进
        self.risk_blink_counter = 0  # 风险闪烁计数器
        
        # 定义颜色映射
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
        
        # 初始化文件映射
        self.initialize_file_mapping()
        
        # 加载数据
        self.load_data()
        
        # 创建全局变量，用于存储动态绘图对象
        self.plot_objects = {
            'platform_markers': {},  # 平台当前位置标记
            'platform_lines': {},    # 平台历史轨迹
            'ref_paths': {},        # 参考轨迹
            'risk_objects': [],     # 风险对象（球体、点等）
            'ball_markers': {}      # 球体轨迹标记
        }
        
        # 创建绘图界面
        self.create_plot()
        
    def find_available_tasks(self):
        """查找可用的任务ID"""
        tasks = set()
        pattern = os.path.join(self.data_dir, "task_*_*.csv")
        files = glob.glob(pattern)
        
        for file in files:
            filename = os.path.basename(file)
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
    
    def load_data(self):
        """加载所有数据"""
        print(f"Loading data for task {self.task_id}...")
        
        # 加载平台位置数据
        self.position_data = None
        if self.file_mapping[self.task_id]['position']:
            file = self.file_mapping[self.task_id]['position']
            try:
                df = pd.read_csv(file)
                self.position_data = df
                self.timestamps = sorted(df['time'].unique())
                self.total_frames = len(self.timestamps)
                print(f"Loaded {self.total_frames} frames from position data")
                
                # 预处理数据 - 按平台ID分组
                self.platforms = {}
                for platform_id, group in df.groupby('platformId'):
                    platform_id = int(platform_id)
                    self.platforms[platform_id] = {
                        'timestamps': group['time'].values,
                        'x': group['x'].values,
                        'y': group['y'].values,
                        'z': group['z'].values,
                        'color': self.colors.get(platform_id, self.colors[9999]),
                        'ref_paths': {}
                    }
                    
                    # 提取参考轨迹 (ref0-ref9)
                    for idx, row in group.iterrows():
                        timestamp = row['time']
                        if timestamp not in self.platforms[platform_id]['ref_paths']:
                            self.platforms[platform_id]['ref_paths'][timestamp] = []
                        
                        ref_points = []
                        for i in range(10):  # ref0 到 ref9
                            if f'ref{i}_x' in row and f'ref{i}_y' in row and f'ref{i}_z' in row:
                                ref_points.append((
                                    row[f'ref{i}_x'],
                                    row[f'ref{i}_y'],
                                    row[f'ref{i}_z']
                                ))
                        
                        self.platforms[platform_id]['ref_paths'][timestamp] = ref_points
                
            except Exception as e:
                print(f"Error loading position data: {e}")
        
        # 加载风险数据
        self.risk_data = None
        if self.file_mapping[self.task_id]['risk']:
            file = self.file_mapping[self.task_id]['risk']
            try:
                df = pd.read_csv(file)
                self.risk_data = df
                print(f"Loaded risk data with {len(df)} entries")
            except Exception as e:
                print(f"Error loading risk data: {e}")
        
        # 加载球体轨迹数据
        self.ball_data = None
        if self.file_mapping[self.task_id]['ball']:
            file = self.file_mapping[self.task_id]['ball']
            try:
                df = pd.read_csv(file)
                self.ball_data = df
                print(f"Loaded ball trajectory data with {len(df)} entries")
            except Exception as e:
                print(f"Error loading ball trajectory data: {e}")
    
    def create_plot(self):
        """创建绘图界面"""
        # 创建图形和子图布局
        self.fig = plt.figure(figsize=(16, 10))
        gs = GridSpec(1, 1, figure=self.fig)
        
        # 3D视图
        self.ax3d = self.fig.add_subplot(gs[0, 0], projection='3d')
        self.ax3d.set_title(f"Plugin Data Visualization - Task {self.task_id}")
        self.ax3d.set_xlabel('X (m)')
        self.ax3d.set_ylabel('Y (m)')
        self.ax3d.set_zlabel('Z (m)')
        
        # 设置合适的坐标轴范围
        self.set_axes_limits()
        
        # 添加控制元素
        plt.subplots_adjust(bottom=0.3)
        
        # 添加帧滑块
        self.ax_slider = plt.axes([0.15, 0.15, 0.7, 0.03])
        self.frame_slider = Slider(
            self.ax_slider, 'Frame', 
            0, self.total_frames - 1,
            valinit=0, valstep=1
        )
        self.frame_slider.on_changed(self.slider_update)
        
        # 添加播放控制按钮
        btn_color = 'lightblue'
        hover_color = 'skyblue'
        
        self.ax_backward = plt.axes([0.15, 0.07, 0.1, 0.03])
        self.btn_backward = Button(self.ax_backward, 'Backward', color=btn_color, hovercolor=hover_color)
        self.btn_backward.on_clicked(self.backward_frame)
        
        self.ax_toggle = plt.axes([0.27, 0.07, 0.1, 0.03])
        self.btn_toggle = Button(self.ax_toggle, 'Play', color=btn_color, hovercolor=hover_color)
        self.btn_toggle.on_clicked(self.toggle_play)
        
        self.ax_forward = plt.axes([0.39, 0.07, 0.1, 0.03])
        self.btn_forward = Button(self.ax_forward, 'Forward', color=btn_color, hovercolor=hover_color)
        self.btn_forward.on_clicked(self.forward_frame)
        
        # 任务选择按钮
        if len(self.available_tasks) > 1:
            self.ax_task = plt.axes([0.55, 0.05, 0.15, 0.15])
            task_labels = [f"Task {task}" for task in self.available_tasks]
            self.task_radio = RadioButtons(
                self.ax_task, task_labels, 
                active=self.available_tasks.index(self.task_id) if self.task_id in self.available_tasks else 0
            )
            self.task_radio.on_clicked(self.change_task)
        
        # 添加状态文本
        self.status_text = self.fig.text(0.5, 0.01, "Ready - Use 'Play' button or slider to start visualization", ha="center")
        
        # 初始化空的绘图对象
        for platform_id in self.platforms:
            # 初始化每个平台的标记和轨迹线
            empty_marker, = self.ax3d.plot([], [], [], 'o', 
                                         color=self.platforms[platform_id]['color'], 
                                         markersize=8, 
                                         label=f"Platform {platform_id}")
            empty_line, = self.ax3d.plot([], [], [], '-', 
                                        color=self.platforms[platform_id]['color'], 
                                        linewidth=1, 
                                        alpha=0.7)
            
            self.plot_objects['platform_markers'][platform_id] = empty_marker
            self.plot_objects['platform_lines'][platform_id] = empty_line
            
            # 初始化参考路径线
            empty_ref_path, = self.ax3d.plot([], [], [], '--', 
                                           color=self.platforms[platform_id]['color'], 
                                           linewidth=1.5, 
                                           alpha=0.5)
            self.plot_objects['ref_paths'][platform_id] = empty_ref_path
        
        # 设置图例
        self.ax3d.legend()
        
        # 创建动画
        self.ani = animation.FuncAnimation(
            self.fig, self.update_animation, 
            init_func=self.init_animation,
            frames=None,  # 无限帧
            interval=100,  # 更新间隔 (ms)
            blit=True,
            cache_frame_data=False
        )
        
        plt.show()
    
    def set_axes_limits(self):
        """设置坐标轴范围"""
        all_x = []
        all_y = []
        all_z = []
        
        for platform_id, data in self.platforms.items():
            all_x.extend(data['x'])
            all_y.extend(data['y'])
            all_z.extend(data['z'])
        
        if all_x and all_y and all_z:
            # 添加边距
            x_min, x_max = min(all_x), max(all_x)
            y_min, y_max = min(all_y), max(all_y)
            z_min, z_max = min(all_z), max(all_z)
            
            padding_x = (x_max - x_min) * 0.1
            padding_y = (y_max - y_min) * 0.1
            padding_z = (z_max - z_min) * 0.1
            
            self.ax3d.set_xlim(x_min - padding_x, x_max + padding_x)
            self.ax3d.set_ylim(y_min - padding_y, y_max + padding_y)
            self.ax3d.set_zlim(z_min - padding_z, z_max + padding_z)
    
    def init_animation(self):
        """初始化动画"""
        # 返回所有将被动画更新的艺术家对象
        artists = []
        
        # 添加平台标记和轨迹线
        for marker in self.plot_objects['platform_markers'].values():
            marker.set_data([], [])
            marker.set_3d_properties([])
            artists.append(marker)
        
        for line in self.plot_objects['platform_lines'].values():
            line.set_data([], [])
            line.set_3d_properties([])
            artists.append(line)
        
        # 添加参考路径线
        for path in self.plot_objects['ref_paths'].values():
            path.set_data([], [])
            path.set_3d_properties([])
            artists.append(path)
        
        # 清理风险对象
        for obj in self.plot_objects['risk_objects']:
            try:
                obj.remove()
            except:
                pass
        self.plot_objects['risk_objects'] = []
        
        return artists
    
    def update_animation(self, frame_num):
        """更新动画帧"""
        # 检查是否正在播放
        if not self.is_paused:
            self.cur_frame = (self.cur_frame + self.frame_step) % self.total_frames
            # 更新滑块但不触发回调
            self.frame_slider.eventson = False
            self.frame_slider.set_val(self.cur_frame)
            self.frame_slider.eventson = True
        
        # 闪烁控制 - 每3帧闪烁一次
        self.risk_blink_counter = (self.risk_blink_counter + 1) % 6
        risk_visible = self.risk_blink_counter < 3
        
        # 获取当前时间戳
        current_timestamp = self.timestamps[self.cur_frame]
        
        # 清除上一帧的风险对象
        for obj in self.plot_objects['risk_objects']:
            try:
                obj.remove()
            except:
                pass
        self.plot_objects['risk_objects'] = []
        
        # 安全地清除球体标记
        for marker_id in list(self.plot_objects['ball_markers'].keys()):
            try:
                self.plot_objects['ball_markers'][marker_id].remove()
            except (ValueError, KeyError):
                # 忽略任何移除错误
                pass
        self.plot_objects['ball_markers'] = {}  # 完全重置球体标记字典
        
        artists = []
        
        # 更新平台位置和轨迹
        for platform_id, platform_data in self.platforms.items():
            try:
                # 找到当前时间戳在该平台数据中的索引
                timestamp_idx = np.where(platform_data['timestamps'] == current_timestamp)[0]
                if len(timestamp_idx) > 0:
                    idx = timestamp_idx[0]
                    
                    # 更新当前位置标记
                    marker = self.plot_objects['platform_markers'][platform_id]
                    marker.set_data([platform_data['x'][idx]], [platform_data['y'][idx]])
                    marker.set_3d_properties([platform_data['z'][idx]])
                    artists.append(marker)
                    
                    # 更新历史轨迹线 (最多显示50个点)
                    start_idx = max(0, idx - 50)
                    x_hist = platform_data['x'][start_idx:idx+1]
                    y_hist = platform_data['y'][start_idx:idx+1]
                    z_hist = platform_data['z'][start_idx:idx+1]
                    
                    line = self.plot_objects['platform_lines'][platform_id]
                    line.set_data(x_hist, y_hist)
                    line.set_3d_properties(z_hist)
                    artists.append(line)
                    
                    # 更新参考路径
                    if current_timestamp in platform_data['ref_paths']:
                        ref_points = platform_data['ref_paths'][current_timestamp]
                        if ref_points:
                            x_ref = [p[0] for p in ref_points]
                            y_ref = [p[1] for p in ref_points]
                            z_ref = [p[2] for p in ref_points]
                            
                            ref_path = self.plot_objects['ref_paths'][platform_id]
                            ref_path.set_data(x_ref, y_ref)
                            ref_path.set_3d_properties(z_ref)
                            artists.append(ref_path)
                        else:
                            # 如果没有参考点，清空线
                            ref_path = self.plot_objects['ref_paths'][platform_id]
                            ref_path.set_data([], [])
                            ref_path.set_3d_properties([])
                            artists.append(ref_path)
                    else:
                        # 如果该时间戳没有参考路径，清空线
                        ref_path = self.plot_objects['ref_paths'][platform_id]
                        ref_path.set_data([], [])
                        ref_path.set_3d_properties([])
                        artists.append(ref_path)
            except Exception as e:
                print(f"Error updating platform {platform_id}: {e}")
        
        # 绘制风险数据
        if self.risk_data is not None and risk_visible:  # 只在闪烁状态为可见时绘制
            # 筛选当前时间戳的风险数据
            current_risks = self.risk_data[self.risk_data['time'] == current_timestamp]
            
            for _, risk in current_risks.iterrows():
                try:
                    risk_type = risk['risk_type']
                    pos_x = risk['pos_0'] 
                    pos_y = risk['pos_1']
                    pos_z = risk['pos_2']
                    
                    if risk_type == 1:  # 风险区域 - 球体
                        # pos_2 是球体半径
                        radius = pos_z
                        
                        # 创建球体网格
                        u = np.linspace(0, 2 * np.pi, 20)
                        v = np.linspace(0, np.pi, 10)
                        
                        sphere_x = pos_x + radius * np.outer(np.cos(u), np.sin(v))
                        sphere_y = pos_y + radius * np.outer(np.sin(u), np.sin(v))
                        sphere_z = pos_z + radius * np.outer(np.ones(np.size(u)), np.cos(v))
                        
                        # 绘制球体
                        sphere = self.ax3d.plot_surface(
                            sphere_x, sphere_y, sphere_z, 
                            color='red',
                            alpha=0.3,
                            linewidth=0
                        )
                        self.plot_objects['risk_objects'].append(sphere)
                    
                    elif risk_type == 0 or risk_type == 2:  # 风险点
                        # 确定风险点的颜色
                        risk_color = 'purple' if risk_type == 0 else 'cyan'
                        
                        # 绘制风险点
                        point = self.ax3d.scatter(
                            pos_x, pos_y, pos_z,
                            color=risk_color,
                            marker='*',
                            s=200,
                            alpha=0.8
                        )
                        self.plot_objects['risk_objects'].append(point)
                except Exception as e:
                    print(f"Error rendering risk data: {e}")
        
        # 绘制球体轨迹
        if self.ball_data is not None:
            # 筛选当前时间戳的球体数据
            current_balls = self.ball_data[self.ball_data['time'] == current_timestamp]
            
            for idx, ball in current_balls.iterrows():
                try:
                    if 'x' in ball and 'y' in ball and 'z' in ball:
                        ball_x = ball['x']
                        ball_y = ball['y']
                        ball_z = ball['z']
                        
                        # 添加到球体标记字典中
                        platform_id = int(ball['platformId']) if 'platformId' in ball else 1801
                        color = self.colors.get(platform_id, self.colors[1801])
                        
                        marker = self.ax3d.scatter(
                            ball_x, ball_y, ball_z,
                            color=color,
                            marker='o',
                            s=150,
                            alpha=0.7
                        )
                        ball_id = f"ball_{idx}"  # 使用唯一ID
                        self.plot_objects['ball_markers'][ball_id] = marker
                        self.plot_objects['risk_objects'].append(marker)  # 也添加到风险对象列表以便清理
                except Exception as e:
                    print(f"Error rendering ball trajectory: {e}")
        
        # 更新状态文本
        self.status_text.set_text(f"Task {self.task_id} - Frame {self.cur_frame+1}/{self.total_frames} - Timestamp: {current_timestamp}")
        
        # 不将风险对象添加到返回的artists列表中，因为它们是每帧重新创建的
        # 这种方式适用于blit=True
        
        return artists
    
    def slider_update(self, val):
        """滑块回调函数"""
        self.cur_frame = int(val)
        self.is_paused = True
        self.btn_toggle.label.set_text("Play")
        
        # 动画更新会自动处理绘图
        # 这里不需要额外调用动画更新函数
    
    def toggle_play(self, event):
        """切换播放/暂停状态"""
        self.is_paused = not self.is_paused
        self.btn_toggle.label.set_text("Pause" if not self.is_paused else "Play")
        
        # 简化动画控制的逻辑
        if self.is_paused:
            self.ani.event_source.stop()
        else:
            self.ani.event_source.start()
    
    def forward_frame(self, event):
        """前进一帧"""
        self.cur_frame = (self.cur_frame + self.frame_step) % self.total_frames
        self.frame_slider.set_val(self.cur_frame)
        self.is_paused = True
        self.btn_toggle.label.set_text("Play")
    
    def backward_frame(self, event):
        """后退一帧"""
        self.cur_frame = (self.cur_frame - self.frame_step) % self.total_frames
        self.frame_slider.set_val(self.cur_frame)
        self.is_paused = True
        self.btn_toggle.label.set_text("Play")
    
    def change_task(self, label):
        """改变当前任务"""
        task_id = int(label.split()[1])
        if task_id != self.task_id:
            # 暂停动画
            self.is_paused = True
            self.btn_toggle.label.set_text("Play")
            
            # 更新任务ID
            self.task_id = task_id
            
            # 重新加载数据
            self.load_data()
            
            # 重置当前帧
            self.cur_frame = 0
            
            # 清除当前的图形对象
            self.ax3d.clear()
            self.plot_objects = {
                'platform_markers': {},
                'platform_lines': {},
                'ref_paths': {},
                'risk_objects': [],
                'ball_markers': {}
            }
            
            # 重新初始化绘图对象
            for platform_id in self.platforms:
                empty_marker, = self.ax3d.plot([], [], [], 'o', 
                                           color=self.platforms[platform_id]['color'], 
                                           markersize=8, 
                                           label=f"Platform {platform_id}")
                empty_line, = self.ax3d.plot([], [], [], '-', 
                                        color=self.platforms[platform_id]['color'], 
                                        linewidth=1, 
                                        alpha=0.7)
                
                self.plot_objects['platform_markers'][platform_id] = empty_marker
                self.plot_objects['platform_lines'][platform_id] = empty_line
                
                empty_ref_path, = self.ax3d.plot([], [], [], '--', 
                                           color=self.platforms[platform_id]['color'], 
                                           linewidth=1.5, 
                                           alpha=0.5)
                self.plot_objects['ref_paths'][platform_id] = empty_ref_path
            
            # 设置图例
            self.ax3d.legend()
            
            # 设置坐标轴
            self.ax3d.set_xlabel('X (m)')
            self.ax3d.set_ylabel('Y (m)')
            self.ax3d.set_zlabel('Z (m)')
            self.ax3d.set_title(f"Plugin Data Visualization - Task {self.task_id}")
            
            # 重新设置坐标轴范围
            self.set_axes_limits()
            
            # 更新滑块
            self.frame_slider.valmax = self.total_frames - 1
            self.frame_slider.ax.set_xlim(0, self.total_frames - 1)
            self.frame_slider.set_val(0)
            
            # 绘制初始帧
            self.update_animation(0)

def main():
    parser = argparse.ArgumentParser(description='Dynamic Plugin Data Visualizer')
    parser.add_argument('--task', type=int, default=101, help='Task ID (default: 101)')
    parser.add_argument('--data-dir', type=str, default='plugin_data', help='Data directory (default: plugin_data)')
    args = parser.parse_args()
    
    visualizer = PluginDataDynamicVisualizer(task_id=args.task, data_dir=args.data_dir)

if __name__ == "__main__":
    main() 