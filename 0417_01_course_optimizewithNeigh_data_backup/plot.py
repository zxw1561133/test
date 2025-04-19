import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Slider, Button, TextBox  # 导入所需控件
from matplotlib.patches import Rectangle

# =============================================================================
# 1. 常量与参数配置
# =============================================================================
# 经纬度转换因子（单位：度/m）
factorLat = 1.0/111000.0
factorLon = 1.0/(111000.0 * 0.8660254) 

# 全局变量，记录当前帧和播放状态
view_mode = 'top'
cur_frame = 0
is_paused = False
frame_step = 50  # 播放时每次跳过的帧数（默认1）

cone_half_angle = np.deg2rad(15)
zoom_target = 'A'  # 默认2D放大目标 UAV
risk_radius_A = 900 # 单位：m
risk_radius_B = 900 # 单位：m
risk_radius_B1 = 900 # 单位：m
zoom_risk = 3000    # 单位：m
waypoint_circle_radius = 1200   # 单位：m

# 用于动态绘制的全局变量
cone_surf = None
risk_circle = None
risk_point0 = None
risk_point2 = None
line_CT = None
line_CT_glow = None
risk_circle_A = None
risk_circle_B = None
risk_circle_B1 = None
waypoint_circle = None
# =============================================================================
# 2. 数据读取与预处理
# =============================================================================
# 请确保 motion_data.csv 文件存在且格式正确
df = pd.read_csv("test29_motion_data.csv")

colors = {'A': 'blue', 'B': 'green', 'B1': 'orange', 'C': 'red', 'T': 'magenta'}
entity_names = ['A', 'B', 'B1', 'C', 'T']

# 获取数据全局的最小和最大GPS值
all_lat =pd.concat([df[f'{ent}_lat'] for ent in entity_names])
all_lon =pd.concat([df[f'{ent}_lon'] for ent in entity_names])
# 计算边距比例:25%
lat_margin = (all_lat.max() - all_lat.min())*0.25
lon_margin = (all_lon.max() - all_lon.min())*0.25
# 根据转换关系确定背景区域的经纬度范围
lat_min = all_lat.min() - lat_margin
lat_max = all_lat.max() + lat_margin
lon_min = all_lon.min() - lon_margin
lon_max = all_lon.max() + lon_margin

# 根据转换因子计算实际的长度（单位：m）
physical_lat_length = (lat_max - lat_min) * 111000.0
physical_lon_length = (lon_max - lon_min) * (111000.0 * 0.8660254) 

# 将短轴扩展为长轴
if physical_lon_length > physical_lat_length:
    # 按照经度的物理距离扩大纬度范围
    desired_lat_rang = physical_lon_length / 111000.0
    center = (lat_min + lat_max) / 2
    lat_min = center - desired_lat_rang / 2
    lat_max = center + desired_lat_rang / 2
else:
    # 按照纬度的物理距离扩大经度范围
    desired_lon_rang = physical_lat_length / (111000.0 * 0.8660254) 
    center = (lon_min + lon_max) / 2
    lon_min = center - desired_lon_rang / 2
    lon_max = center + desired_lon_rang / 2


# 区域分界线（模拟4000m）
lat_div = (lat_min +lat_max) / 2.0
lon_div = (lon_min +lon_max) / 2.0

entity_data = {}
for ent in entity_names:
    entity_data[ent] = {
        'lat': df[f'{ent}_lat'],
        'lon': df[f'{ent}_lon'],
        'alt': df[f'{ent}_alt'],
        'color': colors[ent]
    }
# 读取风险点
risk_type = df['risk_type']
pos1 = df['pos1']
pos2 = df['pos2']
pos3 = df['pos3']

# 读取路径点
waypoint_ahead_lat = df['waypoint_ahead0']
waypoint_ahead_lon = df['waypoint_ahead1']
waypoint_ahead_alt = df['waypoint_ahead2']

# =============================================================================
# 3. 图形与画布初始化（使用 GridSpec 进行优化布局）
# =============================================================================
fig = plt.figure(figsize=(16, 8), dpi=100)
gs = GridSpec(1, 2, width_ratios=[2, 1], wspace=0.25)

# 左侧：3D视图
ax3d = fig.add_subplot(gs[0], projection='3d')
ax3d.set_xlim(lon_min, lon_max)
ax3d.set_ylim(lat_min, lat_max)
ax3d.set_zlim(1695, 3700)
ax3d.set_xlabel("lon (°)")
ax3d.set_ylabel("lat (°)")
ax3d.set_zlabel("alt (m)")
ax3d.set_title("3D")


# 绘制地面边界（z=?）及分界线
ground_lon = [lon_min, lon_max, lon_max, lon_min, lon_min]
ground_lat = [lat_min, lat_min, lat_max, lat_max, lat_min]
ground_alt = [1695,1695,1695,1695,1695]
ax3d.plot(ground_lon, ground_lat, ground_alt, 'k-', linewidth=2)
ax3d.plot([lon_min, lon_max], [lat_div, lat_div], [1695, 1695], 'k--', linewidth=1)
ax3d.plot([lon_div, lon_div], [lat_min, lat_max], [1695, 1695], 'k--', linewidth=1)

markers = {}
lines = {}
for ent in entity_names:
    markers[ent], = ax3d.plot([], [], [], 'o', color=entity_data[ent]['color'], label=ent)
    lines[ent], = ax3d.plot([], [], [], '-', color=entity_data[ent]['color'])
ax3d.legend()

# 右侧：2D局部放大视图
ax2d = fig.add_subplot(gs[1])
ax2d.set_title("2D")
ax2d.set_xlabel("lon (°)")
ax2d.set_ylabel("lat (°)")
ax2d.set_aspect('equal', adjustable='box')

# =============================================================================
# 4. 动画函数定义
# =============================================================================
def init_func():
    global view_mode
    if view_mode == 'top':
        ax3d.view_init(elev=90, azim=-90)
    for ent in entity_names:
        markers[ent].set_data([], [])
        markers[ent].set_3d_properties([])
        lines[ent].set_data([], [])
        lines[ent].set_3d_properties([])
    return list(markers.values()) + list(lines.values())

def update(frame):
    global view_mode, cur_frame, cone_surf, risk_circle, risk_point0, risk_point2, line_CT, line_CT_glow, risk_circle_A, risk_circle_B, risk_circle_B1, zoom_target,waypoint_circle
    cur_frame = frame
    # 同步滑动条
    frame_slider.eventson = False
    frame_slider.set_val(frame)
    frame_slider.eventson = True

    # 3D视图更新
    for ent in entity_names:
        markers[ent].set_data([entity_data[ent]['lon'].iloc[frame]], [entity_data[ent]['lat'].iloc[frame]])
        markers[ent].set_3d_properties([entity_data[ent]['alt'].iloc[frame]])
        lines[ent].set_data(entity_data[ent]['lon'].iloc[:frame+1].values,
                            entity_data[ent]['lat'].iloc[:frame+1].values)
        lines[ent].set_3d_properties(entity_data[ent]['alt'].iloc[:frame+1].values)

    # 绘制T为顶点的圆锥体
    T_lon_val = entity_data['T']['lon'].iloc[frame]
    T_lat_val = entity_data['T']['lat'].iloc[frame]
    T_alt_val = entity_data['T']['alt'].iloc[frame]
    B_alt_val = entity_data['B']['alt'].iloc[frame]
    height_diff = B_alt_val - T_alt_val
    cone_base_radius_m = height_diff * np.tan(cone_half_angle)
    cone_radius_lon = cone_base_radius_m * factorLon
    cone_radius_lat = cone_base_radius_m * factorLat
    f = np.linspace(0, 1, 20)
    theta_vals = np.linspace(0, 2*np.pi, 40)
    f_grid, theta_grid = np.meshgrid(f, theta_vals)
    cone_x = T_lon_val + f_grid * cone_radius_lon * np.cos(theta_grid)
    cone_y = T_lat_val + f_grid * cone_radius_lat * np.sin(theta_grid)
    cone_z = T_alt_val + f_grid * height_diff
    if cone_surf is not None:
        cone_surf.remove()
    cone_surf = ax3d.plot_surface(cone_x, cone_y, cone_z, color='lightblue', alpha=0.5, edgecolor='none')

    # 绘制A飞机的路径点圆
    waypoint_circle_lon = waypoint_circle_radius * factorLon
    waypoint_circle_lat = waypoint_circle_radius * factorLat
    th_A = np.linspace(0, 2*np.pi,40)
    waypoint_circle_lon = waypoint_ahead_lon.iloc[frame] + waypoint_circle_lon * np.cos(th_A)
    waypoint_circle_lat = waypoint_ahead_lat.iloc[frame] + waypoint_circle_lat * np.sin(th_A)
    waypoint_circle_alt = np.full_like(waypoint_circle_lon, waypoint_ahead_alt.iloc[frame])
    if waypoint_circle is not None:
        waypoint_circle.remove()
    waypoint_circle = ax3d.plot(waypoint_circle_lon,waypoint_circle_lat,waypoint_circle_alt,color='darkgreen',linewidth=2,alpha=0.5,linestyle='--')[0]
    
    # 绘制3D风险区域与风险点
    if risk_type.iloc[frame] == 1:
        center_lat = pos1.iloc[frame]
        center_lon = pos2.iloc[frame]
        risk_radius_lon_val = pos3.iloc[frame] * factorLon
        risk_radius_lat_val = pos3.iloc[frame] * factorLat
        th = np.linspace(0, 2*np.pi, 40)
        circle_lon = center_lon + risk_radius_lon_val * np.cos(th)
        circle_lat = center_lat + risk_radius_lat_val * np.sin(th)
        circle_alt = np.full_like(circle_lon, B_alt_val)
        if risk_circle is not None:
            risk_circle.remove()
        risk_circle = ax3d.plot(circle_lon, circle_lat, circle_alt,
                                color='orange', linewidth=2, alpha=0.7, linestyle='--')[0]
    else:
        if risk_circle is not None:
            risk_circle.remove()
            risk_circle = None

    if risk_type.iloc[frame] == 0:
        if risk_point0 is not None:
            risk_point0.remove()
        risk_point0 = ax3d.plot([pos2.iloc[frame]], [pos1.iloc[frame]], [pos3.iloc[frame]],
                                marker='o', color='purple', markersize=8)[0]
    else:
        if risk_point0 is not None:
            risk_point0.remove()
            risk_point0 = None

    if risk_type.iloc[frame] == 2:
        if risk_point2 is not None:
            risk_point2.remove()
        risk_point2 = ax3d.plot([pos2.iloc[frame]], [pos1.iloc[frame]], [pos3.iloc[frame]],
                                marker='o', color='cyan', markersize=8)[0]
    else:
        if risk_point2 is not None:
            risk_point2.remove()
            risk_point2 = None

    if line_CT_glow is not None:
        line_CT_glow.remove()
    line_CT_glow = ax3d.plot([entity_data['C']['lon'].iloc[frame], entity_data['T']['lon'].iloc[frame]],
                             [entity_data['C']['lat'].iloc[frame], entity_data['T']['lat'].iloc[frame]],
                             [entity_data['C']['alt'].iloc[frame], entity_data['T']['alt'].iloc[frame]],
                             color='cyan', linewidth=12, linestyle='-', alpha=0.03)[0]
    if line_CT is not None:
        line_CT.remove()
    line_CT = ax3d.plot([entity_data['C']['lon'].iloc[frame], entity_data['T']['lon'].iloc[frame]],
                        [entity_data['C']['lat'].iloc[frame], entity_data['T']['lat'].iloc[frame]],
                        [entity_data['C']['alt'].iloc[frame], entity_data['T']['alt'].iloc[frame]],
                        color='cyan', linewidth=4, linestyle='-', alpha=0.4)[0]


    th_A = np.linspace(0, 2*np.pi, 40)
    circleA_lon = entity_data['A']['lon'].iloc[frame] + (risk_radius_A * factorLon) * np.cos(th_A)
    circleA_lat = entity_data['A']['lat'].iloc[frame] + (risk_radius_A * factorLat) * np.sin(th_A)
    if risk_circle_A is not None:
        risk_circle_A.remove()
    risk_circle_A = ax3d.plot(circleA_lon, circleA_lat,
                              np.full_like(circleA_lon, entity_data['A']['alt'].iloc[frame]),
                              color='darkgreen', linewidth=2, alpha=0.5, linestyle='--')[0]
    
    th_B = np.linspace(0, 2*np.pi, 40)
    circleB_lon = entity_data['B']['lon'].iloc[frame] + (risk_radius_B * factorLon) * np.cos(th_B)
    circleB_lat = entity_data['B']['lat'].iloc[frame] + (risk_radius_B * factorLat) * np.sin(th_B)
    if risk_circle_B is not None:
        risk_circle_B.remove()
    risk_circle_B = ax3d.plot(circleB_lon, circleB_lat,
                              np.full_like(circleB_lon, entity_data['B']['alt'].iloc[frame]),
                              color='darkblue', linewidth=2, alpha=0.5, linestyle='--')[0]

    th_B1 = np.linspace(0, 2*np.pi, 40)
    circleB1_lon = entity_data['B1']['lon'].iloc[frame] + (risk_radius_B1 * factorLon) * np.cos(th_B1)
    circleB1_lat = entity_data['B1']['lat'].iloc[frame] + (risk_radius_B1 * factorLat) * np.sin(th_B1)
    if risk_circle_B1 is not None:
        risk_circle_B1.remove()
    risk_circle_B1 = ax3d.plot(circleB1_lon, circleB1_lat,
                              np.full_like(circleB1_lon, entity_data['B1']['alt'].iloc[frame]),
                              color='darkred', linewidth=2, alpha=0.5, linestyle='--')[0]

    # 2D局部放大视图更新
    ax2d.clear()
    for name, data in entity_data.items():
        ax2d.plot(data['lon'].iloc[:frame+1].values, data['lat'].iloc[:frame+1].values,
                  color=data['color'], lw=1, label=name)
        ax2d.scatter(data['lon'].iloc[frame], data['lat'].iloc[frame],
                     color=data['color'], s=30, zorder=3)

    # 绘制2d风险区域
    if risk_type.iloc[frame] == 1:
        center_lat = pos1.iloc[frame]
        center_lon = pos2.iloc[frame]
        risk_radius_lon_val = pos3.iloc[frame] * factorLon
        risk_radius_lat_val = pos3.iloc[frame] * factorLat
        th = np.linspace(0, 2*np.pi, 40)
        circle_lon_2d = center_lon + risk_radius_lon_val * np.cos(th)
        circle_lat_2d = center_lat + risk_radius_lat_val * np.sin(th)

        ax2d.plot(circle_lon_2d, circle_lat_2d, color='orange', linewidth=2, alpha=0.7, linestyle='--')

    if risk_type.iloc[frame] == 0:
        ax2d.plot([pos2.iloc[frame]], [pos1.iloc[frame]], [pos3.iloc[frame]], marker='o', color='purple', markersize=8)[0]
    if risk_type.iloc[frame] == 2:
        ax2d.plot([pos2.iloc[frame]], [pos1.iloc[frame]], [pos3.iloc[frame]], marker='o', color='cyan', markersize=8)[0]

    # 绘制A飞机的2d路径点
    waypoint_circle_lon = waypoint_circle_radius * factorLon
    waypoint_circle_lat = waypoint_circle_radius * factorLat
    th_A = np.linspace(0, 2*np.pi,40)
    waypoint_circle_lon = waypoint_ahead_lon.iloc[frame] + waypoint_circle_lon * np.cos(th_A)
    waypoint_circle_lat = waypoint_ahead_lat.iloc[frame] + waypoint_circle_lat * np.sin(th_A)
    waypoint_circle_alt = np.full_like(waypoint_circle_lon, waypoint_ahead_alt.iloc[frame])
    ax2d.plot(waypoint_circle_lon,waypoint_circle_lat,waypoint_circle_alt,color='darkgreen',linewidth=2,alpha=0.5,linestyle='--')[0]    

    center_lon_val = entity_data.get(zoom_target, entity_data['A'])['lon'].iloc[frame]
    center_lat_val = entity_data.get(zoom_target, entity_data['A'])['lat'].iloc[frame]

    margin_lon = zoom_risk * factorLon
    margin_lat = zoom_risk * factorLat

    ax2d.set_xlim(center_lon_val - margin_lon, center_lon_val + margin_lon)
    ax2d.set_ylim(center_lat_val - margin_lat, center_lat_val + margin_lat)
    
    ax2d.set_xlabel("lon (°)")
    ax2d.set_ylabel("lat (°)")
    ax2d.set_title(f"Center: {zoom_target} UAV")
    ax2d.legend(fontsize=8)

    return (list(markers.values()) + list(lines.values()) +
            [cone_surf, risk_circle, risk_point0, risk_point2, line_CT, line_CT_glow, risk_circle_A, risk_circle_B, risk_circle_B1, waypoint_circle])

# =============================================================================
# 5. 添加滑动条、按钮和播放步长TextBox（保持现有位置不动）
# =============================================================================
ax_slider = plt.axes([0.15, 0.01, 0.7, 0.03])
frame_slider = Slider(ax_slider, 'Frame', 0, len(df)-1, valinit=0, valstep=1)

btn_color = 'lightblue'
hover_color = 'skyblue'
ax_backward = plt.axes([0.15, 0.07, 0.1, 0.03])
btn_backward = Button(ax_backward, 'Backward', color=btn_color, hovercolor=hover_color)
ax_toggle = plt.axes([0.27, 0.07, 0.1, 0.03])
btn_toggle = Button(ax_toggle, 'Play', color=btn_color, hovercolor=hover_color)
ax_forward = plt.axes([0.39, 0.07, 0.1, 0.03])
btn_forward = Button(ax_forward, 'Forward', color=btn_color, hovercolor=hover_color)

# 播放步长输入框与"Set"按钮位置
ax_textbox = plt.axes([0.60, 0.07, 0.1, 0.03])
text_box = TextBox(ax_textbox, 'Step:', initial="50")
ax_set = plt.axes([0.72, 0.07, 0.1, 0.03])
btn_set = Button(ax_set, 'Set', color=btn_color, hovercolor=hover_color)
# 添加视角按钮
ax_view = plt.axes([0.72, 0.11, 0.1, 0.03])
view_button = Button(ax_view, "View: Top")

ax_zoom_target = plt.axes([0.60, 0.11, 0.1, 0.03])
zoom_target_box = TextBox(ax_zoom_target, 'Zoom:', initial="A")

# 添加一个透明的浅色矩形框作为背景，覆盖参数设置区域，不遮挡控件，设置透明度
params_rect = Rectangle((0.56, 0.05), 0.29, 0.14, transform=fig.transFigure,
                          facecolor="whitesmoke", alpha=0.3, edgecolor="black", lw=1)
fig.patches.append(params_rect)
# 在矩形框左上角添加文字标识
fig.text(0.57, 0.16, "Params Setting", transform=fig.transFigure,
         fontsize=10, fontweight="bold", color="black")
def submit_step(text):
    pass

text_box.on_submit(submit_step)

def set_step(event):
    global frame_step
    try:
        val = int(text_box.text)
        if val < 1:
            val = 1
    except:
        val = 1
    frame_step = val
    print(f"设置每次跳过帧数: {frame_step}")

btn_set.on_clicked(set_step)

def slider_update(val):
    global is_paused
    frame = int(val)
    update(frame)
    fig.canvas.draw_idle()
    ani.event_source.stop()
    is_paused = True
    btn_toggle.label.set_text("Play")
frame_slider.on_changed(slider_update)

def toggle_play(event):
    global is_paused
    if is_paused:
        ani.event_source.start()
        is_paused = False
        btn_toggle.label.set_text("Pause")
    else:
        ani.event_source.stop()
        is_paused = True
        btn_toggle.label.set_text("Play")
    fig.canvas.draw_idle()
btn_toggle.on_clicked(toggle_play)

def forward_frame(event):
    global is_paused
    current = int(frame_slider.val)
    new_frame = min(current + frame_step, len(df) - 1)
    frame_slider.set_val(new_frame)
    update(new_frame)
    fig.canvas.draw_idle()
    ani.event_source.stop()
    is_paused = True
    btn_toggle.label.set_text("Play")
btn_forward.on_clicked(forward_frame)

def backward_frame(event):
    global is_paused
    current = int(frame_slider.val)
    new_frame = max(current - frame_step, 0)
    frame_slider.set_val(new_frame)
    update(new_frame)
    fig.canvas.draw_idle()
    ani.event_source.stop()
    is_paused = True
    btn_toggle.label.set_text("Play")
btn_backward.on_clicked(backward_frame)

# 统一的参数更新仍由原有btn_set的回调来修改播放步长，若需要加入Zoom Target的更新，可在此处扩展回调逻辑
def update_parameters(event):
    global frame_step, zoom_target
    try:
        val = int(text_box.text)
        if val < 1:
            val = 1
    except:
        val = 1
    frame_step = val
    zoom_target = zoom_target_box.text.strip().upper()
    print(f"更新参数：帧步长 = {frame_step}，Zoom Target = {zoom_target}")
btn_set.on_clicked(update_parameters)

def toggle_view(event):
    global view_mode
    if view_mode == 'top':
        ax3d.view_init(elev=90, azim=-90) #设置为俯视图
        view_mode = '3d'
        view_button.label.set_text("View: 3D")
    else:
        ax3d.view_init(elev=30, azim=-60) #设置为3D视图
        view_mode = 'top'
        view_button.label.set_text("View: Top")
    plt.draw()
view_button.on_clicked(toggle_view)

# =============================================================================
# 7. 动画执行（自动播放，播放完毕后自动重播）
# =============================================================================
def animate(_):
    global cur_frame, frame_step, is_paused
    if not is_paused:
        next_frame = int(cur_frame + frame_step)
        if next_frame < len(df):
            update(next_frame)
        else:
            update(0)
    return (list(markers.values()) + list(lines.values()) +
            [cone_surf, risk_circle, risk_point0, risk_point2, line_CT, line_CT_glow, risk_circle_A, risk_circle_B, risk_circle_B1, waypoint_circle])

ani = animation.FuncAnimation(fig, animate, interval=100, blit=False)

# 移除 plt.tight_layout() 调用以避免警告
# plt.tight_layout()
plt.show()
