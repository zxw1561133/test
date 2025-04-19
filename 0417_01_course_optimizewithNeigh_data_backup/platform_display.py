import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from matplotlib.widgets import Slider, Button, TextBox, CheckButtons, RadioButtons, AxesWidget
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import gc
import time
import warnings
import os
import math
import matplotlib
matplotlib.rcParams['font.size'] = 9  # 设置全局字体大小
import matplotlib.gridspec as gridspec
from matplotlib.widgets import AxesWidget
from matplotlib.lines import Line2D

# 创建一个下拉菜单类
class DropdownMenu(AxesWidget):
    def __init__(self, fig, x, y, width, height, options, initial=0, label='Select: ', callback=None):
        self.fig = fig
        self.x = x  # 左上角x坐标 (0-1)
        self.y = y  # 左上角y坐标 (0-1)
        self.width = width
        self.height = height
        self.options = options
        self.initial = initial
        self.current_idx = initial
        self.label = label
        self.callback = callback
        self.is_open = False
        self.hover_idx = None
        
        # 创建按钮轴
        self.button_ax = plt.axes([x, y, width, height])
        self.button_ax.set_navigate(False)
        self.button_ax.set_frame_on(True)  # 显示边框
        self.button_ax.patch.set_facecolor('lightblue')
        self.button_ax.patch.set_alpha(0.8)
        
        # 存储选项轴的列表
        self.option_axes = []
        
        # 连接事件
        self.fig.canvas.mpl_connect('button_press_event', self._on_click)
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_hover)
        
        # 初始化显示
        self._draw_button()
    
    def _draw_button(self):
        """绘制下拉按钮"""
        self.button_ax.clear()
        self.button_ax.set_xlim(0, 1)
        self.button_ax.set_ylim(0, 1)
        self.button_ax.set_xticks([])
        self.button_ax.set_yticks([])
        
        # 按钮显示当前选择项
        current_text = self.options[self.current_idx] if self.options and len(self.options) > self.current_idx else "None"
        self.button_ax.text(0.05, 0.5, f"{self.label}", ha='left', va='center', fontsize=9, fontweight='bold')
        self.button_ax.text(0.5, 0.5, f"{current_text}", ha='center', va='center', fontsize=9)
        
        # 添加下拉箭头
        arrow = "▼" if not self.is_open else "▲"
        self.button_ax.text(0.95, 0.5, arrow, ha='right', va='center', fontsize=9)
        
        # 设置更明显的边框和背景颜色
        self.button_ax.patch.set_facecolor('skyblue' if not self.is_open else 'lightgreen')
        self.button_ax.patch.set_alpha(0.9)
        self.button_ax.spines['top'].set_color('navy')
        self.button_ax.spines['bottom'].set_color('navy')
        self.button_ax.spines['left'].set_color('navy')
        self.button_ax.spines['right'].set_color('navy')
        self.button_ax.spines['top'].set_linewidth(2)
        self.button_ax.spines['bottom'].set_linewidth(2)
        self.button_ax.spines['left'].set_linewidth(2)
        self.button_ax.spines['right'].set_linewidth(2)
        
        self.fig.canvas.draw_idle()
    
    def _clear_options(self):
        """清除所有选项轴"""
        for ax in self.option_axes:
            ax.remove()
        self.option_axes = []
        self.fig.canvas.draw_idle()
    
    def _draw_options(self):
        """绘制下拉选项"""
        # 先清除现有选项
        self._clear_options()
        
        if not self.is_open:
            return
        
        # 调整选项高度和间隔 - 使选项更紧凑
        option_height = self.height * 0.6  # 选项高度设置为按钮高度的60%
        gap = 0  # 无间隔
        max_options = min(8, len(self.options))  # 最多显示8个选项
        
        # 计算总高度
        total_height = max_options * option_height
        
        # 为每个选项创建单独的轴
        for i in range(max_options):
            # 计算选项位置，从按钮下方开始
            option_y = self.y - (i + 1) * option_height
            
            # 创建选项轴
            option_ax = plt.axes([self.x, option_y, self.width, option_height])
            option_ax.set_navigate(False)
            option_ax.set_frame_on(True)
            
            # 设置选项背景
            if i == self.hover_idx:
                option_ax.patch.set_facecolor('royalblue')
                text_color = 'white'
                fontweight = 'bold'
            else:
                option_ax.patch.set_facecolor('aliceblue' if i % 2 == 0 else 'lavender')
                text_color = 'black'
                fontweight = 'normal'
            
            option_ax.patch.set_alpha(0.9)
            
            # 添加选项文本 - 使用更小的字体
            option_text = self.options[i] if i < len(self.options) else ""
            option_ax.text(0.5, 0.5, option_text, ha='center', va='center', 
                         fontsize=7, color=text_color, fontweight=fontweight)
            
            # 隐藏轴刻度
            option_ax.set_xticks([])
            option_ax.set_yticks([])
            option_ax.set_xlim(0, 1)
            option_ax.set_ylim(0, 1)
            
            # 设置边框 - 使用更细的边框
            option_ax.spines['top'].set_visible(True)
            option_ax.spines['bottom'].set_visible(True)
            option_ax.spines['left'].set_visible(True)
            option_ax.spines['right'].set_visible(True)
            option_ax.spines['top'].set_color('gray')
            option_ax.spines['bottom'].set_color('gray')
            option_ax.spines['left'].set_color('gray')
            option_ax.spines['right'].set_color('gray')
            option_ax.spines['top'].set_linewidth(0.5)
            option_ax.spines['bottom'].set_linewidth(0.5)
            option_ax.spines['left'].set_linewidth(0.5)
            option_ax.spines['right'].set_linewidth(0.5)
            
            # 存储选项轴
            self.option_axes.append(option_ax)
        
        self.fig.canvas.draw_idle()
    
    def _on_click(self, event):
        """处理点击事件"""
        print(f"接收到点击事件: {event.inaxes}")
        if hasattr(event, 'x') and hasattr(event, 'y'):
            print(f"点击坐标: x={event.x}, y={event.y}")
            
            # 获取图形转换器
            trans = self.fig.transFigure.inverted()
            # 将像素坐标转换为图形坐标
            x_fig, y_fig = trans.transform((event.x, event.y))
            print(f"图形坐标: x_fig={x_fig:.4f}, y_fig={y_fig:.4f}")
            print(f"按钮坐标: x={self.x:.4f}, y={self.y:.4f}, width={self.width:.4f}, height={self.height:.4f}")
            
            # 检查是否在按钮区域内
            if (self.x <= x_fig <= self.x + self.width and 
                self.y <= y_fig <= self.y + self.height):
                print(f"点击在按钮区域内！处理下拉菜单打开/关闭操作")
                self.is_open = not self.is_open
                self._draw_button()
                
                if self.is_open:
                    self._draw_options()
                else:
                    self._clear_options()
                return
        
        # 检查是否点击在选项上
        if hasattr(event, 'inaxes') and event.inaxes is not None:
            for i, ax in enumerate(self.option_axes):
                if event.inaxes == ax:
                    print(f"选择选项: {self.options[i]}")
                    old_idx = self.current_idx
                    self.current_idx = i
                    self.is_open = False
                    self._draw_button()
                    self._clear_options()
                    
                    # 调用回调函数
                    if self.callback and old_idx != self.current_idx:
                        self.callback(self.options[self.current_idx])
                    return
        
        # 如果点击在其他地方，关闭下拉菜单
        if self.is_open:
            print("点击在其他区域，关闭下拉菜单")
            self.is_open = False
            self._draw_button()
            self._clear_options()
    
    def _on_hover(self, event):
        """处理鼠标悬停事件"""
        if not self.is_open:
            return
        
        old_hover = self.hover_idx
        self.hover_idx = None
        
        # 检查鼠标是否悬停在选项上
        for i, ax in enumerate(self.option_axes):
            if event.inaxes == ax:
                self.hover_idx = i
                break
        
        # 如果悬停状态改变，重绘选项
        if old_hover != self.hover_idx:
            self._draw_options()
    
    def set_visible(self, visible):
        """设置可见性"""
        self.button_ax.set_visible(visible)
        if not visible:
            self._clear_options()
    
    def get_value(self):
        """获取当前选择的选项"""
        if self.options and len(self.options) > self.current_idx:
            return self.options[self.current_idx]
        return None
    
    def set_options(self, options, initial=0):
        """设置选项列表"""
        self.options = options
        self.current_idx = min(initial, len(options)-1) if options else 0
        self._draw_button()
        if self.is_open:
            self._draw_options()

# 忽略Matplotlib的警告
warnings.filterwarnings("ignore", category=UserWarning)

# 坐标轴范围计算配置
INCLUDE_PLATFORM_POSITIONS = True      # 是否包括平台位置数据
INCLUDE_TARGET_POSITIONS = True        # 是否包括目标点位置
INCLUDE_REFERENCE_POINTS = True        # 是否包括参考轨迹点
INCLUDE_RISK_POSITIONS = True          # 是否包括风险数据位置信息
INCLUDE_BALL_TRAJECTORY = True         # 是否包括球体轨迹数据
MARGIN_PERCENT = 0.2                  # 坐标轴边界空间百分比

# 放大视图配置
ZOOM_VIEW_ENABLED = True              # 是否启用放大视图
ZOOM_TARGET_TYPE = 'host'             # 放大对象类型: 'host'(本机), 'neighbor'(邻居), 'risk_reporter'(发布风险的飞机), 'ground'(地面点)
ZOOM_TARGET_ID = 101                  # 放大对象ID (用于邻居和发布风险的飞机)
ZOOM_RANGE = 2000                     # 放大视图显示范围 (米)

# 新增 - 放大对象选择数据
available_platform_ids = []           # 可用的平台ID列表
available_reporter_ids = []           # 可用的风险发布者ID列表
available_ground_points = []          # 可用的地面点列表
selected_platform_id = None           # 当前选择的平台ID
selected_reporter_id = None           # 当前选择的风险发布者ID
selected_ground_point = None          # 当前选择的地面点

# 读取CSV文件
print("正在加载数据...")
start_time = time.time()

# 主文件路径
main_file = 'plugin_data/task_101_CA_get_next_position_data.csv'
neighbor_file = 'plugin_data/task_101_neiborUAV_next_position_data_file.csv'
risk_file = 'plugin_data/task_101_CRisk_info_data.csv'  # 风险信息文件
ball_traj_file = 'plugin_data/task_101_ballTraj_data_file.csv'  # 球体轨迹文件

# 读取主平台数据
main_df = pd.read_csv(main_file)

# 检查是否存在邻居飞机数据文件
if os.path.exists(neighbor_file):
    # 读取邻居平台数据
    neighbor_df = pd.read_csv(neighbor_file)
    
    # 检查邻居文件是否有实际数据（除了表头外）
    if len(neighbor_df) > 0:
        print("检测到老版本数据存储方式：从两个文件读取数据")
        # 老版本：合并主平台和邻居平台数据
        common_columns = set(main_df.columns) & set(neighbor_df.columns)
        main_df = main_df[list(common_columns)]
        neighbor_df = neighbor_df[list(common_columns)]
        df = pd.concat([main_df, neighbor_df], ignore_index=True)
        
        # 标记为老版本数据
        is_old_version = True
    else:
        print("检测到新版本数据存储方式：仅从主文件读取数据")
        # 新版本：只使用主文件数据
        df = main_df
        is_old_version = False
else:
    print("未找到邻居数据文件，使用主文件数据")
    # 邻居文件不存在，只使用主文件数据
    df = main_df
    is_old_version = False

print(f"数据加载完成! 耗时: {time.time() - start_time:.2f}秒")
print(f"加载了 {len(df)} 条数据记录，包含 {df['platformId'].nunique()} 个平台")

# 读取风险信息数据
risk_df = None
if os.path.exists(risk_file):
    risk_df = pd.read_csv(risk_file)
    print(f"风险信息数据加载完成! 共 {len(risk_df)} 条记录")
    
    # 检查风险类型1的数据
    risk_type_1_count = len(risk_df[risk_df['risk_type'] == 1])
    print(f"其中风险类型1（风险区域）记录数: {risk_type_1_count}")
    
    # 检查是否有命令字段
    if 'cmd_0' in risk_df.columns and 'cmd_1' in risk_df.columns and 'cmd_2' in risk_df.columns and 'riskID' in risk_df.columns:
        print("发布风险飞机位置数据列存在")
    else:
        print("警告: 发布风险飞机位置数据列缺失")
else:
    print("未找到风险信息数据文件")

# 读取球体轨迹数据
ball_traj_df = None
if os.path.exists(ball_traj_file):
    ball_traj_df = pd.read_csv(ball_traj_file)
    print(f"球体轨迹数据加载完成! 共 {len(ball_traj_df)} 条记录")
else:
    print("未找到球体轨迹数据文件")

# 参考坐标点
REF_LAT = 36.6242256  # 参考纬度
REF_LON = 104.9916610  # 参考经度
REF_ALT = 2695.0  # 参考高度（米）

# 显示数据信息
print(f"Z轴数据范围: {df['z'].min()} 到 {df['z'].max()}米")
print(f"参考坐标: 纬度={REF_LAT}°, 经度={REF_LON}°, 高度={REF_ALT}米")

# 设置Z轴的显示范围
Z_DISPLAY_MIN = 1695.0  # Z轴显示的最小值
Z_DISPLAY_MAX = 3700.0  # Z轴显示的最大值

# 将Z轴数据转换为实际高度
df['altitude'] = REF_ALT + df['z']  # 将Z坐标加上参考高度得到真实高度

# 计算坐标轴范围 - 准备阶段
print("正在计算坐标轴范围...")

# 初始化范围变量
x_min_all = float('inf')  # 北向最小值
x_max_all = float('-inf')  # 北向最大值
y_min_all = float('inf')  # 东向最小值
y_max_all = float('-inf')  # 东向最大值

# 考虑本机和邻居飞机的位置数据
if INCLUDE_PLATFORM_POSITIONS:
    x_min_all = min(x_min_all, df['x'].min())
    x_max_all = max(x_max_all, df['x'].max())
    y_min_all = min(y_min_all, df['y'].min())
    y_max_all = max(y_max_all, df['y'].max())

# 考虑目标点位置
if INCLUDE_TARGET_POSITIONS:
    x_min_all = min(x_min_all, df['target_x'].min())
    x_max_all = max(x_max_all, df['target_x'].max())
    y_min_all = min(y_min_all, df['target_y'].min())
    y_max_all = max(y_max_all, df['target_y'].max())

# 考虑参考点数据
if INCLUDE_REFERENCE_POINTS:
    for i in range(10):  # 0-9共10个参考点
        ref_x_col = f'ref{i}_x'
        ref_y_col = f'ref{i}_y'
        
        if ref_x_col in df.columns and ref_y_col in df.columns:
            # 过滤掉NaN值
            valid_ref_x = df[ref_x_col].dropna()
            valid_ref_y = df[ref_y_col].dropna()
            
            if not valid_ref_x.empty and not valid_ref_y.empty:
                x_min_all = min(x_min_all, valid_ref_x.min())
                x_max_all = max(x_max_all, valid_ref_x.max())
                y_min_all = min(y_min_all, valid_ref_y.min())
                y_max_all = max(y_max_all, valid_ref_y.max())

# 考虑风险数据 - 风险点位置
if INCLUDE_RISK_POSITIONS and risk_df is not None:
    # 风险点位置 (pos0=x, pos1=y)
    if 'pos0' in risk_df.columns and 'pos1' in risk_df.columns:
        valid_pos0 = risk_df['pos0'].dropna()
        valid_pos1 = risk_df['pos1'].dropna()
        
        if not valid_pos0.empty and not valid_pos1.empty:
            x_min_all = min(x_min_all, valid_pos0.min())
            x_max_all = max(x_max_all, valid_pos0.max())
            y_min_all = min(y_min_all, valid_pos1.min())
            y_max_all = max(y_max_all, valid_pos1.max())

# 球体轨迹数据
if INCLUDE_BALL_TRAJECTORY and ball_traj_df is not None:
    for i in range(10):  # 0-9共10个参考点
        ref_x_col = f'ref{i}_x'
        ref_y_col = f'ref{i}_y'
        
        if ref_x_col in ball_traj_df.columns and ref_y_col in ball_traj_df.columns:
            valid_ref_x = ball_traj_df[ref_x_col].dropna()
            valid_ref_y = ball_traj_df[ref_y_col].dropna()
            
            if not valid_ref_x.empty and not valid_ref_y.empty:
                x_min_all = min(x_min_all, valid_ref_x.min())
                x_max_all = max(x_max_all, valid_ref_x.max())
                y_min_all = min(y_min_all, valid_ref_y.min())
                y_max_all = max(y_max_all, valid_ref_y.max())

# 添加边界空间 - 使用配置的边界比例
margin_percent = MARGIN_PERCENT
x_range = x_max_all - x_min_all
y_range = y_max_all - y_min_all

x_min_with_margin = x_min_all - margin_percent * x_range
x_max_with_margin = x_max_all + margin_percent * x_range
y_min_with_margin = y_min_all - margin_percent * y_range
y_max_with_margin = y_max_all + margin_percent * y_range

print(f"计算出的坐标轴范围:")
print(f"X轴(北向): {x_min_with_margin:.2f} 到 {x_max_with_margin:.2f}")
print(f"Y轴(东向): {y_min_with_margin:.2f} 到 {y_max_with_margin:.2f}")
print(f"坐标轴范围计算使用配置: 平台位置={INCLUDE_PLATFORM_POSITIONS}, 目标点={INCLUDE_TARGET_POSITIONS}, 参考点={INCLUDE_REFERENCE_POINTS}, 风险点={INCLUDE_RISK_POSITIONS}, 球体轨迹={INCLUDE_BALL_TRAJECTORY}")

# 全局变量
is_paused = False
cur_frame = 0
frame_step = 50  # 初始帧率设置
frame_update_flag = False  # 帧更新状态标志
view_mode = '3d'  # 初始视图模式: '3d' 或 'top'
animation_running = True  # 动画状态标志
trail_length = 5000  # 默认轨迹长度（时间帧数）
risk_reporter_trail_length = 10000  # 风险发布飞机轨迹长度（时间帧数）- 设置更长
show_heading = True  # 是否显示航向角箭头
show_nextpoint = True  # 是否显示下一点位置和方向
show_risk = True  # 是否显示风险信息
show_ref_points = True  # 是否显示参考轨迹点
heading_arrow_length = 500  # 航向角箭头长度
blink_status = True  # 控制风险信息闪烁
blink_counter = 0  # 闪烁计数器
BLINK_INTERVAL = 5  # 闪烁间隔
risk_distance_text = None  # 风险距离文本对象
risk_reporter_markers = []  # 风险发布者飞机标记
risk_reporter_texts = []    # 风险发布者飞机ID文本
risk_reporter_lines = {}    # 风险发布者飞机轨迹线 {risk_id: line_object}
risk_reporter_history = {}  # 风险发布者飞机历史位置 {risk_id: {time: [east, north, alt]}}
risk_ground_markers = []    # 风险区域在地面上的位点标记
risk_laser_lines = []       # 风险发布飞机到地面的激光光束线
risk_cones = []             # 从地面点到风险圆高度的圆锥体
ref_point_markers = []      # 参考轨迹点标记
type_dropdown = None        # 放大视图类型下拉菜单
id_dropdown = None          # 放大视图ID下拉菜单

# 获取所有唯一的平台ID
platform_ids = df['platformId'].unique()

# 颜色方案
colors = plt.cm.tab10(np.linspace(0, 1, len(platform_ids)))
color_dict = {pid: colors[i] for i, pid in enumerate(platform_ids)}

# 到达区域半径（米）
TARGET_RADIUS = 1200

# 创建图形和子图布局
if ZOOM_VIEW_ENABLED:
    # 如果启用了放大视图，创建左右布局，但保留顶部空间给控制面板
    fig = plt.figure(figsize=(16, 10), dpi=100)
    
    # 定义子图位置和尺寸 - 根据用户草图调整为三区域布局
    left_plot_left = 0.05   # 左侧3D视图左边距
    left_plot_width = 0.28  # 左侧3D视图宽度
    right_plot_left = 0.38  # 中间2D视图左边距
    right_plot_width = 0.28 # 中间2D视图宽度
    plots_bottom = 0.15    # 视图底部边距，留出空间给播放控制
    plots_height = 0.75     # 视图高度
    
    # 创建两个独立的轴区域，而不是使用add_subplot的网格规范
    ax = fig.add_axes([left_plot_left, plots_bottom, left_plot_width, plots_height], projection='3d')
    zoom_ax = fig.add_axes([right_plot_left, plots_bottom, right_plot_width, plots_height])
    
    # 设置放大视图标题和比例
    zoom_ax.set_title('Zoom View (2D)', fontsize=14, pad=10)
    zoom_ax.set_aspect('equal')  # 保持坐标轴比例一致
else:
    # 如果没启用放大视图，只有一个3D视图
    fig = plt.figure(figsize=(12, 10), dpi=100)
    ax = fig.add_subplot(111, projection='3d')

ax.set_xlabel('East (m)', fontsize=12)
ax.set_ylabel('North (m)', fontsize=12)
ax.set_zlabel('Altitude (m)', fontsize=12)
ax.set_title('Platform Trajectories - 3D View with Altitude', fontsize=16)

# 设置坐标轴范围
ax.set_ylim(x_min_with_margin, x_max_with_margin)  # Y轴设置为北向，使用新计算的边界
ax.set_xlim(y_min_with_margin, y_max_with_margin)  # X轴设置为东向，使用新计算的边界
ax.set_zlim(Z_DISPLAY_MIN, Z_DISPLAY_MAX)  # Z轴设置为固定范围

# 添加参考平面 - 最低高度平面
x_ground = np.linspace(y_min_with_margin, y_max_with_margin, 10)
y_ground = np.linspace(x_min_with_margin, x_max_with_margin, 10)
X_ground, Y_ground = np.meshgrid(x_ground, y_ground)
Z_min = np.ones(X_ground.shape) * Z_DISPLAY_MIN
ax.plot_surface(X_ground, Y_ground, Z_min, alpha=0.2, color='lightgray')

# 初始化放大视图设置
if ZOOM_VIEW_ENABLED:
    zoom_ax.set_xlabel('East (m)', fontsize=10)
    zoom_ax.set_ylabel('North (m)', fontsize=10)
    # 删除Z轴设置，2D视图不需要
    
    # 2D放大视图不需要参考平面
    # 添加网格
    zoom_ax.grid(True, linestyle='--', alpha=0.6)
    
    # 记录放大视图初始collections
    zoom_ax.collections_init = list(zoom_ax.collections)
    
    # 放大视图对象数据
    zoom_lines = []
    zoom_points = []
    zoom_target_points = []
    
    # 为每个平台创建放大视图对象
    for i, pid in enumerate(platform_ids):
        ln, = zoom_ax.plot([], [], color=color_dict[pid], linewidth=2)
        pt, = zoom_ax.plot([], [], 'o', color=color_dict[pid], markersize=8)
        targ, = zoom_ax.plot([], [], '*', color=color_dict[pid], markersize=10, alpha=0.7)
        
        zoom_lines.append(ln)
        zoom_points.append(pt)
        zoom_target_points.append(targ)
    
    # 放大视图中的其他对象
    zoom_heading_arrows = []
    zoom_risk_markers = []
    zoom_ground_markers = []
    zoom_reporter_markers = []
    zoom_circle_objects = []

# 记录初始collections用于后续清除时避免删除初始元素
ax.collections_init = list(ax.collections)

# 构建时间帧索引
unique_times = sorted(df['time'].unique())

# 初始化轨迹线和当前位置点
lines_3d = []
points_3d = []
target_points = []  # 目标点
target_circles = []  # 目标区域圆
heading_arrows = []  # 航向角箭头
nextpoint_markers = []  # nextPoint位置标记
nextpoint_arrows = []  # nextPoint方向箭头

# 初始化风险信息绘图对象
risk_aircraft_markers = []  # 风险飞机标记
risk_circle_objects = []    # 风险区域圆
risk_point_markers = []     # 风险点标记
risk_reporter_markers = []  # 风险发布者飞机标记
risk_reporter_texts = []    # 风险发布者飞机ID文本

for i, pid in enumerate(platform_ids):
    ln, = ax.plot([], [], [], color=color_dict[pid], linewidth=2, label=f'Platform {int(pid)}')
    pt, = ax.plot([], [], [], 'o', color=color_dict[pid], markersize=8)
    
    # 初始化目标点（使用星形标记）
    targ, = ax.plot([], [], [], '*', color=color_dict[pid], markersize=10, alpha=0.7)
    
    # 初始化nextPoint标记
    np_marker, = ax.plot([], [], [], 'x', color=color_dict[pid], markersize=8, alpha=0.9)
    
    lines_3d.append(ln)
    points_3d.append(pt)
    target_points.append(targ)
    target_circles.append(None)
    heading_arrows.append(None)
    nextpoint_markers.append(np_marker)
    nextpoint_arrows.append(None)

# 添加时间文本和图例
time_text = ax.text2D(0.02, 0.95, '', transform=ax.transAxes, fontsize=12, bbox=dict(facecolor='white', alpha=0.7))

# 不要在这里创建图例，我们将在后面整合所有图例
# ax.legend(loc='upper right', fontsize=10)

# 添加坐标系说明
# ax.text2D(0.98, 0.02, 'NED Coordinate System with Altitude', transform=ax.transAxes, 
#         horizontalalignment='right', fontsize=10, bbox=dict(facecolor='white', alpha=0.7))

# 添加控件
# 滑动条 - 位于底部中央
slider_bottom = 0.06  # 滑动条底部位置
slider_left = 0.15    # 滑动条左侧位置
slider_width = 0.7    # 滑动条宽度
slider_height = 0.03  # 滑动条高度
ax_slider = plt.axes([slider_left, slider_bottom, slider_width, slider_height])
frame_slider = Slider(ax_slider, 'Frame', 0, len(unique_times)-1, valinit=0, valstep=1)

# 播放控制按钮 - 保持在底部上方
btn_color = 'lightblue'
hover_color = 'skyblue'
btn_width = 0.1
btn_height = 0.03
btn_bottom = 0.10    # 按钮底部位置，在滑动条上方
ax_backward = plt.axes([0.30, btn_bottom, btn_width, btn_height])
ax_toggle = plt.axes([0.42, btn_bottom, btn_width, btn_height])
ax_forward = plt.axes([0.54, btn_bottom, btn_width, btn_height])
btn_backward = Button(ax_backward, 'Backward', color=btn_color, hovercolor=hover_color)
btn_toggle = Button(ax_toggle, 'Play', color=btn_color, hovercolor=hover_color)
btn_forward = Button(ax_forward, 'Forward', color=btn_color, hovercolor=hover_color)

# 创建控制面板 - 放在右侧空白区域
panel_width = 0.25    # 控制面板宽度
panel_height = 0.75   # 控制面板高度，与视图区域同高
panel_left = 0.71     # 控制面板左侧位置
panel_bottom = plots_bottom  # 控制面板底部位置，与视图区域对齐

# 控制面板背景
panel_rect = Rectangle((panel_left, panel_bottom), panel_width, panel_height,
                      transform=fig.transFigure,
                      facecolor="whitesmoke", alpha=0.3, edgecolor="black", lw=1)
fig.patches.append(panel_rect)
fig.text(panel_left + 0.01, panel_bottom + panel_height - 0.04, "Control Panel",
         transform=fig.transFigure,
         fontsize=12, fontweight="bold", color="black")

# 步长控制 - 右侧面板顶部
control_y = panel_bottom + panel_height - 0.09  # 起始y位置
control_spacing = 0.05  # 控件间距
control_height = 0.03  # 控件高度

# 步长输入框与"Set"按钮
ax_textbox = plt.axes([panel_left + 0.02, control_y, panel_width * 0.5, control_height])
ax_set = plt.axes([panel_left + panel_width * 0.55, control_y, panel_width * 0.4, control_height])
text_box = TextBox(ax_textbox, 'Step:', initial=str(frame_step))
btn_set = Button(ax_set, 'Set', color=btn_color, hovercolor=hover_color)

# 轨迹长度输入框与按钮
control_y -= control_spacing
ax_trail_textbox = plt.axes([panel_left + 0.02, control_y, panel_width * 0.5, control_height])
ax_trail_set = plt.axes([panel_left + panel_width * 0.55, control_y, panel_width * 0.4, control_height])
trail_text_box = TextBox(ax_trail_textbox, 'Trail:', initial=str(trail_length))
btn_trail_set = Button(ax_trail_set, 'Set', color=btn_color, hovercolor=hover_color)

# 视图切换按钮
control_y -= control_spacing
ax_view = plt.axes([panel_left + 0.02, control_y, panel_width * 0.95, control_height])
view_button = Button(ax_view, 'Switch View', color=btn_color, hovercolor=hover_color)

# 分隔线
control_y -= control_spacing * 0.7
fig.text(panel_left + 0.02, control_y, "Display Options", 
         transform=fig.transFigure,
         fontsize=10, fontweight="bold", color="black")

# 显示选项复选框
control_y -= control_spacing * 0.7
control_box_height = 0.04

# 航向角显示开关
ax_heading = plt.axes([panel_left + 0.02, control_y, panel_width * 0.95, control_box_height])
heading_check = CheckButtons(ax_heading, ['Show Heading'], [show_heading])

# nextPoint显示开关
control_y -= control_spacing
ax_nextpoint = plt.axes([panel_left + 0.02, control_y, panel_width * 0.95, control_box_height])
nextpoint_check = CheckButtons(ax_nextpoint, ['Show NextPoint'], [show_nextpoint])

# 风险信息显示开关
control_y -= control_spacing
ax_risk = plt.axes([panel_left + 0.02, control_y, panel_width * 0.95, control_box_height])
risk_check = CheckButtons(ax_risk, ['Show Risk Info'], [show_risk])

# 参考轨迹点显示开关
control_y -= control_spacing
ax_ref = plt.axes([panel_left + 0.02, control_y, panel_width * 0.95, control_box_height])
ref_check = CheckButtons(ax_ref, ['Show Reference Points'], [show_ref_points])

# 在UI布局代码之前添加放大视图控制的回调函数定义

# 放大视图配置变更回调函数
def on_type_change(selected_option):
    global ZOOM_TARGET_TYPE
    # 更新目标类型
    if selected_option == 'Host':
        ZOOM_TARGET_TYPE = 'host'
        id_dropdown.set_visible(False)
    elif selected_option == 'Neighbor':
        ZOOM_TARGET_TYPE = 'neighbor'
        # 更新ID下拉菜单选项为可用的邻居平台ID
        neighbor_ids = [f"ID: {int(pid)}" for pid in platform_ids if pid != 101]
        if neighbor_ids:
            id_dropdown.set_options(neighbor_ids)
            id_dropdown.set_visible(True)
            # 设置ZOOM_TARGET_ID为第一个邻居ID
            ZOOM_TARGET_ID = platform_ids[platform_ids != 101][0] if len(platform_ids[platform_ids != 101]) > 0 else 101
        else:
            id_dropdown.set_options(["No neighbors available"])
            id_dropdown.set_visible(True)
    elif selected_option == 'Risk Reporter':
        ZOOM_TARGET_TYPE = 'risk_reporter'
        # 更新ID下拉菜单选项为可用的风险发布者ID
        if risk_df is not None and 'riskID' in risk_df.columns:
            reporter_ids = sorted(list(set([f"ID: {int(rid)}" for rid in risk_df['riskID'].dropna().unique()])))
            if reporter_ids:
                id_dropdown.set_options(reporter_ids)
                id_dropdown.set_visible(True)
                # 设置ZOOM_TARGET_ID为第一个风险发布者ID
                ZOOM_TARGET_ID = int(risk_df['riskID'].dropna().unique()[0])
            else:
                id_dropdown.set_options(["No reporters available"])
                id_dropdown.set_visible(True)
        else:
            id_dropdown.set_options(["No risk data"])
            id_dropdown.set_visible(True)
    elif selected_option == 'Ground':
        ZOOM_TARGET_TYPE = 'ground'
        id_dropdown.set_visible(False)
    
    # 更新当前帧以应用变更
    update(cur_frame)
    fig.canvas.draw_idle()

def on_id_change(selected_option):
    global ZOOM_TARGET_ID
    # 从选项文本中提取ID数字
    try:
        id_value = int(selected_option.split(': ')[1])
        ZOOM_TARGET_ID = id_value
        # 更新当前帧以应用变更
        update(cur_frame)
        fig.canvas.draw_idle()
    except:
        pass

def zoom_range_submit(text):
    set_zoom_range(text)

def zoom_range_set(event):
    set_zoom_range(zoom_range_box.text)

# 设置放大视图范围函数
def set_zoom_range(new_range):
    global ZOOM_RANGE
    try:
        val = float(new_range)
        if val <= 0:
            val = 500
        ZOOM_RANGE = val
        update(cur_frame)
        fig.canvas.draw_idle()
    except ValueError:
        pass

# 添加放大视图控制UI - 位置调整到与Display Options区域间隔明确
# 放大视图控制设置部分
control_y -= control_spacing * 1.5  # 与上面的控件保持明确间距
zoom_section_y = control_y
fig.text(panel_left + 0.02, zoom_section_y, "Zoom View Settings", 
         transform=fig.transFigure,
         fontsize=10, fontweight="bold", color="black")

# 放大视图类型选择下拉菜单
control_y -= control_spacing * 0.7
type_options = ['Host', 'Neighbor', 'Risk Reporter', 'Ground']
type_initial = 0  # 默认选择Host

# 控件位置和大小
dropdown_x = panel_left + 0.02
dropdown_y = control_y
dropdown_width = panel_width * 0.95  # 宽度与其他控件一致
dropdown_height = 0.03  # 与其他控件高度保持一致

# 为放大视图控制区域创建相应的控件
# 注意：type_dropdown和id_dropdown已经在全局变量中声明
type_dropdown = DropdownMenu(fig, dropdown_x, dropdown_y, 
                         dropdown_width, dropdown_height,
                         type_options, type_initial, 
                         label='Target Type: ', callback=on_type_change)

# ID选项下拉菜单 - 位置向下偏移
control_y -= control_spacing * 1.2  # 增加间距，确保下拉菜单不会遮挡
id_dropdown = DropdownMenu(fig, dropdown_x, control_y, 
                         dropdown_width, dropdown_height,
                         ["Select ID"], 0, 
                         label='Target ID: ', callback=on_id_change)
id_dropdown.set_visible(False)  # 默认隐藏

# 放大视图范围输入框 - 继续向下偏移
control_y -= control_spacing * 1.2  # 增加间距
ax_zoom_range_box = plt.axes([panel_left + 0.02, control_y, panel_width * 0.5, control_height])
ax_zoom_set = plt.axes([panel_left + panel_width * 0.55, control_y, panel_width * 0.4, control_height])
zoom_range_box = TextBox(ax_zoom_range_box, 'Range (m):', initial=str(ZOOM_RANGE))
btn_zoom_set = Button(ax_zoom_set, 'Set', color=btn_color, hovercolor=hover_color)

# 风险信息区域 - 放在控制面板内，底部区域
risk_section_y = control_y - control_spacing * 2  # 与上面控件保持足够间距
fig.text(panel_left + 0.02, risk_section_y, "Risk Information", 
         transform=fig.transFigure,
         fontsize=10, fontweight="bold", color="black")

# 风险信息显示区域背景 - 高度适当调整确保不超出面板
risk_section_height = min(0.20, risk_section_y - panel_bottom - 0.02)  # 确保不超出底部
risk_info_rect = Rectangle((panel_left + 0.01, panel_bottom + 0.02), 
                          panel_width - 0.02, risk_section_height, 
                          transform=fig.transFigure,
                          facecolor="white", alpha=0.3, edgecolor="gray", lw=1)
fig.patches.append(risk_info_rect)

# 添加经纬度到NED坐标的转换函数
def geo_to_ned(lat, lon, alt, ref_lat, ref_lon, ref_alt):
    """将地理坐标（纬度、经度、高度）转换为NED坐标系（北、东、下）"""
    # 地球半径（米）
    R = 6378137.0
    
    # 纬度和经度转换为弧度
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    ref_lat_rad = math.radians(ref_lat)
    ref_lon_rad = math.radians(ref_lon)
    
    # 纬度差
    dlat = lat_rad - ref_lat_rad
    # 经度差
    dlon = lon_rad - ref_lon_rad
    
    # 计算北向距离
    north = dlat * R
    
    # 计算东向距离
    east = dlon * R * math.cos(ref_lat_rad)
    
    # 计算高度差（下向为正，但因为我们用Z轴表示高度，所以实际上是负的下向值）
    down = ref_alt - alt
    
    return north, east, down

# 处理小键盘按键
def on_key_press(event):
    if event.inaxes != ax_textbox and event.inaxes != ax_trail_textbox:
        return
    
    if hasattr(event, 'key') and event.key:
        key = event.key
        print(f"接收到按键: {key}")
        
        if key.startswith('KP_'):
            digit = key.replace('KP_', '')
            if event.inaxes == ax_textbox:
                current_text = text_box.text
                text_box.set_val(current_text + digit)
            elif event.inaxes == ax_trail_textbox:
                current_text = trail_text_box.text
                trail_text_box.set_val(current_text + digit)

# 应用步长设置
def apply_step_setting():
    global frame_step
    try:
        val = int(text_box.text)
        if val < 1:
            val = 1
            text_box.set_val("1")
        frame_step = val
        print(f"设置每次跳过帧数: {frame_step}")
    except ValueError:
        print(f"无效的帧率值，保持当前值: {frame_step}")
        text_box.set_val(str(frame_step))

def submit_step(text):
    apply_step_setting()

# 应用轨迹长度设置
def apply_trail_setting():
    global trail_length
    try:
        val = int(trail_text_box.text)
        if val < 1:
            val = 1
            trail_text_box.set_val("1")
        trail_length = val
        print(f"设置轨迹长度为: {trail_length} 帧")
        update(cur_frame)
        fig.canvas.draw_idle()
    except ValueError:
        print(f"无效的轨迹长度值，保持当前值: {trail_length}")
        trail_text_box.set_val(str(trail_length))

def submit_trail_length(text):
    apply_trail_setting()

# 设置步长按钮回调函数
def set_step(event):
    apply_step_setting()

# 设置轨迹长度按钮回调函数
def set_trail_length(event):
    apply_trail_setting()

# 滑动条回调函数
def slider_update(val):
    global is_paused, cur_frame
    
    frame = int(val)
    cur_frame = frame
    update(frame)
    fig.canvas.draw_idle()
    
    # 拖动进度条时暂停播放
    is_paused = True
    btn_toggle.label.set_text("Play")

# Play/Pause 按钮回调函数
def toggle_play(event):
    global is_paused
    if is_paused:
        ani.event_source.start()
        is_paused = False
        btn_toggle.label.set_text("Pause")
    else:
        is_paused = True
        btn_toggle.label.set_text("Play")
    fig.canvas.draw_idle()

# 前进按钮回调函数
def forward_frame(event):
    global cur_frame
    current = int(frame_slider.val)
    new_frame = min(current + frame_step, len(unique_times) - 1)
    cur_frame = new_frame
    frame_slider.set_val(new_frame)
    update(new_frame)
    fig.canvas.draw_idle()

# 后退按钮回调函数
def backward_frame(event):
    global cur_frame
    current = int(frame_slider.val)
    new_frame = max(current - frame_step, 0)
    cur_frame = new_frame
    frame_slider.set_val(new_frame)
    update(new_frame)
    fig.canvas.draw_idle()

# 视图切换函数
def toggle_view(event):
    global view_mode
    if view_mode == 'top':
        ax.view_init(elev=30, azim=-60)  # 3D视图
        view_mode = '3d'
        view_button.label.set_text('Top View')
    else:
        ax.view_init(elev=90, azim=-90)  # 俯视图
        view_mode = 'top'
        view_button.label.set_text('3D View')
    fig.canvas.draw_idle()

# 创建3D圆
def create_circle_3d(center_x, center_y, center_z, radius, resolution=30):
    theta = np.linspace(0, 2*np.pi, resolution)
    x = center_x + radius * np.cos(theta)
    y = center_y + radius * np.sin(theta)
    z = np.ones_like(theta) * center_z
    return x, y, z

# 创建3D圆锥
def create_cone_3d(top_x, top_y, top_z, bottom_x, bottom_y, bottom_z, radius, resolution=20):
    """创建一个3D圆锥体，从顶点到底面圆"""
    # 创建底面圆的点
    theta = np.linspace(0, 2*np.pi, resolution)
    circle_x = bottom_x + radius * np.cos(theta)
    circle_y = bottom_y + radius * np.sin(theta)
    circle_z = np.ones_like(theta) * bottom_z
    
    # 创建圆锥的三角面
    cone_verts = []
    for i in range(resolution):
        # 当前点和下一个点构成一个三角形
        next_i = (i + 1) % resolution
        # 一个三角面由顶点和圆上的两个相邻点组成
        tri_verts = [
            (top_x, top_y, top_z),
            (circle_x[i], circle_y[i], circle_z[i]),
            (circle_x[next_i], circle_y[next_i], circle_z[next_i])
        ]
        cone_verts.append(tri_verts)
    
    return cone_verts

# 初始化函数
def init():
    for ln, pt, targ, np_mark in zip(lines_3d, points_3d, target_points, nextpoint_markers):
        ln.set_data([], [])
        ln.set_3d_properties([])
        pt.set_data([], [])
        pt.set_3d_properties([])
        targ.set_data([], [])
        targ.set_3d_properties([])
        np_mark.set_data([], [])
        np_mark.set_3d_properties([])
    
    time_text.set_text('')
    
    # 初始化放大视图
    if ZOOM_VIEW_ENABLED:
        for ln, pt, targ in zip(zoom_lines, zoom_points, zoom_target_points):
            ln.set_data([], [])
            pt.set_data([], [])
            targ.set_data([], [])
    
    # 清空风险信息对象
    global risk_aircraft_markers, risk_circle_objects, risk_point_markers, risk_reporter_markers
    global risk_reporter_texts, risk_reporter_lines, risk_reporter_history, risk_ground_markers, risk_laser_lines, risk_cones
    risk_aircraft_markers = []
    risk_circle_objects = []
    risk_point_markers = []
    risk_reporter_markers = []
    risk_reporter_texts = []
    risk_reporter_lines = {}
    risk_reporter_history = {}
    risk_ground_markers = []
    risk_laser_lines = []
    risk_cones = []
    
    # 强制清除可能残留的所有点和线
    for artist in ax.collections + ax.lines:
        if artist not in lines_3d + points_3d + target_points + nextpoint_markers:
            try:
                artist.remove()
            except:
                pass
    
    # 清除放大视图中的残留对象
    if ZOOM_VIEW_ENABLED:
        for artist in zoom_ax.collections + zoom_ax.lines:
            if artist not in zoom_lines + zoom_points + zoom_target_points:
                try:
                    artist.remove()
                except:
                    pass
    
    return lines_3d + points_3d + target_points + nextpoint_markers + [time_text]

# 更新航向角显示状态
def update_heading_display(label):
    global show_heading
    show_heading = not show_heading
    update(cur_frame)
    fig.canvas.draw_idle()

# 更新nextPoint显示状态
def update_nextpoint_display(label):
    global show_nextpoint
    show_nextpoint = not show_nextpoint
    update(cur_frame)
    fig.canvas.draw_idle()

# 更新风险信息显示状态
def update_risk_display(label):
    global show_risk
    show_risk = not show_risk
    update(cur_frame)
    fig.canvas.draw_idle()

# 更新参考轨迹点显示状态
def update_ref_display(label):
    global show_ref_points
    show_ref_points = not show_ref_points
    update(cur_frame)
    fig.canvas.draw_idle()

# 添加放大视图配置选择函数
def update_zoom_target(target_type, target_id=None):
    global ZOOM_TARGET_TYPE, ZOOM_TARGET_ID
    ZOOM_TARGET_TYPE = target_type
    if target_id is not None:
        ZOOM_TARGET_ID = target_id
    
    # 更新当前帧以立即反映变化
    update(cur_frame)
    fig.canvas.draw_idle()

# 更新函数
def update(frame_idx):
    global cur_frame, view_mode, frame_update_flag, target_circles, heading_arrows, nextpoint_arrows
    global risk_aircraft_markers, risk_circle_objects, risk_point_markers, risk_reporter_markers 
    global risk_reporter_texts, risk_reporter_lines, risk_reporter_history, blink_status, blink_counter
    global risk_distance_text, risk_ground_markers, risk_laser_lines, risk_cones, ref_point_markers
    
    # 放大视图变量 - 避免局部变量问题
    zoom_risk_markers = []
    zoom_ground_markers = []
    zoom_reporter_markers = []
    zoom_circle_objects = []
    
    # 防止重复更新
    if frame_update_flag:
        return lines_3d + points_3d + target_points + nextpoint_markers + [time_text]
    
    frame_update_flag = True
    
    try:
        # 清除之前绘制的所有圆和箭头
        for circle in target_circles:
            if circle is not None:
                try:
                    circle.remove()
                except:
                    pass
        target_circles = []
        
        # 清除航向箭头
        for arrow in heading_arrows:
            if arrow is not None:
                try:
                    if isinstance(arrow, list):
                        for item in arrow:
                            if item is not None:
                                try:
                                    item.remove()
                                except:
                                    pass
                    else:
                        arrow.remove()
                except:
                    if arrow in ax.artists:
                        ax.artists.remove(arrow)
        heading_arrows = []
        
        # 清除nextPoint箭头
        for arrow in nextpoint_arrows:
            if arrow is not None:
                try:
                    if isinstance(arrow, list):
                        for item in arrow:
                            if item is not None:
                                try:
                                    item.remove()
                                except:
                                    pass
                    else:
                        arrow.remove()
                except:
                    if arrow in ax.artists:
                        ax.artists.remove(arrow)
        nextpoint_arrows = []
        
        # 彻底清除风险信息图形
        # 1. 清除已跟踪的风险对象
        for marker in risk_aircraft_markers:
            if marker is not None:
                try:
                    marker.remove()
                except:
                    pass
        
        for circle in risk_circle_objects:
            if circle is not None:
                try:
                    if hasattr(circle, 'remove'):
                        circle.remove()
                    elif circle in ax.collections:
                        ax.collections.remove(circle)
                except:
                    pass
        
        for marker in risk_point_markers:
            if marker is not None:
                try:
                    marker.remove()
                except:
                    pass
        
        # 清除风险发布者标记和文本
        for marker in risk_reporter_markers:
            if marker is not None:
                try:
                    marker.remove()
                except:
                    pass
        
        for text in risk_reporter_texts:
            if text is not None:
                try:
                    text.remove()
                except:
                    pass
        
        # 清除风险区域地面位点标记
        for marker in risk_ground_markers:
            if marker is not None:
                try:
                    marker.remove()
                except:
                    pass
        
        # 清除激光光束线
        for line in risk_laser_lines:
            if line is not None:
                try:
                    line.remove()
                except:
                    pass
        
        # 清除风险圆锥体
        for cone in risk_cones:
            if cone is not None:
                try:
                    cone.remove()
                except:
                    pass
        
        # 清除参考轨迹点标记
        for marker in ref_point_markers:
            if marker is not None:
                try:
                    marker.remove()
                except:
                    pass
        ref_point_markers = []
        
        # 清除风险距离文本
        if risk_distance_text is not None:
            try:
                risk_distance_text.remove()
            except:
                pass
            risk_distance_text = None
        
        # 2. 清除所有可能是风险点的对象
        for artist in list(ax.lines):
            try:
                # 避免删除基本图形元素
                is_risk = False
                if artist not in lines_3d and artist not in points_3d and artist not in target_points and artist not in nextpoint_markers:
                    # 尝试判断是否是风险点（红色点标记）
                    try:
                        if artist.get_color() == 'r' or artist.get_color() == 'red':
                            is_risk = True
                    except:
                        pass
                    
                    if is_risk:
                        artist.remove()
            except:
                pass
        
        # 3. 清除所有collections（可能包含风险圆）
        for collection in list(ax.collections):
            try:
                if collection not in ax.collections_init:  # 避免删除初始化的集合
                    collection.remove()
            except:
                pass
        
        risk_aircraft_markers = []
        risk_circle_objects = []
        risk_point_markers = []
        risk_reporter_markers = []
        risk_reporter_texts = []
        risk_ground_markers = []
        risk_laser_lines = []
        risk_cones = []
        
        # 更新闪烁状态
        blink_counter = (blink_counter + 1) % BLINK_INTERVAL
        if blink_counter == 0:
            blink_status = not blink_status
        
        cur_frame = frame_idx
        t = unique_times[frame_idx]
        time_text.set_text(f'Time: {t:.2f}s')
        
        # 更新滑动条位置
        frame_slider.eventson = False
        frame_slider.set_val(frame_idx)
        frame_slider.eventson = True
        
        # 处理每个平台的数据
        zoom_target_east = None  # 放大目标东向位置
        zoom_target_north = None  # 放大目标北向位置
        zoom_target_alt = None   # 放大目标高度
        
    for i, pid in enumerate(platform_ids):
            # 获取当前平台和时间的数据
            mask = (df['platformId'] == pid) & (df['time'] <= t)
            if np.any(mask):
                subset = df[mask]
                
                # 应用轨迹长度限制
                if len(subset) > 0:
                    current_time_idx = np.where(unique_times == t)[0][0]
                    start_time_idx = max(0, current_time_idx - trail_length)
                    if start_time_idx < len(unique_times):
                        start_time = unique_times[start_time_idx]
                        subset = subset[subset['time'] >= start_time]
                
                # 轨迹历史数据
                east_hist = subset['y'].values
                north_hist = subset['x'].values
                alt_hist = subset['altitude'].values
                
                lines_3d[i].set_data(east_hist, north_hist)
                lines_3d[i].set_3d_properties(alt_hist)
                
                # 当前位置点
                curr_mask = subset['time'] == t
                if np.any(curr_mask):
                    curr = subset[curr_mask]
                    east0 = curr['y'].values[0]
                    north0 = curr['x'].values[0]
                    alt0 = curr['altitude'].values[0]
                    
                    points_3d[i].set_data([east0], [north0])
                    points_3d[i].set_3d_properties([alt0])
                    
                    # 检查是否是放大目标
                    if ZOOM_VIEW_ENABLED:
                        # 本机 (通常ID为101)
                        if ZOOM_TARGET_TYPE == 'host' and pid == 101:
                            zoom_target_east = east0
                            zoom_target_north = north0
                            zoom_target_alt = alt0
                        # 邻居飞机
                        elif ZOOM_TARGET_TYPE == 'neighbor' and pid == ZOOM_TARGET_ID:
                            zoom_target_east = east0
                            zoom_target_north = north0
                            zoom_target_alt = alt0
                    
                    # 目标点数据
                    target_east = curr['target_y'].values[0]
                    target_north = curr['target_x'].values[0]
                    target_alt = REF_ALT + curr['target_z'].values[0]
                    
                    target_points[i].set_data([target_east], [target_north])
                    target_points[i].set_3d_properties([target_alt])
                    
                    # 添加目标区域圆
                    circle_x, circle_y, circle_z = create_circle_3d(target_east, target_north, target_alt, TARGET_RADIUS)
                    circle, = ax.plot(circle_x, circle_y, circle_z, '--', color=color_dict[pid], alpha=0.5, linewidth=1)
                    target_circles.append(circle)
                    
                    # 添加航向角箭头
                    if show_heading:
                        psi = curr['psi'].values[0]
                        
                        # 计算箭头方向
                        angle = np.pi/2 - psi
                        arrow_length = heading_arrow_length * 2
                        head_size = arrow_length * 0.4
                        
                        # 计算三角形位置
                        tri_center_x = east0 + (arrow_length - head_size/2) * np.cos(angle)
                        tri_center_y = north0 + (arrow_length - head_size/2) * np.sin(angle)
                        
                        # 三角形尖端
                        tip_x = tri_center_x + (head_size/2) * np.cos(angle)
                        tip_y = tri_center_y + (head_size/2) * np.sin(angle)
                        
                        # 三角形底部中点
                        base_center_x = tri_center_x - (head_size/2) * np.cos(angle)
                        base_center_y = tri_center_y - (head_size/2) * np.sin(angle)
                        
                        # 计算底部两侧点
                        angle1 = angle + np.pi/2
                        angle2 = angle - np.pi/2
                        base_width = head_size * 0.7
                        base1_x = base_center_x + (base_width/2) * np.cos(angle1)
                        base1_y = base_center_y + (base_width/2) * np.sin(angle1)
                        base2_x = base_center_x + (base_width/2) * np.cos(angle2)
                        base2_y = base_center_y + (base_width/2) * np.sin(angle2)
                        
                        # 绘制线段
                        line, = ax.plot([east0, base_center_x], [north0, base_center_y], [alt0, alt0], 
                                      '-', color=color_dict[pid], linewidth=3, zorder=1000)
                        
                        # 绘制三角形箭头头部
                        tri_x = [tip_x, base1_x, base2_x]
                        tri_y = [tip_y, base1_y, base2_y]
                        tri_z = [alt0, alt0, alt0]
                        
                        tri_verts = [list(zip(tri_x, tri_y, tri_z))]
                        head = Poly3DCollection(tri_verts, alpha=1.0)
                        head.set_color(color_dict[pid])
                        head.set_edgecolor('black')
                        head.set_linewidth(1.5)
                        ax.add_collection3d(head)
                        
                        heading_arrows.append([line, head])
                    else:
                        heading_arrows.append(None)
                    
                    # 添加nextPoint点和箭头
                    if show_nextpoint and 'nextPoint_x' in curr.columns and 'nextPoint_y' in curr.columns:
                        np_east = curr['nextPoint_y'].values[0]
                        np_north = curr['nextPoint_x'].values[0]
                        np_alt = REF_ALT + curr['nextPoint_z'].values[0]
                        
                        # 更新nextPoint标记位置
                        nextpoint_markers[i].set_data([np_east], [np_north])
                        nextpoint_markers[i].set_3d_properties([np_alt])
                        
                        # 添加nextPoint箭头
                        if 'nextPoint_psi' in curr.columns:
                            np_psi = curr['nextPoint_psi'].values[0]
                            
                            # 计算箭头方向
                            np_angle = np.pi/2 - np_psi
                            np_arrow_length = heading_arrow_length * 1.5
                            np_head_size = np_arrow_length * 0.4
                            
                            # 计算三角形位置
                            np_tri_center_x = np_east + (np_arrow_length - np_head_size/2) * np.cos(np_angle)
                            np_tri_center_y = np_north + (np_arrow_length - np_head_size/2) * np.sin(np_angle)
                            
                            # 三角形尖端
                            np_tip_x = np_tri_center_x + (np_head_size/2) * np.cos(np_angle)
                            np_tip_y = np_tri_center_y + (np_head_size/2) * np.sin(np_angle)
                            
                            # 三角形底部中点
                            np_base_center_x = np_tri_center_x - (np_head_size/2) * np.cos(np_angle)
                            np_base_center_y = np_tri_center_y - (np_head_size/2) * np.sin(np_angle)
                            
                            # 计算底部两侧点
                            np_angle1 = np_angle + np.pi/2
                            np_angle2 = np_angle - np.pi/2
                            np_base_width = np_head_size * 0.7
                            np_base1_x = np_base_center_x + (np_base_width/2) * np.cos(np_angle1)
                            np_base1_y = np_base_center_y + (np_base_width/2) * np.sin(np_angle1)
                            np_base2_x = np_base_center_x + (np_base_width/2) * np.cos(np_angle2)
                            np_base2_y = np_base_center_y + (np_base_width/2) * np.sin(np_angle2)
                            
                            # 绘制线段
                            np_line, = ax.plot([np_east, np_base_center_x], [np_north, np_base_center_y], [np_alt, np_alt], 
                                          '-', color=color_dict[pid], linewidth=2, zorder=1000)
                            
                            # 绘制三角形箭头头部
                            np_tri_x = [np_tip_x, np_base1_x, np_base2_x]
                            np_tri_y = [np_tip_y, np_base1_y, np_base2_y]
                            np_tri_z = [np_alt, np_alt, np_alt]
                            
                            np_tri_verts = [list(zip(np_tri_x, np_tri_y, np_tri_z))]
                            np_head = Poly3DCollection(np_tri_verts, alpha=0.8)
                            np_head.set_color(color_dict[pid])
                            np_head.set_edgecolor('black')
                            np_head.set_linewidth(1.0)
                            ax.add_collection3d(np_head)
                            
                            nextpoint_arrows.append([np_line, np_head])
                        else:
                            nextpoint_arrows.append(None)
                    else:
                        nextpoint_markers[i].set_data([], [])
                        nextpoint_markers[i].set_3d_properties([])
                        nextpoint_arrows.append(None)
                else:
                    # 清空当前帧数据
                    points_3d[i].set_data([], [])
                    points_3d[i].set_3d_properties([])
                    target_points[i].set_data([], [])
                    target_points[i].set_3d_properties([])
                    nextpoint_markers[i].set_data([], [])
                    nextpoint_markers[i].set_3d_properties([])
                    heading_arrows.append(None)
                    nextpoint_arrows.append(None)
            else:
                # 清空所有数据
                lines_3d[i].set_data([], [])
                lines_3d[i].set_3d_properties([])
                points_3d[i].set_data([], [])
                points_3d[i].set_3d_properties([])
                target_points[i].set_data([], [])
                target_points[i].set_3d_properties([])
                nextpoint_markers[i].set_data([], [])
                nextpoint_markers[i].set_3d_properties([])
                heading_arrows.append(None)
                nextpoint_arrows.append(None)
                
        # 风险信息距离数据收集
        risk_distance_info = []
        if risk_df is not None:
            try:
                # 获取当前时间的风险信息
                risk_data = risk_df[risk_df['time'] == t]
                
                # 找到本平台数据（假设本平台ID为101）以获取高度信息
                host_platform_id = 101
                host_data = df[(df['platformId'] == host_platform_id) & (df['time'] == t)]
                host_alt = Z_DISPLAY_MIN  # 默认高度
                if len(host_data) > 0:
                    host_alt = host_data['altitude'].values[0]
                
                if len(risk_data) > 0:
                    for idx, row in risk_data.iterrows():
                        risk_type = row['risk_type']
                        
                        # 获取距离信息（如果有）
                        if 'distanceToObst' in row and not pd.isna(row['distanceToObst']):
                            dist = row['distanceToObst']
                            risk_name = ""
                            
                            # 根据风险类型设置不同的名称
                            if risk_type == 0:
                                risk_name = "Risk Aircraft"
                            elif risk_type == 1:
                                risk_name = "Risk Area"
                            elif risk_type == 2:
                                risk_name = "Risk Point"
                            
                            # 记录到列表中
                            risk_distance_info.append(f"{risk_name} {idx}: {dist:.1f}m")
                        
                        # 根据风险类型绘制不同的标记（使用闪烁）
                        # show_risk控制风险飞机和风险点的显示
                        if risk_type != 1 and blink_status and show_risk:  # 非风险区域类型使用闪烁
                            # 避碰风险飞机 (risk_type = 0)
                            if risk_type == 0:
                                east = row['pos_1']  # 调整坐标以匹配平台数据的显示方式
                                north = row['pos_0']
                                alt = REF_ALT + row['pos_2']  # 调整高度
                                
                                # 使用小圆点标记表示风险飞机，与风险点一致
                                marker, = ax.plot([east], [north], [alt], '.', color='red', 
                                                markersize=10, alpha=1.0, zorder=2000)
                                risk_aircraft_markers.append(marker)
                                
                            # 风险点 (risk_type = 2)
                            elif risk_type == 2:
                                east = row['pos_1']
                                north = row['pos_0']
                                alt = REF_ALT + row['pos_2']  # 调整高度
                                
                                # 使用小圆点标记表示风险点，闪烁显示
                                marker, = ax.plot([east], [north], [alt], '.', color='red', 
                                                 markersize=10, alpha=1.0, zorder=1900)
                                risk_point_markers.append(marker)
                        
                        # 风险区域圆 (risk_type = 1)：根据show_risk控制，但圆锥体等始终显示
                        if risk_type == 1:
                            # 获取风险区域的数据
                            center_east = row['pos_1']
                            center_north = row['pos_0']
                            radius = row['pos_2']  # 风险圆半径
                            
                            # 绘制风险区域圆 - 空心圆，高度在本平台高度上（受show_risk和闪烁控制）
                            if show_risk and blink_status:
                                circle_x, circle_y, circle_z = create_circle_3d(
                                    center_east, center_north, host_alt, radius)
                                circle, = ax.plot(circle_x, circle_y, circle_z, '-', color='red', 
                                                 linewidth=2, alpha=0.8, zorder=1500)
                                risk_circle_objects.append(circle)
                            
                            # 在地面上添加风险区域位点 - 始终显示
                            ground_marker, = ax.plot([center_east], [center_north], [Z_DISPLAY_MIN], 
                                                   '.', color='darkred', markersize=5, alpha=1.0, zorder=1200)
                            risk_ground_markers.append(ground_marker)
                            
                            # 检查是否是地面放大目标
                            if ZOOM_VIEW_ENABLED and ZOOM_TARGET_TYPE == 'ground':
                                zoom_target_east = center_east
                                zoom_target_north = center_north
                                zoom_target_alt = Z_DISPLAY_MIN
                            
                            # 添加从地面点到风险圆高度的倒圆锥 - 始终显示，使用15度半开角
                            cone_top_z = host_alt * 1.2  # 圆锥体顶部高度
                            height_diff = cone_top_z - Z_DISPLAY_MIN  # 高度差
                            cone_half_angle = 15 * np.pi / 180  # 15度半开角转换为弧度
                            cone_base_radius = height_diff * np.tan(cone_half_angle)  # 基于15度半开角计算底部半径
                            
                            cone_verts = create_cone_3d(
                                center_east, center_north, Z_DISPLAY_MIN,  # 顶点（地面点）
                                center_east, center_north, cone_top_z,  # 底面圆心（风险圆高度上方20%）
                                cone_base_radius,  # 基于15度半开角计算的底部半径
                                resolution=20
                            )
                            cone = Poly3DCollection(cone_verts, alpha=0.5, linewidth=0, edgecolor='none', 
                                                   facecolor='lightblue', zorder=1000)
                            ax.add_collection3d(cone)
                            risk_cones.append(cone)
                            
                            # 绘制发布风险信息的飞机位置及轨迹 - 始终显示
                            if 'cmd_0' in row and 'cmd_1' in row and 'cmd_2' in row and 'riskID' in row:
                                if not pd.isna(row['cmd_0']) and not pd.isna(row['cmd_1']) and not pd.isna(row['cmd_2']) and not pd.isna(row['riskID']):
                                    # 获取经纬度和高度数据
                                    reporter_lat = row['cmd_0']  # 纬度坐标 
                                    reporter_lon = row['cmd_1']  # 经度坐标
                                    reporter_alt = row['cmd_2']  # 高度 - 直接使用
                                    reporter_id = row['riskID']  # 发布风险信息的飞机ID
                                    
                                    # 将经纬度转换为NED坐标系
                                    north, east, _ = geo_to_ned(
                                        reporter_lat, reporter_lon, 0,  # 高度参数给0，因为我们不使用计算出的down值
                                        REF_LAT, REF_LON, REF_ALT
                                    )
                                    
                                    # 记录历史位置
                                    reporter_id_str = str(int(reporter_id))
                                    if reporter_id_str not in risk_reporter_history:
                                        risk_reporter_history[reporter_id_str] = {}
                                        # 创建一条新的轨迹线 - 使用紫色
                                        ln, = ax.plot([], [], [], '-', color='purple', linewidth=2, zorder=1000)
                                        risk_reporter_lines[reporter_id_str] = ln
                                    
                                    # 记录当前时间点的位置
                                    risk_reporter_history[reporter_id_str][t] = [east, north, reporter_alt]
                                    
                                    # 检查是否是风险发布者放大目标
                                    if ZOOM_VIEW_ENABLED and ZOOM_TARGET_TYPE == 'risk_reporter' and int(reporter_id) == ZOOM_TARGET_ID:
                                        zoom_target_east = east
                                        zoom_target_north = north
                                        zoom_target_alt = reporter_alt
                                    
                                    # 收集历史轨迹
                                    reporter_times = sorted([time_val for time_val in risk_reporter_history[reporter_id_str].keys() if time_val <= t])
                                    
                                    # 应用轨迹长度限制 - 使用更长的风险发布飞机轨迹长度
                                    current_time_idx = np.where(unique_times == t)[0][0]
                                    start_time_idx = max(0, current_time_idx - risk_reporter_trail_length)
                                    if start_time_idx < len(unique_times):
                                        start_time = unique_times[start_time_idx]
                                        reporter_times = [time_val for time_val in reporter_times if time_val >= start_time]
                                    
                                    if reporter_times:
                                        # 提取历史轨迹坐标
                                        east_hist = []
                                        north_hist = []
                                        alt_hist = []
                                        
                                        for time_val in reporter_times:
                                            e, n, a = risk_reporter_history[reporter_id_str][time_val]
                                            east_hist.append(e)
                                            north_hist.append(n)
                                            alt_hist.append(a)
                                        
                                        # 更新轨迹线
                                        risk_reporter_lines[reporter_id_str].set_data(east_hist, north_hist)
                                        risk_reporter_lines[reporter_id_str].set_3d_properties(alt_hist)
                                        
                                        # 使用当前位置绘制标记 - 使用紫色
                                        reporter_marker, = ax.plot([east], [north], [reporter_alt], 
                                                                  'o', color='purple', markersize=8, alpha=1.0, zorder=1000)
                                        risk_reporter_markers.append(reporter_marker)
                                        
                                        # 添加激光光束连线 - 从飞机位置到地面点，使用青色并添加发光效果
                                        laser_line, = ax.plot([east, center_east], [north, center_north], 
                                                             [reporter_alt, Z_DISPLAY_MIN], ':', color='cyan', 
                                                             linewidth=3, alpha=0.7, zorder=1100)
                                        risk_laser_lines.append(laser_line)
                    
                    # 创建风险距离信息显示区域
                    if risk_distance_info:
                        # 增加表头
                        risk_distance_text_content = "Risk Distances:\n" + "\n".join(risk_distance_info)
                        # 在控制面板的风险信息区域内创建文本框
                        risk_distance_text = fig.text(panel_left + 0.02, risk_section_y - 0.05, risk_distance_text_content,
                                                    transform=fig.transFigure,
                                                    fontsize=9, verticalalignment='top',
                                                    bbox=dict(facecolor='white', alpha=0.7, 
                                                            edgecolor='black', boxstyle='round'))
            except Exception as e:
                print(f"Error processing risk data: {e}")
        
        # 绘制参考轨迹点
        if show_ref_points:
            # 首先绘制当前平台（本机）的参考轨迹点 - 通常ID为101
            host_platform_id = 101
            host_data = df[(df['platformId'] == host_platform_id) & (df['time'] == t)]
            
            if not host_data.empty:
                # 获取当前平台数据的第一行
                host_row = host_data.iloc[0]
                # 使用绿色系渐变，与其他参考点区分
                host_colors = plt.cm.Greens(np.linspace(0.3, 1, 10))
                
                # 绘制当前平台的10个参考点
                for i in range(10):
                    ref_x_col = f'ref{i}_x'
                    ref_y_col = f'ref{i}_y'
                    ref_z_col = f'ref{i}_z'
                    
                    if ref_x_col in host_row and ref_y_col in host_row and ref_z_col in host_row:
                        if not pd.isna(host_row[ref_x_col]) and not pd.isna(host_row[ref_y_col]) and not pd.isna(host_row[ref_z_col]):
                            # 获取参考点坐标
                            ref_north = host_row[ref_x_col]
                            ref_east = host_row[ref_y_col]
                            ref_alt = REF_ALT + host_row[ref_z_col]  # 加上参考高度
                            
                            # 绘制参考点，使用绿色渐变标记，大小比其他参考点稍大
                            marker, = ax.plot([ref_east], [ref_north], [ref_alt], 
                                            'o', color=host_colors[i], markersize=6, alpha=0.9, zorder=1850)
                            ref_point_markers.append(marker)
            
            # 然后处理风险相关的参考轨迹点
            if risk_df is not None:
                # 获取当前时间的风险信息
                risk_data = risk_df[risk_df['time'] == t]
                
                if len(risk_data) > 0:
                    for idx, row in risk_data.iterrows():
                        risk_type = row['risk_type']
                        risk_id = row.get('riskID')
                        
                        # risk_type=0：风险飞机的参考轨迹点
                        if risk_type == 0 and not pd.isna(risk_id):
                            # 转换为整数ID
                            platform_id = int(risk_id)
                            
                            # 根据版本选择数据源
                            ref_data_source = None
                            if is_old_version:
                                # 老版本：从邻居飞机数据中查找
                                if 'neighbor_df' in locals() and neighbor_df is not None:
                                    ref_data_source = neighbor_df
                            else:
                                # 新版本：从主文件中查找
                                ref_data_source = main_df
                            
                            if ref_data_source is not None:
                                # 查找特定时间和平台ID的参考点数据
                                platform_time_data = ref_data_source[
                                    (ref_data_source['time'] == t) & 
                                    (ref_data_source['platformId'] == platform_id)
                                ]
                                
                                if not platform_time_data.empty:
                                    # 有参考点数据，绘制10个参考点
                                    ref_row = platform_time_data.iloc[0]
                                    ref_colors = plt.cm.cool(np.linspace(0, 1, 10))  # 使用颜色渐变
                                    
                                    for i in range(10):
                                        ref_x_col = f'ref{i}_x'
                                        ref_y_col = f'ref{i}_y'
                                        ref_z_col = f'ref{i}_z'
                                        
                                        if ref_x_col in ref_row and ref_y_col in ref_row and ref_z_col in ref_row:
                                            if not pd.isna(ref_row[ref_x_col]) and not pd.isna(ref_row[ref_y_col]) and not pd.isna(ref_row[ref_z_col]):
                                                # 获取参考点坐标
                                                ref_north = ref_row[ref_x_col]
                                                ref_east = ref_row[ref_y_col]
                                                ref_alt = REF_ALT + ref_row[ref_z_col]  # 加上参考高度
                                                
                                                # 绘制参考点，使用渐变色标记
                                                marker, = ax.plot([ref_east], [ref_north], [ref_alt], 
                                                                'o', color=ref_colors[i], markersize=4, alpha=0.8, zorder=1800)
                                                ref_point_markers.append(marker)
                        
                        # risk_type=1：风险区域（球体）的参考轨迹点
                        elif risk_type == 1 and ball_traj_df is not None:
                            # 在球体轨迹数据中查找对应时间的数据
                            ball_time_data = ball_traj_df[ball_traj_df['time'] == t]
                            
                            if not ball_time_data.empty:
                                # 有球体轨迹数据，绘制10个参考点
                                ball_row = ball_time_data.iloc[0]
                                ball_colors = plt.cm.autumn(np.linspace(0, 1, 10))  # 使用不同的颜色渐变
                                
                                for i in range(10):
                                    ref_x_col = f'ref{i}_x'
                                    ref_y_col = f'ref{i}_y'
                                    ref_z_col = f'ref{i}_z'
                                    
                                    if ref_x_col in ball_row and ref_y_col in ball_row and ref_z_col in ball_row:
                                        if not pd.isna(ball_row[ref_x_col]) and not pd.isna(ball_row[ref_y_col]) and not pd.isna(ball_row[ref_z_col]):
                                            # 获取参考点坐标
                                            ref_north = ball_row[ref_x_col]
                                            ref_east = ball_row[ref_y_col]
                                            ref_alt = REF_ALT + ball_row[ref_z_col]  # 加上参考高度
                                            
                                            # 绘制参考点，使用渐变色标记
                                            marker, = ax.plot([ref_east], [ref_north], [ref_alt], 
                                                            '*', color=ball_colors[i], markersize=5, alpha=0.8, zorder=1800)
                                            ref_point_markers.append(marker)
        
        # 更新放大视图
        if ZOOM_VIEW_ENABLED and zoom_target_east is not None and zoom_target_north is not None:
            # 设置放大视图范围
            half_range = ZOOM_RANGE / 2
            zoom_ax.set_xlim(zoom_target_east - half_range, zoom_target_east + half_range)
            zoom_ax.set_ylim(zoom_target_north - half_range, zoom_target_north + half_range)
            
            # 添加放大区域标题
            if ZOOM_TARGET_TYPE == 'host':
                zoom_ax.set_title(f'Zoom View (2D) - Host Platform', fontsize=14)
            elif ZOOM_TARGET_TYPE == 'neighbor':
                zoom_ax.set_title(f'Zoom View (2D) - Neighbor Platform ID {ZOOM_TARGET_ID}', fontsize=14)
            elif ZOOM_TARGET_TYPE == 'risk_reporter':
                zoom_ax.set_title(f'Zoom View (2D) - Risk Reporter ID {ZOOM_TARGET_ID}', fontsize=14)
            elif ZOOM_TARGET_TYPE == 'ground':
                zoom_ax.set_title(f'Zoom View (2D) - Ground Risk Area', fontsize=14)
            
            # 更新放大视图中的平台轨迹和位置
            for i, pid in enumerate(platform_ids):
                mask = (df['platformId'] == pid) & (df['time'] <= t)
                if np.any(mask):
                    subset = df[mask]
                    
                    # 应用轨迹长度限制
                    if len(subset) > 0:
                        current_time_idx = np.where(unique_times == t)[0][0]
                        start_time_idx = max(0, current_time_idx - trail_length)
                        if start_time_idx < len(unique_times):
                            start_time = unique_times[start_time_idx]
                            subset = subset[subset['time'] >= start_time]
                    
                    # 轨迹历史数据
                    east_hist = subset['y'].values
                    north_hist = subset['x'].values
                    
                    # 更新放大视图中的轨迹线 - 只用2D数据
                    zoom_lines[i].set_data(east_hist, north_hist)
                    
                    # 当前位置点
                    curr_mask = subset['time'] == t
                    if np.any(curr_mask):
                        curr = subset[curr_mask]
                        east0 = curr['y'].values[0]
                        north0 = curr['x'].values[0]
                        
                        # 更新放大视图中的当前位置点 - 只用2D数据
                        zoom_points[i].set_data([east0], [north0])
                        
                        # 目标点数据
                        target_east = curr['target_y'].values[0]
                        target_north = curr['target_x'].values[0]
                        
                        # 更新放大视图中的目标点 - 只用2D数据
                        zoom_target_points[i].set_data([target_east], [target_north])
                        
                        # 在2D视图中添加简单的航向指示线
                        if show_heading and 'psi' in curr.columns:
                            psi = curr['psi'].values[0]
                            angle = np.pi/2 - psi
                            arrow_length = heading_arrow_length * 0.5  # 缩短箭头长度，适合2D视图
                            
                            # 计算箭头终点
                            arrow_end_x = east0 + arrow_length * np.cos(angle)
                            arrow_end_y = north0 + arrow_length * np.sin(angle)
                            
                            # 绘制航向线
                            for old_arrow in zoom_heading_arrows:
                                if old_arrow is not None:
                                    try:
                                        old_arrow.remove()
                                    except:
                                        pass
                            
                            heading_arrow = zoom_ax.annotate('', 
                                xy=(arrow_end_x, arrow_end_y), 
                                xytext=(east0, north0),
                                arrowprops=dict(arrowstyle='->', color=color_dict[pid], lw=2),
                                annotation_clip=False)
                            
                            zoom_heading_arrows.append(heading_arrow)
            
            # 添加风险区域到2D放大视图
            if show_risk and risk_df is not None:
                # 清除之前的风险标记
                for marker in zoom_risk_markers:
                    if marker is not None:
                        try:
                            marker.remove()
                        except:
                            pass
                zoom_risk_markers = []
                
                # 清除之前的圆形对象
                for circle in zoom_circle_objects:
                    if circle is not None:
                        try:
                            circle.remove()
                        except:
                            pass
                zoom_circle_objects = []
                
                # 获取当前时间的风险信息
                risk_data = risk_df[risk_df['time'] == t]
                if len(risk_data) > 0:
                    for idx, row in risk_data.iterrows():
                        risk_type = row['risk_type']
                        
                        # 风险飞机和风险点
                        if risk_type != 1 and blink_status:
                            east = row['pos_1']  # 东向坐标
                            north = row['pos_0']  # 北向坐标
                            
                            # 检查是否在放大视图范围内
                            if (abs(east - zoom_target_east) <= half_range and 
                                abs(north - zoom_target_north) <= half_range):
                                
                                # 风险点标记
                                color = 'red' if risk_type == 2 else 'orangered'
                                marker, = zoom_ax.plot([east], [north], '.', color=color, 
                                                     markersize=10, alpha=1.0, zorder=100)
                                zoom_risk_markers.append(marker)
                        
                        # 风险区域
                        elif risk_type == 1:
                            center_east = row['pos_1']
                            center_north = row['pos_0']
                            radius = row['pos_2']  # 风险圆半径
                            
                            # 检查是否在放大视图范围内
                            if (abs(center_east - zoom_target_east) <= half_range and 
                                abs(center_north - zoom_target_north) <= half_range):
                                
                                # 在2D视图中添加风险区域圆
                                if blink_status:
                                    circle = plt.Circle((center_east, center_north), radius, 
                                                       fill=False, color='red', linestyle='-', 
                                                       linewidth=2, alpha=0.8)
                                    zoom_ax.add_artist(circle)
                                    zoom_circle_objects.append(circle)
                                
                                # 添加风险区域中心点 - 始终显示
                                ground_marker, = zoom_ax.plot([center_east], [center_north], 'v', 
                                                            color='darkred', markersize=8, alpha=1.0)
                                zoom_risk_markers.append(ground_marker)
            
            # 添加风险发布者到2D放大视图
            for marker in zoom_reporter_markers:
                if marker is not None:
                    try:
                        marker.remove()
                    except:
                        pass
            zoom_reporter_markers = []
            
            for reporter_id_str, history in risk_reporter_history.items():
                reporter_times = sorted([time_val for time_val in history.keys() if time_val <= t])
                
                # 应用轨迹长度限制
                current_time_idx = np.where(unique_times == t)[0][0]
                start_time_idx = max(0, current_time_idx - risk_reporter_trail_length)
                if start_time_idx < len(unique_times):
                    start_time = unique_times[start_time_idx]
                    reporter_times = [time_val for time_val in reporter_times if time_val >= start_time]
                
                if reporter_times:
                    # 获取最新位置
                    latest_time = reporter_times[-1]
                    east, north, _ = history[latest_time]
                    
                    # 检查是否在放大视图范围内
                    if (abs(east - zoom_target_east) <= half_range and 
                        abs(north - zoom_target_north) <= half_range):
                        
                        # 添加风险发布者标记
                        reporter_marker, = zoom_ax.plot([east], [north], 's', 
                                                      color='purple', markersize=8, alpha=1.0)
                        zoom_reporter_markers.append(reporter_marker)
                        
                        # 添加ID文本
                        label = zoom_ax.annotate(f"ID:{reporter_id_str}", 
                                               xy=(east, north), 
                                               xytext=(5, 5), 
                                               textcoords='offset points',
                                               color='purple', fontsize=8)
                        zoom_reporter_markers.append(label)
                        
                        # 绘制轨迹
                        east_hist = []
                        north_hist = []
                        for time_val in reporter_times:
                            e, n, _ = history[time_val]
                            east_hist.append(e)
                            north_hist.append(n)
                        
                        track, = zoom_ax.plot(east_hist, north_hist, '-', 
                                            color='purple', linewidth=1.5, alpha=0.7)
                        zoom_reporter_markers.append(track)
    
    except Exception as e:
        print(f"更新错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        frame_update_flag = False
    
    # 垃圾回收
    if frame_idx % 200 == 0:
        gc.collect()
    
    # 返回所有有效的艺术家对象
    artists = lines_3d + points_3d + target_points + nextpoint_markers + [time_text]
    
    # 添加箭头对象
    for arrow_list in [heading_arrows, nextpoint_arrows]:
        for arrow in arrow_list:
            if arrow is not None:
                if isinstance(arrow, list):
                    for a in arrow:
                        if a is not None:
                            artists.append(a)
                else:
                    artists.append(arrow)
    
    # 添加风险信息对象
    artists.extend([marker for marker in risk_aircraft_markers if marker is not None])
    artists.extend([circle for circle in risk_circle_objects if circle is not None])
    artists.extend([marker for marker in risk_point_markers if marker is not None])
    artists.extend([marker for marker in risk_reporter_markers if marker is not None])
    artists.extend([text for text in risk_reporter_texts if text is not None])
    artists.extend([marker for marker in risk_ground_markers if marker is not None])
    artists.extend([line for line in risk_laser_lines if line is not None])
    artists.extend([cone for cone in risk_cones if cone is not None])
    
    # 添加参考轨迹点
    artists.extend([marker for marker in ref_point_markers if marker is not None])
    
    # 添加风险发布者飞机轨迹线
    for line in risk_reporter_lines.values():
        if line is not None:
            artists.append(line)
    
    if risk_distance_text is not None:
        artists.append(risk_distance_text)
            
    # 添加放大视图对象
    if ZOOM_VIEW_ENABLED:
        # 添加放大视图中的艺术家对象
        artists.extend(zoom_lines + zoom_points + zoom_target_points)
        
        # 添加其他放大视图对象
        artists.extend([obj for obj in zoom_heading_arrows if obj is not None])
        artists.extend([obj for obj in zoom_risk_markers if obj is not None])
        artists.extend([obj for obj in zoom_ground_markers if obj is not None])
        artists.extend([obj for obj in zoom_reporter_markers if obj is not None])
        artists.extend([obj for obj in zoom_circle_objects if obj is not None])
    
    return artists

# 动画函数
def animate(_):
    global cur_frame, frame_step, is_paused
    
    if not is_paused:
        next_frame = min((cur_frame + frame_step), len(unique_times) - 1)
        cur_frame = next_frame
        update(next_frame)
    
    # 返回所有有效的艺术家对象
    artists = lines_3d + points_3d + target_points + nextpoint_markers + [time_text]
    
    # 添加箭头对象
    for arrow_list in [heading_arrows, nextpoint_arrows]:
        for arrow in arrow_list:
            if arrow is not None:
                if isinstance(arrow, list):
                    for a in arrow:
                        if a is not None:
                            artists.append(a)
                else:
                    artists.append(arrow)
    
    # 添加风险信息对象
    artists.extend([marker for marker in risk_aircraft_markers if marker is not None])
    artists.extend([circle for circle in risk_circle_objects if circle is not None])
    artists.extend([marker for marker in risk_point_markers if marker is not None])
    artists.extend([marker for marker in risk_reporter_markers if marker is not None])
    artists.extend([text for text in risk_reporter_texts if text is not None])
    artists.extend([marker for marker in risk_ground_markers if marker is not None])
    artists.extend([line for line in risk_laser_lines if line is not None])
    artists.extend([cone for cone in risk_cones if cone is not None])
    
    # 添加参考轨迹点
    artists.extend([marker for marker in ref_point_markers if marker is not None])
    
    # 添加风险发布者飞机轨迹线
    for line in risk_reporter_lines.values():
        if line is not None:
            artists.append(line)
    
    if risk_distance_text is not None:
        artists.append(risk_distance_text)
            
    return artists

# 图形关闭事件处理
def on_close(event):
    global animation_running
    animation_running = False
    print("关闭图形，释放资源...")

fig.canvas.mpl_connect('close_event', on_close)

# 连接所有事件处理器
fig.canvas.mpl_connect('key_press_event', on_key_press)

# 这里先移除旧的提交处理器，仅保留按钮处理器，避免重复调用
# text_box.on_submit(submit_step)
# trail_text_box.on_submit(submit_trail_length)

btn_set.on_clicked(set_step)
btn_trail_set.on_clicked(set_trail_length)
frame_slider.on_changed(slider_update)
btn_toggle.on_clicked(toggle_play)
btn_forward.on_clicked(forward_frame)
btn_backward.on_clicked(backward_frame)
view_button.on_clicked(toggle_view)
heading_check.on_clicked(update_heading_display)
nextpoint_check.on_clicked(update_nextpoint_display)
risk_check.on_clicked(update_risk_display)
ref_check.on_clicked(update_ref_display)

# 初始化视图
if view_mode == '3d':
    ax.view_init(elev=30, azim=-60)
else:
    ax.view_init(elev=90, azim=-90)

print("正在创建动画...")
ani = FuncAnimation(fig, animate, init_func=init, blit=False, interval=100, cache_frame_data=False)

# 确保初始帧正确显示
update(0)

# 创建图例元素
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=8, label='Current Position'),
    Line2D([0], [0], marker='*', color='w', markerfacecolor='green', markersize=8, label='Target'),
    Line2D([0], [0], linestyle='--', color='green', label='Arrival Area'),
    Line2D([0], [0], marker='>', color='w', markerfacecolor='blue', markersize=8, label='Heading'),
    Line2D([0], [0], marker='x', color='blue', linestyle='none', markersize=8, label='Next Point'),
    Line2D([0], [0], marker='.', color='red', linestyle='none', markersize=10, label='Risk Point'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='purple', markersize=8, label='Risk Reporter'),
    Line2D([0], [0], marker='.', color='darkred', linestyle='none', markersize=8, label='Risk Area Ground'),
    Line2D([0], [0], linestyle=':', color='cyan', linewidth=2, label='Laser Line'),
    Line2D([0], [0], marker='^', color='w', markerfacecolor='lightblue', markersize=8, label='Risk Cone'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=6, label='Ref Point (Host)'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=6, label='Ref Point (Risk AC)'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=6, label='Ref Point (Risk Area)')
]

# 获取平台图例句柄和标签
platform_handles, platform_labels = ax.get_legend_handles_labels()

# 组合所有图例元素
all_handles = platform_handles + legend_elements
all_labels = platform_labels + [element.get_label() for element in legend_elements]

# 将图例位置调整到3D视图右上角
legend = ax.legend(all_handles, all_labels, loc='upper right', 
                  fontsize=8,
                  ncol=2,  # 使用2列显示，适应3D视图的宽度
                  framealpha=0.7)

# 注：放大视图控制UI已在前面添加

# 连接放大视图控制回调
zoom_range_box.on_submit(zoom_range_submit)
btn_zoom_set.on_clicked(zoom_range_set)

plt.tight_layout(rect=[0, 0.05, 1, 1])
print("准备完成，开始显示...")

# 保存当前UI布局截图用于调试
plt.savefig('ui_layout_debug.png', dpi=100)
print("已保存UI调试图像: ui_layout_debug.png")

plt.show()

# 清理资源
print("清理资源...")
del df
gc.collect()
print("程序结束")
