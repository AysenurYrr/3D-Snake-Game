import sys
import random
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from PIL import Image  # PIL kütüphanesini ekledik
import time

# Global variables
window_width, window_height = 1000, 1000
map_size = 20
cell_size = 1
snake = [(5, 5)]
snake_dir = (1, 0)
game_over = False
angle = -30
speed = 100
button_pos = (-0.32, -0.5, 0.4, -0.3)
main_window = None
game_over_window = None
ghost_mode = False
ghost_mode_start_time = None

# Apple positions
red_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
bomb_apples = [(random.randint(0, map_size-1), random.randint(0, map_size-1)) for _ in range(4)]
diamond_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
stone_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
gold_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
ghost_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))

# Apple textures
snake_tail_texture=None
snake_head_texture=None
red_texture = None
bomb_texture = None
diamond_texture = None
stone_texture = None
gold_texture = None
ghost_texture = None

# Apple timers
diamond_apple_timeout = 2000
stone_apple_timeout = 2000
ghost_apple_timeout = 10000  
bomb_apple_timeout = 5000
ghost_apple_delay = 10000

# Load PNG file as texture
def load_texture(filename):
    try:
        image = Image.open(filename)
        flipped_image = image.transpose(Image.FLIP_TOP_BOTTOM)  # Yüklenen görüntüyü ters çevir
        ix = flipped_image.size[0]
        iy = flipped_image.size[1]
        image = flipped_image.tobytes("raw", "RGB")
        glClearColor(0.0, 0.0, 0.0, 0.0)	

        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        #glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, ix, iy, 0, GL_RGB, GL_UNSIGNED_BYTE, image)
        glEnable(GL_TEXTURE_2D)
        return texture_id
    except IOError as e:
        print(f"Error loading texture: {e}")
        return -1

def load_textures():
    global red_texture, bomb_texture, diamond_texture, stone_texture, gold_texture, ghost_texture, snake_head_texture, snake_tail_texture
    red_texture = load_texture("apple.png")
    bomb_texture = load_texture("bomb.jpg")
    diamond_texture = load_texture("diamond_apple.png")
    stone_texture = load_texture("stone_apple.png")
    gold_texture = load_texture("gold_apple.jpg")
    ghost_texture = load_texture("ghost_apple.JPG")
    snake_head_texture = load_texture("snake1.jpeg")
    snake_tail_texture = load_texture("snake.JPG")

    # Eğer texture'lar yüklenemediyse hata mesajı yazdır
    if red_texture == -1 or bomb_texture == -1 or diamond_texture == -1 or stone_texture == -1 or gold_texture == -1 or ghost_texture == -1:
        print("Texture loading failed. Check if the files exist and are in the correct format.")
        
def load_sounds():
    global eat_sound, bomb_sound, stone_sound, game_over_sound
    pygame.mixer.init()
    eat_sound = pygame.mixer.Sound("eat.wav")
    bomb_sound = pygame.mixer.Sound("bomb_sound.wav")
    stone_sound = pygame.mixer.Sound("stone_sound.wav")
    game_over_sound = pygame.mixer.Sound("game_over_sound.wav")
    
# Initialize OpenGL
def init():
    glEnable(GL_DEPTH_TEST)
    gluPerspective(55, window_width / window_height, 1, 100)
    glTranslatef(-map_size / 2, -map_size / 2, -map_size * 1.09)
    
# Draw the game grid
def draw_grid():
    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_LINES)
    for x in range(map_size + 1):
        glVertex3f(x, 0, 0)
        glVertex3f(x, map_size, 0)
    for y in range(map_size + 1):
        glVertex3f(0, y, 0)
        glVertex3f(map_size, y, 0)
    glEnd()

# Draw a cube at a given position
def draw_cube(position, texture_id):
    x, y = position
    glBindTexture(GL_TEXTURE_2D, texture_id)

    half_depth = -0.5  # Küpün yarı derinliği

    # Front face
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex3f(x, y, -half_depth)
    glTexCoord2f(1, 0)
    glVertex3f(x + 1, y, -half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x + 1, y + 1, -half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x, y + 1, -half_depth)
    glEnd()

    # Back face
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex3f(x, y, half_depth)
    glTexCoord2f(1, 0)
    glVertex3f(x + 1, y, half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x + 1, y + 1, half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x, y + 1, half_depth)
    glEnd()

    # Top face
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex3f(x, y + 1, -half_depth)
    glTexCoord2f(1, 0)
    glVertex3f(x + 1, y + 1, -half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x + 1, y + 1, half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x, y + 1, half_depth)
    glEnd()

    # Bottom face
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex3f(x, y, -half_depth)
    glTexCoord2f(1, 0)
    glVertex3f(x, y, half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x + 1, y, half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x + 1, y, -half_depth)
    glEnd()

    # Right face
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex3f(x + 1, y, -half_depth)
    glTexCoord2f(1, 0)
    glVertex3f(x + 1, y, half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x + 1, y + 1, half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x + 1, y + 1, -half_depth)
    glEnd()

    # Left face
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex3f(x, y, -half_depth)
    glTexCoord2f(1, 0)
    glVertex3f(x, y + 1, -half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x, y + 1, half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x, y, half_depth)
    glEnd()

# Draw the snake
def draw_snake_tail():
    glColor3f(0.0, 0.5, 0.0)
    for segment in snake[:-1]:
        draw_cube(segment, snake_tail_texture)

def draw_snake_head():
    glColor3f(0.0, 1.0, 0.0)
    draw_cube(snake[-1], snake_head_texture)
    draw_snake_tail()  # Kuyruk kısmını yeşil renkte çiz
# Draw the apples
def draw_red_apple():
    glColor3f(1.0, 1.0, 1.0)
    glBindTexture(GL_TEXTURE_2D, red_texture)
    draw_cube(red_apple, red_texture)
    
def draw_bomb_apples():
    glColor3f(1.0, 1.0, 1.0)
    for bomb_apple in bomb_apples:
        glBindTexture(GL_TEXTURE_2D, bomb_texture)
        draw_cube(bomb_apple, bomb_texture)

def draw_diamond_apple():
    glColor3f(1.0, 1.0, 1.0)
    glBindTexture(GL_TEXTURE_2D, diamond_texture)
    draw_cube(diamond_apple, diamond_texture)

def draw_stone_apple():
    glColor3f(1.0, 1.0, 1.0)
    glBindTexture(GL_TEXTURE_2D, stone_texture)
    draw_cube(stone_apple, stone_texture)

def draw_gold_apple():
    glColor3f(1.0, 1.0, 1.0)
    glBindTexture(GL_TEXTURE_2D, gold_texture)
    draw_cube(gold_apple, gold_texture)

def draw_ghost_apple():
    glColor3f(1.0, 1.0, 1.0)
    glBindTexture(GL_TEXTURE_2D, ghost_texture)
    draw_cube(ghost_apple, ghost_texture)

def display():
    global angle
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glPushMatrix()
    glRotatef(angle, 9, 0, 0)
    draw_grid()
    draw_snake_tail()
    draw_snake_head()
    draw_red_apple()
    draw_bomb_apples()
    draw_diamond_apple()
    draw_stone_apple()
    draw_gold_apple()
    draw_ghost_apple()  # Yeni eklenen satır
    glPopMatrix()
    glutSwapBuffers()

# Timer callback
def timer(value):
    global game_over
    if not game_over:
        move_snake()
        check_collision()
        update_apple_timers()
        glutPostRedisplay()
        glutTimerFunc(speed, timer, 0)

def special_input(key, x, y):
    global snake_dir
    if key == GLUT_KEY_UP and snake_dir != (0, -1):
        snake_dir = (0, 1)
    elif key == GLUT_KEY_DOWN and snake_dir != (0, 1):
        snake_dir = (0, -1)
    elif key == GLUT_KEY_LEFT and snake_dir != (1, 0):
        snake_dir = (-1, 0)
    elif key == GLUT_KEY_RIGHT and snake_dir != (-1, 0):
        snake_dir = (1, 0)

def keyboard(key, x, y):
    global snake_dir, angle
    if key == b'w' and snake_dir != (0, -1):
        snake_dir = (0, 1)
    elif key == b's' and snake_dir != (0, 1):
        snake_dir = (0, -1)
    elif key == b'a' and snake_dir != (1, 0):
        snake_dir = (-1, 0)
    elif key == b'd' and snake_dir != (-1, 0):
        snake_dir = (1, 0)
    elif key == b'z':
        angle = (angle + 5) % 360
    elif key == b'x':
        angle = (angle - 5) % 360
        
# Move the snake
def move_snake():
    global snake, game_over
    new_head = (snake[-1][0] + snake_dir[0], snake[-1][1] + snake_dir[1])
    
    if new_head[0] >= map_size:
        new_head = (0, new_head[1])
    elif new_head[0] < 0:
        new_head = (map_size - 1, new_head[1])
    elif new_head[1] >= map_size:
        new_head = (new_head[0], 0)
    elif new_head[1] < 0:
        new_head = (new_head[0], map_size - 1)

    if new_head in snake or not (0 <= new_head[0] < map_size and 0 <= new_head[1] < map_size):
        game_over = True
        show_game_over_window()
        return

    snake.append(new_head)
    snake.pop(0)

# Place a new apple
def place_red_apple():
    global red_apple
    while True:
        new_apple = (random.randint(0, map_size - 1), random.randint(0, map_size - 1))
        if new_apple not in snake and new_apple not in bomb_apples:
            red_apple = new_apple
            break

def place_bomb_apples():
    global bomb_apples
    bomb_apples = []
    for _ in range(4):
        while True:
            new_bomb_apple = (random.randint(0, map_size - 1), random.randint(0, map_size - 1))
            if new_bomb_apple not in snake and new_bomb_apple != red_apple:
                bomb_apples.append(new_bomb_apple)
                break

def place_diamond_apple():
    global diamond_apple
    while True:
        new_diamond_apple = (random.randint(0, map_size - 1), random.randint(0, map_size - 1))
        if new_diamond_apple not in snake and new_diamond_apple != red_apple and new_diamond_apple not in bomb_apples:
            diamond_apple = new_diamond_apple
            break

def place_stone_apple():
    global stone_apple
    while True:
        new_stone_apple = (random.randint(0, map_size - 1), random.randint(0, map_size - 1))
        if new_stone_apple not in snake and new_stone_apple != red_apple and new_stone_apple not in bomb_apples:
            stone_apple = new_stone_apple
            break

def place_gold_apple():
    global gold_apple
    while True:
        new_gold_apple = (random.randint(0, map_size - 1), random.randint(0, map_size - 1))
        if new_gold_apple not in snake and new_gold_apple != red_apple and new_gold_apple not in bomb_apples:
            gold_apple = new_gold_apple
            break

def place_ghost_apple():
    global ghost_apple
    while True:
        new_ghost_apple = (random.randint(0, map_size - 1), random.randint(0, map_size - 1))
        if new_ghost_apple not in snake and new_ghost_apple != red_apple and new_ghost_apple not in bomb_apples:
            ghost_apple = new_ghost_apple
            break
        
def enable_ghost_mode():
    global ghost_mode, ghost_mode_start_time, snake_tail_texture, snake_head_texture
    ghost_mode = True
    ghost_mode_start_time = time.time()
    snake_tail_texture = load_texture("snak.JPG")
    glColor3f(0.0, 0.0, 0.0)
    snake_head_texture = load_texture("snake1.jpeg")

def disable_ghost_mode():
    global ghost_mode, snake_tail_texture, snake_head_texture
    ghost_mode = False
    snake_tail_texture = load_texture("snake.JPG")
    snake_head_texture = load_texture("snake1.jpeg")

def show_game_over_window():
    global game_over_window
    if game_over_window is not None:
        glutDestroyWindow(game_over_window)
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(400, 300)
    game_over_window = glutCreateWindow(b'Game Over')
    glutDisplayFunc(display_game_over)
    game_over_sound.play()
    glutMouseFunc(mouse_click)
    glutMainLoop()
    
def draw_play_button_text():
    glColor3f(0, 0, 0)
    glRasterPos2f(-0.27, -0.45)
    for char in b"TEKRAR OYNA":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, char)

def display_game_over():
    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(1, 1, 1)
    glRasterPos2f(-0.23, 0.2)
    for char in b"GAME OVER":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, char)
    glColor3f(1, 1, 1)
    score_text = f"SCORE: {len(snake)-1}"
    glRasterPos2f(-0.15, 0.0)
    for char in score_text.encode():
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, char)
    
    glColor3f(1, 1, 1)
    glBegin(GL_QUADS)
    glVertex2f(button_pos[0], button_pos[1])
    glVertex2f(button_pos[2], button_pos[1])
    glVertex2f(button_pos[2], button_pos[3])
    glVertex2f(button_pos[0], button_pos[3])
    glEnd()
    
    draw_play_button_text()
    
    glFlush()

def mouse_click(button, state, x, y):
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        ogl_x = (x / 400.0) * 2 - 1
        ogl_y = -((y / 300.0) * 2 - 1)
        if button_pos[0] <= ogl_x <= button_pos[2] and button_pos[1] <= ogl_y <= button_pos[3]:
            restart_game()

def restart_game():
    global snake, snake_dir, game_over, red_apple, diamond_apple, stone_apple, gold_apple, main_window, game_over_window, ghost_apple
    snake = [(5, 5)]
    snake_dir = (1, 0)
    game_over = False
    red_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
    place_bomb_apples()
    diamond_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
    ghost_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
    stone_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
    gold_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
    if game_over_window is not None:
        glutDestroyWindow(game_over_window)
    glutSetWindow(main_window)
    glutDisplayFunc(display)
    glutTimerFunc(speed, timer, 0)  
# Check for collisions
def check_collision():
    global game_over, ghost_mode, ghost_mode_start_time
    head = snake[-1]
    if not (0 <= head[0] < map_size and 0 <= head[1] < map_size) or head in snake[:-1]:
        game_over = True
        show_game_over_window()
        return

    if not ghost_mode and head in bomb_apples:
        bomb_sound.play()  # Bomb apple çarptığında patlama sesi oynat
        game_over = True
        show_game_over_window()
        return

    if head == red_apple:
        eat_sound.play()  # Yeme sesi
        snake.append(snake[-1])
        place_red_apple()

    elif head == diamond_apple:
        eat_sound.play()  # Yeme sesi
        snake.append(snake[-1])
        snake.append(snake[-1])
        snake.append(snake[-1])
        place_diamond_apple()

    elif head == stone_apple:
        stone_sound.play()  # Çarpma sesi
        if len(snake) == 1:
            game_over = True
            show_game_over_window()
            return
        else:
            snake.pop()
        place_stone_apple()

    elif head == gold_apple:
        eat_sound.play()  # Yeme sesi
        snake.append(snake[-1])
        snake.append(snake[-1])
        place_gold_apple()

    elif head == ghost_apple:
        eat_sound.play()  # Yeme sesi
        enable_ghost_mode()
        place_ghost_apple()

    # Check if ghost mode is active and time exceeded 4 seconds
    if ghost_mode and (time.time() - ghost_mode_start_time) > 4:
        disable_ghost_mode()
           
# Timer callback function
def timer(value):
    global game_over, ghost_mode_timer
    if not game_over:
        move_snake()
        check_collision()
        update_apple_timers()
        glutPostRedisplay()
        glutTimerFunc(speed, timer, 0)
        
# Apple timers update function
def update_apple_timers():
    global diamond_apple_timeout, stone_apple_timeout, ghost_apple_timeout, bomb_apple_timeout, custom_ghost_apple_timeout,ghost_apple_delay
    diamond_apple_timeout -= speed
    stone_apple_timeout -= speed
    
    bomb_apple_timeout -= speed
  

    if diamond_apple_timeout <= 0:
        place_diamond_apple()
        diamond_apple_timeout = 2000

    if stone_apple_timeout <= 0:
        place_stone_apple()
        stone_apple_timeout = 2000
        
    if bomb_apple_timeout <= 0:
        place_bomb_apples()
        bomb_apple_timeout = 5000
        
    if ghost_apple_delay > 0:
        ghost_apple_delay -= speed
    else:
        if ghost_apple_timeout <= 0:
            place_ghost_apple()
            ghost_apple_timeout = 10000  # 10 saniye
# Main function
def main():
    global main_window

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(window_width, window_height)
    main_window = glutCreateWindow(b"OpenGL Snake Game")
    glEnable(GL_TEXTURE_2D)
    load_textures()
    load_sounds()
    init()
    glutDisplayFunc(display)
    glutTimerFunc(speed, timer, 0)
    glutSpecialFunc(special_input)
    glutKeyboardFunc(keyboard)

    glutMainLoop()

if __name__ == "__main__":
    main()
