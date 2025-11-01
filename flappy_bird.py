import pygame
import random
import sys
import math
import os

# 初始化pygame
pygame.init()
# 初始化音频系统
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# 游戏常量
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 资源路径
ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')
IMAGES_DIR = os.path.join(ASSETS_DIR, 'images')
SOUNDS_DIR = os.path.join(ASSETS_DIR, 'sounds')

# 资源加载器类
class AssetLoader:
    """资源加载器 - 负责加载外部图片和音乐文件"""
    
    @staticmethod
    def load_image(filename, size=None):
        """
        加载图片文件
        :param filename: 图片文件名（如 'bird.png'）
        :param size: 可选，缩放到指定大小 (width, height)
        :return: pygame.Surface 或 None（如果文件不存在）
        """
        filepath = os.path.join(IMAGES_DIR, filename)
        try:
            image = pygame.image.load(filepath).convert_alpha()
            if size:
                image = pygame.transform.scale(image, size)
            print(f"[OK] 加载图片: {filename}")
            return image
        except (pygame.error, FileNotFoundError) as e:
            print(f"[INFO] 未找到图片文件: {filename}，将使用程序绘制")
            return None
    
    @staticmethod
    def load_music(filename):
        """
        加载背景音乐文件
        :param filename: 音乐文件名（如 'background.mp3', 'background.ogg', 'background.wav'）
        :return: True 表示成功加载，False 表示失败
        """
        # 尝试多种音频格式
        for ext in ['.mp3', '.ogg', '.wav', '.m4a']:
            name_without_ext = os.path.splitext(filename)[0]
            filepath = os.path.join(SOUNDS_DIR, name_without_ext + ext)
            if os.path.exists(filepath):
                try:
                    pygame.mixer.music.load(filepath)
                    print(f"[OK] 加载背景音乐: {name_without_ext}{ext}")
                    return True
                except pygame.error as e:
                    print(f"[ERROR] 音乐文件加载失败: {e}")
                    continue
        
        print(f"[INFO] 未找到音乐文件: {filename}，将使用程序合成音乐")
        return False

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
SKY_BLUE = (135, 206, 235)
DARK_GREEN = (0, 150, 0)
GRAY = (128, 128, 128)

# 难度设置
DIFFICULTY_SETTINGS = {
    "简单": {
        "pipe_speed": 1.5,  # 更慢的速度
        "pipe_gap": 200,    # 更大的间距
        "pipe_spawn_interval": 150,  # 更长的间隔
        "gravity": 0.5,     # 更轻的重力
        "jump_strength": -8,  # 更小的跳跃力度
        "has_moving_pipes": False,  # 没有移动管道
        "has_powerups": False,      # 没有道具
        "has_obstacles": False      # 没有额外障碍物
    },
    "中等": {
        "pipe_speed": 3,
        "pipe_gap": 200,    # 与简单模式相同的间距
        "pipe_spawn_interval": 90,
        "gravity": 0.8,
        "jump_strength": -12,
        "has_moving_pipes": True,   # 有移动管道
        "has_powerups": True,       # 有道具
        "has_obstacles": True       # 有额外障碍物
    },
    "难": {
        "pipe_speed": 4.5,  # 比中等版更快
        "pipe_gap": 130,    # 更小的间距
        "pipe_spawn_interval": 70,  # 更短的间隔
        "gravity": 1.0,
        "jump_strength": -14,
        "has_moving_pipes": True,   # 有移动管道
        "has_powerups": True,       # 有道具
        "has_obstacles": True       # 有额外障碍物
    }
}

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.music_volume = 0.3
        self.sound_volume = 0.5
        self.music_enabled = True
        self.sound_enabled = True
        self.using_external_music = False
        
        # 尝试加载外部背景音乐
        if AssetLoader.load_music('background'):
            self.using_external_music = True
        
        # 创建简单的音效（使用pygame的合成音效）
        self.create_sounds()
        
    def create_sounds(self):
        """创建改进的音效 - 使用numpy生成"""
        try:
            import numpy as np
            
            # 跳跃音效 - 清脆的上升音调
            jump_sound = pygame.sndarray.make_sound(
                self.generate_chord([440, 554, 659], 0.15, 'sine')
            )
            self.sounds['jump'] = jump_sound
            
            # 得分音效 - 愉快的上升音阶
            score_sound = pygame.sndarray.make_sound(
                self.generate_melody([523, 659, 784, 1047], 0.3, 'sine')
            )
            self.sounds['score'] = score_sound
            
            # 碰撞音效 - 低沉的下降音调
            crash_sound = pygame.sndarray.make_sound(
                self.generate_tone(220, 0.4, 'sawtooth', decay=True)
            )
            self.sounds['crash'] = crash_sound
            
            # 道具收集音效 - 魔法音效
            powerup_sound = pygame.sndarray.make_sound(
                self.generate_chord([659, 784, 988], 0.2, 'sine', vibrato=True)
            )
            self.sounds['powerup'] = powerup_sound
            
            # 菜单选择音效
            menu_select = pygame.sndarray.make_sound(
                self.generate_tone(330, 0.1, 'sine')
            )
            self.sounds['menu_select'] = menu_select
            
            # 菜单确认音效
            menu_confirm = pygame.sndarray.make_sound(
                self.generate_chord([440, 554], 0.15, 'sine')
            )
            self.sounds['menu_confirm'] = menu_confirm
            
            # 背景音乐 - 简单的循环旋律
            background_music = pygame.sndarray.make_sound(
                self.generate_background_music()
            )
            self.sounds['background'] = background_music
            
            # 倒计时音效 - 清脆的提示音
            countdown_sound = pygame.sndarray.make_sound(
                self.generate_tone(800, 0.15, 'sine', decay=False)
            )
            self.sounds['countdown'] = countdown_sound
            
            print("[OK] 所有音效创建成功")
            
        except ImportError:
            print("[ERROR] numpy未安装，音效系统无法工作")
            print("请运行: pip install numpy")
            # 如果numpy未安装，创建空的音效
            self.sounds = {key: None for key in ['jump', 'score', 'crash', 'powerup', 'menu_select', 'menu_confirm', 'background', 'countdown']}
        except Exception as e:
            print(f"[ERROR] 音效创建失败: {e}")
            # 如果音效创建失败，创建空的音效
            self.sounds = {key: None for key in ['jump', 'score', 'crash', 'powerup', 'menu_select', 'menu_confirm', 'background']}
    
    def generate_tone(self, frequency, duration, wave_type='sine', decay=True, vibrato=False):
        """生成改进的音调"""
        import numpy as np
        
        sample_rate = 22050
        frames = int(duration * sample_rate)
        
        # 使用numpy创建数组
        arr = np.zeros((frames, 2), dtype=np.int16)
        
        for i in range(frames):
            time = float(i) / sample_rate
            
            # 颤音效果
            freq_mod = frequency
            if vibrato:
                freq_mod = frequency * (1 + 0.1 * math.sin(time * 20))
            
            if wave_type == 'sine':
                wave = math.sin(freq_mod * 2 * math.pi * time)
            elif wave_type == 'sawtooth':
                wave = 2 * (time * freq_mod - math.floor(time * freq_mod + 0.5))
            else:
                wave = math.sin(freq_mod * 2 * math.pi * time)
            
            # 添加衰减效果
            if decay:
                envelope = 1.0 - (i / frames)
                wave *= envelope
            
            # 转换为16位整数
            sample = int(wave * 32767)
            arr[i] = [sample, sample]
        
        return arr
    
    def generate_chord(self, frequencies, duration, wave_type='sine', vibrato=False):
        """生成和弦音效"""
        import numpy as np
        
        sample_rate = 22050
        frames = int(duration * sample_rate)
        arr = np.zeros((frames, 2), dtype=np.int16)
        
        for i in range(frames):
            time = float(i) / sample_rate
            wave = 0
            
            for freq in frequencies:
                if wave_type == 'sine':
                    wave += math.sin(freq * 2 * math.pi * time) / len(frequencies)
                elif wave_type == 'sawtooth':
                    wave += (2 * (time * freq - math.floor(time * freq + 0.5))) / len(frequencies)
            
            # 添加衰减效果
            envelope = 1.0 - (i / frames)
            wave *= envelope
            
            sample = int(wave * 32767)
            arr[i] = [sample, sample]
        
        return arr
    
    def generate_melody(self, frequencies, duration, wave_type='sine'):
        """生成旋律音效"""
        import numpy as np
        
        sample_rate = 22050
        frames = int(duration * sample_rate)
        arr = np.zeros((frames, 2), dtype=np.int16)
        note_duration = duration / len(frequencies)
        
        for i in range(frames):
            time = float(i) / sample_rate
            note_index = int(time / note_duration)
            
            if note_index >= len(frequencies):
                note_index = len(frequencies) - 1
            
            freq = frequencies[note_index]
            
            if wave_type == 'sine':
                wave = math.sin(freq * 2 * math.pi * time)
            elif wave_type == 'sawtooth':
                wave = 2 * (time * freq - math.floor(time * freq + 0.5))
            
            # 添加衰减效果
            envelope = 1.0 - (i / frames)
            wave *= envelope
            
            sample = int(wave * 32767)
            arr[i] = [sample, sample]
        
        return arr
    
    def generate_background_music(self):
        """生成背景音乐 - 轻快愉悦的旋律"""
        import numpy as np
        
        sample_rate = 22050
        duration = 16.0  # 16秒循环
        frames = int(duration * sample_rate)
        arr = np.zeros((frames, 2), dtype=np.int16)
        
        # 更柔和愉悦的旋律 - C大调五声音阶（去掉半音，更和谐）
        # 五声音阶：C D E G A (523, 587, 659, 784, 880)
        melody = [
            523, 659, 784, 880,  # C E G A - 上升
            784, 659, 523, 659,  # G E C E - 下降回旋
            587, 784, 880, 784,  # D G A G - 转调
            659, 523, 587, 523,  # E C D C - 结束
            
            659, 784, 880, 1047, # E G A C' - 上升到高音
            880, 784, 659, 784,  # A G E G - 高音回旋
            523, 659, 784, 659,  # C E G E - 回到开始
            587, 523, 659, 523   # D C E C - 温和结束
        ]
        
        # 每个音符的时长（秒）
        note_duration = duration / len(melody)
        
        for i in range(frames):
            time = float(i) / sample_rate
            # 计算当前应该播放哪个音符
            note_index = int(time / note_duration) % len(melody)
            freq = melody[note_index]
            
            # 计算音符内的相对时间（用于包络）
            note_time = (time % note_duration) / note_duration
            
            # 柔和的ADSR包络
            if note_time < 0.15:  # Attack - 更柔和的起音
                envelope = (note_time / 0.15) * 0.7
            elif note_time < 0.75:  # Sustain - 保持
                envelope = 0.7
            else:  # Release - 渐弱
                envelope = 0.7 * (1 - (note_time - 0.75) / 0.25)
            
            # 主旋律 - 使用纯净的正弦波，音量降低
            wave = math.sin(freq * 2 * math.pi * time) * envelope * 0.08
            
            # 添加柔和的三度和声
            wave += math.sin(freq * 1.25 * 2 * math.pi * time) * envelope * 0.04
            
            # 添加低音衬托（降低音量）
            wave += math.sin(freq * 0.5 * 2 * math.pi * time) * envelope * 0.03
            
            # 添加一点点颤音效果让声音更生动
            vibrato = 1 + 0.015 * math.sin(5 * 2 * math.pi * time)
            wave *= vibrato
            
            sample = int(wave * 32767)
            arr[i] = [sample, sample]
        
        return arr
    
    def play_sound(self, sound_name):
        """播放音效"""
        if self.sound_enabled and sound_name in self.sounds and self.sounds[sound_name]:
            try:
                self.sounds[sound_name].set_volume(self.sound_volume)
                self.sounds[sound_name].play()
            except Exception as e:
                pass
    
    def set_sound_volume(self, volume):
        """设置音效音量"""
        self.sound_volume = max(0.0, min(1.0, volume))
    
    def set_music_volume(self, volume):
        """设置音乐音量"""
        self.music_volume = max(0.0, min(1.0, volume))
    
    def toggle_sound(self):
        """切换音效开关"""
        self.sound_enabled = not self.sound_enabled
    
    def toggle_music(self):
        """切换音乐开关"""
        self.music_enabled = not self.music_enabled
    
    def play_background_music(self):
        """播放背景音乐"""
        if not self.music_enabled:
            return
        
        # 如果使用外部音乐文件
        if self.using_external_music:
            try:
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1)  # -1表示循环播放
            except Exception as e:
                print(f"[ERROR] 播放外部音乐失败: {e}")
        # 否则使用合成音乐
        elif 'background' in self.sounds and self.sounds['background']:
            try:
                self.sounds['background'].set_volume(self.music_volume)
                self.sounds['background'].play(-1)  # -1表示循环播放
            except Exception as e:
                pass
    
    def stop_background_music(self):
        """停止背景音乐"""
        # 停止外部音乐
        if self.using_external_music:
            try:
                pygame.mixer.music.stop()
            except:
                pass
        # 停止合成音乐
        elif 'background' in self.sounds and self.sounds['background']:
            try:
                self.sounds['background'].stop()
            except:
                pass

class Particle:
    def __init__(self, x, y, color, velocity_x=0, velocity_y=0, life=30):
        self.x = x
        self.y = y
        self.color = color
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.life = life
        self.max_life = life
        self.size = random.randint(2, 5)
    
    def update(self):
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_y += 0.2  # 重力
        self.life -= 1
        
        # 添加一些随机性
        self.velocity_x += random.uniform(-0.5, 0.5)
    
    def draw(self, screen):
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            size = int(self.size * (self.life / self.max_life))
            if size > 0:
                pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def add_explosion(self, x, y, color=YELLOW, count=10):
        """添加爆炸粒子效果"""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            velocity_x = math.cos(angle) * speed
            velocity_y = math.sin(angle) * speed
            particle = Particle(x, y, color, velocity_x, velocity_y)
            self.particles.append(particle)
    
    def add_trail(self, x, y, color=WHITE, count=3):
        """添加轨迹粒子效果"""
        for _ in range(count):
            velocity_x = random.uniform(-1, 1)
            velocity_y = random.uniform(-2, 2)
            particle = Particle(x, y, color, velocity_x, velocity_y, life=15)
            self.particles.append(particle)
    
    def update(self):
        self.particles = [p for p in self.particles if p.life > 0]
        for particle in self.particles:
            particle.update()
    
    def draw(self, screen):
        for particle in self.particles:
            particle.draw(screen)

class Bird:
    def __init__(self, x, y, difficulty="中等", bird_image=None):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.velocity = 0
        
        # 根据难度调整参数
        settings = DIFFICULTY_SETTINGS[difficulty]
        self.gravity = settings["gravity"]
        self.jump_strength = settings["jump_strength"]
        
        self.rotation = 0
        self.max_rotation = 25
        self.wing_animation = 0
        self.wing_speed = 0.5  # 从0.3增加到0.5，让翅膀扇动更快
        
        # 使用缓存的小鸟图片（如果提供）
        self.bird_image = bird_image
        self.use_custom_image = self.bird_image is not None
        
    def jump(self):
        """小鸟跳跃"""
        self.velocity = self.jump_strength
        
    def update(self):
        """更新小鸟位置和物理"""
        # 应用重力
        self.velocity += self.gravity
        self.y += self.velocity
        
        # 翅膀动画
        self.wing_animation += self.wing_speed
        
        # 根据速度调整旋转角度
        if self.velocity < 0:  # 向上飞
            self.rotation = min(self.max_rotation, -self.velocity * 2)
        else:  # 向下落
            self.rotation = max(-self.max_rotation, -self.velocity * 2)
            
    def draw(self, screen):
        """绘制更生动的小鸟"""
        center_x = self.x + self.width//2
        center_y = self.y + self.height//2
        
        # 如果有自定义图片，使用图片
        if self.use_custom_image:
            # 旋转图片
            rotated_bird = pygame.transform.rotate(self.bird_image, self.rotation)
            rotated_rect = rotated_bird.get_rect(center=(center_x, center_y))
            screen.blit(rotated_bird, rotated_rect)
            return
        
        # 否则使用程序绘制
        # 创建一个临时surface用于旋转
        bird_surface = pygame.Surface((self.width * 2, self.height * 2), pygame.SRCALPHA)
        temp_center = self.width
        
        # 绘制小鸟身体（圆形）
        # 外层阴影
        pygame.draw.circle(bird_surface, (200, 200, 0), (temp_center, temp_center), self.width//2 + 2)
        # 主体 - 黄色
        pygame.draw.circle(bird_surface, (255, 220, 0), (temp_center, temp_center), self.width//2)
        # 高光
        pygame.draw.circle(bird_surface, (255, 255, 150), (temp_center - 4, temp_center - 4), self.width//4)
        
        # 绘制翅膀动画（更生动的扇动效果）
        # 增强动画幅度，让翅膀扇动更明显
        wing_phase = math.sin(self.wing_animation * 1.5)  # 加快翅膀扇动频率
        wing_offset = int(wing_phase * 15)  # 增加翅膀上下摆动的幅度
        wing_scale = 1 + abs(wing_phase) * 0.8  # 翅膀张开更大，更明显
        
        # 翅膀角度变化，让扇动更真实
        wing_angle_offset = wing_phase * 0.3  # 翅膀角度随动画变化
        
        # 翅膀（左侧）- 放在身体的侧边中部
        # 翅膀的起始点应该在身体的中间位置
        wing_start_x = temp_center - 8  # 翅膀起始X位置（在身体左侧）
        wing_start_y = temp_center - 2  # 翅膀起始Y位置（在身体中部，更协调）
        
        wing_points = [
            (wing_start_x, wing_start_y + wing_offset),
            (wing_start_x - int(15 * wing_scale), wing_start_y - 4 + wing_offset + int(wing_angle_offset * 6)),  # 翅膀上部向前（更短）
            (wing_start_x - int(16 * wing_scale), wing_start_y + 6 + wing_offset),  # 翅膀下部（更短）
            (wing_start_x - 4, wing_start_y + 4 + wing_offset)
        ]
        # 翅膀阴影
        shadow_points = [(p[0] + 1, p[1] + 1) for p in wing_points]
        pygame.draw.polygon(bird_surface, (180, 100, 0), shadow_points)
        # 翅膀主体 - 颜色随动画变化，模拟光照效果
        wing_brightness = int(140 + abs(wing_phase) * 30)
        pygame.draw.polygon(bird_surface, (255, wing_brightness, 0), wing_points)
        
        # 绘制翅膀羽毛细节（让翅膀更生动）
        if abs(wing_phase) > 0.5:  # 翅膀张开时显示羽毛
            feather_color = (230, wing_brightness - 20, 0)
            # 羽毛线条从翅膀起始点出发（调整长度匹配短翅膀）
            pygame.draw.line(bird_surface, feather_color,
                           (wing_start_x - 3, wing_start_y + wing_offset),
                           (wing_start_x - int(13 * wing_scale), wing_start_y - 2 + wing_offset + int(wing_angle_offset * 6)), 2)
            # 再添加一条羽毛线，让翅膀更丰富（调整长度）
            pygame.draw.line(bird_surface, feather_color,
                           (wing_start_x - 4, wing_start_y + 2 + wing_offset),
                           (wing_start_x - int(14 * wing_scale), wing_start_y + 4 + wing_offset), 2)
        
        # 绘制小鸟肚子（白色）
        pygame.draw.ellipse(bird_surface, (255, 255, 255), 
                           (temp_center - 6, temp_center + 2, 12, 10))
        
        # 绘制小鸟眼睛（合适的大小，更协调）
        eye_radius = 4
        # 眼白
        pygame.draw.circle(bird_surface, WHITE, (temp_center + 6, temp_center - 6), eye_radius)
        # 瞳孔（根据速度方向略微移动）
        pupil_offset_y = -1 if self.velocity < 0 else 1
        pygame.draw.circle(bird_surface, BLACK, (temp_center + 7, temp_center - 5 + pupil_offset_y), 2)
        # 高光
        pygame.draw.circle(bird_surface, WHITE, (temp_center + 7.5, temp_center - 6 + pupil_offset_y), 1)
        
        # 绘制腮红（浅粉色，更自然的颜色）
        blush_color = (255, 200, 200, 100)  # 浅粉色，半透明
        # 左脸颊
        blush_surface = pygame.Surface((8, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(blush_surface, blush_color, (0, 0, 8, 6))
        bird_surface.blit(blush_surface, (temp_center - 12, temp_center))
        # 右脸颊
        bird_surface.blit(blush_surface, (temp_center - 6, temp_center))
        
        # 绘制小鸟嘴巴（更立体，稍微小一点）
        beak_points = [
            (temp_center + 10, temp_center + 1),
            (temp_center + 15, temp_center - 1),
            (temp_center + 15, temp_center + 3)
        ]
        # 嘴巴阴影
        shadow_beak = [(p[0] + 1, p[1] + 1) for p in beak_points]
        pygame.draw.polygon(bird_surface, (200, 80, 0), shadow_beak)
        # 嘴巴主体
        pygame.draw.polygon(bird_surface, (255, 140, 0), beak_points)
        
        # 绘制眉毛（增加表情，调整位置）
        eyebrow_start = (temp_center + 2, temp_center - 9)
        eyebrow_end = (temp_center + 9, temp_center - 8)
        pygame.draw.line(bird_surface, (50, 50, 50), eyebrow_start, eyebrow_end, 2)
        
        # 旋转整个小鸟
        rotated_bird = pygame.transform.rotate(bird_surface, self.rotation)
        rotated_rect = rotated_bird.get_rect(center=(center_x, center_y))
        screen.blit(rotated_bird, rotated_rect)
        
    def get_rect(self):
        """获取小鸟的碰撞矩形"""
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Pipe:
    def __init__(self, x, difficulty="中等"):
        self.x = x
        self.width = 60
        
        # 根据难度调整参数
        settings = DIFFICULTY_SETTINGS[difficulty]
        self.gap = settings["pipe_gap"]
        self.speed = settings["pipe_speed"]
        
        # 随机生成管道高度
        self.top_height = random.randint(50, SCREEN_HEIGHT - self.gap - 50)
        self.bottom_y = self.top_height + self.gap
        
    def update(self):
        """更新管道位置"""
        self.x -= self.speed
        
    def draw(self, screen):
        """绘制美化的管道"""
        # 绘制上管道 - 添加渐变和阴影效果
        top_pipe = pygame.Rect(self.x, 0, self.width, self.top_height)
        
        # 管道主体渐变
        for i in range(self.width):
            alpha = int(255 * (1 - i / self.width * 0.3))
            color = (0, int(200 - i * 0.5), 0)
            pygame.draw.line(screen, color, 
                           (self.x + i, 0), (self.x + i, self.top_height))
        
        # 管道边框
        pygame.draw.rect(screen, DARK_GREEN, top_pipe, 3)
        
        # 管道顶部装饰
        pygame.draw.rect(screen, DARK_GREEN, 
                        (self.x - 5, self.top_height - 20, self.width + 10, 20))
        
        # 绘制下管道
        bottom_pipe = pygame.Rect(self.x, self.bottom_y, self.width, 
                                 SCREEN_HEIGHT - self.bottom_y)
        
        # 管道主体渐变
        for i in range(self.width):
            alpha = int(255 * (1 - i / self.width * 0.3))
            color = (0, int(200 - i * 0.5), 0)
            pygame.draw.line(screen, color, 
                           (self.x + i, self.bottom_y), 
                           (self.x + i, SCREEN_HEIGHT))
        
        # 管道边框
        pygame.draw.rect(screen, DARK_GREEN, bottom_pipe, 3)
        
        # 管道底部装饰
        pygame.draw.rect(screen, DARK_GREEN, 
                        (self.x - 5, self.bottom_y, self.width + 10, 20))
        
    def get_rects(self):
        """获取管道的碰撞矩形"""
        top_rect = pygame.Rect(self.x, 0, self.width, self.top_height)
        bottom_rect = pygame.Rect(self.x, self.bottom_y, self.width, 
                                SCREEN_HEIGHT - self.bottom_y)
        return top_rect, bottom_rect
        
    def is_off_screen(self):
        """检查管道是否离开屏幕"""
        return self.x + self.width < 0
        
    def is_passed(self, bird_x):
        """检查小鸟是否已经通过管道"""
        return bird_x > self.x + self.width

class Background:
    def __init__(self):
        # 尝试加载外部背景图片
        self.background_image = AssetLoader.load_image('background.png', (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.use_custom_background = self.background_image is not None
        
        # 背景滚动相关
        self.bg_scroll_x = 0  # 背景滚动位置
        self.bg_scroll_speed = 0.5  # 背景滚动速度（慢速，营造远景感）
        
        # 动态元素
        self.sun_y = 100  # 太阳的Y位置
        self.sun_direction = 0.1  # 太阳移动方向
        
        # 远景飞鸟
        self.distant_birds = []
        for i in range(3):
            self.distant_birds.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(80, 200),
                'speed': random.uniform(0.3, 0.8),
                'wing_phase': random.uniform(0, 6.28)
            })
        
        self.clouds = []
        self.cloud_speed = 1
        
        # 生成初始云朵（速度更慢）
        for i in range(5):
            cloud = {
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(50, SCREEN_HEIGHT // 2),
                'size': random.randint(25, 45),
                'speed': random.uniform(0.2, 0.6),  # 初始速度更慢
                'puffiness': random.uniform(0.8, 1.2),  # 云朵蓬松度
                'wobble': random.uniform(0, 6.28),  # 云朵摆动相位
                'alpha': random.randint(220, 245)  # 云朵透明度
            }
            self.clouds.append(cloud)
        
        # 草叶摇摆动画变量
        self.grass_wave = 0  # 草叶摇摆相位
        
        # 预先生成草叶数据（只在初始化时生成一次，避免每帧重新随机）
        self.grass_blades = []
        grass_base_y = SCREEN_HEIGHT - 80
        # 生成适度密集的草叶（减少数量以提高性能，降低卡顿）
        for x in range(0, SCREEN_WIDTH, 10):  # 每10像素一根，减少数量以提高性能
            # 为每根草预生成偏移值，避免绘制时使用random
            x_offset = random.randint(-2, 2)
            x_offset2 = random.randint(-1, 1)
            height_offset = random.randint(-2, 2)
            angle_offset = random.uniform(-0.1, 0.1)
            
            blade = {
                'x': x + x_offset,
                'base_y': grass_base_y,
                'height': random.randint(18, 35),
                'angle': random.uniform(-0.3, 0.3),  # 倾斜角度
                'color': (100 + random.randint(-15, 15), 180 + random.randint(-15, 15), 100 + random.randint(-15, 15)),
                'has_branch': random.random() < 0.25,  # 25%的草叶有分叉
                'x_offset2': x_offset2,  # 预生成第二根草的偏移
                'height_offset': height_offset,  # 预生成高度偏移
                'angle_offset': angle_offset  # 预生成角度偏移
            }
            self.grass_blades.append(blade)
    
    def update(self):
        """更新背景"""
        # 更新背景滚动位置（用于自定义背景图片）
        self.bg_scroll_x -= self.bg_scroll_speed * 1.5  # 加快背景滚动速度，让动态更明显
        # 当滚动超过一个屏幕宽度时重置，实现无限循环
        if self.bg_scroll_x <= -SCREEN_WIDTH:
            self.bg_scroll_x = 0
        
        # 更新太阳位置（缓慢上下移动）
        self.sun_y += self.sun_direction
        if self.sun_y < 80 or self.sun_y > 120:
            self.sun_direction *= -1
        
        # 更新远景飞鸟
        for bird in self.distant_birds:
            bird['x'] -= bird['speed']
            bird['wing_phase'] += 0.15
            if bird['x'] < -50:
                bird['x'] = SCREEN_WIDTH + 50
                bird['y'] = random.randint(80, 200)
        
        # 更新云朵位置（所有云朵都要动起来，但速度更慢）
        for cloud in self.clouds:
            # 横向移动（速度减慢）
            cloud['x'] -= cloud['speed'] * 0.5  # 云朵速度减慢，更自然
            # 添加轻微的上下飘动（幅度更大，更明显）
            cloud['wobble'] += 0.04  # 减慢上下飘动频率
            # 确保wobble值在合理范围内
            if cloud['wobble'] > 6.28:
                cloud['wobble'] -= 6.28
            
            # 如果云朵离开屏幕，重新生成
            if cloud['x'] + cloud['size'] * 2 < 0:
                cloud['x'] = SCREEN_WIDTH + cloud['size']
                cloud['y'] = random.randint(50, SCREEN_HEIGHT // 2)
                cloud['size'] = random.randint(25, 45)
                cloud['speed'] = random.uniform(0.2, 0.6)  # 速度范围减小
                cloud['puffiness'] = random.uniform(0.8, 1.2)
                cloud['wobble'] = random.uniform(0, 6.28)
                cloud['alpha'] = random.randint(220, 245)
        
        # 更新草叶摇摆动画（适中的速度）
        self.grass_wave += 0.1  # 适中的摆动速度
        if self.grass_wave > 6.28:
            self.grass_wave -= 6.28
    
    def draw(self, screen):
        """绘制渐变背景和云朵"""
        # 如果有自定义背景图片，实现滚动效果
        if self.use_custom_background:
            # 绘制两份背景图片实现无缝循环滚动
            screen.blit(self.background_image, (self.bg_scroll_x, 0))
            screen.blit(self.background_image, (self.bg_scroll_x + SCREEN_WIDTH, 0))
            return  # 使用自定义背景时不绘制云朵
        
        # 否则绘制默认的天空渐变（带呼吸效果，优化性能）
        time_cycle = pygame.time.get_ticks() / 5000.0  # 5秒一个周期
        sky_brightness = math.sin(time_cycle) * 5  # 天空明暗变化
        
        # 使用较大的步长绘制渐变，提高性能
        for y in range(0, SCREEN_HEIGHT, 2):  # 每2像素一行，减少绘制次数
            # 从明亮的天空蓝到浅蓝的渐变，带呼吸效果（更明亮）
            ratio = y / SCREEN_HEIGHT
            r = int(160 + (200 - 160) * ratio + sky_brightness)  # 更亮的红色
            g = int(220 + (235 - 220) * ratio + sky_brightness)  # 更亮的绿色
            b = int(255 + (255 - 255) * ratio + sky_brightness)  # 最亮的蓝色
            # 确保颜色值在有效范围内
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            color = (r, g, b)
            pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))
        
        # 绘制太阳（带光晕效果）
        sun_x = SCREEN_WIDTH - 100
        sun_radius = 30
        # 光晕（多层）
        for i in range(3):
            glow_radius = sun_radius + (i + 1) * 10
            glow_alpha = 30 - i * 8
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (255, 255, 150, glow_alpha), 
                             (glow_radius, glow_radius), glow_radius)
            screen.blit(glow_surface, (sun_x - glow_radius, int(self.sun_y) - glow_radius))
        # 太阳主体
        pygame.draw.circle(screen, (255, 255, 100), (sun_x, int(self.sun_y)), sun_radius)
        pygame.draw.circle(screen, (255, 255, 200), (sun_x - 5, int(self.sun_y) - 5), sun_radius // 3)  # 高光
        
        # 先绘制远景飞鸟（小剪影）和云朵（在后面）
        for bird in self.distant_birds:
            bird_x = int(bird['x'])
            bird_y = int(bird['y'])
            wing_offset = int(math.sin(bird['wing_phase']) * 3)
            
            # 简单的V字形飞鸟
            bird_color = (80, 80, 100, 150)  # 半透明的暗色
            bird_surface = pygame.Surface((15, 8), pygame.SRCALPHA)
            # 左翅膀
            pygame.draw.line(bird_surface, bird_color, (7, 4), (2, 1 + wing_offset), 2)
            # 右翅膀
            pygame.draw.line(bird_surface, bird_color, (7, 4), (12, 1 + wing_offset), 2)
            screen.blit(bird_surface, (bird_x, bird_y))
        
        # 绘制云朵（在天空图层）
        for cloud in self.clouds:
            # 绘制更真实生动的云朵
            center_x = int(cloud['x'])
            center_y = int(cloud['y'] + math.sin(cloud['wobble']) * 5)  # 增加上下飘动幅度
            size = cloud['size']
            puff = cloud['puffiness']
            
            # 创建一个透明的surface来绘制云朵
            cloud_surface = pygame.Surface((size * 3, size * 2), pygame.SRCALPHA)
            
            # 云朵底部阴影（柔和的灰色）
            shadow_color = (210, 210, 220, cloud['alpha'] - 50)
            pygame.draw.ellipse(cloud_surface, shadow_color, 
                              (size//4, int(size * 1.3), int(size * 2.5), size//3))
            
            # 云朵主体 - 简化版本，减少圆形数量以提高性能
            # 中央大圆
            pygame.draw.circle(cloud_surface, (255, 255, 255, cloud['alpha']), 
                             (int(size * 1.2), size), int(size * puff))
            
            # 左侧（减少细节）
            pygame.draw.circle(cloud_surface, (255, 255, 255, cloud['alpha']), 
                             (int(size * 0.7), int(size * 1.1)), int(size * 0.7 * puff))
            
            # 右侧（减少细节）
            pygame.draw.circle(cloud_surface, (255, 255, 255, cloud['alpha']), 
                             (int(size * 1.8), int(size * 1.05)), int(size * 0.8 * puff))
            
            # 顶部
            pygame.draw.circle(cloud_surface, (255, 255, 255, cloud['alpha']), 
                             (int(size * 1.1), int(size * 0.7)), int(size * 0.6 * puff))
            
            # 将云朵绘制到屏幕上
            screen.blit(cloud_surface, (center_x - size, center_y - size))
        
        # 绘制草地（更浅更明亮的绿色，优化性能）
        grass_height = 80
        grass_start_y = SCREEN_HEIGHT - grass_height
        for y in range(grass_start_y, SCREEN_HEIGHT, 2):  # 每2像素一行
            # 从浅绿到较深的绿的渐变（更明亮）
            ratio = (y - grass_start_y) / grass_height
            r = int(140 + (80 - 140) * ratio)  # 更亮的红色
            g = int(220 + (180 - 220) * ratio)  # 更亮的绿色
            b = int(140 + (80 - 140) * ratio)  # 更亮的蓝色
            color = (r, g, b)
            pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))
        
        # 绘制草地上的草叶（使用预生成数据，添加微弱的摇摆动画）
        grass_base_y = SCREEN_HEIGHT - grass_height
        
        # 计算微弱的摇摆动画（使用正弦波模拟微风）
        wave_offset = math.sin(self.grass_wave) * 0.3  # 极其轻微的摇摆，几乎静止
        
        # 使用预生成的草叶数据绘制
        for blade in self.grass_blades:
            # 根据草叶位置计算摇摆幅度（远处的草摇摆更明显）
            grass_x_pos = blade['x'] / SCREEN_WIDTH
            local_wave = wave_offset * (0.7 + grass_x_pos * 0.3)  # 渐变摇摆效果
            
            # 计算草叶顶端位置（加上摇摆）
            tip_x = blade['x'] + blade['angle'] * blade['height'] + local_wave * (1 + blade['height'] / 30)
            tip_y = blade['base_y'] - blade['height']
            
            # 绘制主草叶（单根草，提高性能）
            pygame.draw.line(screen, blade['color'], 
                           (blade['x'], blade['base_y']), (tip_x, tip_y), 2)
        
        # 绘制小花（草地上的装饰）
        # 使用系统的云朵wobble来同步花朵的轻微摆动
        flower_time = pygame.time.get_ticks() / 500.0
        for i in range(8):  # 8朵花
            flower_x = (i * 100 + 50) % SCREEN_WIDTH
            flower_y = SCREEN_HEIGHT - grass_height - 5 + int(math.sin(flower_time * 2 + i) * 2)
            
            # 花茎
            pygame.draw.line(screen, (50, 150, 50), 
                           (flower_x, SCREEN_HEIGHT - grass_height),
                           (flower_x, flower_y), 2)
            
            # 花朵（不同颜色）
            flower_colors = [(255, 182, 193), (255, 20, 147), (255, 255, 0), (255, 165, 0)]
            flower_color = flower_colors[i % len(flower_colors)]
            
            # 花瓣
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                petal_x = flower_x + int(math.cos(rad) * 5)
                petal_y = flower_y + int(math.sin(rad) * 5)
                pygame.draw.circle(screen, flower_color, (petal_x, petal_y), 3)
            
            # 花心
            pygame.draw.circle(screen, (255, 200, 0), (flower_x, flower_y), 3)

class PowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.speed = 3
        self.type = random.choice(['shield', 'slow_motion', 'double_score'])
        self.collected = False
        self.animation = 0
        self.glow_intensity = 0
        
    def update(self):
        """更新道具位置和动画"""
        self.x -= self.speed
        self.animation += 0.2
        self.glow_intensity = math.sin(self.animation) * 0.5 + 0.5
        
    def draw(self, screen):
        """绘制美化的道具"""
        center_x = int(self.x)
        center_y = int(self.y)
        
        if self.type == 'shield':
            base_color = BLUE
        elif self.type == 'slow_motion':
            base_color = YELLOW
        else:  # double_score
            base_color = RED
            
        # 发光效果
        glow_radius = int(15 + self.glow_intensity * 5)
        glow_color = tuple(int(c * 0.3) for c in base_color)
        pygame.draw.circle(screen, glow_color, (center_x, center_y), glow_radius)
        
        # 道具主体
        pygame.draw.circle(screen, base_color, (center_x, center_y), self.width//2)
        pygame.draw.circle(screen, BLACK, (center_x, center_y), self.width//2, 2)
        
        # 内部装饰
        inner_color = tuple(min(255, c + 50) for c in base_color)
        pygame.draw.circle(screen, inner_color, (center_x, center_y), self.width//3)
        
    def get_rect(self):
        """获取道具的碰撞矩形"""
        return pygame.Rect(self.x - self.width//2, self.y - self.height//2, 
                          self.width, self.height)
        
    def is_off_screen(self):
        """检查道具是否离开屏幕"""
        return self.x + self.width < 0

class MovingPipe(Pipe):
    def __init__(self, x, difficulty="中等"):
        super().__init__(x, difficulty)
        self.move_speed = 1
        self.move_direction = 1
        self.move_timer = 0
        
    def update(self):
        """更新移动管道"""
        super().update()
        
        # 上下移动
        self.move_timer += 1
        if self.move_timer >= 30:  # 每30帧改变方向
            self.move_direction *= -1
            self.move_timer = 0
            
        self.top_height += self.move_direction * self.move_speed
        self.bottom_y = self.top_height + self.gap
        
        # 限制移动范围
        if self.top_height < 50:
            self.top_height = 50
            self.move_direction = 1
        elif self.top_height > SCREEN_HEIGHT - self.gap - 50:
            self.top_height = SCREEN_HEIGHT - self.gap - 50
            self.move_direction = -1

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("飞翔的小鸟")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 游戏状态
        self.state = "MENU"  # MENU, PLAYING, GAME_OVER, SETTINGS, DIFFICULTY_SELECT
        self.difficulty = "中等"
        self.paused = False
        
        # 字体 - 使用系统默认字体以支持中文，调整大小
        try:
            # 尝试使用系统字体，调整到合适的大小
            self.font = pygame.font.SysFont('simhei', 28)  # 主字体
            self.big_font = pygame.font.SysFont('simhei', 48)  # 大标题
            self.small_font = pygame.font.SysFont('simhei', 20)  # 小字体
            self.title_font = pygame.font.SysFont('simhei', 36)  # 标题字体
            self.countdown_font = pygame.font.SysFont('simhei', 96)  # 倒计时字体 - 更大更明显
        except:
            # 如果系统字体不可用，使用默认字体
            self.font = pygame.font.Font(None, 28)
            self.big_font = pygame.font.Font(None, 48)
            self.small_font = pygame.font.Font(None, 20)
            self.title_font = pygame.font.Font(None, 36)
            self.countdown_font = pygame.font.Font(None, 96)  # 倒计时字体 - 更大更明显
        
        # 预加载资源（避免游戏开始时卡顿）
        self.bird_image_cache = AssetLoader.load_image('bird.png', (60, 60))  # 预加载小鸟图片
        
        # 游戏对象
        self.bird = None
        self.pipes = []
        self.powerups = []
        self.background = Background()
        self.particle_system = ParticleSystem()
        self.sound_manager = SoundManager()
        
        # 测试音效是否正常工作
        print("=" * 50)
        print("音效系统初始化状态:")
        print(f"音效启用: {self.sound_manager.sound_enabled}")
        print(f"音乐启用: {self.sound_manager.music_enabled}")
        print(f"音效数量: {len(self.sound_manager.sounds)}")
        for sound_name, sound_obj in self.sound_manager.sounds.items():
            status = "[OK]" if sound_obj else "[NO]"
            print(f"  {status} {sound_name}")
        print("=" * 50)
        
        # 预热音频系统（避免第一次播放时卡顿）
        # 播放一个极短的静音来初始化音频通道
        if self.sound_manager.sounds.get('menu_select'):
            temp_volume = self.sound_manager.sound_volume
            self.sound_manager.set_sound_volume(0.0)  # 临时静音
            self.sound_manager.play_sound('menu_select')
            pygame.time.wait(10)  # 等待10毫秒
            self.sound_manager.set_sound_volume(temp_volume)  # 恢复音量
        
        # 游戏数据
        self.score = 0
        self.high_score = 0
        self.pipe_spawn_timer = 0
        self.powerup_spawn_timer = 0
        
        # 难度相关
        settings = DIFFICULTY_SETTINGS[self.difficulty]
        self.pipe_spawn_interval = settings["pipe_spawn_interval"]
        self.powerup_spawn_interval = 300  # 帧数
        
        # 游戏状态
        self.shield_active = False
        self.shield_timer = 0
        self.slow_motion_active = False
        self.slow_motion_timer = 0
        self.double_score_active = False
        self.double_score_timer = 0
        
        # UI状态
        self.menu_selection = 0
        self.settings_selection = 0
        self.difficulty_selection = 0
        self.volume_dragging = False
        
        # 倒计时相关
        self.countdown_timer = 0
        self.countdown_active = False
        self.countdown_text = ""
    
    def draw_text(self, text, font, color, x, y):
        """绘制普通文字"""
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        self.screen.blit(text_surface, text_rect)
        
    def handle_events(self):
        """处理游戏事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == "PLAYING":
                        self.paused = not self.paused
                    elif self.state == "SETTINGS":
                        self.state = "MENU"
                    elif self.state == "DIFFICULTY_SELECT":
                        self.state = "SETTINGS"
                    elif self.state == "GAME_OVER":
                        self.state = "MENU"
                    else:
                        self.running = False
                elif event.key == pygame.K_SPACE:
                    if self.state == "MENU":
                        self.start_game()
                    elif self.state == "PLAYING" and not self.paused:
                        self.bird.jump()
                        self.sound_manager.play_sound('jump')
                    elif self.state == "GAME_OVER":
                        self.start_game()
                elif event.key == pygame.K_RETURN:
                    if self.state == "MENU":
                        self.sound_manager.play_sound('menu_confirm')
                        if self.menu_selection == 0:
                            self.start_game()
                        elif self.menu_selection == 1:
                            self.state = "SETTINGS"
                        elif self.menu_selection == 2:
                            self.running = False
                    elif self.state == "SETTINGS":
                        # 在设置界面按Enter键执行当前选中的操作
                        self.sound_manager.play_sound('menu_confirm')
                        if self.settings_selection == 0:  # 游戏难度
                            self.state = "DIFFICULTY_SELECT"
                        elif self.settings_selection == 2:  # 返回主菜单
                            self.state = "MENU"
                    elif self.state == "DIFFICULTY_SELECT":
                        # 选择难度并直接开始游戏
                        difficulties = list(DIFFICULTY_SETTINGS.keys())
                        self.difficulty = difficulties[self.difficulty_selection]
                        self.sound_manager.play_sound('menu_confirm')
                        self.start_game()
                elif event.key == pygame.K_UP:
                    if self.state == "MENU":
                        self.menu_selection = (self.menu_selection - 1) % 3
                        self.sound_manager.play_sound('menu_select')
                    elif self.state == "SETTINGS":
                        self.settings_selection = (self.settings_selection - 1) % 3
                        self.sound_manager.play_sound('menu_select')
                    elif self.state == "DIFFICULTY_SELECT":
                        self.difficulty_selection = (self.difficulty_selection - 1) % 3
                        self.sound_manager.play_sound('menu_select')
                elif event.key == pygame.K_DOWN:
                    if self.state == "MENU":
                        self.menu_selection = (self.menu_selection + 1) % 3
                        self.sound_manager.play_sound('menu_select')
                    elif self.state == "SETTINGS":
                        self.settings_selection = (self.settings_selection + 1) % 3
                        self.sound_manager.play_sound('menu_select')
                    elif self.state == "DIFFICULTY_SELECT":
                        self.difficulty_selection = (self.difficulty_selection + 1) % 3
                        self.sound_manager.play_sound('menu_select')
                elif event.key == pygame.K_LEFT:
                    if self.state == "SETTINGS" and self.settings_selection == 1:  # 音效音量
                        self.sound_manager.set_sound_volume(
                            max(0, self.sound_manager.sound_volume - 0.1)
                        )
                        self.sound_manager.play_sound('menu_select')
                elif event.key == pygame.K_RIGHT:
                    if self.state == "SETTINGS" and self.settings_selection == 1:  # 音效音量
                        self.sound_manager.set_sound_volume(
                            min(1, self.sound_manager.sound_volume + 0.1)
                        )
                        self.sound_manager.play_sound('menu_select')
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    
                    if self.state == "MENU":
                        # 检查是否点击了菜单选项
                        for i in range(3):
                            y_pos = 200 + i * 80
                            if (SCREEN_WIDTH//2 - 200 <= mouse_x <= SCREEN_WIDTH//2 + 200 and 
                                y_pos - 10 <= mouse_y <= y_pos + 40):
                                self.menu_selection = i
                                self.sound_manager.play_sound('menu_select')
                                if i == 0:  # 开始游戏
                                    self.start_game()
                                elif i == 1:  # 游戏设置
                                    self.state = "SETTINGS"
                                elif i == 2:  # 退出游戏
                                    self.running = False
                                break
                    elif self.state == "PLAYING" and not self.paused:
                        self.bird.jump()
                        self.sound_manager.play_sound('jump')
                    elif self.state == "GAME_OVER":
                        self.start_game()
                    elif self.state == "SETTINGS":
                        # 检查是否点击了左上角返回按钮
                        if (20 <= mouse_x <= 100 and 20 <= mouse_y <= 55):
                            self.sound_manager.play_sound('menu_select')
                            self.state = "MENU"
                        # 检查是否点击了设置选项
                        else:
                            for i in range(3):
                                y_pos = 220 + i * 80  # 与绘制位置一致
                                if (SCREEN_WIDTH//2 - 200 <= mouse_x <= SCREEN_WIDTH//2 + 200 and 
                                    y_pos - 10 <= mouse_y <= y_pos + 40):
                                    self.settings_selection = i
                                    self.sound_manager.play_sound('menu_select')
                                    if i == 0:  # 游戏难度
                                        self.state = "DIFFICULTY_SELECT"
                                    elif i == 2:  # 返回主菜单
                                        self.state = "MENU"
                                    break
                        
                        # 检查是否点击了音量滑块（扩大点击区域）
                        slider_x = SCREEN_WIDTH//2 + 80  # 与绘制位置一致
                        slider_y = 220 + 1 * 80 - 10  # 音量选项的Y位置（i=1的y_pos - 10）
                        slider_width = 200
                        slider_height = 20
                        
                        # 扩大点击区域，让滑块更容易点击
                        if (slider_x - 10 <= mouse_x <= slider_x + slider_width + 10 and 
                            slider_y - 10 <= mouse_y <= slider_y + slider_height + 10):
                            self.volume_dragging = True
                            # 立即设置音量
                            volume = max(0, min(1, (mouse_x - slider_x) / slider_width))
                            self.sound_manager.set_sound_volume(volume)
                    elif self.state == "DIFFICULTY_SELECT":
                        # 检查是否点击了左上角返回按钮
                        if (20 <= mouse_x <= 100 and 20 <= mouse_y <= 55):
                            self.sound_manager.play_sound('menu_select')
                            self.state = "SETTINGS"
                        # 检查是否点击了难度选项
                        else:
                            difficulties = list(DIFFICULTY_SETTINGS.keys())
                            for i, difficulty in enumerate(difficulties):
                                y_pos = 220 + i * 100  # 与绘制位置一致
                                if (SCREEN_WIDTH//2 - 250 <= mouse_x <= SCREEN_WIDTH//2 + 250 and 
                                    y_pos - 15 <= mouse_y <= y_pos + 55):
                                    self.difficulty_selection = i
                                    self.sound_manager.play_sound('menu_select')
                                    self.difficulty = difficulty
                                    self.start_game()
                                    break
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.volume_dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.volume_dragging and self.state == "SETTINGS":
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    slider_x = SCREEN_WIDTH//2 + 80  # 与绘制位置一致
                    slider_width = 200
                    
                    # 计算音量值
                    volume = max(0, min(1, (mouse_x - slider_x) / slider_width))
                    self.sound_manager.set_sound_volume(volume)
                else:
                    # 鼠标悬停效果
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    
                    if self.state == "MENU":
                        for i in range(3):
                            y_pos = 220 + i * 80  # 与绘制位置一致
                            if (SCREEN_WIDTH//2 - 200 <= mouse_x <= SCREEN_WIDTH//2 + 200 and 
                                y_pos - 10 <= mouse_y <= y_pos + 40):
                                if self.menu_selection != i:
                                    self.menu_selection = i
                                    self.sound_manager.play_sound('menu_select')
                                break
                    elif self.state == "SETTINGS":
                        for i in range(3):
                            y_pos = 220 + i * 80  # 与绘制位置一致
                            if (SCREEN_WIDTH//2 - 200 <= mouse_x <= SCREEN_WIDTH//2 + 200 and 
                                y_pos - 10 <= mouse_y <= y_pos + 40):
                                if self.settings_selection != i:
                                    self.settings_selection = i
                                    self.sound_manager.play_sound('menu_select')
                                break
                    elif self.state == "DIFFICULTY_SELECT":
                        difficulties = list(DIFFICULTY_SETTINGS.keys())
                        for i, difficulty in enumerate(difficulties):
                            y_pos = 220 + i * 100  # 与绘制位置一致
                            if (SCREEN_WIDTH//2 - 250 <= mouse_x <= SCREEN_WIDTH//2 + 250 and 
                                y_pos - 15 <= mouse_y <= y_pos + 55):
                                if self.difficulty_selection != i:
                                    self.difficulty_selection = i
                                    self.sound_manager.play_sound('menu_select')
                                break
    
    def start_game(self):
        """开始游戏"""
        self.state = "PLAYING"
        # 传递缓存的图片，避免重复加载
        self.bird = Bird(SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT // 2, self.difficulty, self.bird_image_cache)
        self.pipes = []
        self.powerups = []
        self.score = 0
        self.pipe_spawn_timer = 0
        self.powerup_spawn_timer = 0
        
        # 重置游戏状态
        self.shield_active = False
        self.shield_timer = 0
        self.slow_motion_active = False
        self.slow_motion_timer = 0
        self.double_score_active = False
        self.double_score_timer = 0
        
        # 清空粒子系统（不重新创建对象）
        self.particle_system.particles = []
        
        # 更新难度设置
        settings = DIFFICULTY_SETTINGS[self.difficulty]
        self.pipe_spawn_interval = settings["pipe_spawn_interval"]
        
        # 开始倒计时
        self.countdown_active = True
        self.countdown_timer = 240  # 4秒倒计时（60fps * 4秒）
        self.countdown_text = "3"
        
        # 播放开始音效
        self.sound_manager.play_sound('menu_confirm')
        
        # 播放背景音乐
        self.sound_manager.play_background_music()
    
    def restart_game(self):
        """重新开始游戏"""
        self.state = "MENU"
    
    def update(self):
        """更新游戏逻辑"""
        if self.state == "PLAYING" and self.bird and not self.paused:
            # 处理倒计时
            if self.countdown_active:
                self.countdown_timer -= 1
                if self.countdown_timer <= 0:
                    self.countdown_active = False
                    # 倒计时结束时播放特殊音效
                    self.sound_manager.play_sound('menu_confirm')
                elif self.countdown_timer == 60:  # 刚好1秒时
                    self.countdown_text = "游戏开始"
                    self.sound_manager.play_sound('menu_confirm')
                elif self.countdown_timer == 120:  # 刚好2秒时
                    self.countdown_text = "1"
                    self.sound_manager.play_sound('countdown')
                elif self.countdown_timer == 180:  # 刚好3秒时
                    self.countdown_text = "2"
                    self.sound_manager.play_sound('countdown')
                elif self.countdown_timer == 240:  # 刚好4秒时（显示"3"）
                    self.countdown_text = "3"
                    self.sound_manager.play_sound('countdown')
                return  # 倒计时期间不更新游戏逻辑
            
            self.bird.update()
            self.background.update()
            self.particle_system.update()
            
            # 更新道具效果计时器
            if self.shield_active:
                self.shield_timer -= 1
                if self.shield_timer <= 0:
                    self.shield_active = False
                    
            if self.slow_motion_active:
                self.slow_motion_timer -= 1
                if self.slow_motion_timer <= 0:
                    self.slow_motion_active = False
                    
            if self.double_score_active:
                self.double_score_timer -= 1
                if self.double_score_timer <= 0:
                    self.double_score_active = False
            
            # 生成新管道
            self.pipe_spawn_timer += 1
            if self.pipe_spawn_timer >= self.pipe_spawn_interval:
                settings = DIFFICULTY_SETTINGS[self.difficulty]
                
                # 根据难度设置选择管道类型
                if settings["has_moving_pipes"] and random.random() < 0.4:  # 40%概率生成移动管道
                    self.pipes.append(MovingPipe(SCREEN_WIDTH, self.difficulty))
                else:
                    self.pipes.append(Pipe(SCREEN_WIDTH, self.difficulty))
                self.pipe_spawn_timer = 0
            
            # 生成道具（仅在中等和难模式下）
            settings = DIFFICULTY_SETTINGS[self.difficulty]
            if settings["has_powerups"]:
                self.powerup_spawn_timer += 1
                if self.powerup_spawn_timer >= self.powerup_spawn_interval:
                    y = random.randint(100, SCREEN_HEIGHT - 100)
                    self.powerups.append(PowerUp(SCREEN_WIDTH, y))
                    self.powerup_spawn_timer = 0
            
            # 更新管道
            for pipe in self.pipes[:]:
                if not self.slow_motion_active:
                    pipe.update()
                else:
                    # 慢动作效果：管道移动速度减半
                    pipe.x -= pipe.speed // 2
                
                # 检查碰撞
                bird_rect = self.bird.get_rect()
                top_rect, bottom_rect = pipe.get_rects()
                
                if bird_rect.colliderect(top_rect) or bird_rect.colliderect(bottom_rect):
                    if not self.shield_active:
                        self.state = "GAME_OVER"
                        self.sound_manager.play_sound('crash')
                        # 停止背景音乐
                        self.sound_manager.stop_background_music()
                        # 添加爆炸粒子效果
                        self.particle_system.add_explosion(
                            self.bird.x + self.bird.width//2,
                            self.bird.y + self.bird.height//2,
                            RED, 15
                        )
                        break
                
                # 检查得分
                if pipe.is_passed(self.bird.x) and not hasattr(pipe, 'scored'):
                    score_increase = 2 if self.double_score_active else 1
                    self.score += score_increase
                    pipe.scored = True
                    self.sound_manager.play_sound('score')
                    
                    # 更新最高分
                    if self.score > self.high_score:
                        self.high_score = self.score
                
                # 移除离开屏幕的管道
                if pipe.is_off_screen():
                    self.pipes.remove(pipe)
            
            # 更新道具
            for powerup in self.powerups[:]:
                if not self.slow_motion_active:
                    powerup.update()
                else:
                    # 慢动作效果：道具移动速度减半
                    powerup.x -= powerup.speed // 2
                
                # 检查道具收集
                bird_rect = self.bird.get_rect()
                if bird_rect.colliderect(powerup.get_rect()) and not powerup.collected:
                    powerup.collected = True
                    self.collect_powerup(powerup)
                    self.sound_manager.play_sound('powerup')
                    # 添加收集粒子效果
                    self.particle_system.add_explosion(
                        powerup.x, powerup.y, powerup.type == 'shield' and BLUE or 
                        powerup.type == 'slow_motion' and YELLOW or RED, 8
                    )
                    self.powerups.remove(powerup)
                
                # 移除离开屏幕的道具
                if powerup.is_off_screen():
                    self.powerups.remove(powerup)
            
            # 检查小鸟是否撞到地面或天花板
            if self.bird.y + self.bird.height >= SCREEN_HEIGHT or self.bird.y <= 0:
                if not self.shield_active:
                    self.state = "GAME_OVER"
                    self.sound_manager.play_sound('crash')
                    # 停止背景音乐
                    self.sound_manager.stop_background_music()
                    # 添加爆炸粒子效果
                    self.particle_system.add_explosion(
                        self.bird.x + self.bird.width//2,
                        self.bird.y + self.bird.height//2,
                        RED, 15
                    )
    
    def collect_powerup(self, powerup):
        """收集道具"""
        if powerup.type == 'shield':
            self.shield_active = True
            self.shield_timer = 300  # 5秒
        elif powerup.type == 'slow_motion':
            self.slow_motion_active = True
            self.slow_motion_timer = 180  # 3秒
        elif powerup.type == 'double_score':
            self.double_score_active = True
            self.double_score_timer = 300  # 5秒
    
    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(SKY_BLUE)
        
        if self.state == "MENU":
            self.draw_menu()
        elif self.state == "PLAYING":
            self.draw_game()
        elif self.state == "GAME_OVER":
            self.draw_game_over()
        elif self.state == "SETTINGS":
            self.draw_settings()
        elif self.state == "DIFFICULTY_SELECT":
            self.draw_difficulty_select()
        
        pygame.display.flip()
    
    def draw_menu(self):
        """绘制主菜单"""
        # 绘制背景
        self.background.draw(self.screen)
        
        # 标题
        self.draw_text("飞翔的小鸟", self.big_font, BLACK, SCREEN_WIDTH//2, 100)
        
        # 菜单选项
        menu_options = [
            ("[1]", "开始游戏"),
            ("[2]", "游戏设置"),
            ("[3]", "退出游戏")
        ]
        
        for i, (icon, option) in enumerate(menu_options):
            y_pos = 220 + i * 80  # 调整到统一的起始位置
            
            # 选中状态的高亮背景
            if i == self.menu_selection:
                # 调整高亮框位置，使其与文本垂直居中对齐
                highlight_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, y_pos - 20, 400, 50)
                # 使用更透明的高亮背景
                highlight_surface = pygame.Surface((400, 50))
                highlight_surface.set_alpha(30)  # 降低透明度
                highlight_surface.fill(YELLOW)
                self.screen.blit(highlight_surface, (SCREEN_WIDTH//2 - 200, y_pos - 20))
                pygame.draw.rect(self.screen, YELLOW, highlight_rect, 2)
            
            # 图标
            icon_color = YELLOW if i == self.menu_selection else BLACK
            self.draw_text(icon, self.font, icon_color, SCREEN_WIDTH//2 - 150, y_pos)
            
            # 选项文字
            option_color = YELLOW if i == self.menu_selection else BLACK
            self.draw_text(option, self.font, option_color, SCREEN_WIDTH//2, y_pos)
        
        # 操作提示
        self.draw_text("使用 ↑↓ 方向键选择，回车键确认", self.small_font, GRAY, SCREEN_WIDTH//2, SCREEN_HEIGHT - 80)
        
        # 空格键提示
        self.draw_text("或按空格键快速开始游戏", self.small_font, GRAY, SCREEN_WIDTH//2, SCREEN_HEIGHT - 50)
    
    def draw_settings(self):
        """绘制设置界面"""
        # 背景
        self.background.draw(self.screen)
        
        # 左上角返回按钮
        back_button_rect = pygame.Rect(20, 20, 80, 35)
        pygame.draw.rect(self.screen, WHITE, back_button_rect)
        pygame.draw.rect(self.screen, BLACK, back_button_rect, 2)
        self.draw_text("← 返回", self.small_font, BLACK, 60, 37)
        
        # 标题
        self.draw_text("游戏设置", self.title_font, BLACK, SCREEN_WIDTH//2, 100)
        
        # 设置选项
        settings_data = [
            ("[1]", "游戏难度"),
            ("[2]", "音效音量"),
            ("[3]", "返回主菜单")
        ]
        
        for i, (icon, name) in enumerate(settings_data):
            y_pos = 220 + i * 80  # 调整到统一的起始位置
            
            # 选中状态的高亮背景
            if i == self.settings_selection:
                # 调整高亮框位置，使其与文本垂直居中对齐
                highlight_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, y_pos - 20, 400, 50)
                # 使用更透明的高亮背景
                highlight_surface = pygame.Surface((400, 50))
                highlight_surface.set_alpha(30)  # 降低透明度
                highlight_surface.fill(YELLOW)
                self.screen.blit(highlight_surface, (SCREEN_WIDTH//2 - 200, y_pos - 20))
                pygame.draw.rect(self.screen, YELLOW, highlight_rect, 2)
            
            # 图标
            icon_color = YELLOW if i == self.settings_selection else BLACK
            self.draw_text(icon, self.font, icon_color, SCREEN_WIDTH//2 - 150, y_pos)
            
            # 设置名称
            name_color = YELLOW if i == self.settings_selection else BLACK
            self.draw_text(name, self.font, name_color, SCREEN_WIDTH//2, y_pos)
            
            # 特殊处理：音量滑块
            if i == 1:  # 音效音量选项
                slider_x = SCREEN_WIDTH//2 + 80  # 增加与文字的距离
                slider_y = y_pos - 10  # 调整到与文字同一高度（垂直居中）
                slider_width = 200
                slider_height = 20
                
                # 绘制滑块背景
                pygame.draw.rect(self.screen, GRAY, (slider_x, slider_y, slider_width, slider_height))
                pygame.draw.rect(self.screen, BLACK, (slider_x, slider_y, slider_width, slider_height), 2)
                
                # 绘制滑块
                slider_pos = int(slider_x + self.sound_manager.sound_volume * slider_width)
                pygame.draw.rect(self.screen, YELLOW, (slider_pos - 5, slider_y - 2, 10, slider_height + 4))
                
                # 显示音量百分比
                volume_text = self.small_font.render(f"{int(self.sound_manager.sound_volume * 100)}%", True, BLACK)
                volume_rect = volume_text.get_rect(center=(slider_x + slider_width + 30, slider_y + slider_height//2))
                self.screen.blit(volume_text, volume_rect)
        
        # 操作提示
        self.draw_text("使用 ↑↓ 方向键选择，Enter确认，ESC返回", self.small_font, GRAY, SCREEN_WIDTH//2, SCREEN_HEIGHT - 80)
        
        # 音量滑块提示
        self.draw_text("音量：←→键或点击拖拽滑块调节", self.small_font, GRAY, SCREEN_WIDTH//2, SCREEN_HEIGHT - 50)
    
    def draw_difficulty_select(self):
        """绘制难度选择界面"""
        # 背景
        self.background.draw(self.screen)
        
        # 左上角返回按钮
        back_button_rect = pygame.Rect(20, 20, 80, 35)
        pygame.draw.rect(self.screen, WHITE, back_button_rect)
        pygame.draw.rect(self.screen, BLACK, back_button_rect, 2)
        self.draw_text("← 返回", self.small_font, BLACK, 60, 37)
        
        # 标题
        self.draw_text("选择难度", self.title_font, BLACK, SCREEN_WIDTH//2, 100)
        
        # 难度选项
        difficulties = list(DIFFICULTY_SETTINGS.keys())
        difficulty_descriptions = {
            "简单": "管道间距大，移动慢，适合新手",
            "中等": "平衡的难度，适合大多数玩家",
            "难": "管道间距小，移动快，极具挑战"
        }
        
        for i, difficulty in enumerate(difficulties):
            y_pos = 220 + i * 100  # 调整到统一的起始位置
            
            # 选中状态的高亮背景
            if i == self.difficulty_selection:
                # 调整高亮框位置，使其与文本垂直居中对齐
                highlight_rect = pygame.Rect(SCREEN_WIDTH//2 - 250, y_pos - 25, 500, 70)
                # 使用更透明的高亮背景
                highlight_surface = pygame.Surface((500, 70))
                highlight_surface.set_alpha(30)  # 降低透明度
                highlight_surface.fill(YELLOW)
                self.screen.blit(highlight_surface, (SCREEN_WIDTH//2 - 250, y_pos - 25))
                pygame.draw.rect(self.screen, YELLOW, highlight_rect, 2)
            
            # 难度名称
            difficulty_color = YELLOW if i == self.difficulty_selection else BLACK
            self.draw_text(difficulty, self.font, difficulty_color, SCREEN_WIDTH//2, y_pos)
            
            # 难度描述
            self.draw_text(difficulty_descriptions[difficulty], self.small_font, GRAY, SCREEN_WIDTH//2, y_pos + 25)
            
            # 当前选中的难度标记
            if difficulty == self.difficulty:
                self.draw_text("(当前)", self.small_font, GREEN, SCREEN_WIDTH//2 + 100, y_pos)
        
        # 操作提示
        self.draw_text("使用 ↑↓ 方向键选择，Enter直接开始游戏，ESC返回", self.small_font, GRAY, SCREEN_WIDTH//2, SCREEN_HEIGHT - 80)
    
    def draw_game(self):
        """绘制游戏画面"""
        # 绘制背景
        self.background.draw(self.screen)
        
        # 绘制管道
        for pipe in self.pipes:
            pipe.draw(self.screen)
        
        # 绘制道具
        for powerup in self.powerups:
            powerup.draw(self.screen)
        
        # 绘制粒子效果
        self.particle_system.draw(self.screen)
        
        # 绘制小鸟
        if self.bird:
            self.bird.draw(self.screen)
            
            # 绘制护盾效果
            if self.shield_active:
                pygame.draw.circle(self.screen, BLUE, 
                                 (self.bird.x + self.bird.width//2, 
                                  self.bird.y + self.bird.height//2), 
                                 self.bird.width//2 + 10, 3)
        
        # 绘制UI信息
        self.draw_game_ui()
        
        # 绘制暂停界面
        if self.paused:
            self.draw_pause_screen()
        
        # 绘制倒计时
        if self.countdown_active:
            self.draw_countdown()
    
    def draw_game_ui(self):
        """绘制游戏UI"""
        # 绘制分数
        score_text = self.font.render(f"分数: {self.score}", True, BLACK)
        self.screen.blit(score_text, (10, 10))
        
        # 绘制最高分
        high_score_text = self.font.render(f"最高分: {self.high_score}", True, BLACK)
        self.screen.blit(high_score_text, (10, 50))
        
        # 绘制难度
        difficulty_text = self.font.render(f"难度: {self.difficulty}", True, BLACK)
        self.screen.blit(difficulty_text, (10, 90))
        
        # 绘制状态指示器
        y_offset = 130
        if self.shield_active:
            shield_text = self.font.render(f"护盾: {self.shield_timer//60 + 1}秒", True, BLUE)
            self.screen.blit(shield_text, (10, y_offset))
            y_offset += 30
            
        if self.slow_motion_active:
            slow_text = self.font.render(f"慢动作: {self.slow_motion_timer//60 + 1}秒", True, YELLOW)
            self.screen.blit(slow_text, (10, y_offset))
            y_offset += 30
            
        if self.double_score_active:
            double_text = self.font.render(f"双倍分数: {self.double_score_timer//60 + 1}秒", True, RED)
            self.screen.blit(double_text, (10, y_offset))
    
    def draw_pause_screen(self):
        """绘制暂停界面"""
        # 半透明覆盖层
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # 暂停文字
        pause_text = self.big_font.render("游戏暂停", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        self.screen.blit(pause_text, pause_rect)
        
        # 继续提示
        continue_text = self.font.render("按ESC继续游戏", True, WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        self.screen.blit(continue_text, continue_rect)
    
    def draw_countdown(self):
        """绘制倒计时"""
        # 半透明覆盖层
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # 倒计时文字 - 使用更大的字体
        countdown_text = self.countdown_font.render(self.countdown_text, True, WHITE)
        countdown_rect = countdown_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(countdown_text, countdown_rect)
    
    def draw_game_over(self):
        """绘制游戏结束画面"""
        # 绘制背景
        self.background.draw(self.screen)
        
        # 绘制管道（让玩家看到死在哪里）
        for pipe in self.pipes:
            pipe.draw(self.screen)
        
        # 绘制小鸟（显示死亡位置）
        if self.bird:
            # 让小鸟保持静止并显示
            self.bird.draw(self.screen)
        
        # 绘制粒子效果
        self.particle_system.draw(self.screen)
        
        # 游戏结束文字（标题）
        game_over_text = self.big_font.render("游戏结束", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(game_over_text, game_over_rect)
        
        # 显示最终分数（与下面的文字在一起）
        final_score_text = self.font.render(f"最终分数: {self.score}", True, BLACK)
        final_score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
        self.screen.blit(final_score_text, final_score_rect)
        
        # 显示最高分
        if self.score == self.high_score and self.score > 0:
            new_record_text = self.font.render("新纪录！", True, YELLOW)
            new_record_rect = new_record_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 10))
            self.screen.blit(new_record_text, new_record_rect)
        
        # 提示：空格再来一次 / ESC返回主菜单
        retry_text = self.font.render("按 空格 再来一次", True, BLACK)
        retry_rect = retry_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
        self.screen.blit(retry_text, retry_rect)
        
        back_text = self.small_font.render("按 ESC 返回主菜单", True, GRAY)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100))
        self.screen.blit(back_text, back_rect)
    
    def run(self):
        """主游戏循环"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
