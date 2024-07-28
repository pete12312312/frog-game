import os, time, random, math, pygame, asyncio, sys
from turtle import right
import tkinter as tk
from os import listdir
from os.path import isfile, join


pygame.init()
pygame.mixer.init()

pygame.display.set_caption("Frog Jump!!")

screen_width = 1300
screen_height = 800

screen = pygame.display.set_mode((screen_width, screen_height))
WIDTH, HEIGHT = 1300, 800
FPS = 60
PLAYER_VEL = 5

log_size = 96
block_size = 96
exit_size = 96
Blob_size = 96
shaddow_size = 96
crab_size = 96
bat_size = 96

pygame.mixer.music.load("sound effects/Pete's Soundtrack.mp3")
pygame.mixer.music.play(-1)

font = pygame.font.SysFont("arialblack", 40)
TEXT_COL = (255, 25, 255)

window = pygame.display.set_mode((WIDTH, HEIGHT))


def check_player_health(player):
    if player.health <= 0:      
            show_game_over_screen(window)

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]



def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)

def get_half_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size // 2), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size // 2)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)

class Bat(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    SPRITES = load_sprite_sheets("MainCharacters", "Bat", 46, 30, True)
    ANIMATION_DELAY = 3
    FLY_ANIMATION = "fly"
    DAMAGE = 75

    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.speed = random.uniform(1, 3)  # Slowed down speed
        self.direction = random.choice(["left", "right"])
        self.move_timer = 0
        self.name = "Bat"
        self.change_direction_time = random.randint(60, 120)  # Longer duration before change
        self.velocity = pygame.math.Vector2(0, 0)
        self.set_random_velocity()

    def set_random_velocity(self):
        angle = random.uniform(0, 2 * math.pi)
        self.velocity = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * self.speed

    def move_randomly(self):
        if self.move_timer >= self.change_direction_time:
            self.move_timer = 0
            self.change_direction_time = random.randint(60, 120)
            self.set_random_velocity()

        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y

        # Boundary check to keep the bat within the game window
        if self.rect.left < 0 or self.rect.right > 1300:
            self.velocity.x *= -1
            self.rect.x = max(0, min(self.rect.x, 1300 - self.rect.width))

        if self.rect.top < 0 or self.rect.bottom > 800:
            self.velocity.y *= -1
            self.rect.y = max(0, min(self.rect.y, 800 - self.rect.height))

        if self.velocity.x > 0:
            self.direction = "left"
        else:
            self.direction = "right"

        self.move_timer += 1

    def update_sprite(self):
        sprite_sheet_name = self.FLY_ANIMATION
        sprites = self.SPRITES[sprite_sheet_name + "_" + self.direction]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        if self.animation_count // self.ANIMATION_DELAY >= len(sprites):
            self.animation_count = 0
    def update(self):
        self.mask = pygame.mask.from_surface(self.image)

    def check_collision(self, player):

        if pygame.sprite.collide_mask(self, player):

            player.decrease_health(self.DAMAGE, self.DAMAGE)# Apply damage

    def loop(self, player):
            self.move_randomly()
            self.update_sprite()
            self.check_collision(player)  # Check for collision with player
            self.update()



    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

    
class log(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    SPRITES = load_sprite_sheets("MainCharacters", "Trunk", 64, 64, True)
    ANIMATION_DELAY = 3
    SHOOT_ANIMATION = "attack"
    IDLE_ANIMATION = "idle"

    def __init__(self, x, y, width, height, direction="right"):
        super().__init__()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self.direction = direction
        self.animation_count = 0
        self.health = 100
        self.max_health = 100
        self.last_shoot_time = 0
        self.shoot_interval = random.randint(3000, 5000)
        self.is_shooting = False
        self.name = "log"
        self.projectiles = pygame.sprite.Group()
        self.current_sprite = None

    def initiate_shoot(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shoot_time >= self.shoot_interval:
            self.last_shoot_time = current_time
            self.shoot_interval = random.randint(3000, 5000)
            self.is_shooting = True
            self.animation_count = 0

    def complete_shoot(self):
        if self.is_shooting:
            self.is_shooting = False
            projectile = Projectile(self.rect.centerx, self.rect.centery, self.direction)
            self.projectiles.add(projectile)

    def update_sprite(self):
        sprite_sheet_name = self.SHOOT_ANIMATION if self.is_shooting else self.IDLE_ANIMATION
        sprites = self.SPRITES[sprite_sheet_name + "_" + self.direction]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        if self.animation_count // self.ANIMATION_DELAY >= len(sprites):
            if self.is_shooting:
                self.complete_shoot()
            self.animation_count = 0

    def loop(self, player):  # Pass the player to the loop method
        self.initiate_shoot()
        self.update_sprite()
        self.projectiles.update()
        for projectile in self.projectiles:
            projectile.check_collision(player) 

    def update(self):
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))
        for projectile in self.projectiles:
            projectile.draw(win, offset_x)

class Projectile(pygame.sprite.Sprite):
    SPEED = 30
    DAMAGE = 25

    def __init__(self, x, y, direction):
        super().__init__()
        path = join("assets", "MainCharacters", "bullet.png")
        self.image = pygame.image.load(path).convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        if self.direction == "right":
            self.rect.x -= self.SPEED
        else:
            self.rect.x += self.SPEED
    

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

    def check_collision(self, player):
        if pygame.sprite.collide_mask(self, player):
            player.decrease_health(self.DAMAGE)
            self.kill()


class Projectile(pygame.sprite.Sprite):
    SPEED = 20
    DAMAGE = 25
    
    def __init__(self, x, y, direction):
        super().__init__()
        path = join("assets", "MainCharacters", "bullet.png")
        self.image = pygame.image.load(path).convert_alpha()  
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        if self.direction == "right":
            self.rect.x -= self.SPEED
        else:
            self.rect.x += self.SPEED

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))
    def check_collision(self, player):
        if pygame.sprite.collide_mask(self, player):
            player.decrease_health(self.DAMAGE, self.DAMAGE)  # Apply damage
            self.kill() 



class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "Ninjafrog", 32, 32, True)
    ANIMATION_DELAY = 3
    last_executed_time = 0
    last_decrease_time = 0

    def decrease_health(self, min_amount, max_amount):
        current_time = time.time()
        if current_time - self.last_decrease_time >= 3:
            amount = random.randint(min_amount, max_amount)
            self.health -= amount
            if self.health < 0:
                self.health = 0
            self.last_decrease_time = current_time
        else:
            pass # this text is here to pass meaning it dose absolutely nothing 

    def can_execute(self):
        now = time.time()
        if now - self.last_executed_time >= 10:
            self.last_executed_time = now
            return True
        return False
   
    def dash(self):
        if self.can_execute():
            self.x_vel = 100

    
    def dash2(self):
        if self.can_execute():
            self.x_vel = -100


    
    def increase_health(self, amount):
        self.health += amount
        if self.health > self.max_health:
            self.health = self.max_health
  
    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.health = 100
        self.max_health = 100



    def draw_health_bar(self, win):
        health_width = self.rect.width * (self.health / self.max_health) * 3
        health_height = 25
        health_bar_surface = pygame.Surface((health_width, health_height)) 
        health_bar_surface.fill((0, 255, 0))
        win.blit(health_bar_surface, (10, 10))
        health_percentage = f'{int((self.health / self.max_health) * 100)}%'
        health_text = font.render(health_percentage, True, (255, 255, 255))
        win.blit(health_text, (health_width + 15, 10))
    
    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)
  
        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

    
class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Blob(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, path_length, start_direction="left"):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.width = width
        self.height = height
        self.path_length = path_length
        self.start_x = x
        self.x_vel = 2 if start_direction == "right" else -2
        self.direction = start_direction
        self.load_image()
        self.mask = pygame.mask.from_surface(self.image)
        self.name = Blob


    def load_image(self):
        path = join("assets", "Other", "blob.png")
        image = pygame.image.load(path).convert_alpha()
        self.image = pygame.transform.scale(image, (self.width, self.height))

    def move(self):
        self.rect.x += self.x_vel
        if self.rect.x <= self.start_x - self.path_length or self.rect.x >= self.start_x + self.path_length:
            self.reverse_direction()

    def reverse_direction(self):
        self.x_vel *= -1

    def loop(self):
        self.move()

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))
        


class Crab(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, path_length, start_direction="left"):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.width = width
        self.height = height
        self.path_length = path_length
        self.start_x = x
        self.x_vel = 2 if start_direction == "right" else -2
        self.direction = start_direction
        self.load_image()
        self.mask = pygame.mask.from_surface(self.image)
        self.name = Crab
        self.move_duration = random.randint(60, 120)
        self.pause_duration = random.randint(60, 180)
        self.time_since_last_move = 0
        self.moving = True

    def load_image(self):
        path = join("assets", "Other", "the.png")
        image = pygame.image.load(path).convert_alpha()
        self.image = pygame.transform.scale(image, (self.width, self.height))

    def move(self):
        self.rect.x += self.x_vel
        if self.rect.x <= self.start_x - self.path_length or self.rect.x >= self.start_x + self.path_length:
            self.reverse_direction()

    def reverse_direction(self):
        self.x_vel *= -1

    def loop(self):

        if self.moving:
            self.time_since_last_move += 1

            if self.time_since_last_move <= self.move_duration:
                self.move()
            else:
                self.moving = False
                self.time_since_last_move = 0
        else:
            self.time_since_last_move += 1
            if self.time_since_last_move >= self.pause_duration:
                self.moving = True
                self.time_since_last_move = 0
                self.x_vel = random.choice([-2, 2])
    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class HalfBlock(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size // 2)
        half_block = get_half_block(size)
        self.image.blit(half_block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y, size_multiplier):
        super().__init__()
        self.original_image = pygame.image.load("exit.png").convert_alpha()
        self.original_rect = self.original_image.get_rect(topleft=(x, y))
        self.size_multiplier = size_multiplier
        self.image = pygame.transform.scale(self.original_image, (self.original_rect.width * size_multiplier, self.original_rect.height * size_multiplier))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.name = Exit
    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class shaddow(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.original_image = pygame.image.load("shaddow.png").convert_alpha()
        self.image = pygame.transform.scale(self.original_image, (self.original_image.get_width() * 2, self.original_image.get_height() * 2))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.name = shaddow

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))
    
    def follow_player(self, player):
        if self.rect.x < player.rect.x:
            self.rect.x += 3
        if self.rect.x > player.rect.x:
            self.rect.x -= 3
        if self.rect.y < player.rect.y:
            self.rect.y += 1.5
        if self.rect.y > player.rect.y:
            self.rect.y -= 1.5


class Heart(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load("heart.png").convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.name = Heart

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"
    
    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image

def draw(window, background, bg_image, player, objects, offset_x, score, elapsed_time):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)
    player.draw(window, offset_x)
    player.draw_health_bar(window)
    score_text = font.render(f'level : {score}', True, TEXT_COL)
    window.blit(score_text, (WIDTH - score_text.get_width() - 20, 20))
    timer_text = font.render(f' {elapsed_time:.3f} ', True, TEXT_COL)
    window.blit(timer_text, (1120, 70))
    pygame.display.update()


def show_victory_screen(window):
    image_path = os.path.join("assets", "Background", "victory.png")
    victory_image = pygame.image.load(image_path)
    victory_image = pygame.transform.scale(victory_image, (WIDTH, HEIGHT))
    window.fill((0, 0, 0))
    window.blit(victory_image, (0, 0))
    pygame.display.update()
    time.sleep(4)
    pygame.quit()
    sys.exit()

def show_game_over_screen(window):
    image_path = os.path.join("assets", "Background", "gameover.png")
    victory_image = pygame.image.load(image_path)
    victory_image = pygame.transform.scale(victory_image, (WIDTH, HEIGHT))
    window.fill((0, 0, 0))
    window.blit(victory_image, (0, 0))
    pygame.display.update()
    time.sleep(4)
    pygame.quit()
    sys.exit()

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()
            
            collided_objects.append(obj)

    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if not isinstance(obj, Exit) and pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
    player.move(-dx, 0)
    player.update()
    return collided_object

def handle_move(player, objects, dx):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 3)
    collide_right = collide(player, objects, PLAYER_VEL * 3)


    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)
    if keys[pygame.K_d] and not collide_right:
        player.move_right(PLAYER_VEL)
    if keys[pygame.K_a] and not collide_left:
        player.move_left(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, * vertical_collide]

    for obj in to_check:
        if obj and obj.name == "heart, Crab, Blob, shaddow, bat":
            player.make_hit()
        if isinstance(obj, Heart):
            player.increase_health(25)
            objects.remove(obj)
            break
        
        if isinstance(obj, Blob):
            player.decrease_health(25, 25)
            player.hit = 1
        if isinstance(obj, Crab):
            player.decrease_health(25,25)
            player.hit = 1

               
        elif isinstance(obj, Crab) and PLAYER_VEL >= 5:
            objects.remove(obj)

        if obj and obj.name == "shaddow":
            player.make_hit()
        if isinstance(obj, shaddow):
            player.decrease_health(70,95)


    if dx > 0:
        collide_right = collide(player, objects, dx)
        if collide_right and collide_right.name in ["heart, Crab, Blob, shaddow, log, Bat"]:
            player.make_hit()
        elif collide_right and isinstance(collide_right, Block):
            if collide_right.rect.right - player.rect.right < 20:
                player.move_right(20)
            elif collide_right and collide_right.rect.right - player.rect.right < 10:
                player.move_right(10)
            
    

    if dx > 0:
        collide_right = collide(player, objects, dx)
        if collide_right and collide_right.name in ["heart, Crab, Blob, shaddow, log, Bat"]:
            player.make_hit()

        elif collide_right and isinstance(collide_right, Block):
            if collide_right.rect.right - player.rect.right < 10:
                player.move_right(10)
            elif collide_right and collide_right.rect.right - player.rect.right < 20:
                player.move_right(20)
    else:
        collide_left = collide(player, objects, dx)
        if collide_left and collide_left.name in ["heart, Crab, Blob, shaddow, log, Bat"]:
            player.make_hit()
        elif collide_left and isinstance(collide_left, Block):
            if collide_left.rect.left - player.rect.left < 10:
                player.move_left(10)
            elif collide_left and collide_left.rect.left - player.rect.left < 20:
                player.move_left(20)

    player.update()
    return collide_left, collide_right


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if not isinstance(obj, Exit) and pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
    player.move(-dx, 0)
    player.update()
    return collided_object

levels = [
    

    { # level 0
        "background": "lvl 0.png",
        "player_start": (0, 600),
        "obstacles": [
            Block(block_size * 0, HEIGHT - block_size * 1, block_size),
            Block(block_size * 1, HEIGHT - block_size * 1, block_size),
            Block(block_size * 2, HEIGHT - block_size * 1, block_size),
            Block(block_size * 3, HEIGHT - block_size * 1, block_size),
            Block(block_size * 4, HEIGHT - block_size * 1, block_size),
            Block(block_size * 5, HEIGHT - block_size * 1, block_size),
            Block(block_size * 6, HEIGHT - block_size * 1, block_size),
            Block(block_size * 7, HEIGHT - block_size * 1, block_size),
            Block(block_size * 8, HEIGHT - block_size * 1, block_size),
            Block(block_size * 9, HEIGHT - block_size * 1, block_size),
            Block(block_size * 10, HEIGHT - block_size * 1, block_size),
            Block(block_size * 11, HEIGHT - block_size * 1, block_size),
            Block(block_size * 12, HEIGHT - block_size * 1, block_size),
            Block(block_size * 13, HEIGHT - block_size * 1, block_size),
            Block(block_size * 14, HEIGHT - block_size * 1, block_size),
            Block(block_size * 15, HEIGHT - block_size * 1, block_size),
            Block(block_size * 16, HEIGHT - block_size * 1, block_size),
 
        ],
        "enemies": [
            Exit(1001, HEIGHT - block_size * 2.25, 4),
            log(1200, 640, 64, 64, direction="right"),


        ]
    },


    { #level 1
        "background": "Gray.png",
        "player_start": (100, 600),
        "obstacles": [
            Block(0, HEIGHT - block_size, block_size),
            Block(block_size * 1, HEIGHT - block_size * 1, block_size),
            Block(block_size * 4, HEIGHT - block_size * 1, block_size),
            Block(block_size * 5, HEIGHT - block_size * 1, block_size),
            Block(block_size * 8, HEIGHT - block_size * 1, block_size),
            Block(block_size * 7, HEIGHT - block_size * 1, block_size),
            Block(block_size * 8, HEIGHT - block_size * 2, block_size),
            Block(block_size * 8, HEIGHT - block_size * 3, block_size),
            Block(block_size * 8, HEIGHT - block_size * 2, block_size),
            Block(block_size * 9, HEIGHT - block_size * 4, block_size),
            Block(block_size * 10, HEIGHT - block_size * 5, block_size),
            Block(block_size * 10, HEIGHT - block_size * 5, block_size),
            Block(block_size * 11, HEIGHT - block_size * 5, block_size),
            Block(block_size * 12, HEIGHT - block_size * 5, block_size),
            Block(block_size * 13, HEIGHT - block_size * 5, block_size),
            Block(block_size * 14, HEIGHT - block_size * 5, block_size),
            Block(block_size * 15, HEIGHT - block_size * 5, block_size),
        
        ],
        "enemies": [
            Exit(1300, HEIGHT - block_size * 6.25, 4),
        ]
    },
    { #level 2
        "background": "sky.png",
        "player_start": (0, 600),
        "obstacles": [
            Block(0, HEIGHT - block_size, block_size),
            Block(block_size * 3, HEIGHT - block_size * 3, block_size),
            Block(block_size * 2, HEIGHT - block_size * 3, block_size),
            Block(block_size * 5, HEIGHT - block_size * 5, block_size),
            Block(block_size * 8, HEIGHT - block_size * 5, block_size),
            Block(block_size * 9, HEIGHT - block_size * 5, block_size),
            Block(block_size * 10, HEIGHT - block_size * 5, block_size),
            Block(block_size * 11, HEIGHT - block_size * 5, block_size),
            Block(block_size * 12, HEIGHT - block_size * 5, block_size),
            Block(block_size * 13, HEIGHT - block_size * 5, block_size),
            Block(block_size * 15, HEIGHT - block_size * 5, block_size),
            Block(block_size * 16, HEIGHT - block_size * 5, block_size),
            Block(block_size * 17, HEIGHT - block_size * 5, block_size),
        ],
        "enemies": [
            Exit(1600, HEIGHT - block_size * 6.25, 4),
        ]

    },
    { #level 3
    "background": "Blue.png",
    "player_start": (0, 600),
    "obstacles": [
        Block(0, HEIGHT - block_size, block_size),
        Block(block_size * 2, HEIGHT - block_size * 2, block_size),
        Block(block_size * 4, HEIGHT - block_size * 3, block_size),
        Block(block_size * 6, HEIGHT - block_size * 4, block_size),
        Block(block_size * 5, HEIGHT - block_size * 4, block_size),
        Block(block_size * 4, HEIGHT - block_size * 4, block_size),
        Block(block_size * 5, HEIGHT - block_size * 4, block_size),
        Block(block_size * 6, HEIGHT - block_size * 5, block_size),
    ],
    "enemies": [
        Exit(800, HEIGHT - block_size * 6, 4),

    ]
},
{# level 4
    "background": "Blue.png",
    "player_start": (0, 600),
    "obstacles": [
        Block(0, HEIGHT - block_size, block_size),
        Block(block_size * 3, HEIGHT - block_size * 1, block_size),
        Block(block_size * 6, HEIGHT - block_size * 2, block_size),
        Block(block_size * 9, HEIGHT - block_size * 3, block_size),
        Block(block_size * 12, HEIGHT - block_size * 4, block_size),
        Block(block_size * 15, HEIGHT - block_size * 5, block_size),
        Block(block_size * 18, HEIGHT - block_size * 6, block_size),
        Block(block_size * 21, HEIGHT - block_size * 7, block_size),
        Block(block_size * 24, HEIGHT - block_size * 7, block_size),
        Block(block_size * 27, HEIGHT - block_size * 7, block_size),
        Block(block_size * 28, HEIGHT - block_size * 7, block_size),
        Block(block_size * 29, HEIGHT - block_size * 7, block_size),
        Block(block_size * 30, HEIGHT - block_size * 6, block_size),
        Block(block_size * 31, HEIGHT - block_size * 5, block_size),
        Block(block_size * 32, HEIGHT - block_size * 5, block_size),
        Block(block_size * 33, HEIGHT - block_size * 5, block_size),
    ],
    "enemies": [
        Exit(3100, HEIGHT - block_size * 6.25, 4),
    ]
    },
    { #level 5
        "background": "blue.png",
        "player_start": (0, 600),
        "obstacles": [
            Block(0, HEIGHT - block_size, block_size),
            Block(block_size * 1, HEIGHT - block_size * 2, block_size),
            Block(block_size * 2, HEIGHT - block_size * 2, block_size),
            Block(block_size * 1.5, HEIGHT - block_size * 8, block_size),
            Block(block_size * 1.5, HEIGHT - block_size * 7, block_size),
            Block(block_size * 1.5, HEIGHT - block_size * 6, block_size),
            Block(block_size * 1.5, HEIGHT - block_size * 5, block_size),
            Block(block_size * 1.5, HEIGHT - block_size * 11, block_size),
            Block(block_size * 1.5, HEIGHT - block_size * 10, block_size),
            Block(block_size * 1.5, HEIGHT - block_size * 9, block_size),
            Block(block_size * 2, HEIGHT - block_size * 5, block_size),
            Block(block_size * 2, HEIGHT - block_size * 2, block_size),
            Block(block_size * 5, HEIGHT - block_size * 2, block_size),
            Block(block_size * 6, HEIGHT - block_size * 2, block_size),
            HalfBlock(block_size * 4, HEIGHT - block_size * 4, block_size),
            HalfBlock(block_size * 5, HEIGHT - block_size * 4, block_size),
            Block(block_size * 3, HEIGHT - block_size * 5, block_size),
            Block(block_size * 5, HEIGHT - block_size * 6, block_size),
            Block(block_size * 7, HEIGHT - block_size * 3, block_size),
            Block(block_size * 6, HEIGHT - block_size * 6, block_size),
            Block(block_size * 7, HEIGHT - block_size * 6, block_size),
            Block(block_size * 8, HEIGHT - block_size * 6, block_size),
            Block(block_size * 9, HEIGHT - block_size * 6, block_size),
            Block(block_size * 10, HEIGHT - block_size * 6, block_size),
            Block(block_size * 11, HEIGHT - block_size * 6, block_size),
            Block(block_size * 12, HEIGHT - block_size * 6, block_size),
            Block(block_size * 13, HEIGHT - block_size * 6, block_size),
            Block(block_size * 14, HEIGHT - block_size * 6, block_size),
            Block(block_size * 15, HEIGHT - block_size * 6, block_size),
        ],
        "enemies": [
            Exit(1300, HEIGHT - block_size * 7.25, 4),
            Heart(1200, 180),

        ]
        },
        { #level 6
            "background": "Gray.png",
            "player_start": (0, 600),
            "obstacles": [
            Block(0, HEIGHT - block_size, block_size),
            Block(block_size * 1, HEIGHT - block_size * 1, block_size),
            Block(block_size * 1, HEIGHT - block_size * 1, block_size),
            Block(block_size * 1, HEIGHT - block_size * 1, block_size),
            Block(block_size * 2, HEIGHT - block_size * 1, block_size),
            Block(block_size * 3, HEIGHT - block_size * 1, block_size),
            Block(block_size * 4, HEIGHT - block_size * 1, block_size),
            Block(block_size * 5, HEIGHT - block_size * 1, block_size),
            Block(block_size * 6, HEIGHT - block_size * 1, block_size),
            Block(block_size * 7, HEIGHT - block_size * 1, block_size),
            Block(block_size * 8, HEIGHT - block_size * 1, block_size),
            Block(block_size * 9, HEIGHT - block_size * 1, block_size),
            Block(block_size * 10, HEIGHT - block_size * 1, block_size),
            Block(block_size * 11, HEIGHT - block_size * 1, block_size),
            Block(block_size * 12, HEIGHT - block_size * 1, block_size),
            Block(block_size * 13, HEIGHT - block_size * 1, block_size),
            Block(block_size * 14, HEIGHT - block_size * 1, block_size),
            Block(block_size * 15, HEIGHT - block_size * 1, block_size),
            Block(block_size * 16, HEIGHT - block_size * 1, block_size),
            Block(block_size * 17, HEIGHT - block_size * 1, block_size),
            Block(block_size * 18, HEIGHT - block_size * 1, block_size),
            Block(block_size * 19, HEIGHT - block_size * 1, block_size),
            Block(block_size * 20, HEIGHT - block_size * 1, block_size),
            Block(block_size * 21, HEIGHT - block_size * 1, block_size),
            Block(block_size * 22, HEIGHT - block_size * 1, block_size),
            Block(block_size * 23, HEIGHT - block_size * 1, block_size),
            Block(block_size * 24, HEIGHT - block_size * 1, block_size),
            Block(block_size * 15, HEIGHT - block_size * 2, block_size),
            Block(block_size * 15, HEIGHT - block_size * 3, block_size),
            Block(block_size * 15, HEIGHT - block_size * 4, block_size),



            ],
                "enemies": [
            Exit(1300, HEIGHT - block_size * 2.25, 4),
            Blob(500, HEIGHT - block_size * 1.5, 50, 50, 500, "left"),
            

        ]
            
        },
        {# level 7
        "background": "Yellow.png",
        "player_start": (-20, 600),
        "obstacles": [
            Block(block_size * -7, HEIGHT - block_size * 11, block_size),
            Block(block_size * -7, HEIGHT - block_size * 10, block_size),
            Block(block_size * -7, HEIGHT - block_size * 9, block_size),
            Block(block_size * -7, HEIGHT - block_size * 8, block_size),
            Block(block_size * -7, HEIGHT - block_size * 7, block_size),
            Block(block_size * -7, HEIGHT - block_size * 6, block_size),
            Block(block_size * -7, HEIGHT - block_size * 5, block_size),
            Block(block_size * -7, HEIGHT - block_size * 4, block_size),
            Block(block_size * -7, HEIGHT - block_size * 3, block_size),
            Block(block_size * -6, HEIGHT - block_size * 3, block_size),
            Block(block_size * -6, HEIGHT - block_size * 0, block_size),
            Block(block_size * -6, HEIGHT - block_size * 1, block_size),
            Block(block_size * -6, HEIGHT - block_size * 2, block_size),
            Block(block_size * -6, HEIGHT - block_size * 3, block_size),
            Block(block_size * -5, HEIGHT - block_size * 3, block_size),
            Block(block_size * -5, HEIGHT - block_size * 2, block_size),
            Block(block_size * -5, HEIGHT - block_size * 1, block_size),
            Block(block_size * -5, HEIGHT - block_size * 3, block_size),
            Block(block_size * -4, HEIGHT - block_size * 2, block_size),
            Block(block_size * -4, HEIGHT - block_size * 1, block_size),
            Block(block_size * -3, HEIGHT - block_size * 5, block_size),
            Block(block_size * -3, HEIGHT - block_size * 1, block_size),
            Block(block_size * 0, HEIGHT - block_size * 1, block_size),
            Block(block_size * 0, HEIGHT - block_size * 4, block_size),
            Block(block_size * 1, HEIGHT - block_size * 1, block_size),
            Block(block_size * 1, HEIGHT - block_size * 2, block_size),
            Block(block_size * 1, HEIGHT - block_size * 3, block_size),
            Block(block_size * 1, HEIGHT - block_size * 4, block_size),
            Block(block_size * 2, HEIGHT - block_size * 1, block_size),
            Block(block_size * 3, HEIGHT - block_size * 1, block_size),
            Block(block_size * 5, HEIGHT - block_size * 1, block_size),
            Block(block_size * 6, HEIGHT - block_size * 1, block_size),
            Block(block_size * 6, HEIGHT - block_size * 1, block_size),
            Block(block_size * 11, HEIGHT - block_size * 1, block_size),
            Block(block_size * 12, HEIGHT - block_size * 1, block_size),
            Block(block_size * 12, HEIGHT - block_size * 2, block_size),
            Block(block_size * 13, HEIGHT - block_size * 2, block_size),
            Block(block_size * 13, HEIGHT - block_size * 1, block_size),
            Block(block_size * 13, HEIGHT - block_size * 2, block_size),
            Block(block_size * 14, HEIGHT - block_size * 1, block_size),
            Block(block_size * 14, HEIGHT - block_size * 2, block_size),

        ],
        "enemies": [
            Exit(1300, HEIGHT - block_size * 3.25, 4),
            Blob(600, HEIGHT - block_size * 1.5, 50, 50, 115, "right"),
            Heart(1200, 570)
        ]

    },

    {# level 8
    "background": "Yellow.png",
    "player_start": (0, 600),
    "obstacles": [
        Block(block_size * 0, HEIGHT - block_size * 1, block_size),
        Block(block_size * 1, HEIGHT - block_size * 2, block_size),
        Block(block_size * 2, HEIGHT - block_size * 2, block_size),
        Block(block_size * 3, HEIGHT - block_size * 2, block_size),
        Block(block_size * 3, HEIGHT - block_size * 3, block_size),
        Block(block_size * 4, HEIGHT - block_size * 4, block_size),
        Block(block_size * 5, HEIGHT - block_size * 4, block_size),
        Block(block_size * 9, HEIGHT - block_size * 4, block_size),
        Block(block_size * 10, HEIGHT - block_size * 4, block_size),
        Block(block_size * 14, HEIGHT - block_size * 5, block_size),
        Block(block_size * 15, HEIGHT - block_size * 5, block_size),
        Block(block_size * 16, HEIGHT - block_size * 5, block_size),
        Block(block_size * 17, HEIGHT - block_size * 5, block_size),
        Block(block_size * 22, HEIGHT - block_size * 2, block_size),
        Block(block_size * 23, HEIGHT - block_size * 4, block_size),
        Block(block_size * 24, HEIGHT - block_size * 4, block_size),
        Block(block_size * 25, HEIGHT - block_size * 4, block_size),
        Block(block_size * 26, HEIGHT - block_size * 6, block_size),
        Block(block_size * 26, HEIGHT - block_size * 4, block_size),
        Block(block_size * 23, HEIGHT - block_size * 4, block_size),
        Block(block_size * 27, HEIGHT - block_size * 4, block_size),
        Block(block_size * 30, HEIGHT - block_size * 4, block_size),
        Block(block_size * 31, HEIGHT - block_size * 5, block_size),
        Block(block_size * 32, HEIGHT - block_size * 6, block_size),
        Block(block_size * 33, HEIGHT - block_size * 6, block_size),
        Block(block_size * 34, HEIGHT - block_size * 6, block_size),
        Block(block_size * 35, HEIGHT - block_size * 6, block_size),
    ],
    "enemies": [
        Exit(3200, HEIGHT - block_size * 7.25, 4),
        Blob(940, HEIGHT - block_size * 4.5, 50, 50, 80, "left"),
        Heart(3100, 100)
    ]
},
    {# level9
        "background": "Green.png",
        "player_start": (0, 600),
        "obstacles": [
            Block(block_size * 0, HEIGHT - block_size * 1, block_size),
            Block(block_size * 1, HEIGHT - block_size * 1, block_size),
            Block(block_size * 2, HEIGHT - block_size * 1, block_size),
            Block(block_size * 3, HEIGHT - block_size * 1, block_size),
            Block(block_size * 4, HEIGHT - block_size * 1, block_size),
            Block(block_size * 5, HEIGHT - block_size * 1, block_size),
            Block(block_size * 6, HEIGHT - block_size * 1, block_size),
            Block(block_size * 7, HEIGHT - block_size * 1, block_size),
            Block(block_size * 8, HEIGHT - block_size * 1, block_size),
            Block(block_size * 9, HEIGHT - block_size * 1, block_size),
            Block(block_size * 10, HEIGHT - block_size * 1, block_size),
            Block(block_size * 11, HEIGHT - block_size * 1, block_size),
            Block(block_size * 12, HEIGHT - block_size * 1, block_size),
            Block(block_size * 13, HEIGHT - block_size * 1, block_size),
            Block(block_size * 14, HEIGHT - block_size * 1, block_size),
            Block(block_size * 15, HEIGHT - block_size * 1, block_size),
            Block(block_size * 16, HEIGHT - block_size * 1, block_size),
 
        ],
        "enemies": [
            Exit(1001, HEIGHT - block_size * 2.25, 4),
            shaddow(1050, 900)
        ]
    },
{# level 10
    "background": "Green.png",
    "player_start": [0,600],
    "obstacles": [
        Block(block_size * 0, HEIGHT - block_size * 0, block_size),
        Block(block_size * 3, HEIGHT - block_size * 1, block_size),
        Block(block_size * 5, HEIGHT - block_size * 2, block_size),
        Block(block_size * 0, HEIGHT - block_size * 1, block_size),
        Block(block_size * 1, HEIGHT - block_size * 1, block_size),
        Block(block_size * 2, HEIGHT - block_size * 1, block_size),
        Block(block_size * 7, HEIGHT - block_size * 3, block_size),
        Block(block_size * 9, HEIGHT - block_size * 2, block_size),
        Block(block_size * 13, HEIGHT - block_size * 2, block_size),
        Block(block_size * 16, HEIGHT - block_size * 3, block_size),
        Block(block_size * 21, HEIGHT - block_size * 2, block_size),
        Block(block_size * 18, HEIGHT - block_size * 2, block_size),
        Block(block_size * 24, HEIGHT - block_size * 2, block_size),
        Block(block_size * 28, HEIGHT - block_size * 2, block_size),
        Block(block_size * 29, HEIGHT - block_size * 2, block_size),
        Block(block_size * 30, HEIGHT - block_size * 2, block_size),
        Block(block_size * 31, HEIGHT - block_size * 2, block_size),
        
    ],

    "enemies": [
        Exit(3000, HEIGHT - block_size * 3.25, 4),
        shaddow(200, 200),
        Heart(2910, 500)
    ]
    },
    {# level 11
        "background": "Blue.png",
        "player_start": (0, 600),
        "obstacles": [
            Block(block_size * 0, HEIGHT - block_size * 1, block_size),
            Block(block_size * 1, HEIGHT - block_size * 1, block_size),
            Block(block_size * 2, HEIGHT - block_size * 1, block_size),
            Block(block_size * 3, HEIGHT - block_size * 1, block_size),
            Block(block_size * 4, HEIGHT - block_size * 1, block_size),
            Block(block_size * 5, HEIGHT - block_size * 1, block_size),
            Block(block_size * 6, HEIGHT - block_size * 1, block_size),
            Block(block_size * 7, HEIGHT - block_size * 1, block_size),
            Block(block_size * 8, HEIGHT - block_size * 1, block_size),
            Block(block_size * 9, HEIGHT - block_size * 1, block_size),
            Block(block_size * 10, HEIGHT - block_size * 1, block_size),
            Block(block_size * 11, HEIGHT - block_size * 1, block_size),
            Block(block_size * 12, HEIGHT - block_size * 1, block_size),
            Block(block_size * 13, HEIGHT - block_size * 1, block_size),
            Block(block_size * 14, HEIGHT - block_size * 1, block_size),
            Block(block_size * 15, HEIGHT - block_size * 1, block_size),
            Block(block_size * 16, HEIGHT - block_size * 1, block_size),
 
        ],
        "enemies": [
            Exit(1001, HEIGHT - block_size * 2.25, 4),
            Crab(500, HEIGHT - block_size * 1.4, 50, 50, 500, "left"),
            Bat(200, 200, 45, 45)
        ]
    },
    {
    "background": "sky.png",
    "player_start": [0, 600],
    "obstacles": [
         Block(block_size * 0, HEIGHT - block_size * 1, block_size),
         Block(block_size * 1, HEIGHT - block_size * 1, block_size),
         Block(block_size * 2, HEIGHT - block_size * 1, block_size),
         Block(block_size * 3, HEIGHT - block_size * 2, block_size),
         Block(block_size * 6, HEIGHT - block_size * 3, block_size),
         Block(block_size * 8, HEIGHT - block_size * 3, block_size),
         Block(block_size * 11, HEIGHT - block_size * 3, block_size),
         Block(block_size * 13, HEIGHT - block_size * 5, block_size),
         Block(block_size * 13, HEIGHT - block_size * 4, block_size),
         Block(block_size * 12, HEIGHT - block_size * 4, block_size),
         Block(block_size * 3, HEIGHT - block_size * 1, block_size),
         Block(block_size * 3, HEIGHT - block_size * 0, block_size),
         Block(block_size * 6, HEIGHT - block_size * 2, block_size),
         Block(block_size * 6, HEIGHT - block_size * 1, block_size),
         Block(block_size * 6, HEIGHT - block_size * 0, block_size),
         Block(block_size * 14, HEIGHT - block_size * 6, block_size),
         Block(block_size * 17, HEIGHT - block_size * 6, block_size),
         Block(block_size * 14, HEIGHT - block_size * 5, block_size),
         Block(block_size * 14, HEIGHT - block_size * 3, block_size),
         Block(block_size * 14, HEIGHT - block_size * 4, block_size),
         Block(block_size * 13, HEIGHT - block_size * 3, block_size),
         Block(block_size * 12, HEIGHT - block_size * 3, block_size),
         Block(block_size * 19, HEIGHT - block_size * 8, block_size),
         Block(block_size * 22, HEIGHT - block_size * 7, block_size),
         Block(block_size * 22, HEIGHT - block_size * 6, block_size),
         Block(block_size * 22, HEIGHT - block_size * 5, block_size),
         Block(block_size * 22, HEIGHT - block_size * 3, block_size),
         Block(block_size * 22, HEIGHT - block_size * 2, block_size),
         Block(block_size * 22, HEIGHT - block_size * 4, block_size),
         Block(block_size * 22, HEIGHT - block_size * 0, block_size),
         Block(block_size * 22, HEIGHT - block_size * 1, block_size),
         Block(block_size * 19, HEIGHT - block_size * 7, block_size),
         Block(block_size * 19, HEIGHT - block_size * 5, block_size),
         Block(block_size * 17, HEIGHT - block_size * 5, block_size),
         Block(block_size * 19, HEIGHT - block_size * 6, block_size),
         Block(block_size * 17, HEIGHT - block_size * 4, block_size),
         Block(block_size * 17, HEIGHT - block_size * 3, block_size),
         Block(block_size * 17, HEIGHT - block_size * 2, block_size),
         Block(block_size * 17, HEIGHT - block_size * 1, block_size),
         Block(block_size * 19, HEIGHT - block_size * 4, block_size),
         Block(block_size * 19, HEIGHT - block_size * 3, block_size),
         Block(block_size * 19, HEIGHT - block_size * 2, block_size),
         Block(block_size * 19, HEIGHT - block_size * 1, block_size),
         Block(block_size * 11, HEIGHT - block_size * 2, block_size),
         Block(block_size * 12, HEIGHT - block_size * 2, block_size),
         Block(block_size * 14, HEIGHT - block_size * 2, block_size),
         Block(block_size * 13, HEIGHT - block_size * 2, block_size),
         Block(block_size * 11, HEIGHT - block_size * 1, block_size),
         Block(block_size * 14, HEIGHT - block_size * 1, block_size),
         Block(block_size * 12, HEIGHT - block_size * 1, block_size),
         Block(block_size * 13, HEIGHT - block_size * 1, block_size),
         Block(block_size * 24, HEIGHT - block_size * 6, block_size),
         Block(block_size * 25, HEIGHT - block_size * 6, block_size),
         Block(block_size * 26, HEIGHT - block_size * 6, block_size),
         Block(block_size * 27, HEIGHT - block_size * 6, block_size),
         Block(block_size * 28, HEIGHT - block_size * 6, block_size),
    ],
    "enemies": [
        shaddow(200, 200),
        Exit(2800, HEIGHT - block_size * 6.25, 4),
    ]
    },
    {
    "background": "Pink.png",
    "player_start": [0, 600],
    "obstacles": [
        Block(block_size * 0, HEIGHT - block_size * 1, block_size),
        Block(block_size * 2, HEIGHT - block_size * 1, block_size),
        Block(block_size * 4, HEIGHT - block_size * 1, block_size),
        Block(block_size * 6, HEIGHT - block_size * 2, block_size),
        Block(block_size * 8, HEIGHT - block_size * 4, block_size),
        Block(block_size * 10, HEIGHT - block_size * 4, block_size),
        Block(block_size * 13, HEIGHT - block_size * 4, block_size),
        Block(block_size * 12, HEIGHT - block_size * 4, block_size),
        Block(block_size * 15, HEIGHT - block_size * 4, block_size),
        Block(block_size * 17, HEIGHT - block_size * 3, block_size),
        Block(block_size * 19, HEIGHT - block_size * 5, block_size),
        Block(block_size * 21, HEIGHT - block_size * 2, block_size),
        Block(block_size * 24, HEIGHT - block_size * 2, block_size),
        Block(block_size * 26, HEIGHT - block_size * 4, block_size),
        Block(block_size * 28, HEIGHT - block_size * 5, block_size),
        Block(block_size * 27, HEIGHT - block_size * 4, block_size),
        Block(block_size * 28, HEIGHT - block_size * 4, block_size)
        ],
    "enemies": [
        Exit(2800, HEIGHT - block_size * 6.25, 4)
    ]
    },
    {
    "background": "Gray.png",
    "player_start": [0,600],
    "obstacles": [
        Block(block_size * 0, HEIGHT - block_size * 1, block_size),
        Block(block_size * 1, HEIGHT - block_size * 1, block_size),
        Block(block_size * 2, HEIGHT - block_size * 1, block_size),
        Block(block_size * 5, HEIGHT - block_size * 1, block_size),
        Block(block_size * 6, HEIGHT - block_size * 2, block_size),
        Block(block_size * 6, HEIGHT - block_size * 1, block_size),
        Block(block_size * 7, HEIGHT - block_size * 2, block_size),
        Block(block_size * 7, HEIGHT - block_size * 1, block_size),
        Block(block_size * 7, HEIGHT - block_size * 3, block_size),
        Block(block_size * 9, HEIGHT - block_size * 4, block_size),
        Block(block_size * 10, HEIGHT - block_size * 5, block_size),
        Block(block_size * 10, HEIGHT - block_size * 4, block_size),
        Block(block_size * 9, HEIGHT - block_size * 3, block_size),
        Block(block_size * 10, HEIGHT - block_size * 3, block_size),
        Block(block_size * 11, HEIGHT - block_size * 5, block_size),
        Block(block_size * 12, HEIGHT - block_size * 5, block_size),
        Block(block_size * 11, HEIGHT - block_size * 4, block_size),
        Block(block_size * 11, HEIGHT - block_size * 3, block_size),
        Block(block_size * 12, HEIGHT - block_size * 4, block_size),
        Block(block_size * 12, HEIGHT - block_size * 3, block_size),
        Block(block_size * 14, HEIGHT - block_size * 5, block_size),
        Block(block_size * 15, HEIGHT - block_size * 5, block_size),
        Block(block_size * 16, HEIGHT - block_size * 5, block_size),
        Block(block_size * 17, HEIGHT - block_size * 5, block_size),
        Block(block_size * 18, HEIGHT - block_size * 5, block_size),
        Block(block_size * 14, HEIGHT - block_size * 4, block_size),
        Block(block_size * 14, HEIGHT - block_size * 4, block_size),
        Block(block_size * 14, HEIGHT - block_size * 3, block_size),
        Block(block_size * 21, HEIGHT - block_size * 6, block_size),
        Block(block_size * 23, HEIGHT - block_size * 7, block_size),
        Block(block_size * 24, HEIGHT - block_size * 7, block_size),
        Block(block_size * 24, HEIGHT - block_size * 7, block_size),
        Block(block_size * 25, HEIGHT - block_size * 7, block_size),
        Block(block_size * 26, HEIGHT - block_size * 7, block_size),
        Block(block_size * 27, HEIGHT - block_size * 7, block_size)
    ],
    "enemies": [
        Blob(1075, HEIGHT - block_size * 5.5, 50, 50, 125, 'right'),
        Crab(1540, HEIGHT - block_size * 5.4, 50, 50, 220, 'right'),
        Blob(2400, HEIGHT - block_size * 7.5, 50, 50, 125, 'right'),
        Exit(2601, HEIGHT - block_size * 8.25, 4),
        shaddow(0, 400),
        shaddow(0, 800)
    ]
},
{
    "background": "Blue.png",
    "player_start": [0, 600],
    "obstacles": [
        Block(block_size * 0, HEIGHT - block_size * 1, block_size),
        Block(block_size * 2, HEIGHT - block_size * 1, block_size),
        Block(block_size * 1, HEIGHT - block_size * 1, block_size),
        Block(block_size * 6, HEIGHT - block_size * 1, block_size),
        Block(block_size * 7, HEIGHT - block_size * 2, block_size),
        Block(block_size * 7, HEIGHT - block_size * 1, block_size),
        Block(block_size * 7, HEIGHT - block_size * 0, block_size),
        Block(block_size * 8, HEIGHT - block_size * 3, block_size),
        Block(block_size * 9, HEIGHT - block_size * 3, block_size),
        Block(block_size * 8, HEIGHT - block_size * 2, block_size),
        Block(block_size * 9, HEIGHT - block_size * 2, block_size),
        Block(block_size * 9, HEIGHT - block_size * 1, block_size),
        Block(block_size * 8, HEIGHT - block_size * 1, block_size),
        Block(block_size * 8, HEIGHT - block_size * 0, block_size),
        Block(block_size * 9, HEIGHT - block_size * 0, block_size),
        Block(block_size * 6, HEIGHT - block_size * 0, block_size),
        Block(block_size * 10, HEIGHT - block_size * 1, block_size),
        Block(block_size * 11, HEIGHT - block_size * 1, block_size),
        Block(block_size * 2, HEIGHT - block_size * 0, block_size),
        Block(block_size * 1, HEIGHT - block_size * 0, block_size),
        Block(block_size * 0, HEIGHT - block_size * 0, block_size),
        Block(block_size * 10, HEIGHT - block_size * 2, block_size),
        Block(block_size * 10, HEIGHT - block_size * 3, block_size),
        Block(block_size * 11, HEIGHT - block_size * 3, block_size),
        Block(block_size * 11, HEIGHT - block_size * 2, block_size),
        Block(block_size * 13, HEIGHT - block_size * 3, block_size),
        Block(block_size * 16, HEIGHT - block_size * 3, block_size),
        Block(block_size * 16, HEIGHT - block_size * 2, block_size),
        Block(block_size * 16, HEIGHT - block_size * 1, block_size),
        Block(block_size * 13, HEIGHT - block_size * 2, block_size),
        Block(block_size * 13, HEIGHT - block_size * 1, block_size),
        Block(block_size * 19, HEIGHT - block_size * 3, block_size),
        Block(block_size * 19, HEIGHT - block_size * 2, block_size),
        Block(block_size * 19, HEIGHT - block_size * 1, block_size),
        Block(block_size * 21, HEIGHT - block_size * 3, block_size),
        Block(block_size * 20, HEIGHT - block_size * 3, block_size),
        Block(block_size * 24, HEIGHT - block_size * 4, block_size),
        Block(block_size * 21, HEIGHT - block_size * 2, block_size),
        Block(block_size * 21, HEIGHT - block_size * 1, block_size),
        Block(block_size * 20, HEIGHT - block_size * 1, block_size),
        Block(block_size * 20, HEIGHT - block_size * 2, block_size),
        Block(block_size * 20, HEIGHT - block_size * 0, block_size),
        Block(block_size * 19, HEIGHT - block_size * 0, block_size),
        Block(block_size * 21, HEIGHT - block_size * 0, block_size),
        Block(block_size * 24, HEIGHT - block_size * 3, block_size),
        Block(block_size * 24, HEIGHT - block_size * 2, block_size),
        Block(block_size * 24, HEIGHT - block_size * 1, block_size),
        Block(block_size * 24, HEIGHT - block_size * 0, block_size),
        Block(block_size * 25, HEIGHT - block_size * 4, block_size),
        Block(block_size * 26, HEIGHT - block_size * 4, block_size),
        Block(block_size * 25, HEIGHT - block_size * 3, block_size),
        Block(block_size * 26, HEIGHT - block_size * 3, block_size),
        Block(block_size * 25, HEIGHT - block_size * 2, block_size),
        Block(block_size * 26, HEIGHT - block_size * 2, block_size),
        Block(block_size * 25, HEIGHT - block_size * 1, block_size),
        Block(block_size * 26, HEIGHT - block_size * 1, block_size),
        Block(block_size * 26, HEIGHT - block_size * 0, block_size),
        Block(block_size * 27, HEIGHT - block_size * 0, block_size),
        Block(block_size * 25, HEIGHT - block_size * 0, block_size)
    ],
    "enemies": [
        shaddow(100, 1),
        shaddow(200, 1),
        shaddow(300, 1),
        shaddow(400, 1),
        Exit(2501, HEIGHT - block_size * 5.25, 4),
    ]
},
    {
        "background": "Green.png",
        "player_start": (0, 600),
        "obstacles": [
            Block(block_size * 0, HEIGHT - block_size * 1, block_size),
            Block(block_size * 1, HEIGHT - block_size * 1, block_size),
            Block(block_size * 2, HEIGHT - block_size * 1, block_size),
            Block(block_size * 3, HEIGHT - block_size * 1, block_size),
            Block(block_size * 4, HEIGHT - block_size * 1, block_size),
            Block(block_size * 5, HEIGHT - block_size * 1, block_size),
            Block(block_size * 6, HEIGHT - block_size * 1, block_size),
            Block(block_size * 7, HEIGHT - block_size * 1, block_size),
            Block(block_size * 8, HEIGHT - block_size * 1, block_size),
            Block(block_size * 9, HEIGHT - block_size * 1, block_size),
            Block(block_size * 10, HEIGHT - block_size * 1, block_size),
            Block(block_size * 11, HEIGHT - block_size * 1, block_size),
            Block(block_size * 12, HEIGHT - block_size * 1, block_size),
            Block(block_size * 13, HEIGHT - block_size * 1, block_size),
            Block(block_size * 14, HEIGHT - block_size * 1, block_size),
            Block(block_size * 15, HEIGHT - block_size * 1, block_size),
            Block(block_size * 16, HEIGHT - block_size * 1, block_size),
 
        ],
        "enemies": [
            Exit(1001, HEIGHT - block_size * 2.25, 4),
            log(1200, 640, 64, 64, direction="right"),

        ]
    },
    
        {
    "background": "Yellow.png",
    "player_start": [0,600],
    "obstacles": [
        Block(block_size * 0, HEIGHT - block_size * 1, block_size),
        Block(block_size * 2, HEIGHT - block_size * 1, block_size),
        Block(block_size * 5, HEIGHT - block_size * 1, block_size),
        Block(block_size * 6, HEIGHT - block_size * 2, block_size),
        Block(block_size * 7, HEIGHT - block_size * 3, block_size),
        Block(block_size * 7, HEIGHT - block_size * 2, block_size),
        Block(block_size * 7, HEIGHT - block_size * 1, block_size),
        Block(block_size * 6, HEIGHT - block_size * 1, block_size),
        Block(block_size * 9, HEIGHT - block_size * 3, block_size),
        Block(block_size * 10, HEIGHT - block_size * 3, block_size),
        Block(block_size * 11, HEIGHT - block_size * 5, block_size),
        Block(block_size * 13, HEIGHT - block_size * 6, block_size),
        Block(block_size * 14, HEIGHT - block_size * 8, block_size),
        Block(block_size * 13, HEIGHT - block_size * 5, block_size),
        Block(block_size * 14, HEIGHT - block_size * 7, block_size),
        Block(block_size * 13, HEIGHT - block_size * 7, block_size),
        Block(block_size * 16, HEIGHT - block_size * 6, block_size),
        Block(block_size * 18, HEIGHT - block_size * 5, block_size),
        Block(block_size * 17, HEIGHT - block_size * 5, block_size),
        Block(block_size * 21, HEIGHT - block_size * 4, block_size),
        Block(block_size * 22, HEIGHT - block_size * 4, block_size),
        Block(block_size * 23, HEIGHT - block_size * 4, block_size),
        Block(block_size * 24, HEIGHT - block_size * 4, block_size),
        Block(block_size * 25, HEIGHT - block_size * 4, block_size),
        Block(block_size * 14, HEIGHT - block_size * 4, block_size)
    ],
    "enemies": [
        log(1300, 352, 64, 64, direction="right"),
        log(1350, 352, 64, 64, direction="left"),
        shaddow(-500, 500),
        Exit(2500, HEIGHT - block_size * 5.25, 4)
    ]
},
]


async def main(window):
    def check_player_health(player):
       if player.health <= 0: 
            show_game_over_screen(window)

    clock = pygame.time.Clock()
    current_level = 0
    score = 0
    background, bg_image = get_background(levels[current_level]["background"])
    player = Player(*levels[current_level]["player_start"], 50, 50)
    objects = [*levels[current_level]["obstacles"], *levels[current_level]["enemies"]]
    offset_x = 0
    scroll_area_width = 750
    elapsed_time = 0  
    
    run = True
    while run:
        clock.tick(FPS)
        elapsed_time += 1 / FPS

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                player.dash()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                player.dash2()


        player.loop(FPS)
        handle_move(player, objects, 0)
        
        for obj in objects:
            if isinstance(obj, Blob):
                obj.loop()
            if isinstance(obj, Crab): 
                obj.loop()
            if isinstance(obj, shaddow):
                obj.follow_player(player)
            if isinstance(obj, log):
                obj.loop(player)
            if isinstance(obj, Bat):
                obj.loop(player)

        exit_collision = pygame.sprite.spritecollideany(player, [obj for obj in objects if isinstance(obj, Exit)])
        if exit_collision:
            score += 1
            time.sleep(0.2)
            current_level += 1

            if current_level < len(levels):
                background, bg_image = get_background(levels[current_level]["background"])
                player.rect.topleft = levels[current_level]["player_start"]
                objects = [*levels[current_level]["obstacles"], *levels[current_level]["enemies"]]
                offset_x = 0
            else:
                show_victory_screen(window)
                
        check_player_health(player)
        draw(window, background, bg_image, player, objects, offset_x, score, elapsed_time)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

        if player.rect.bottom > HEIGHT:
            player.rect.topleft = levels[current_level]["player_start"]
            player.x_vel = 0
            player.y_vel = 0
            player.fall_count = 0
            player.jump_count = 2
            offset_x = 0
            player.hit = 1
            time.sleep(0.2)
            player.decrease_health(1, 25)
    await asyncio.sleep(0)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main(window)
asyncio.run(main(window))



#ashton salter senior directer of art made heart and lvl 0 background and shaddow