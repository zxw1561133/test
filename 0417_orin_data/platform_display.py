import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from matplotlib.widgets import Slider, Button, TextBox, CheckButtons
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import gc
import time
import warnings
import os
import math

# 忽略Matplotlib的警告
warnings.filterwarnings("ignore", category=UserWarning)

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

# 获取所有唯一的平台ID
platform_ids = df['platformId'].unique()

# 颜色方案
colors = plt.cm.tab10(np.linspace(0, 1, len(platform_ids)))
color_dict = {pid: colors[i] for i, pid in enumerate(platform_ids)}

# 到达区域半径（米）
TARGET_RADIUS = 1200

# 创建图形和3D轴
fig = plt.figure(figsize=(12, 10), dpi=100)
ax = fig.add_subplot(111, projection='3d')
ax.set_xlabel('East (m)', fontsize=12)
ax.set_ylabel('North (m)', fontsize=12)
ax.set_zlabel('Altitude (m)', fontsize=12)
ax.set_title('Platform Trajectories - 3D View with Altitude', fontsize=16)

# 设置坐标轴范围
x_min, x_max = df['x'].min(), df['x'].max()  # 北向范围
y_min, y_max = df['y'].min(), df['y'].max()  # 东向范围
margin = 0.1

# 设置坐标轴范围
ax.set_ylim(x_min - margin*(x_max - x_min), x_max + margin*(x_max - x_min))  # Y轴设置为北向
ax.set_xlim(y_min - margin*(y_max - y_min), y_max + margin*(y_max - y_min))  # X轴设置为东向
ax.set_zlim(Z_DISPLAY_MIN, Z_DISPLAY_MAX)  # Z轴设置为固定范围

# 添加参考平面 - 最低高度平面
x_ground = np.linspace(y_min - margin*(y_max - y_min), y_max + margin*(y_max - y_min), 10)
y_ground = np.linspace(x_min - margin*(x_max - x_min), x_max + margin*(x_max - x_min), 10)
X_ground, Y_ground = np.meshgrid(x_ground, y_ground)
Z_min = np.ones(X_ground.shape) * Z_DISPLAY_MIN
ax.plot_surface(X_ground, Y_ground, Z_min, alpha=0.2, color='lightgray')

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
ax.legend(loc='upper right', fontsize=10)

# 添加坐标系说明
ax.text2D(0.98, 0.02, 'NED Coordinate System with Altitude', transform=ax.transAxes, 
        horizontalalignment='right', fontsize=10, bbox=dict(facecolor='white', alpha=0.7))

# 添加控件
# 滑动条
ax_slider = plt.axes([0.15, 0.01, 0.7, 0.03])
frame_slider = Slider(ax_slider, 'Frame', 0, len(unique_times)-1, valinit=0, valstep=1)

# 按钮
btn_color = 'lightblue'
hover_color = 'skyblue'
ax_backward = plt.axes([0.15, 0.07, 0.1, 0.03])
btn_backward = Button(ax_backward, 'Backward', color=btn_color, hovercolor=hover_color)
ax_toggle = plt.axes([0.27, 0.07, 0.1, 0.03])
btn_toggle = Button(ax_toggle, 'Play', color=btn_color, hovercolor=hover_color)
ax_forward = plt.axes([0.39, 0.07, 0.1, 0.03])
btn_forward = Button(ax_forward, 'Forward', color=btn_color, hovercolor=hover_color)

# 步长输入框与"Set"按钮
ax_textbox = plt.axes([0.60, 0.07, 0.1, 0.03])
text_box = TextBox(ax_textbox, 'Step:', initial=str(frame_step))
ax_set = plt.axes([0.72, 0.07, 0.1, 0.03])
btn_set = Button(ax_set, 'Set', color=btn_color, hovercolor=hover_color)

# 轨迹长度输入框与按钮
ax_trail_textbox = plt.axes([0.60, 0.14, 0.1, 0.03])
trail_text_box = TextBox(ax_trail_textbox, 'Trail:', initial=str(trail_length))
ax_trail_set = plt.axes([0.72, 0.14, 0.1, 0.03])
btn_trail_set = Button(ax_trail_set, 'Set', color=btn_color, hovercolor=hover_color)

# 视图切换按钮
ax_view = plt.axes([0.60, 0.11, 0.22, 0.03])
view_button = Button(ax_view, 'Switch View', color=btn_color, hovercolor=hover_color)

# 航向角显示开关
ax_heading = plt.axes([0.60, 0.18, 0.22, 0.03])
heading_check = CheckButtons(ax_heading, ['Show Heading'], [show_heading])

# nextPoint显示开关
ax_nextpoint = plt.axes([0.60, 0.22, 0.22, 0.03])
nextpoint_check = CheckButtons(ax_nextpoint, ['Show NextPoint'], [show_nextpoint])

# 添加风险信息显示开关
ax_risk = plt.axes([0.60, 0.26, 0.22, 0.03])
risk_check = CheckButtons(ax_risk, ['Show Risk Points & Circles'], [show_risk])

# 添加参考轨迹点显示开关
ax_ref = plt.axes([0.60, 0.30, 0.22, 0.03])
ref_check = CheckButtons(ax_ref, ['Show Reference Points'], [show_ref_points])

# 控件背景，调整高度
params_rect = Rectangle((0.56, 0.05), 0.29, 0.35, transform=fig.transFigure,
                        facecolor="whitesmoke", alpha=0.3, edgecolor="black", lw=1)
fig.patches.append(params_rect)
fig.text(0.57, 0.37, "Params Setting", transform=fig.transFigure,
         fontsize=10, fontweight="bold", color="black")

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

# 更新函数
def update(frame_idx):
    global cur_frame, view_mode, frame_update_flag, target_circles, heading_arrows, nextpoint_arrows
    global risk_aircraft_markers, risk_circle_objects, risk_point_markers, risk_reporter_markers 
    global risk_reporter_texts, risk_reporter_lines, risk_reporter_history, blink_status, blink_counter
    global risk_distance_text, risk_ground_markers, risk_laser_lines, risk_cones, ref_point_markers
    
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
                    # 在图形右侧创建一个文本框
                    risk_distance_text = fig.text(0.87, 0.6, risk_distance_text_content,
                                                 transform=fig.transFigure,
                                                 fontsize=9, verticalalignment='top',
                                                 bbox=dict(facecolor='white', alpha=0.7, 
                                                          edgecolor='black', boxstyle='round'))
        
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

plt.tight_layout(rect=[0, 0.05, 1, 1])
print("准备完成，开始显示...")
plt.show()

# 清理资源
print("清理资源...")
del df
gc.collect()
print("程序结束")

# 添加图例说明
fig.text(0.02, 0.02, "○: Current Position  *: Target  --: Arrival Area  →: Heading  x: Next Point  •: Risk Info  ○: Risk Reporter  •: Risk Area Ground  ⠇: Cyan Laser  ▽: Risk Cone  ○: Ref Points (Green: Current, Blue: Risk AC, Orange: Risk Area)", 
         transform=fig.transFigure, fontsize=8, bbox=dict(facecolor='white', alpha=0.7))

# 添加风险距离信息显示区域背景
risk_info_rect = Rectangle((0.84, 0.35), 0.15, 0.30, transform=fig.transFigure,
                          facecolor="whitesmoke", alpha=0.3, edgecolor="black", lw=1)
fig.patches.append(risk_info_rect)
fig.text(0.85, 0.62, "Risk Distance Info", transform=fig.transFigure,
         fontsize=10, fontweight="bold", color="black")
