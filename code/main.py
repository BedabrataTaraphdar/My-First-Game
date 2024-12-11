from settings import *
from player import Player
from button import Button
from sprites import *
from random import randint, choice
from pytmx.util_pygame import load_pygame
from groups import AllSprites
import os
import sys
import csv
from tabulate import tabulate

class Game():
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT))
        pygame.display.set_caption('Survivor')
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False
        self.game_paused = True
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        #self.all_buttons = pygame.sprite.Group()

        #enemy timer
        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 300)
        self.spawn_positions = []
        self.enemy_cooldown = 600

        self.can_shoot = True
        self.can_spawn = False
        self.shoot_time = 0
        self.gun_cooldown = 300

        #setup
        self.load_images()
        self.setup()

        #score
        self.score = 0
        self.font_tiny = pygame.font.SysFont('Lucida Sans', 14)
        self.font_small = pygame.font.SysFont('Lucida Sans', 20)
        self.font_big = pygame.font.SysFont('Lucida Sans', 100)
        self.data = list()
        self.List=list()
        self.ScoreList = list()
        self.Top10 = list()
        self.rowcount = 0

        #buttons
        self.name_Screen = pygame.image.load(join('images','BG','NameScreen.jpg')).convert_alpha()
        self.bg = pygame.image.load(join('images','BG','BackGround.jpg')).convert_alpha()
        self.gO = pygame.image.load(join('images','BG','gameOver.jpg')).convert_alpha()
        self.scoreDis = pygame.image.load(join('images','BG','scoreDisplay.png'))
        self.image = pygame.image.load(join('images','buttons','Start.png')).convert_alpha()
        self.start_btn = Button(50, WINDOW_HEIGHT//5,self.image,1.5)
        self.restart = pygame.image.load(join('images','buttons','Restart.png')).convert_alpha()
        self.restart_btn = Button(500, WINDOW_HEIGHT//3,self.restart,1.5)
        self.leaderboard = pygame.image.load(join('images','buttons','Leaderboard.png')).convert_alpha()
        self.lead_btn = Button(50,WINDOW_HEIGHT//2,self.leaderboard,1.5)
        self.back = pygame.image.load(join('images','buttons','Menu.png')).convert_alpha()
        self.back_btn = Button(500,WINDOW_HEIGHT//1.2,self.back,1.5)
        self.menu = pygame.image.load(join('images','buttons','Menu.png')).convert_alpha()
        self.menu_btn = Button(500,WINDOW_HEIGHT//1.5,self.menu,1.5)

        #GUI
        self.manager = pygame_gui.UIManager((WINDOW_WIDTH,WINDOW_HEIGHT))
        self.text_input = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((200,275), (900,50)), manager=self.manager, object_id='#main_text_entry')
        self.menu_state = 'main'
        

        if os.path.exists('score.txt'):
            with open('score.txt', 'r') as f:
                self.highscore = int(f.read())
        else:
            self.highscore = 0

        #design
        self.black = (0,0,0)
        self.white = (210,180,140)
        self.red = (102,0,0)
        self.yellow = (255,233,42)
        self.fade_counter = 0

    def load_images(self):
        self.bullet_surf = pygame.image.load(join('images','gun','bullet.png')).convert_alpha()

        folders = list(walk(join('images','enemies')))[0][1]
        self.enemy_frames = {}
        for folder in folders:
            for folder_path, _, file_names in walk(join('images','enemies',folder)):
                self.enemy_frames[folder] = []
                for file_name in sorted(file_names, key = lambda name: int(name.split('.')[0])):
                    full_path = join(folder_path, file_name)
                    surf = pygame.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)

    def draw_text(self, text, font, text_col, x, y):
        img = font.render(text, True, text_col)
        self.display_surface.blit(img, (x, y))

    def draw_panel(self):
        pygame.draw.rect(self.display_surface, self.black, (0,0, WINDOW_WIDTH, 30))
        pygame.draw.line(self.display_surface, self.black, (0, 30), (WINDOW_WIDTH, 30), 2)
        self.draw_text('SCORE: '+str(self.score), self.font_small, self.red, 0,0 )

    def input(self):
        if pygame.mouse.get_pressed()[0] and self.can_shoot:
            pos = self.gun.rect.center + self.gun.player_direction * 50
            Bullet(self.bullet_surf, pos, self.gun.player_direction, (self.all_sprites, self.bullet_sprites))
            self.can_shoot = False
            self.shoot_time = pygame.time.get_ticks()

    def gun_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.gun_cooldown:
                self.can_shoot = True

    def enemy_timer(self):
        if not self.can_spawn:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.enemy_cooldown:
                self.can_spawn = True

    def setup(self):
        map = load_pygame(join('data','maps','world.tmx'))

        for x, y, image in map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE), image, self.all_sprites)
        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x,obj.y), obj.image, (self.all_sprites, self.collision_sprites))
        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x,obj.y), pygame.Surface((obj.width,obj.height)),self.collision_sprites)

        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player(self.all_sprites, (obj.x,obj.y), self.collision_sprites)
                self.gun = Gun(self.player, self.all_sprites)
            else:
                self.spawn_positions.append((obj.x,obj.y))

    def bullet_collision(self):
        if self.bullet_sprites:
            for bullet in self.bullet_sprites:
                collision_sprites = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
                if collision_sprites:
                    self.score+=1
                    for sprite in collision_sprites:
                        sprite.destroy()
                    bullet.kill()

    def player_collision(self):
        if pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask):
            self.game_over = True

    def user_name_input(self, dt):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(0)
                if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED and event.ui_object_id == '#main_text_entry':
                    self.data.append(event.text)
                    self.game_paused = False
                    return self.game_paused
            
                self.manager.process_events(event)
            self.manager.update(dt)
            self.display_surface.blit(self.name_Screen)
            self.manager.draw_ui(self.display_surface)
            pygame.display.update()

    def read_score(self):
        with open('score.csv','r') as g:
            data = csv.reader(g)
            for r in data:
                self.List.append(r)
                self.rowcount+=1
        for i in range(self.rowcount):
            if len(self.List[i]) >= 1:
                for j in range(1):
                    self.ScoreList.append(self.List[i])
        for i in range(len(self.ScoreList)-1):
            for j in range(len(self.ScoreList)-i-1):
                if int(self.ScoreList[j][1]) < int(self.ScoreList[j+1][1]):
                    self.ScoreList[j+1],self.ScoreList[j] = self.ScoreList[j],self.ScoreList[j+1]
        for ele in self.ScoreList:
            for i in range(2):
                for tele in self.ScoreList:
                    if int(ele[1]) > int(tele[1]) and tele[0] == ele[0]:
                        self.ScoreList.remove(tele)
        self.Top10 = [["Name","Score","Rank"]]
        if len(self.ScoreList)<10:
            for i in range(len(self.ScoreList)):
                temp = self.ScoreList[i]
                temp.append(i+1)
                self.Top10.append(temp)
        else:
            for i in range(10):
                temp = self.ScoreList[i]
                temp.append(i+1)
                self.Top10.append(temp)

    def show_score(self):
        self.display_surface.blit(self.scoreDis)
        self.read_score()
        self.draw_text(tabulate(self.Top10, headers="firstrow", tablefmt="pipe"), self.font_tiny, self.yellow,470,200)
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            if self.back_btn.draw(self.display_surface):
                self.running = False
                return None
            pygame.display.update()

    def saveFile(self):
        with open('score.csv', 'a') as f:
            writer = csv.writer(f)
            #writer.writerow(self.List[0:])
            writer.writerow([self.data[0],self.data[1]])

    def Menu(self):
        dt = self.clock.tick(60)/1000
        self.display_surface.blit(self.bg)
        while self.running:
            for event in pygame.event.get():
                self.display_surface.blit(self.bg)
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.K_SPACE:
                    self.game_paused = True
            if self.start_btn.draw(self.display_surface):
                self.menu_state = 'start'
            if self.lead_btn.draw(self.display_surface):
                self.menu_state = 'leaderboard'
            if self.menu_state == 'start':
                self.user_name_input(dt/7)
            if self.menu_state == 'leaderboard':
                return 'ScoreBoard'
            pygame.display.update()
            break
            
    def Restart(self):
        self.display_surface.blit(self.gO)
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            self.draw_text('SCORE: ' + str(self.score), self.font_big, self.red, 385, 200)

            if self.menu_btn.draw(self.display_surface):
                self.data.append(self.score)
                self.saveFile()
                self.running = False
                
            pygame.display.update()   
    
    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000
            if self.game_paused == True:
                if self.menu_state == 'restart':
                    self.Restart()
                if self.menu_state == 'main' or self.show_score() == None:
                    self.Menu()
            else:
                # update
                if self.game_over == False:
                    self.gun_timer()
                    self.input()
                    self.all_sprites.update(dt)
                    self.bullet_collision()
                    self.player_collision()
                    # draw the game
                    self.display_surface.fill('black')
                    self.all_sprites.draw(self.player.rect.center)
                    self.draw_panel()
                
                if self.game_over == True:
                    self.game_paused = True
                    self.menu_state = 'restart'
                    #self.gameOver()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    if event.type == pygame.K_SPACE:
                        self.game_paused = True
                    if event.type == self.enemy_event:
                        Enemy(choice(self.spawn_positions), choice(list(self.enemy_frames.values())), (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites)
            pygame.display.update()

    pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()

