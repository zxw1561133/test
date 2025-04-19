import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D

# 读取CSV数据（每行包含：
# time, x,y,z,psi, target_x, target_y, target_z, target_psi, nextPoint_x, nextPoint_y, nextPoint_z, nextPoint_psi）
df = pd.read_csv("/home/zxw/zxw/桌面/V1.1/C++/cursor_plot/plugin_data/motion_data/engage_data/separated_platforms/platform2_data.csv")

#df = pd.read_csv("/home/dell/code/test25_盘旋圆相交_测试3_全程速度模式/CA_get_next_position_data.txt")

# 飞机A对调x和y坐标
planA_x = df['y']
planA_y = df['x']
planA_z = df['z']
psi = df['psi']

# 目标圆心，绘图同样对调x和y数据
target_circle_x = df['target_y']
target_circle_y = df['target_x']
target_circle_z = df['target_z']

# nextPoint,同样对调数据
nextPoint_x = df['nextPoint_y']
nextPoint_y = df['nextPoint_x']
nextPoint_z = df['nextPoint_z']
nextPoint_psi = df['nextPoint_psi']

# ref数据
ref_config  = {
    i:{
        'x':f'ref{i}_y',
        'y':f'ref{i}_x',
        'z':f'ref{i}_z',
        'psi':f'ref{i}_psi'
    }for i in range(0,10)
}

selected_refs = [0,1,2,3,4,5,6,7,8,9]
ref_x_data = df[[ref_config[i]['x'] for i in selected_refs]].values
ref_y_data = df[[ref_config[i]['y'] for i in selected_refs]].values


time_vals = df['time']

# 可配置变量
multiplier = 4         # 倍数
uav_speed = 60          # 单位：m/s
uav_circle_radius = multiplier * uav_speed  # 半径
target_circle_radius = 1200 # 单位: m
refresh_interval = 40   # 帧数

# 箭头长度（单位：m）
arrow_length_A = 800
arrow_length_next = 800

# 全局变量，保存固定圆心,箭头
fixed_circle_center  = None
quiver_A = None
quiver_next = None
# 创建图
fig, ax = plt.subplots(figsize=(8,8))
ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")
ax.set_title("trail")

# 绘图范围
ax.set_aspect('equal')
ax.set_xlim(df['y'].min()-2000,df['y'].max()+2000)
ax.set_ylim(df['x'].min()-2000,df['x'].max()+2000)

#ax.set_xlim(-21000,-4000)
#ax.set_ylim(-5000,20000)

# 创建飞机A的轨迹线和当前点的标记
planA_trail, = ax.plot([],[],'b-',lw=2,label="planA trail")
planA_marker, = ax.plot([],[],'bo',markersize=6,label='planA')

# 创建动态园更随飞机A
planA_circle, = ax.plot([],[],'r-',lw=2,label="planA circle")

# 创建以目标点的圆
target_circle_line, = ax.plot([],[],'g--',lw=2,label="target circle")

# 创建 nextPoint标记
nextPoint_trail_line, = ax.plot([],[],'ko',lw=2,markersize=4,label="NextPoint trail")
nextPoint_marker, = ax.plot([],[],'ko',markersize=4,label="NextPoint")

# 创建 ref
scatters = [ax.scatter([],[],label=f'Ref {i}') for i in selected_refs]


def init():
    planA_trail.set_data([],[])
    planA_marker.set_data([],[])
    planA_circle.set_data([],[])
    target_circle_line.set_data([],[])
    nextPoint_trail_line.set_data([],[])
    nextPoint_marker.set_data([],[])
    ax.legend()
    return planA_trail,planA_marker,planA_circle,target_circle_line,nextPoint_marker,(*scatters)
# scatters[0],scatters[1],scatters[2],scatters[3],scatters[4],scatters[5]
def update(frame):
    global fixed_circle_center,quiver_A,quiver_next
    # 保存当前帧数
    idx = frame

    # 飞机A的当前位置
    plan_current_x = planA_x.iloc[idx]
    plan_current_y = planA_y.iloc[idx]
    # 更新轨迹
    planA_trail.set_data(planA_x.iloc[:idx+1],planA_y.iloc[:idx+1])
    # 更新飞机的当前点标记
    planA_marker.set_data(plan_current_x,plan_current_y)

    # 绘制飞机动态圆
    th_plan = np.linspace(0, 2*np.pi,100)
    plan_circle_dyn_x = plan_current_x + uav_circle_radius * np.cos(th_plan)
    plan_circle_dyn_y = plan_current_y + uav_circle_radius * np.sin(th_plan)
    planA_circle.set_data(plan_circle_dyn_x,plan_circle_dyn_y)

    # 绘制目标点圆
    cur_target_x = target_circle_x.iloc[idx]
    cur_target_y = target_circle_y.iloc[idx]
    th_target = np.linspace(0, 2*np.pi,100)

    target_fix_x = cur_target_x + target_circle_radius * np.cos(th_target)
    target_fix_y = cur_target_y + target_circle_radius * np.sin(th_target)
    target_circle_line.set_data(target_fix_x,target_fix_y)
    if fixed_circle_center is not None:
        fixed_circle_center.remove()
    fixed_circle_center = ax.plot([cur_target_x],[cur_target_y],'go',markersize=6)[0]

    # 更新 nextPoint点
    np_x = nextPoint_x.iloc[idx]
    np_y = nextPoint_y.iloc[idx]
    nextPoint_trail_line.set_data(nextPoint_x.iloc[:idx+1],nextPoint_y.iloc[:idx+1])
    nextPoint_marker.set_data(np_x,np_y)

    # 更新飞机A的航向箭头
    angle_A = np.pi/2 - psi.iloc[idx]
    u_A = arrow_length_A * np.cos(angle_A)
    v_A = arrow_length_A * np.sin(angle_A)
    if quiver_A is not None:
        quiver_A.remove()
    quiver_A = ax.quiver(plan_current_x,plan_current_y,u_A,v_A,angles='xy',scale_units='xy',scale=0.5,color='orange')

    # 更新nextPoint的航向箭头
    angle_next = np.pi/2 - nextPoint_psi.iloc[idx]
    u_next = arrow_length_next * np.cos(angle_next)
    v_next = arrow_length_next * np.sin(angle_next)
    if quiver_next is not None:
        quiver_next.remove()
    quiver_next = ax.quiver(np_x,np_y,u_next,v_next,angles='xy',scale_units='xy',scale=0.5,color='magenta')

    current_row = df.iloc[idx]

    for idx,ref_id in enumerate(selected_refs):
        x = current_row[ref_config[ref_id]['x']]
        y = current_row[ref_config[ref_id]['y']]
        scatters[idx].set_offsets([x,y])

    for idx in range(len(selected_refs)):
        scatters[idx].set_offsets([[ref_x_data[frame,idx],ref_y_data[frame,idx]]])

    return planA_trail,planA_marker,planA_circle,target_circle_line,nextPoint_marker,fixed_circle_center,quiver_A,quiver_next,(*scatters)

ani = animation.FuncAnimation(fig, update,frames=range(0,len(time_vals),refresh_interval),init_func=init,interval=100,blit=True)

plt.show()
