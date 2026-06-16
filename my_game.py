import pygame
import random
import time
import threading

# pythonosc：一个处理OSC协议（Open Sound Control）的第三方库
# OSC是一种网络通信协议，常用于脑机接口设备与电脑之间的数据传输
# dispatcher：负责把收到的OSC消息分发到对应的处理函数
# osc_server：提供OSC服务器功能，监听并接收来自脑电设备的信号
from pythonosc import dispatcher, osc_server

pygame.init()

# SCREEN_WIDTH：游戏窗口的宽度，单位是像素（px）
SCREEN_WIDTH = 900

# SCREEN_HEIGHT：游戏窗口的高度，单位是像素（px）
SCREEN_HEIGHT = 800

# pygame.display.set_mode() 创建一个窗口，返回一个 Surface 对象（可以理解为画布）
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# pygame.display.set_caption() 设置窗口标题栏显示的文字
pygame.display.set_caption('SJTU Run')


#颜色定义
WHITE = (255, 255, 255)       
BLACK = (0, 0, 0)             
RED = (255, 0, 0)             
GRAY = (100, 100, 100)        
GREEN = (0, 200, 0)            
BLUE = (0, 0, 255)             
SKY_BLUE = (135, 206, 235)     
GROUND_COLOR = (83, 83, 83)    
DARK_GREEN = (0, 150, 0)       


def load_image(path, size=None):
    """
    安全地加载一张图片文件，如果文件不存在则返回一个占位图形。
    即使图片文件丢失，游戏也不会崩溃。

    参数:
        path (str): 图片文件的路径
        size (tuple | None): 可选，缩放后的尺寸 (宽, 高)

    返回:
        pygame.Surface: 加载并处理后的图片对象
    """
    try:
        # pygame.image.load() 从文件加载图片
        # .convert_alpha() 转换图片格式以保留透明通道，同时优化渲染速度。不保留可能会有白色背景
        img = pygame.image.load(path).convert_alpha()

        # 如果指定了 size 参数，就缩放图片到指定大小
        if size:
            # pygame.transform.scale() 缩放图片到指定尺寸
            img = pygame.transform.scale(img, size)

        return img

    except FileNotFoundError:
        print(f"警告：未找到图像文件 {path}，使用默认图形替代")

        # 创建一个纯色方块作为占位替代
        # pygame.Surface() 创建一个新的空白画布
        # pygame.SRCALPHA 表示这个Surface支持透明通道（RGBA模式）
        # size if size else (40, 40) 意思是：如果传了size用size，否则默认(40, 40)
        surf = pygame.Surface(size if size else (40, 40), pygame.SRCALPHA)

        # surf.fill() 用指定颜色填充整个Surface
        surf.fill((100, 100, 100))  # 灰色填充

        return surf

#加载障碍物
obstacle_data = [
    # load_image("Pre.jpg", (40, 50)) 加载图片并缩放到 40×50 像素
    # "Pre" 是这个障碍物的显示名称（当玩家被该障碍物撞到时显示）
    (load_image("Pre.jpg", (40, 50)), "Pre"),
    (load_image("GPA.jpg", (35, 45)), "GPA"),
    (load_image("体测.jpg", (45, 55)), "体测"),
    (load_image("大作业.jpg", (40, 40)), "大作业"),
    (load_image("大物实验报告.jpg", (40, 40)), "大物实验报告"),
]

# 分数背景图片
img_score_bg = load_image("img_score.jpg", (150, 50))



# 游戏常量
# FPS = Frames Per Second（每秒帧数）
# 每秒刷新60次画面，越高越流畅但消耗更多计算资源
FPS = 60

# GROUND_Y：地面的Y坐标（地面顶部的Y位置）
GROUND_Y = 650

# PLAYER_X：玩家的固定X（水平）坐标
PLAYER_X = 200

# 玩家碰撞检测用的宽和高（像素）
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 50

# 跳跃最大高度（像素）
JUMP_HEIGHT = 200

# 一次跳跃的总时长（秒）
JUMP_DURATION = 0.8

#障碍物移动速度范围
OBSTACLE_MIN_SPEED = 4   
OBSTACLE_MAX_SPEED = 10   

# 障碍物宽度的随机范围
OBSTACLE_MIN_WIDTH = 30
OBSTACLE_MAX_WIDTH = 65

# 障碍物高度的随机范围
OBSTACLE_MIN_HEIGHT = 30
OBSTACLE_MAX_HEIGHT = 100

# 1.5~3.0 秒内随机生成一个新的障碍物
MIN_SPAWN_INTERVAL = 1.0
MAX_SPAWN_INTERVAL = 3.0

# 给玩家一点准备时间
INITIAL_SPAWN_DELAY = 1.0

# pygame.Rect(x, y, width, height) 创建一个矩形对象
# 用于表示按钮的位置和大小，以及检测鼠标点击是否在按钮范围内

# SCREEN_WIDTH // 2 - 100：水平居中（屏幕宽900，按钮宽200，所以从350开始）
# SCREEN_HEIGHT // 2 - 50：垂直方向在屏幕中间偏上
restart_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, 200, 50)
quit_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 20, 200, 50)
start_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50)

import os as _os

# 字体加载：优先使用项目中捆绑的 font.ttc，再回退到系统字体
# 捆绑的字体为文泉驿微米黑（GPL 许可，支持中英文），确保在所有平台都能正常显示
_FONT_FILE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "font.ttc")

def _create_font(size):
    if _os.path.exists(_FONT_FILE):
        return pygame.font.Font(_FONT_FILE, size)
    try:
        return pygame.font.SysFont(
            ["Microsoft YaHei", "SimHei", "WenQuanYi Micro Hei", "Noto Sans CJK SC"],
            size,
        )
    except Exception:
        return pygame.font.Font(None, size)


font = _create_font(36)
small_font = _create_font(24)
big_font = _create_font(56)
death_font = _create_font(48)


# 预渲染常用文字
# font.render() 把文字渲染成 Surface（图片）对象
# 参数：(要渲染的文字, 是否开启抗锯齿, 文字颜色)
# 抗锯齿（True）让文字边缘更平滑，不会有锯齿感
restart_text = font.render("Restart", True, WHITE)
quit_text = font.render("Quit", True, WHITE)
start_text = font.render("Start Game", True, WHITE)
title_text = big_font.render("SJTU RUN", True, BLACK)


# OSC（Open Sound Control）脑电信号通信相关设置
# ip：服务器监听的IP地址，"127.0.0.1" 表示只接收本机发送的数据
ip = "127.0.0.1"
# OSC_address_prefix：OSC地址前缀（用户输入的，用于匹配脑电设备的OSC地址格式）
# 不同脑电设备可能使用不同的OSC地址前缀，留空则不加前缀
OSC_address_prefix = ''
# port_number：OSC服务器监听的端口号（用户输入）
port_number = None

# global_osc_server：全局的OSC服务器对象，在主程序中创建，在清理时关闭
global_osc_server = None

# eeg_lock：线程锁（threading.Lock()）
# 因为OSC服务器在独立线程中运行并修改 eeg_commands，
# 而主游戏循环也在读取 eeg_commands，
# 互斥锁（Lock）保证同一时间只有一个线程在访问这些数据，防止数据冲突
eeg_lock = threading.Lock()

# eeg_commands：存储当前脑电信号状态的字典（dictionary）
# 字典是一种"键→值"的映射数据结构，用花括号 {} 表示
# 这里的键是信号名称（字符串），值是 True/False（布尔值）或时间戳（浮点数）
# 例如 eeg_commands["blink"] 表示"是否正在眨眼"
eeg_commands = {
    "left_eyebrow": False,       # 左眉毛动作信号（当前未使用于游戏控制）
    "right_eyebrow": False,      # 右眉毛/咬牙信号 → 用于"跳跃"指令
    "clench_teeth": False,       # 咬牙信号（当前未直接使用）
    "blink": False,              # 眨眼信号 → 用于角色选择
    "forward_end_time": 0,       # 眨眼信号的结束时间（用于维持眨眼状态一段时间）
    "last_clench_time": 0        # 上次咬牙的时间戳，防止短时间内重复触发
}



# EEG 信号处理函数（OSC 回调函数）
def eeg_handler(address, *args):
    """
    OSC 脑电信号的"回调函数"——当 OSC 服务器收到消息时自动调用此函数。

    脑电设备会不断发送 OSC 数据，其中包含各种信号的值（如眉毛抬起程度、咬牙力度等）。
    这个函数解析这些信号，并将它们翻译成游戏能理解的"指令"。

    例如：
        - 咬牙力度 > 0.99 → 触发跳跃信号（eeg_commands["right_eyebrow"] = True）
        - 眨眼强度 > 0.7 → 设置眨眼结束时间，维持0.2秒

    参数:
        address (str): OSC 消息的地址（如 "/elements/eeg/eeg[0]"），标识这是什么信号
        *args: 可变长度参数，OSC消息携带的数据值，通常 args[0] 是信号的数值
    """
    # 声明我们要修改的是全局变量 eeg_commands，而不是创建一个局部变量
    global eeg_commands

    # 如果 args 是空的（没有附带数据），直接返回不做任何处理
    if not args:
        return

    # args[0] 是信号的数值，例如 0.95 表示95%的咬牙力度
    value = args[0]

    # time.time() 返回当前的时间戳（浮点数，单位：秒）
    current_time = time.time()

    # with eeg_lock：获取线程锁，进入"临界区"
    # 确保在修改 eeg_commands 字典时，游戏主循环不会同时读取它
    # 这防止了数据竞争（data race）问题
    with eeg_lock:
        # address.endswith("eeg/eeg[0]")：
        #   检查OSC地址是否以 "eeg/eeg[0]" 结尾
        #   "eeg/eeg[0]" 通常是左眉毛的信号通道
        if address.endswith("eeg/eeg[0]"):
            # 如果信号值大于0.001（有微弱的眉毛活动），则认为左眉毛动了
            # 这是一个阈值判断：大于阈值为True，否则为False
            eeg_commands["left_eyebrow"] = value > 0.001

        # address.endswith("jaw_clench")：
        #   "jaw_clench" 是咬牙（下颌咬紧）的信号通道
        elif address.endswith("jaw_clench"):
            # value > 0.99：咬牙力度超过99%才被认为是"有效咬牙"
            # 这么高的阈值是为了防止误触发（如说话、吞咽等被误判为咬牙）
            if value > 0.99:
                # 计算距上次有效咬牙过去了多少时间
                time_since_last = current_time - eeg_commands["last_clench_time"]

                # 防抖（debounce）：只有距上次咬牙超过0.8秒才触发新跳跃
                # 这是为了防止一次咬牙被多次检测，导致连续跳跃
                if time_since_last > 0.8:
                    # 将 right_eyebrow 设为 True → 游戏中的跳跃信号
                    # （虽然变量名叫"右眉毛"，但在游戏中用于表示跳跃指令）
                    eeg_commands["right_eyebrow"] = True

                    # 记录这次咬牙的时间，用于下次判断间隔
                    eeg_commands["last_clench_time"] = current_time
                else:
                    # 间隔太短，忽略这次咬牙
                    eeg_commands["right_eyebrow"] = False
            else:
                # 咬牙力度不足99%，释放跳跃信号
                eeg_commands["right_eyebrow"] = False

        # address.endswith("blink")：
        #   "blink" 是眨眼的信号通道
        elif address.endswith("blink"):
            # value > 0.7：眨眼强度超过70%才认为是有效眨眼
            if value > 0.7:
                # 设置"眨眼状态"的结束时间为当前时间 + 0.2秒
                # 这意味着眨眼信号会维持0.2秒（即使实际眨眼只有一瞬间）
                # 游戏在检查时会判断 current_time < forward_end_time
                eeg_commands["forward_end_time"] = time.time() + 0.2

        # address.endswith("touching_forehead")：
        #   "touching_forehead" 是触摸额头的信号通道
        elif address.endswith("touching_forehead"):
            # value > 0.9999：极高的阈值（99.99%），确保只有明确的触摸才触发
            # 这个信号用于角色选择界面中的"blink"指令
            # （触摸额头被视为另一种形式的眨眼确认）
            eeg_commands["blink"] = value > 0.9999

# OSC 服务器线程函数
def osc_server_thread(address_prefix, port):
    """
    在独立线程中运行 OSC 服务器的函数。

    OSC（Open Sound Control）服务器负责：
        1. 监听指定的IP地址和端口
        2. 接收脑电设备发来的OSC数据包
        3. 将数据包分发给对应的处理函数（eeg_handler）

    为什么要在独立线程中运行？
        - serve_forever() 是一个阻塞函数，会一直运行不返回
        - 如果放在主线程，游戏界面会卡住无法响应
        - 放在独立线程中，OSC服务器和游戏循环可以同时运行

    参数:
        address_prefix (str): OSC 地址前缀（设备特定的前缀）
        port (int): 监听的端口号
    """
    # 声明我们要使用的是外部的全局变量 global_osc_server
    global global_osc_server

    # 处理 OSC 地址前缀
    # 如果用户输入了前缀，在后面加 "/" 使其成为标准的OSC地址格式
    # 例如前缀 "muse" → "muse/"
    # 如果前缀为空字符串，则保持为空
    prefix = address_prefix + "/" if address_prefix else ""

    # 创建 OSC 消息分发器（Dispatcher）
    # Dispatcher 的作用：把收到的OSC消息按照地址匹配到对应的处理函数
    osc_dispatcher = dispatcher.Dispatcher()

    # osc_dispatcher.map(地址模式, 处理函数)
    # 为不同的 OSC 地址注册对应的处理函数
    # 当收到匹配地址的OSC消息时，自动调用 eeg_handler

    # f-string（格式化字符串）：f"..." 允许在字符串中嵌入变量
    # f"/{prefix}elements/eeg/eeg[0]" → 例如 "/muse/elements/eeg/eeg[0]"
    osc_dispatcher.map(f"/{prefix}elements/eeg/eeg[0]", eeg_handler)     # 左眉毛信号
    osc_dispatcher.map(f"/{prefix}elements/jaw_clench", eeg_handler)      # 咬牙信号
    osc_dispatcher.map(f"/{prefix}elements/blink", eeg_handler)           # 眨眼信号
    osc_dispatcher.map(f"/{prefix}elements/touching_forehead", eeg_handler)  # 触摸额头信号

    try:
        # 创建 OSC UDP 服务器（多线程版本）
        # ThreadingOSCUDPServer 可以同时处理多个请求
        # (ip, port)：监听地址和端口
        # osc_dispatcher：消息分发器
        global_osc_server = osc_server.ThreadingOSCUDPServer((ip, port), osc_dispatcher)

        # 打印启动信息到控制台
        print(f"OSC服务器启动在 {ip}:{port}")

        # serve_forever() 启动服务器，进入无限循环等待接收OSC消息
        # 这是一个阻塞调用，会一直运行直到 shutdown() 被调用
        global_osc_server.serve_forever()

    except Exception as e:
        # 如果服务器启动失败（如端口被占用），打印错误信息
        print(f"OSC服务器错误: {e}")


def cleanup():
    """
    清理 OSC 服务器资源，在程序退出前调用。

    如果不正确关闭 OSC 服务器：
        - 端口可能被占用，下次启动会失败
        - 后台线程可能继续运行，导致程序无法正常退出

    这个函数会：
        1. 关闭 OSC 服务器
        2. 等待 OSC 线程结束
    """
    global global_osc_server, osc_thread

    # 如果 OSC 服务器存在（已创建），则安全关闭它
    if global_osc_server:
        # shutdown() 停止 serve_forever() 的无限循环
        global_osc_server.shutdown()
        # server_close() 释放网络端口
        global_osc_server.server_close()
        # 将引用设为 None，方便垃圾回收
        global_osc_server = None

    # 检查 osc_thread 是否存在于全局变量中，且线程仍在运行
    # globals() 返回所有全局变量的字典
    # osc_thread.is_alive() 检查线程是否还活着
    if 'osc_thread' in globals() and osc_thread.is_alive():
        # join(1.0) 等待线程结束，最多等待1秒
        # 如果1秒后线程还没结束，也不等了（避免程序卡住）
        osc_thread.join(1.0)
        osc_thread = None


# ============================================================
# OSC 参数输入界面：获取 OSC 地址前缀
# ============================================================
def get_osc_address_prefix():
    """
    显示一个输入界面，让用户输入 OSC 地址前缀。

    OSC 地址前缀是脑电设备发送数据时使用的地址命名空间。
    不同品牌的脑电设备可能使用不同的前缀（如 "muse"、"openbci" 等）。
    如果不确定前缀，可以留空（直接按回车）。

    返回:
        str: 用户输入的地址前缀字符串（可能为空）
    """
    # input_text：存储用户当前输入的字符
    input_text = ''

    # input_active：控制输入循环的标志，True 表示继续等待输入
    input_active = True

    # 输入循环：一直运行直到用户按下回车
    while input_active:
        # ---- 绘制界面 ----

        # screen.fill(BLACK)：用黑色填充整个屏幕（清空上一帧的内容）
        screen.fill(BLACK)

        # font.render() 渲染提示文字为 Surface
        prompt = font.render("Enter OSC address prefix (leave empty for none):", True, WHITE)

        # screen.blit(图片, 位置) 把图片"贴"到画布上的指定位置
        # (50, SCREEN_HEIGHT // 3) 是左上角的坐标
        screen.blit(prompt, (50, SCREEN_HEIGHT // 3))

        # 渲染并显示用户当前输入的文本
        input_surf = font.render(input_text, True, WHITE)
        screen.blit(input_surf, (50, SCREEN_HEIGHT // 3 + 40))

        # 渲染并显示操作提示
        hint = small_font.render("Press Enter to confirm", True, GRAY)
        screen.blit(hint, (50, SCREEN_HEIGHT // 3 + 80))

        # pygame.display.update() 更新屏幕显示
        # 把之前所有 blit() 操作的内容真正显示到屏幕上
        pygame.display.update()

        # ---- 事件处理 ----
        # pygame.event.get() 获取自上次调用以来发生的所有事件（按键、鼠标点击等）
        for event in pygame.event.get():
            # event.type：事件的类型
            # pygame.QUIT：用户点击了窗口的关闭按钮（×）
            if event.type == pygame.QUIT:
                cleanup()       # 清理OSC资源
                pygame.quit()   # 退出pygame
                exit()          # 退出Python程序

            # pygame.KEYDOWN：键盘按键被按下
            if event.type == pygame.KEYDOWN:
                # event.key：被按下的具体是哪个键
                # pygame.K_RETURN：回车键
                if event.key == pygame.K_RETURN:
                    # 用户按下回车 → 确认输入，返回输入的文本
                    return input_text

                # pygame.K_BACKSPACE：退格键（删除键）
                elif event.key == pygame.K_BACKSPACE:
                    # input_text[:-1] 是Python的切片语法
                    # 表示"从开头到倒数第二个字符"，即删除最后一个字符
                    input_text = input_text[:-1]

                # 其他按键 → 把输入的字符追加到 input_text
                else:
                    # event.unicode 是按键对应的字符（支持中文等多语言输入）
                    input_text += event.unicode


# ============================================================
# OSC 参数输入界面：获取端口号
# ============================================================
def get_port_number():
    """
    显示一个输入界面，让用户输入 OSC 服务器的端口号。

    端口号是一个 0~65535 之间的整数，脑电设备的数据会发送到这个端口。
    常见端口如 5000、5001 等。
    只接受数字输入，输入非数字的按键会被忽略。

    返回:
        int: 用户输入的端口号
    """
    # 外层循环：如果输入为空就重新来
    while True:
        input_text = ''
        input_active = True

        # 输入循环
        while input_active:
            # ---- 绘制界面 ----
            screen.fill(BLACK)
            prompt = font.render("Enter port number:", True, WHITE)
            screen.blit(prompt, (50, SCREEN_HEIGHT // 3))
            input_surf = font.render(input_text, True, WHITE)
            screen.blit(input_surf, (50, SCREEN_HEIGHT // 3 + 40))
            hint = small_font.render("Press Enter to confirm", True, GRAY)
            screen.blit(hint, (50, SCREEN_HEIGHT // 3 + 80))
            pygame.display.update()

            # ---- 事件处理 ----
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    cleanup()
                    pygame.quit()
                    exit()

                if event.type == pygame.KEYDOWN:
                    # 回车键 + 输入不为空 → 结束输入
                    if event.key == pygame.K_RETURN and input_text:
                        input_active = False

                    # 退格键 → 删除最后一个字符
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]

                    # event.unicode.isdigit()：
                    #   isdigit() 检查字符串是否全是数字字符
                    #   只允许输入数字，过滤掉字母、符号等非数字输入
                    elif event.unicode.isdigit():
                        input_text += event.unicode

        # 如果输入了有效文本，转换为整数并返回
        if input_text:
            return int(input_text)  # int() 把字符串转换为整数


# ============================================================
# Player 类（类的定义）
# ============================================================
# class 是用来创建"对象"的模板
# 对象 = 数据（属性）+ 行为（方法/函数）
# 比如 Player 类封装了玩家的位置、跳跃逻辑、绘制逻辑等

class Player:
    """
    玩家类：管理玩家的位置、跳跃、碰撞检测和绘制。

    属性（数据）:
        x, y：玩家脚底的坐标
        width, height：玩家的碰撞体积
        is_jumping：是否正在跳跃
        jump_start_time：跳跃开始的时间戳
        character_image：玩家角色的图片

    方法（行为）:
        jump()：触发跳跃
        update()：每帧更新位置（跳跃的抛物线运动）
        get_rect()：获取碰撞检测用的矩形
        draw()：绘制玩家到屏幕
        is_on_ground()：检查玩家是否站在地面上
    """
    def __init__(self, x, ground_y, character_image=None):
        """
        初始化（创建）一个玩家对象。

        参数:
            x (int): 玩家的X坐标（固定不变）
            ground_y (int): 地面的Y坐标（玩家站立时的脚底Y坐标）
            character_image (Surface | None): 角色的图片，None则使用默认蓝色方块
        """
        self.x = x                           # 玩家的水平位置（固定）
        self.ground_y = ground_y             # 地面高度（玩家踩在地面上时的 Y 坐标）
        self.y = ground_y                    # 玩家当前的脚底 Y 坐标（初始站在地面上）
        self.width = PLAYER_WIDTH            # 碰撞检测用的宽度
        self.height = PLAYER_HEIGHT          # 碰撞检测用的高度
        self.is_jumping = False              # 是否正在跳跃中（初始为否）
        self.jump_start_time = 0            # 跳跃开始的时间戳（初始为0）
        self.character_image = character_image  # 角色图片（在角色选择界面选中的）

    def jump(self):
        """
        触发一次跳跃。

        只有在玩家站在地面上时（is_jumping == False）才能起跳。
        如果玩家已经在空中则忽略（不能二段跳）。
        跳跃的逻辑：
            1. 将 is_jumping 设为 True
            2. 记录跳跃开始时间，供后续抛物线计算使用
        """
        # 如果当前没有在跳跃，则可以起跳
        if not self.is_jumping:
            self.is_jumping = True                    # 标记为"正在跳跃"
            self.jump_start_time = time.time()       # 记录跳跃开始的时间戳

    def update(self):
        """
        根据跳跃状态更新玩家的 Y 坐标（垂直位置）。

        使用抛物线运动模拟跳跃：
            - 玩家上升阶段：Y 坐标逐渐减小（视觉上向上移动）
            - 玩家下降阶段：Y 坐标逐渐增大（视觉上向下移动）
            - 跳跃结束：Y 坐标回到地面

        抛物线公式：
            y_offset = JUMP_HEIGHT × (1 - (2×t - 1)²)
            其中 t = 已过时间 / 总时长，范围 0→1

            当 t=0（开始）：y_offset = JUMP_HEIGHT × (1-1) = 0（在地面）
            当 t=0.5（中点）：y_offset = JUMP_HEIGHT × (1-0) = JUMP_HEIGHT（最高点）
            当 t=1（结束）：y_offset = JUMP_HEIGHT × (1-1) = 0（回到地面）

            这是一条对称的抛物线，上升和下降花的时间相同。
        """
        if self.is_jumping:
            # 计算从跳跃开始到现在的经过时间
            elapsed = time.time() - self.jump_start_time

            # 如果跳跃时间已到或超过总时长，跳跃结束
            if elapsed >= JUMP_DURATION:
                self.is_jumping = False    # 标记跳跃结束
                self.y = self.ground_y    # 落回地面
            else:
                # t：跳跃进度，0=刚开始，0.5=最高点，1=结束
                t = elapsed / JUMP_DURATION

                # 抛物线公式：(2*t - 1)^2 在 t=0.5 时取得最小值0
                # 1 - (2*t - 1)^2 在 t=0 和 t=1 时为0，在 t=0.5 时为1
                y_offset = JUMP_HEIGHT * (1 - (2 * t - 1) ** 2)

                # 地面上移y_offset像素 → 视觉上向上跳
                # Y轴向下为正，所以用 ground_y - y_offset 表示向上
                self.y = self.ground_y - y_offset

    def get_rect(self):
        """
        获取玩家的碰撞检测矩形。

        pygame.Rect 是一个矩形对象，常用于碰撞检测。
        矩形位置：
            - X：self.x（玩家的水平位置）
            - Y：self.y - self.height（矩形左上角，因为self.y是脚底坐标）
            - 宽度：self.width
            - 高度：self.height

        为什么 Y 是 self.y - self.height？
            玩家的 self.y 存储的是"脚底"的Y坐标。
            碰撞矩形需要的是"左上角"坐标。
            所以：左上角Y = 脚底Y - 高度

        返回:
            pygame.Rect: 玩家的碰撞矩形
        """
        return pygame.Rect(self.x, self.y - self.height, self.width, self.height)

    def draw(self, screen):
        """
        在屏幕上绘制玩家。

        如果有角色图片（character_image），就绘制图片。
        如果没有（character_image 为 None），就绘制一个蓝色方块作为占位。

        参数:
            screen (pygame.Surface): 要绘制到的画布（游戏窗口的主画面）
        """
        # 获取玩家的碰撞矩形
        rect = self.get_rect()

        if self.character_image:
            # 绘制角色图片到矩形左上角
            # rect.topleft 返回 (x, y) 元组，即矩形的左上角坐标
            screen.blit(self.character_image, rect.topleft)
        else:
            # 没有图片时的占位绘制：
            # 1. 画一个蓝色矩形作为身体
            pygame.draw.rect(screen, BLUE, rect)
            # 2. 画一个黑色小矩形作为"眼睛"
            pygame.draw.rect(screen, BLACK, (self.x + 10, self.y - self.height + 10, 10, 10))

    def is_on_ground(self):
        """
        检查玩家是否站在地面上。

        返回:
            bool: True 表示在地面上（没有在跳跃），False 表示在空中
        """
        return not self.is_jumping

class Obstacle:
    """
    障碍物类：管理单个障碍物的位置、移动、碰撞检测和绘制。

    障碍物从屏幕右边生成，以随机速度向左移动。
    当移动到屏幕左边之外时会被删除。

    属性:
        x, y：位置
        speed：移动速度（像素/帧）
        width, height：尺寸（随机生成）
        image：障碍物图片
        name：障碍物名称（如"Pre"、"GPA"等）
        passed：是否已被玩家跳过（用于计分，避免重复计分）

    方法:
        update()：每帧向左移动
        draw()：绘制障碍物到屏幕
        get_rect()：获取碰撞检测矩形
        is_offscreen()：检查是否已经完全移出屏幕左侧
    """

    def __init__(self, ground_y, speed):
        """
        创建一个新的障碍物。

        参数:
            ground_y (int): 地面的Y坐标（障碍物底部对齐地面）
            speed (float): 移动速度（像素/帧）
        """
        # self.x：障碍物的X坐标，初始在屏幕最右边（刚刚进入屏幕）
        self.x = SCREEN_WIDTH

        self.ground_y = ground_y    # 地面Y坐标（障碍物底部与此对齐）

        self.speed = speed           # 存储分配的随机移动速度

        # random.randint(a, b)：生成 a~b 之间（包含a和b）的随机整数
        self.width = random.randint(OBSTACLE_MIN_WIDTH, OBSTACLE_MAX_WIDTH)
        self.height = random.randint(OBSTACLE_MIN_HEIGHT, OBSTACLE_MAX_HEIGHT)

        # random.choice(列表)：从列表中随机选一个元素
        # obstacle_data 的元素是 (图片, 名称) 元组
        # if obstacle_data else ... 是一个安全判断：如果列表为空（图片都没加载成功），使用默认值
        img, name = random.choice(obstacle_data) if obstacle_data else (None, "???")

        self.image = img    # 障碍物的图片（Surface对象或None）
        self.name = name    # 障碍物的名称（用于死亡时显示"你被XXX杀死了"）

        # passed：标记这个障碍物是否已被玩家跳过去过了
        # 初始为 False，一旦被跳过就设为 True，确保每个障碍物只计一次分
        self.passed = False

    def update(self):
        """
        每帧更新障碍物位置：向左移动 speed 像素。

        在游戏主循环中，每一帧都会调用这个函数。
        障碍物只能水平向左移动（X坐标减小），不能上下移动。
        """
        # self.x -= self.speed 是 self.x = self.x - self.speed 的简写
        # X坐标每帧减少 speed 像素，视觉效果是障碍物从右往左移动
        self.x -= self.speed

    def draw(self, screen):
        """
        在屏幕上绘制障碍物。

        如果有图片（self.image 不为 None），就把图片缩放到障碍物的实际尺寸后绘制。
        如果没有图片，就绘制一个带纹理的灰色矩形作为占位。

        参数:
            screen (pygame.Surface): 要绘制到的画布
        """
        rect = self.get_rect()  # 获取障碍物的碰撞矩形

        if self.image:
            # 把障碍物图片缩放到障碍物的实际尺寸（self.width × self.height）
            scaled_img = pygame.transform.scale(self.image, (self.width, self.height))
            # 绘制缩放后的图片
            screen.blit(scaled_img, rect.topleft)
        else:
            # ---- 占位图形：灰色矩形 + 装饰纹理 ----
            # 1. 绘制灰色填充矩形
            pygame.draw.rect(screen, GRAY, rect)

            # 2. 绘制深灰色边框（线宽2像素）
            pygame.draw.rect(screen, (60, 60, 60), rect, 2)

            # 3. 绘制3条横线作为纹理装饰
            # range(3) 生成序列 0, 1, 2
            for i in range(3):
                # 每条横线的Y坐标：在矩形内均匀分布
                # rect.top 是矩形顶部Y坐标
                # (i + 1) * self.height // 4：把高度分成4份，线在第1、2、3份的分界处
                line_y = rect.top + (i + 1) * self.height // 4

                # pygame.draw.line(画布, 颜色, 起点坐标, 终点坐标, 线宽)
                pygame.draw.line(screen, (80, 80, 80),
                                 (rect.left + 4, line_y),     # 起点：左边留4像素边距
                                 (rect.right - 4, line_y),    # 终点：右边留4像素边距
                                 1)                             # 线宽1像素

    def get_rect(self):
        """
        获取障碍物的碰撞检测矩形。

        矩形的位置和尺寸与障碍物在屏幕上的实际位置对应。
        底部对齐地面（ground_y）。

        返回:
            pygame.Rect: 障碍物的碰撞矩形
        """
        # X：self.x（障碍物左上角X坐标）
        # Y：self.ground_y - self.height（障碍物底部贴地，所以顶部Y = 地面Y - 高度）
        return pygame.Rect(self.x, self.ground_y - self.height, self.width, self.height)

    def is_offscreen(self):
        """
        检查障碍物是否已经完全移出屏幕左侧。

        当障碍物的右边缘（self.x + self.width）也移出屏幕左边（< 0）时，
        说明障碍物已经完全不可见，可以从列表中删除以节省内存。

        返回:
            bool: True 表示已完全移出屏幕
        """
        return self.x + self.width < 0

# 地面绘制函数
def draw_ground(screen):
    """
    绘制游戏的地面。

    地面包括：
        1. 一个深灰色填充矩形（从 GROUND_Y 到屏幕底部）
        2. 一条深色顶部线条（地面与天空的分界线）
        3. 随机散布的小碎石（圆形装饰，每帧随机位置，让地面看起来不单调）

    参数:
        screen (pygame.Surface): 要绘制到的画布
    """
    # ---- 1. 地面主体 ----
    # 绘制深灰色矩形填充地面区域
    # 矩形从 Y=GROUND_Y 到 Y=SCREEN_HEIGHT（屏幕底部）
    pygame.draw.rect(screen, GROUND_COLOR,
                     (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))

    # ---- 2. 地面线（天空与地面的分界线） ----
    pygame.draw.line(screen, (60, 60, 60), (0, GROUND_Y), (SCREEN_WIDTH, GROUND_Y), 2)

    # ---- 3. 地面碎石纹理 ----
    # for _ in range(20)：循环20次，_ 是一个约定，表示"我不需要用到这个循环变量"
    for _ in range(20):
        # 随机X坐标（0到屏幕宽度之间）
        gx = random.randint(0, SCREEN_WIDTH)
        # 随机Y坐标（地面顶部+5 到 屏幕底部-5 之间）
        gy = random.randint(GROUND_Y + 5, SCREEN_HEIGHT - 5)
        # 画一个随机大小的小圆（半径1~3像素）作为碎石
        pygame.draw.circle(screen, (100, 100, 100), (gx, gy), random.randint(1, 3))


# ============================================================
# 云朵绘制函数
# ============================================================
def draw_clouds(screen, clouds):
    """
    绘制天空中的云朵。

    每朵云由3个交叠的椭圆组成，看起来像蓬松的卡通云朵。

    参数:
        screen (pygame.Surface): 要绘制到的画布
        clouds (list): 云朵数据的列表，每个元素是 (x, y, 宽度) 元组
                       x, y 是云朵的参考位置，宽度决定云朵的大小
    """
    # 遍历每朵云的数据
    for cx, cy, cw in clouds:
        # 椭圆1：主体椭圆（水平方向略扁）
        # pygame.draw.ellipse(画布, 颜色, (x, y, 宽, 高))
        pygame.draw.ellipse(screen, WHITE, (cx, cy, cw, cw // 2))

        # 椭圆2：右侧偏上的椭圆
        # cx + cw // 3：在主体偏右的位置
        # cy - cw // 4：在主体偏上的位置
        pygame.draw.ellipse(screen, WHITE, (cx + cw // 3, cy - cw // 4, cw * 2 // 3, cw // 2))

        # 椭圆3：左侧偏下的椭圆
        pygame.draw.ellipse(screen, WHITE, (cx - cw // 6, cy + cw // 6, cw * 2 // 3, cw // 2))


# ============================================================
# 开始界面（Start Screen）
# ============================================================
def show_start_screen():
    """
    显示游戏的开始界面。

    开始界面包含：
        - 天蓝色天空背景 + 云朵装饰 + 地面
        - "SJTU RUN" 大标题
        - 绿色"Start Game"按钮
        - 操作说明文字

    玩家可以：
        - 点击"Start Game"按钮 → 进入游戏
        - 按回车键（Enter）或空格键（Space） → 进入游戏
        - 点击窗口关闭按钮（×） → 退出程序
    """
    # waiting：控制循环的标志，True时持续显示开始界面
    waiting = True

    while waiting:
        # ---- 绘制界面 ----

        # 用天蓝色填充整个屏幕作为天空背景
        screen.fill(SKY_BLUE)

        # 绘制云朵装饰
        # 这里的列表定义了4朵云的位置和大小
        # (x坐标, y坐标, 宽度) — 云朵的Y坐标不同让天空看起来有层次
        draw_clouds(screen, [
            (100, 80, 80),    # 左上方的云
            (350, 50, 100),   # 偏上较大的云
            (600, 100, 70),   # 右上方较小的云
            (750, 60, 90)     # 右上方的云
        ])

        # 绘制地面
        draw_ground(screen)

        # 绘制标题"DNOSAUR RUN"
        title_surf = big_font.render("SJTU RUN", True, BLACK)
        # 居中显示标题
        # get_width() 获取文字图片的宽度
        # SCREEN_WIDTH // 2 - 宽度 // 2 = 水平居中位置
        screen.blit(title_surf,
                    (SCREEN_WIDTH // 2 - title_surf.get_width() // 2,
                     SCREEN_HEIGHT // 4))  # 在屏幕上1/4高度的位置

        # 绘制绿色开始按钮（圆角矩形）
        # border_radius=8 让矩形的四个角变成圆角
        pygame.draw.rect(screen, GREEN, start_button, border_radius=8)

        # 在按钮上绘制"Start Game"文字（居中显示在按钮上）
        # centerx / centery 是按钮的中心坐标
        screen.blit(start_text,
                    (start_button.centerx - start_text.get_width() // 2,
                     start_button.centery - start_text.get_height() // 2))

        # 操作说明文字列表
        instructions = [
            "How to Play:",                                           # 标题
            "Clench Teeth : Jump",                              # 脑电咬牙 → 跳跃
            "Space / Up Arrow: Jump (keyboard backup)",              # 键盘空格/上箭头 → 跳跃（备用）
            "Avoid all obstacles!",                                  # 避开所有障碍物
        ]

        # enumerate() 同时遍历列表的索引 i 和元素 text
        # i 从0开始，用于计算每行文字的Y坐标偏移
        for i, text in enumerate(instructions):
            # 渲染每条说明文字
            surf = small_font.render(text, True, BLACK)
            # 居中显示，每行间隔28像素
            screen.blit(surf,
                        (SCREEN_WIDTH // 2 - surf.get_width() // 2,
                         SCREEN_HEIGHT // 2 - 100 + i * 28))

        # pygame.display.flip() 更新整个屏幕
        # 和 update() 类似，但 flip() 更新整个窗口（更彻底）
        pygame.display.flip()

        # ---- 事件处理 ----
        for event in pygame.event.get():
            # 关闭窗口 → 退出
            if event.type == pygame.QUIT:
                cleanup()
                pygame.quit()
                exit()

            # 鼠标按下事件
            if event.type == pygame.MOUSEBUTTONDOWN:
                # event.pos 是鼠标点击的 (x, y) 坐标
                # start_button.collidepoint(event.pos) 检查鼠标点击位置是否在按钮范围内
                if start_button.collidepoint(event.pos):
                    waiting = False  # 点击了开始按钮 → 退出循环，进入游戏

            # 键盘按下事件
            if event.type == pygame.KEYDOWN:
                # event.key in (pygame.K_RETURN, pygame.K_SPACE)：
                #   检查按下的键是否为回车或空格
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    waiting = False  # 按了回车或空格 → 退出循环，进入游戏


# ============================================================
# 角色选择界面（Character Select Screen）
# ============================================================
def show_character_select_screen():
    """
    显示角色选择界面，让玩家选择使用哪个角色进入游戏。

    有两种选择方式：
        1. 脑电信号：
            - 眨眼（Blink）→ 选择 Player 1
            - 咬牙（Clench Teeth）→ 选择 Player 2
        2. 键盘/鼠标：
            - 按键盘1或点击卡片 → 选择 Player 1
            - 按键盘2或点击卡片 → 选择 Player 2

    选中后会有一个绿色闪烁的确认动画（0.5秒），然后自动进入游戏。

    返回:
        str: 选中的角色图片文件路径（如 "player1.jpg" 或 "player2.jpg"）
    """
    # 加载两个角色的放大预览图片（150×150像素，比实际游戏中的大）
    char1_img = load_image("player1.jpg", (150, 150))
    char2_img = load_image("player2.jpg", (150, 150))

    # ---- 两个角色卡片的区域定义 ----
    # card_w, card_h：每个卡片的宽和高
    card_w, card_h = 260, 360

    # char1_rect：Player 1 卡片的矩形区域
    # SCREEN_WIDTH // 4 - card_w // 2 → 屏幕左半部分的中央
    char1_rect = pygame.Rect(SCREEN_WIDTH // 4 - card_w // 2,
                              SCREEN_HEIGHT // 2 - card_h // 2 - 30,
                              card_w, card_h)

    # char2_rect：Player 2 卡片的矩形区域
    # 3 * SCREEN_WIDTH // 4 → 屏幕右半部分的中央
    char2_rect = pygame.Rect(3 * SCREEN_WIDTH // 4 - card_w // 2,
                              SCREEN_HEIGHT // 2 - card_h // 2 - 30,
                              card_w, card_h)

    # ---- 选择状态变量 ----
    # selected：None 表示还没选，选好后存储文件路径字符串
    selected = None

    # selection_start：记录选中的时间戳，用于确认动画（0表示还没选中）
    selection_start = 0

    # blink_prev / clench_prev：记录上一帧的眨眼/咬牙状态
    # 用于"边沿检测"——只在信号从 False 变 True 的那一瞬间触发一次
    # 防止持续按住/眨眼导致重复选择
    blink_prev = False
    clench_prev = False

    # clock：pygame的时钟对象，用于控制帧率
    clock = pygame.time.Clock()

    # 进入选择前清掉残留的咬牙信号
    # 防止之前在开始界面咬牙、到了选择界面被误触发
    with eeg_lock:
        eeg_commands["right_eyebrow"] = False

    # ---- 选择界面主循环 ----
    # selected is None 表示还没选中角色，继续循环
    while selected is None:
        # ---- 绘制界面 ----
        screen.fill(SKY_BLUE)   # 天蓝色背景
        draw_clouds(screen, [(100, 80, 80), (350, 50, 100), (600, 100, 70), (750, 60, 90)])
        draw_ground(screen)

        # 标题："SELECT YOUR CHARACTER"
        title_surf = big_font.render("SELECT YOUR CHARACTER", True, BLACK)
        screen.blit(title_surf,
                    (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 70))

        # 副标题：说明脑电控制方式
        sub_surf = font.render("Blink = Player 1              Clench Teeth = Player 2", True, (60, 60, 60))
        screen.blit(sub_surf,
                    (SCREEN_WIDTH // 2 - sub_surf.get_width() // 2, 130))

        # ---- 绘制两个角色卡片 ----
        # pygame.mouse.get_pos() 获取当前鼠标位置 (x, y)
        mouse_pos = pygame.mouse.get_pos()

        # 遍历两个卡片：每个卡片包含 (矩形区域, 预览图, 角色名, 快捷键提示, 高亮颜色)
        for rect, img, label, key_hint, color in [
            (char1_rect, char1_img, "Player 1", "Blink  /  Press [1]", (70, 130, 230)),      # 蓝色调
            (char2_rect, char2_img, "Player 2", "Clench  /  Press [2]", (230, 120, 50)),      # 橙色调
        ]:
            # 检测鼠标是否悬停在卡片上
            hover = rect.collidepoint(mouse_pos)

            # 悬停时边框更粗、颜色变为高亮色
            border_color = color if hover else BLACK
            border_w = 5 if hover else 3

            # 绘制卡片白色背景（圆角矩形）
            pygame.draw.rect(screen, WHITE, rect, border_radius=14)
            # 绘制卡片边框
            pygame.draw.rect(screen, border_color, rect, border_w, border_radius=14)

            # 绘制角色预览图（在卡片内部上方居中）
            img_x = rect.centerx - img.get_width() // 2
            img_y = rect.top + 30
            screen.blit(img, (img_x, img_y))

            # 绘制角色名（在图片下方）
            label_surf = font.render(label, True, BLACK)
            screen.blit(label_surf,
                        (rect.centerx - label_surf.get_width() // 2,
                         rect.top + 210))

            # 绘制操作提示（在角色名下方）
            hint_surf = small_font.render(key_hint, True, GRAY)
            screen.blit(hint_surf,
                        (rect.centerx - hint_surf.get_width() // 2,
                         rect.top + 250))

            # 如果鼠标悬停，再画一层高亮边框
            if hover:
                pygame.draw.rect(screen, color, rect, 2, border_radius=14)

        # 底部提示文字
        tip_surf = small_font.render("Keyboard: press 1 or 2 | Mouse: click on card", True, (80, 80, 80))
        screen.blit(tip_surf,
                    (SCREEN_WIDTH // 2 - tip_surf.get_width() // 2,
                     SCREEN_HEIGHT - 60))

        # ---- 确认动画：选中后闪烁绿色0.5秒 ----
        # selection_start > 0 表示已经选中了（记录的是选中的时间戳）
        if selection_start > 0:
            elapsed = time.time() - selection_start

            # 0.5秒后动画结束，break跳出循环
            if elapsed > 0.5:
                break

            # alpha：透明度，从150逐渐减小到0
            # 150 * (1 - elapsed / 0.5)：
            #   动画开始（elapsed=0）：alpha = 150
            #   动画结束（elapsed=0.5）：alpha = 0
            alpha = int(150 * (1 - elapsed / 0.5))

            # 创建一个支持透明度的临时画布
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            # 填充半透明绿色（(0, 200, 0, alpha) 中最后一个值是透明度）
            overlay.fill((0, 200, 0, alpha))
            # 把半透明遮罩贴在屏幕上
            screen.blit(overlay, (0, 0))

        # 刷新屏幕显示
        pygame.display.flip()

        # ====================================================
        # 事件处理（键盘和鼠标）
        # ====================================================
        for event in pygame.event.get():
            # 关闭窗口 → 退出程序
            if event.type == pygame.QUIT:
                cleanup()
                pygame.quit()
                exit()

            # 键盘按下
            if event.type == pygame.KEYDOWN:
                # 按数字键 1 → 选择 Player 1
                if event.key == pygame.K_1:
                    selected = "player1.jpg"           # 记录选中的角色文件路径
                    selection_start = time.time()      # 记录选中时间，开始确认动画

                # 按数字键 2 → 选择 Player 2
                elif event.key == pygame.K_2:
                    selected = "player2.jpg"
                    selection_start = time.time()

                # 按回车键 → 默认选择 Player 1
                elif event.key == pygame.K_RETURN:
                    selected = "player1.jpg"
                    selection_start = time.time()

            # 鼠标点击（且还没开始确认动画时）
            if event.type == pygame.MOUSEBUTTONDOWN and selection_start == 0:
                # collidepoint() 检查点击位置是否在卡片矩形内
                if char1_rect.collidepoint(event.pos):
                    selected = "player1.jpg"
                    selection_start = time.time()
                elif char2_rect.collidepoint(event.pos):
                    selected = "player2.jpg"
                    selection_start = time.time()

        # ====================================================
        # 脑电信号处理（眨眼 → Player1，咬牙 → Player2）
        # ====================================================
        # 获取当前脑电信号状态（加锁保护，避免线程冲突）
        with eeg_lock:
            # blink_active：当前是否处于"眨眼激活"状态
            # 判断方式：当前时间 < 眨眼结束时间（eeg_handler中设置的 time.time() + 0.2）
            blink_active = eeg_commands["forward_end_time"] > time.time()

            # clench_active：当前是否有咬牙信号
            clench_active = eeg_commands["right_eyebrow"]

        # ---- 边沿检测（edge detection） ----
        # blink_active and not blink_prev：
        #   当前帧眨眼信号为True，且上一帧为False → 上升沿（刚眨眼的那一瞬间）
        # selection_start == 0：还没开始确认动画（防止动画期间重复触发）
        if blink_active and not blink_prev and selection_start == 0:
            selected = "player1.jpg"
            selection_start = time.time()

        # 更新眨眼的前一帧状态（供下一帧做边沿检测）
        blink_prev = blink_active

        # 同样的边沿检测逻辑：咬牙上升沿 → 选择 Player 2
        if clench_active and not clench_prev and selection_start == 0:
            selected = "player2.jpg"
            selection_start = time.time()

        # 更新咬牙的前一帧状态
        clench_prev = clench_active

        # clock.tick(FPS)：控制帧率，让循环每秒最多运行 FPS（60）次
        # 这个调用会让程序在这里暂停合适的时间，确保稳定的帧率
        clock.tick(FPS)

    # ---- 选中后清理 ----
    # 清掉咬牙信号，防止游戏开始时意外触发跳跃
    with eeg_lock:
        eeg_commands["right_eyebrow"] = False

    # 返回选中的角色图片路径
    return selected

def show_game_over_screen(score, killer_name=""):
    """
    显示游戏结束画面。

    画面内容：
        - 半透明黑色遮罩
        - "GAME OVER" 红色大字标题
        - 死亡信息：被哪个障碍物撞死的（如"你被GPA杀死了！"）
        - 最终得分
        - 绿色"Restart"按钮（重新开始游戏）
        - 红色"Quit"按钮（退出游戏）

    参数:
        score (int): 玩家的最终得分
        killer_name (str): 撞死玩家的障碍物名称（空字符串表示没有具体名称）

    返回:
        bool: True = 玩家选择重新开始，False = 玩家选择退出
    """
    clock = pygame.time.Clock()

    # 循环等待玩家选择
    while True:
        # ---- 绘制背景 ----
        screen.fill(SKY_BLUE)
        draw_ground(screen)

        # ---- 半透明黑色遮罩（让背景暗下来，突出文字） ----
        # 创建一个支持透明度的画布
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        # 填充半透明黑色：(R, G, B, A) — A=128 表示50%透明度（范围0-255）
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))  # 覆盖在整个屏幕上

        # ---- "GAME OVER" 标题 ----
        go_text = big_font.render("GAME OVER", True, RED)
        screen.blit(go_text,
                    (SCREEN_WIDTH // 2 - go_text.get_width() // 2,
                     SCREEN_HEIGHT // 3 - 120))

        # ---- 死亡信息 ----
        if killer_name:
            # f-string 格式化：把变量值插入字符串
            # 例如 killer_name="GPA" → "你被GPA杀死了！"
            death_text = death_font.render(f"你被{killer_name}杀死了！", True, WHITE)
            screen.blit(death_text,
                        (SCREEN_WIDTH // 2 - death_text.get_width() // 2,
                         SCREEN_HEIGHT // 3 - 20))

        # ---- 最终得分 ----
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text,
                    (SCREEN_WIDTH // 2 - score_text.get_width() // 2,
                     SCREEN_HEIGHT // 3 + 30))

        # ---- 重新开始按钮（绿色，圆角） ----
        pygame.draw.rect(screen, GREEN, restart_button, border_radius=8)
        screen.blit(restart_text,
                    (restart_button.centerx - restart_text.get_width() // 2,
                     restart_button.centery - restart_text.get_height() // 2))

        # ---- 退出按钮（红色，圆角） ----
        pygame.draw.rect(screen, RED, quit_button, border_radius=8)
        screen.blit(quit_text,
                    (quit_button.centerx - quit_text.get_width() // 2,
                     quit_button.centery - quit_text.get_height() // 2))

        # 刷新屏幕
        pygame.display.flip()

        # ---- 事件处理 ----
        for event in pygame.event.get():
            # 关闭窗口 → 返回 False（退出）
            if event.type == pygame.QUIT:
                return False

            # 鼠标点击
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 点击 Restart 按钮 → 返回 True（重新开始）
                if restart_button.collidepoint(event.pos):
                    return True
                # 点击 Quit 按钮 → 返回 False（退出）
                elif quit_button.collidepoint(event.pos):
                    return False

            # 键盘按下
            if event.type == pygame.KEYDOWN:
                # 回车或空格 → 重新开始
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return True
                # Esc键 → 退出
                elif event.key == pygame.K_ESCAPE:
                    return False

        # 控制帧率
        clock.tick(FPS)

def main(character_image=None):
    """
    参数:
        character_image (Surface | None): 玩家选中的角色图片，None则使用默认图形
    """
    # 创建时钟对象，用于控制帧率
    clock = pygame.time.Clock()

    # 创建玩家对象——传入固定的X坐标、地面Y坐标 和 选中的角色图片
    player = Player(PLAYER_X, GROUND_Y, character_image)

    # obstacles 列表：存储当前屏幕上所有活跃的障碍物
    # 初始为空，随着游戏进行会不断添加和移除障碍物
    obstacles = []

    # ---- 计时与计分变量 ----
    # game_start_time：游戏开始的时间戳，用于计算"生存时间"分数
    game_start_time = time.time()

    # last_spawn_time：上次生成障碍物的时间戳
    last_spawn_time = time.time()

    # next_spawn_delay：距离下一个障碍物生成的等待时间（秒）
    # 初始设为 INITIAL_SPAWN_DELAY（2秒），给玩家准备时间
    next_spawn_delay = INITIAL_SPAWN_DELAY

    # score：跳过障碍物的数量（每跳过一个+1分）
    score = 0

    # killer_name：记录是什么障碍物撞死了玩家（用于死亡界面显示）
    # 空字符串表示还没被撞到
    killer_name = ""

    # prev_clench：上一帧的咬牙状态
    # 用于边沿检测：只在咬牙从"松"变"紧"的那一帧触发跳跃
    # 防止持续咬牙导致连续跳跃
    prev_clench = False

    # 云朵数据：4朵云的位置和大小
    clouds = [(100, 80, 80), (350, 50, 100), (600, 100, 70), (750, 60, 90)]

    # running：游戏循环的标志变量
    # True = 游戏继续运行，False = 游戏结束（玩家被撞到或按了退出）
    running = True

    # ============================================================
    # 游戏主循环
    # ============================================================
    while running:
        # ----------------------------------------------------
        # 1. 事件处理（键盘、关闭窗口）
        # ----------------------------------------------------
        for event in pygame.event.get():
            # 点击关闭按钮 → 退出游戏
            if event.type == pygame.QUIT:
                running = False

            # 键盘按下
            if event.type == pygame.KEYDOWN:
                # Esc键 → 退出游戏
                if event.key == pygame.K_ESCAPE:
                    running = False
                # 空格键 或 上箭头 → 跳跃（键盘备用触发方式）
                elif event.key in (pygame.K_SPACE, pygame.K_UP):
                    player.jump()

        # ----------------------------------------------------
        # 2. 脑电信号处理：咬牙 = 跳跃
        # ----------------------------------------------------
        # 使用线程锁安全地读取脑电信号
        with eeg_lock:
            clench = eeg_commands["right_eyebrow"]  # 读取当前的咬牙信号

        # 边沿检测：clench为True且prev_clench为False → 咬牙的上升沿
        # 只在咬牙"刚按下"的那一帧触发跳跃，避免一直咬牙导致连续跳跃
        if clench and not prev_clench:
            player.jump()

        # 更新前一帧状态，供下一帧判断
        prev_clench = clench

        # ----------------------------------------------------
        # 3. 更新玩家状态（跳跃的抛物线运动）
        # ----------------------------------------------------
        player.update()

        # ----------------------------------------------------
        # 4. 障碍物生成逻辑
        # ----------------------------------------------------
        # time.time() 获取当前时间戳
        now = time.time()

        # 如果距上次生成障碍物已经过了 next_spawn_delay 秒，就生成新障碍物
        if now - last_spawn_time >= next_spawn_delay:
            # 随机生成障碍物的移动速度
            # random.uniform(a, b)：生成 a~b 之间的随机浮点数
            speed = random.uniform(OBSTACLE_MIN_SPEED, OBSTACLE_MAX_SPEED)

            # 创建新障碍物并添加到列表
            obstacles.append(Obstacle(GROUND_Y, speed))

            # 更新上次生成时间
            last_spawn_time = now

            # 随机生成下一个障碍物的等待时间
            next_spawn_delay = random.uniform(MIN_SPAWN_INTERVAL, MAX_SPAWN_INTERVAL)

        # ----------------------------------------------------
        # 5. 更新障碍物位置 & 碰撞检测 & 计分
        # ----------------------------------------------------
        # 获取玩家的碰撞矩形（每帧都重新获取，因为玩家的Y坐标在变化）
        player_rect = player.get_rect()

        # obstacles[:] 是列表的"浅拷贝"
        # 这样做的原因：在遍历过程中可能会删除元素（remove），
        # 直接遍历原列表同时删除元素会导致跳过某些元素
        for obs in obstacles[:]:
            # 更新障碍物位置（向左移动）
            obs.update()

            # ---- 碰撞检测 ----
            # colliderect()：检查两个矩形是否重叠（相交）
            # 如果玩家和障碍物重叠 → 发生碰撞！
            if player_rect.colliderect(obs.get_rect()):
                killer_name = obs.name    # 记录撞死玩家的障碍物名称
                running = False           # 设置游戏结束标志

            # ---- 计分：障碍物安全通过玩家 ----
            # 判断条件：
            #   1. not obs.passed：这个障碍物还没被计过分（防止重复计分）
            #   2. obs.x + obs.width < player.x：障碍物的右边缘已经移到了玩家左边
            #      （障碍物完全经过了玩家，没有被碰撞）
            if not obs.passed and obs.x + obs.width < player.x:
                obs.passed = True   # 标记"已通过"，防止重复计分
                score += 1          # 分数+1

            # ---- 移除已经移出屏幕的障碍物 ----
            # is_offscreen() 检查障碍物是否完全移到了屏幕左边之外
            if obs.is_offscreen():
                obstacles.remove(obs)   # 从列表中删除，释放内存

        # ----------------------------------------------------
        # 6. 计算"生存分数"（随时间增长的分数）
        # ----------------------------------------------------
        # int() 把浮点数转换为整数（去掉小数部分，不是四舍五入）
        # (time.time() - game_start_time) 是游戏已经运行了多少秒
        # × 10 表示每秒得10分（存活越久分数越高）
        survival_score = int((time.time() - game_start_time) * 10)

        # ----------------------------------------------------
        # 7. 绘制画面（渲染所有视觉元素）
        # ----------------------------------------------------
        # ---- 天空背景 ----
        screen.fill(SKY_BLUE)

        # ---- 云朵 ----
        draw_clouds(screen, clouds)

        # ---- 地面 ----
        draw_ground(screen)

        # ---- 障碍物 ----
        # 遍历所有活跃的障碍物，逐个绘制
        for obs in obstacles:
            obs.draw(screen)

        # ---- 玩家 ----
        player.draw(screen)

        # ---- 分数面板 ----
        # 如果有分数背景图，先绘制背景装饰
        if img_score_bg:
            screen.blit(img_score_bg, (10, 10))  # 放在屏幕左上角(10, 10)位置

        # 总分数 = 跳过障碍物得分 + 存活时间得分
        total_score = score + survival_score

        # 渲染分数文字并显示
        score_text = font.render(f"Score: {total_score}", True, BLACK)
        screen.blit(score_text, (20, 15))

        # ---- 脑电信号状态显示（调试用） ----
        # 在屏幕左侧显示当前的脑电信号状态，方便调试
        with eeg_lock:
            status_lines = [
                f"Clench (Jump): {eeg_commands['right_eyebrow']}",  # 显示咬牙信号状态
            ]
        # 逐行绘制状态信息
        for i, text in enumerate(status_lines):
            surf = small_font.render(text, True, BLACK)
            screen.blit(surf, (20, 60 + i * 22))  # 从Y=60开始，每行间距22像素

        # ---- 刷新屏幕 ----
        # flip() 把后台绘制的完整画面一次性显示到屏幕（双缓冲技术，防止画面撕裂）
        pygame.display.flip()

        # ---- 控制帧率 ----
        # tick(FPS) 确保每秒最多60帧，维持稳定的游戏速度
        # 在不同的电脑上游戏速度保持一致
        clock.tick(FPS)

    # ================================================================
    # 游戏结束处理（退出 while running 循环后执行）
    # ================================================================

    # 计算最终的总分
    total_score = score + int((time.time() - game_start_time) * 10)

    # 显示游戏结束画面
    # show_game_over_screen() 返回 True（重新开始）或 False（退出）
    if show_game_over_screen(total_score, killer_name):
        # 玩家选择重新开始 → 递归调用 main() 函数，重新开始游戏
        # character_image 参数保持不变，使用之前选中的角色
        main(character_image)

    # 如果玩家选择退出（返回False），函数自然结束，回到调用处
    # 后续的清理工作由调用者（__main__ 部分）负责

# 程序入口（Entry Point）
# if __name__ == "__main__": 是Python的特殊语法
#
# 当一个 .py 文件被直接运行时（如 `python my_game.py`），
# Python会把 __name__ 这个特殊变量设置为 "__main__"
#
# 当这个文件被"导入"（import）到另一个文件时，
# __name__ 会被设置为文件名 "my_game"，而不是 "__main__"
#
# 这个判断确保：只有直接运行这个文件时，才会执行下面的启动代码；
# 如果被别人import，就只导入函数和类定义，不自动运行游戏。

if __name__ == "__main__":
    # ---- 第1步：获取 OSC 配置 ----
    # 让用户输入 OSC 地址前缀（如 "muse" 或留空）
    OSC_address_prefix = get_osc_address_prefix()

    # 让用户输入 OSC 端口号（如 5000）
    port_number = get_port_number()

    # ---- 第2步：启动 OSC 服务器（在独立线程中运行） ----
    # threading.Thread() 创建一个新的线程
    # target=osc_server_thread：线程运行的函数
    # args=(OSC_address_prefix, port_number)：传给线程函数的参数
    # daemon=True：设为守护线程，主程序退出时自动跟着退出
    osc_thread = threading.Thread(
        target=osc_server_thread,
        args=(OSC_address_prefix, port_number),
        daemon=True
    )
    # start() 启动线程（开始执行 osc_server_thread 函数）
    osc_thread.start()

    # ---- 第3步：显示开始界面 ----
    # 玩家看到标题画面，点击/按键后进入下一步
    show_start_screen()

    # ---- 第4步：角色选择界面 ----
    # 玩家通过脑电信号（眨眼/咬牙）或键盘（1/2）选择角色
    # 返回选中的角色图片文件路径
    selected_path = show_character_select_screen()

    # 加载选中的角色图片，缩放到游戏中的实际大小（50×50）
    char_img = load_image(selected_path, (50, 50))

    # ---- 第5步：进入主游戏 ----
    # 传入选中的角色图片，开始游戏循环
    main(char_img)

    # ---- 第6步：清理退出 ----
    # 游戏结束后，清理OSC服务器资源
    cleanup()
    # 退出pygame，释放所有pygame分配的资源
    pygame.quit()
