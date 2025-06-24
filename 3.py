#----------------------------------------------ИМПОРТ БИБЛИОТЕК----------------------------------------------
import random
import pygame
import math
from enum import Enum
#----------------------------------------------ИНИЦИАЛИЗАЦИЯ----------------------------------------------
pygame.init()
pygame.font.init()
#----------------------------------------------КОНСТАНТЫ----------------------------------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700
GRID_SIZE = 5
FPS = 120
DEFAULT_CAVALRY = 0
DEFAULT_INFANTRY = 0
TOP_PANEL_HEIGHT = 30
global_player_cavalry = DEFAULT_CAVALRY
global_player_infantry = DEFAULT_INFANTRY
global_enemy_cavalry = DEFAULT_CAVALRY
global_enemy_infantry = DEFAULT_INFANTRY
global_player_cavalry_positions = []
global_player_infantry_positions = []
global_environment = None
global_enemy_positions = []
#----------------------------------------------ЦВЕТА----------------------------------------------
COLORS = {
    'player_infantry': (100, 255, 100),
    'player_cavalry': (100, 100, 255),
    'player_artillery': (150, 150, 255),  # Новый цвет для артиллерии игрока
    'enemy_infantry': (255, 100, 100),
    'enemy_cavalry': (255, 255, 100),
    'enemy_artillery': (255, 150, 100),   # Новый цвет для артиллерии врага
    'background': (0, 100, 0),
    'selection': (255, 255, 0, 150),
    'path_line': (255, 255, 255),
    'panel_bg': (50, 50, 50),
    'panel_border': (200, 200, 200),
    'highlight': (255, 255, 0),
    'text': (255, 255, 255),
    'button': (100, 100, 100),
    'button_hover': (150, 150, 150),
    'outline': (0, 0, 0),
    'menu_bg': (30, 30, 60),
    'deployment_area': (50, 50, 80),
    'enemy_area': (80, 50, 50),
    'unit_counter': (200, 200, 200),
    'corpse': (30, 30, 30),
    'top_panel': (40, 40, 40),
    'victory_panel': (30, 60, 30),
    'defeat_panel': (60, 30, 30)
}
#----------------------------------------------СОЗДАНИЕ ЭКРАНА----------------------------------------------
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Пиксельные армии")
#----------------------------------------------ТИП ЮНИТА----------------------------------------------
class UnitType(Enum):
    INFANTRY = 1
    CAVALRY = 2
    ARTILLERY = 3  # Новый тип юнита
#----------------------------------------------КЛАСС СОЛДАТА----------------------------------------------
class Soldier:
    def __init__(self, x, y, team, unit_type):
        self.x = x
        self.y = y
        self.team = team
        self.type = unit_type
        self.health = 100
        self.selected = False
        self.direction = None
        self.special_cooldown = 0
        self.attack_cooldown = 0
        self.target_direction = None
        self.current_target = None
        self.avoidance_force = 0
        self.last_attack_time = 0
        self.temporary_movement_end_time = 0
        self.temporary_direction = None
        self.formation_position = None
        self.avoidance_force = [0, 0]
        self.formation_spacing = GRID_SIZE + 2
        self.last_artillery_shot = 0  # Время последнего выстрела артиллерии
        self.artillery_target = None  # Цель для артиллерии

        # Усиленные характеристики для вражеских юнитов
        if team == 'enemy':
            if self.type == UnitType.INFANTRY:
                self.stats = {
                    'power': random.randint(90, 100),
                    'armor': random.randint(50, 90),
                    'speed': 0.1,
                    'range': GRID_SIZE * 2,
                    'attack_speed': 100,
                    'detection_range': GRID_SIZE * 4,
                    'vs_cavalry_bonus': 1.0,
                    'vs_artillery_bonus': 1.2  # Бонус против артиллерии
                }
                self.color = COLORS['enemy_infantry']
            elif self.type == UnitType.CAVALRY:
                self.stats = {
                    'power': random.randint(90, 180),
                    'armor': random.randint(50, 90),
                    'speed': 0.3,
                    'range': GRID_SIZE * 2,
                    'attack_speed': 30,
                    'detection_range': GRID_SIZE * 5,
                    'vs_infantry_penalty': 1.5,
                    'vs_artillery_bonus': 1.5  # Больший бонус против артиллерии
                }
                self.color = COLORS['enemy_cavalry']
            else:  # ARTILLERY
                self.stats = {
                    'power': 70,
                    'armor': 30,
                    'speed': 0,
                    'range': GRID_SIZE * 30,
                    'attack_speed': 4000,
                    'detection_range': GRID_SIZE * 10,
                    'splash_radius': 20,
                    'knockback_force': 20.0
                }
                self.color = COLORS['enemy_artillery']
        else:
            # Стандартные характеристики для игрока
            if self.type == UnitType.INFANTRY:
                self.stats = {
                    'power': random.randint(40, 80),
                    'armor': random.randint(50, 90),
                    'speed': 0.1,
                    'range': GRID_SIZE * 2,
                    'attack_speed': 30,
                    'detection_range': GRID_SIZE * 4,
                    'vs_cavalry_bonus': 1.0,
                    'vs_artillery_bonus': 1.2
                }
                self.color = COLORS['player_infantry']
            elif self.type == UnitType.CAVALRY:
                self.stats = {
                    'power': random.randint(40, 80),
                    'armor': random.randint(50, 90),
                    'speed': 0.3,
                    'range': GRID_SIZE * 2,
                    'attack_speed': 30,
                    'detection_range': GRID_SIZE * 5,
                    'vs_infantry_penalty': 1.5,
                    'vs_artillery_bonus': 1.5
                }
                self.color = COLORS['player_cavalry']
            else:  # ARTILLERY
                self.stats = {
                    'power': 70,
                    'armor': 30,
                    'speed': 0,
                    'range': GRID_SIZE * 30,
                    'attack_speed': 4000,
                    'detection_range': GRID_SIZE * 10,
                    'splash_radius': 20,
                    'knockback_force': 20.0
                }
                self.color = COLORS['player_artillery']

    def draw(self, layer="background"):
        """Отрисовка юнита с учетом слоев"""
        if self.health <= 0 and layer == "background":
            # Рисуем труп как часть фона (нижний слой)
            corpse_color = (
                max(0, min(255, COLORS['corpse'][0] + random.randint(-10, 10))),
                max(0, min(255, COLORS['corpse'][1] + random.randint(-10, 10))),
                max(0, min(255, COLORS['corpse'][2] + random.randint(-10, 10)))
            )
            pygame.draw.rect(screen, corpse_color, (self.x, self.y, GRID_SIZE, GRID_SIZE))
            # Добавляем тень для реализма
            shadow = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 30))
            screen.blit(shadow, (self.x, self.y))
        elif self.health > 0 and layer == "foreground":
            # Увеличенные размеры
            unit_width = GRID_SIZE * 0.8
            unit_height = GRID_SIZE * 1.6

            if self.type == UnitType.CAVALRY:
                horse_color = (139, 69, 19)  # Темно-коричневый
                horse_body_width = unit_width * 1.2
                horse_body_height = unit_height * 0.6

                # Определение направления
                direction = 1  # вправо
                if self.direction is not None:
                    angle = self.direction % (2 * math.pi)
                    if math.pi / 2 < angle < 3 * math.pi / 2:
                        direction = -1  # влево

                # Смещение головы лошади в зависимости от направления
                head_offset = 8 * direction
                head_x = self.x + head_offset if direction == 1 else self.x - horse_body_width
                head_y = self.y + unit_height * 0.4

                # Тело лошади
                pygame.draw.rect(screen, horse_color, (
                    self.x - horse_body_width, self.y + unit_height * 0.4, horse_body_width + 9,
                    horse_body_height + 1))

                # Голова лошади
                pygame.draw.circle(screen, horse_color, (int(head_x), int(head_y)),
                                   int(horse_body_height * 0.5))

                # Ноги лошади
                leg_length_horse = horse_body_height * 1.3
                leg_width_horse = GRID_SIZE * 0.5
                for i in range(4):
                    pygame.draw.rect(screen, horse_color, (
                        self.x - horse_body_width * 0.9 + (i % 2) * horse_body_width * 2,
                        self.y + unit_height * 0.4 + horse_body_height,
                        leg_width_horse, leg_length_horse))

                # Контур тела
                pygame.draw.rect(screen, COLORS['outline'], (
                    self.x - horse_body_width, self.y + unit_height * 0.4, horse_body_width + 9,
                    horse_body_height + 1), 1)

                # Контур головы
                pygame.draw.circle(screen, COLORS['outline'], (int(head_x), int(head_y)),
                                   int(horse_body_height * 0.5), 1)
            # Рисуем артиллерию
            if self.type == UnitType.ARTILLERY:

                pygame.draw.rect(screen, self.color,
                                 (self.x, self.y + GRID_SIZE // 2, GRID_SIZE*2, GRID_SIZE))  # Корпус пушки
                pygame.draw.circle(screen, (0, 0, 0), (self.x + GRID_SIZE, self.y + GRID_SIZE * 1.5), 3)  # Колесо
                pygame.draw.rect(screen, COLORS['outline'], (
                    self.x, self.y + GRID_SIZE // 2, GRID_SIZE*2, GRID_SIZE),1)

            if self.selected:
                pygame.draw.rect(screen, COLORS['highlight'], (self.x , self.y -10, unit_width, 2),
                                 0)
                # Для артиллерии показываем радиус атаки
                if self.type == UnitType.ARTILLERY:
                    radius_surface = pygame.Surface((self.stats['range'] * 2, self.stats['range'] * 2), pygame.SRCALPHA)
                    pygame.draw.circle(radius_surface, (*COLORS['highlight'][:3], 50),
                                       (self.stats['range'], self.stats['range']), self.stats['range'], 1)
                    screen.blit(radius_surface, (
                        self.x + unit_width / 2 - self.stats['range'], self.y + unit_height / 2 - self.stats['range']))

            if self.type != UnitType.ARTILLERY and UnitType.CAVALRY:
                # Рисуем антропоморфного юнита (верхний слой)
                # Тело
                pygame.draw.rect(screen, self.color, (self.x, self.y, unit_width, unit_height))
                # Контур тела
                pygame.draw.rect(screen, COLORS['outline'], (self.x, self.y, unit_width, unit_height), 1)

                # Голова
                head_radius = GRID_SIZE * 0.4
                head_center = (self.x + unit_width / 2, self.y - head_radius)
                pygame.draw.circle(screen, self.color, head_center, head_radius)
                # Контур головы
                pygame.draw.circle(screen, COLORS['outline'], head_center, head_radius, 1)

                # Ноги
                leg_width = GRID_SIZE * 0.25
                leg_length = unit_height * 0.6
                pygame.draw.rect(screen, self.color,
                                 (self.x + unit_width * 0.1, self.y + unit_height, leg_width,
                                  leg_length))  # Левая нога
                pygame.draw.rect(screen, self.color,
                                 (self.x + unit_width * 0.65, self.y + unit_height, leg_width,
                                  leg_length))  # Правая нога
                # Контуры ног
                pygame.draw.rect(screen, COLORS['outline'],
                                 (self.x + unit_width * 0.1, self.y + unit_height, leg_width, leg_length), 1)
                pygame.draw.rect(screen, COLORS['outline'],
                                 (self.x + unit_width * 0.65, self.y + unit_height, leg_width, leg_length), 1)

    def artillery_attack(self, target_x, target_y, enemies):
        """Специальная атака для артиллерии"""
        if self.health <= 0:  # Мертвая артиллерия не может стрелять
            return False

        current_time = pygame.time.get_ticks()
        if current_time - self.last_artillery_shot < self.stats['attack_speed']:
            return False

        self.last_artillery_shot = current_time

        # Рассчитываем направление выстрела
        dx = target_x - (self.x + GRID_SIZE // 2)
        dy = target_y - (self.y + GRID_SIZE // 2)
        distance = max(1, math.sqrt(dx * dx + dy * dy))

        # Ограничиваем дальность стрельбы
        if distance > self.stats['range']:
            target_x = self.x + GRID_SIZE // 2 + dx / distance * self.stats['range']
            target_y = self.y + GRID_SIZE // 2 + dy / distance * self.stats['range']

        # Анимация выстрела
        self.draw_artillery_shot(target_x, target_y)

        # Наносим урон всем врагам в радиусе
        splash_radius = self.stats['splash_radius']
        for enemy in enemies:
            if enemy.health <= 0:
                continue

            enemy_dx = (enemy.x + GRID_SIZE // 2) - target_x
            enemy_dy = (enemy.y + GRID_SIZE // 2) - target_y
            enemy_dist = math.sqrt(enemy_dx * enemy_dx + enemy_dy * enemy_dy)

            if enemy_dist <= splash_radius:
                # Уменьшаем урон для дальних целей
                damage = self.stats['power'] * (1 - enemy_dist / splash_radius)
                enemy.health -= damage

                # Отбрасываем врага
                knockback = self.stats['knockback_force'] * (1 - enemy_dist / splash_radius)
                if enemy_dist > 0:
                    enemy.x += enemy_dx / enemy_dist * knockback
                    enemy.y += enemy_dy / enemy_dist * knockback

                # Ограничиваем позицию
                enemy.x = max(0, min(enemy.x, SCREEN_WIDTH - GRID_SIZE))
                enemy.y = max(TOP_PANEL_HEIGHT, min(enemy.y, SCREEN_HEIGHT - GRID_SIZE))

        return True

    def draw_artillery_shot(self, target_x, target_y):
        """Анимация выстрела артиллерии"""
        start_x = self.x + GRID_SIZE // 2
        start_y = self.y + GRID_SIZE // 2

        # Линия выстрела
        pygame.draw.line(screen, (255, 200, 0), (start_x, start_y), (target_x, target_y), 2)

        # Взрыв на цели
        pygame.draw.circle(screen, (255, 100, 0), (int(target_x), int(target_y)),
                           self.stats['splash_radius'] // 2)
        pygame.draw.circle(screen, (255, 200, 0), (int(target_x), int(target_y)),
                           self.stats['splash_radius'] // 4)

        # Эффект дыма
        for _ in range(10):
            smoke_x = target_x + random.randint(-10, 10)
            smoke_y = target_y + random.randint(-10, 10)
            smoke_size = random.randint(2, 5)
            pygame.draw.circle(screen, (100, 100, 100, 150),
                               (int(smoke_x), int(smoke_y)), smoke_size)

    def attack(self, enemy):
        # Для артиллерии используем специальную атаку
        if self.type == UnitType.ARTILLERY:
            return self.artillery_attack(enemy.x + GRID_SIZE // 2, enemy.y + GRID_SIZE // 2, [enemy])

        # Обычная атака для других юнитов
        base_damage = self.stats['power']
        armor_reduction = enemy.stats['armor'] * 0.3

        # Применяем бонусы/штрафы
        if self.type == UnitType.INFANTRY:
            if enemy.type == UnitType.CAVALRY:
                base_damage *= self.stats['vs_cavalry_bonus']
            elif enemy.type == UnitType.ARTILLERY:
                base_damage *= self.stats['vs_artillery_bonus']
        elif self.type == UnitType.CAVALRY:
            if enemy.type == UnitType.INFANTRY:
                base_damage *= self.stats['vs_infantry_penalty']
            elif enemy.type == UnitType.ARTILLERY:
                base_damage *= self.stats['vs_artillery_bonus']

        damage = max(5, base_damage - armor_reduction)
        enemy.health -= damage

        # Эффект отбрасывания
        push_force = 2.0
        dx = enemy.x - self.x
        dy = enemy.y - self.y
        dist = max(1, math.sqrt(dx * dx + dy * dy))

        enemy.x += int(dx / dist * push_force)
        enemy.y += int(dy / dist * push_force)

        # Ограничение позиции
        enemy.x = max(0, min(enemy.x, SCREEN_WIDTH - GRID_SIZE))
        enemy.y = max(0, min(enemy.y, SCREEN_HEIGHT - GRID_SIZE))

        self.attack_cooldown = self.stats['attack_speed']
        self.last_attack_time = pygame.time.get_ticks()

    def update_movement(self, enemies, allies, environment=None):
        if self.health <= 0:
            return
        # Константы
        TOP_PANEL_HEIGHT = 30
        BORDER_BUFFER = 10
        OBSTACLE_AVOIDANCE_FORCE = 1.5
        OBSTACLE_DETECTION_RANGE = GRID_SIZE * 3
        COVER_RADIUS = GRID_SIZE * 5  # Радиус поиска укрытия

        current_time = pygame.time.get_ticks()

        river_current = (0, 0)
        if environment:
            for obj in environment:
                if isinstance(obj, River):
                    current_force = obj.get_current_force(self.x + GRID_SIZE / 2,
                                                          self.y + GRID_SIZE / 2)
                    river_current = (current_force[0], current_force[1])

        # Приоритет 1: Временное направление от игрока
        if current_time < self.temporary_movement_end_time and self.temporary_direction is not None:
            self.direction = self.temporary_direction
            self.target_direction = self.temporary_direction
            self.current_target = None  # Сбрасываем цель, чтобы следовать направлению

            # Основные параметры движения
            base_speed = self.stats['speed']

            # Проверка нахождения в реке
            in_river = False
            if environment:
                for obj in environment:
                    if isinstance(obj, River) and obj.contains(self.x + GRID_SIZE / 2, self.y + GRID_SIZE / 2):
                        in_river = True
                        break
            speed_multiplier = 0.5 if in_river else 1.0
            actual_speed = base_speed * speed_multiplier

            # Основной вектор движения
            desired_move = [
                math.cos(self.direction) * actual_speed,
                math.sin(self.direction) * actual_speed
            ]

            # Силы избегания
            avoidance_force = [0, 0]
            cover_force = [0, 0]  # Сила движения к укрытию
            obstacle_circle_force = [0, 0]

            # 1. Избегание границ
            if self.x < BORDER_BUFFER:
                avoidance_force[0] += (BORDER_BUFFER - self.x) * 0.05
            elif self.x > SCREEN_WIDTH - BORDER_BUFFER - GRID_SIZE:
                avoidance_force[0] -= (self.x - (SCREEN_WIDTH - BORDER_BUFFER - GRID_SIZE)) * 0.05

            if self.y < TOP_PANEL_HEIGHT + BORDER_BUFFER:
                avoidance_force[1] += (TOP_PANEL_HEIGHT + BORDER_BUFFER - self.y) * 0.05
            elif self.y > SCREEN_HEIGHT - BORDER_BUFFER - GRID_SIZE:
                avoidance_force[1] -= (self.y - (SCREEN_HEIGHT - BORDER_BUFFER - GRID_SIZE)) * 0.05

            # 2. Поиск укрытия (если есть враги поблизости)
            closest_enemy = None
            min_enemy_distance = float('inf')

            for enemy in enemies:
                if enemy.health <= 0:
                    continue

                dx = enemy.x - self.x
                dy = enemy.y - self.y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < self.stats['detection_range'] and distance < min_enemy_distance:
                    min_enemy_distance = distance
                    closest_enemy = enemy

            # Если враг обнаружен и мы не в укрытии, ищем дерево для укрытия
            if closest_enemy and environment:
                best_cover = None
                best_cover_score = 0

                for obj in environment:
                    if isinstance(obj, Tree):
                        # Проверяем, может ли это дерево быть укрытием
                        tree_to_unit = math.sqrt((obj.x - self.x) ** 2 + (obj.y - self.y) ** 2)
                        tree_to_enemy = math.sqrt((obj.x - closest_enemy.x) ** 2 + (obj.y - closest_enemy.y) ** 2)

                        # Угол между юнитом, деревом и врагом
                        angle = math.atan2(closest_enemy.y - obj.y, closest_enemy.x - obj.x) - \
                                math.atan2(self.y - obj.y, self.x - obj.x)
                        angle = (angle + math.pi) % (2 * math.pi) - math.pi  # Нормализуем угол

                        # Оценка пригодности укрытия
                        if (tree_to_unit < COVER_RADIUS and
                                abs(angle) > math.pi / 2 and  # Дерево должно быть между юнитом и врагом
                                tree_to_enemy > obj.size / 2):  # Враг не должен быть слишком близко к дереву

                            # Чем больше дерево и чем лучше оно закрывает, тем выше оценка
                            score = (obj.size / 10) * (1 - tree_to_unit / COVER_RADIUS) * (abs(angle) / (math.pi))

                            if score > best_cover_score:
                                best_cover_score = score
                                best_cover = obj

                # Если нашли хорошее укрытие
                if best_cover and best_cover_score > 0.3:
                    # Вектор к укрытию (позиция за деревом относительно врага)
                    cover_dx = best_cover.x - closest_enemy.x
                    cover_dy = best_cover.y - closest_enemy.y
                    cover_dist = max(1, math.sqrt(cover_dx ** 2 + cover_dy ** 2))

                    # Нормализуем и немного уменьшаем расстояние, чтобы встать прямо за деревом
                    cover_dx = cover_dx / cover_dist * (best_cover.size / 2 + GRID_SIZE * 2)
                    cover_dy = cover_dy / cover_dist * (best_cover.size / 2 + GRID_SIZE * 2)

                    target_x = best_cover.x + cover_dx
                    target_y = best_cover.y + cover_dy

                    # Вектор движения к укрытию
                    cover_force[0] = (target_x - self.x) * 0.1
                    cover_force[1] = (target_y - self.y) * 0.1

            # 3. Обход препятствий (если не движемся к укрытию)
            if math.sqrt(cover_force[0] ** 2 + cover_force[1] ** 2) < 0.5:  # Если нет сильного стремления к укрытию
                closest_obstacle = None
                min_obstacle_distance = float('inf')

                if environment:
                    for obj in environment:
                        if isinstance(obj, (House, Tree)):
                            dx = (self.x + GRID_SIZE / 2) - obj.x
                            dy = (self.y + GRID_SIZE / 2) - obj.y
                            distance = math.sqrt(dx * dx + dy * dy)
                            obstacle_radius = obj.size / 2 if isinstance(obj, Tree) else obj.size * 0.7

                            if distance < obstacle_radius + OBSTACLE_DETECTION_RANGE:
                                if distance < min_obstacle_distance:
                                    min_obstacle_distance = distance
                                    closest_obstacle = obj

                if closest_obstacle:
                    obstacle_dx = (self.x + GRID_SIZE / 2) - closest_obstacle.x
                    obstacle_dy = (self.y + GRID_SIZE / 2) - closest_obstacle.y
                    obstacle_distance = max(1, math.sqrt(obstacle_dx ** 2 + obstacle_dy ** 2))
                    obstacle_dx /= obstacle_distance
                    obstacle_dy /= obstacle_distance
                    obstacle_radius = closest_obstacle.size / 2 if isinstance(closest_obstacle,
                                                                              Tree) else closest_obstacle.size * 0.7

                    if obstacle_distance < obstacle_radius + GRID_SIZE:
                        push_force = OBSTACLE_AVOIDANCE_FORCE * 2
                        avoidance_force[0] += obstacle_dx * push_force
                        avoidance_force[1] += obstacle_dy * push_force
                    else:
                        desired_dx = math.cos(self.direction)
                        desired_dy = math.sin(self.direction)
                        projection = desired_dx * obstacle_dx + desired_dy * obstacle_dy

                        if projection > 0:
                            perp_dx = -obstacle_dy
                            perp_dy = obstacle_dx
                            cross_product = desired_dx * obstacle_dy - desired_dy * obstacle_dx
                            if cross_product > 0:
                                perp_dx, perp_dy = obstacle_dy, -obstacle_dx

                            avoidance_strength = OBSTACLE_AVOIDANCE_FORCE * (
                                    1 - min(1, (obstacle_distance - obstacle_radius) / OBSTACLE_DETECTION_RANGE))

                            obstacle_circle_force[0] = perp_dx * avoidance_strength * 2
                            obstacle_circle_force[1] = perp_dy * avoidance_strength * 2
                            avoidance_force[0] += obstacle_dx * avoidance_strength * 0.5
                            avoidance_force[1] += obstacle_dy * avoidance_strength * 0.5

            # 4. Избегание союзников (с более сильным отталкиванием)
            ally_avoidance = self.calculate_avoidance(allies)
            avoidance_force[0] += ally_avoidance[0]
            avoidance_force[1] += ally_avoidance[1]

            # Комбинируем все силы (приоритет у укрытия)
            final_move = [
                desired_move[0] + avoidance_force[0] + obstacle_circle_force[0] + cover_force[0],
                desired_move[1] + avoidance_force[1] + obstacle_circle_force[1] + cover_force[1]
            ]

            # Нормализуем вектор
            move_length = math.sqrt(final_move[0] ** 2 + final_move[1] ** 2)
            if move_length > 0:
                final_move = [
                    final_move[0] / move_length * actual_speed,
                    final_move[1] / move_length * actual_speed
                ]

            # Применяем движение
            new_x = self.x + final_move[0]
            new_y = self.y + final_move[1]

            # Ограничиваем позицию
            self.x = max(0, min(new_x, SCREEN_WIDTH - GRID_SIZE))
            self.y = max(TOP_PANEL_HEIGHT, min(new_y, SCREEN_HEIGHT - GRID_SIZE))
            return

        # Приоритет 2: Боевое поведение (если нет временного направления)
        # Основные параметры движения
        base_speed = self.stats['speed']
        desired_direction = self.target_direction

        if desired_direction is None:
            self.update_attack_cooldown()
            return

        # Проверка нахождения в реке
        in_river = False
        if environment:
            for obj in environment:
                if isinstance(obj, River) and obj.contains(self.x + GRID_SIZE / 2, self.y + GRID_SIZE / 2):
                    in_river = True
                    break
        speed_multiplier = 0.5 if in_river else 1.0
        actual_speed = base_speed * speed_multiplier

        # Основной вектор движения
        desired_move = [
            math.cos(desired_direction) * actual_speed,
            math.sin(desired_direction) * actual_speed
        ]

        # Силы избегания
        avoidance_force = [0, 0]
        cover_force = [0, 0]  # Сила движения к укрытию
        obstacle_circle_force = [0, 0]

        # 1. Избегание границ
        if self.x < BORDER_BUFFER:
            avoidance_force[0] += (BORDER_BUFFER - self.x) * 0.05
        elif self.x > SCREEN_WIDTH - BORDER_BUFFER - GRID_SIZE:
            avoidance_force[0] -= (self.x - (SCREEN_WIDTH - BORDER_BUFFER - GRID_SIZE)) * 0.05

        if self.y < TOP_PANEL_HEIGHT + BORDER_BUFFER:
            avoidance_force[1] += (TOP_PANEL_HEIGHT + BORDER_BUFFER - self.y) * 0.05
        elif self.y > SCREEN_HEIGHT - BORDER_BUFFER - GRID_SIZE:
            avoidance_force[1] -= (self.y - (SCREEN_HEIGHT - BORDER_BUFFER - GRID_SIZE)) * 0.05

        # 2. Поиск укрытия (если есть враги поблизости)
        closest_enemy = None
        min_enemy_distance = float('inf')

        for enemy in enemies:
            if enemy.health <= 0:
                continue

            dx = enemy.x - self.x
            dy = enemy.y - self.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < self.stats['detection_range'] and distance < min_enemy_distance:
                min_enemy_distance = distance
                closest_enemy = enemy

        # Если враг обнаружен и мы не в укрытии, ищем дерево для укрытия
        if closest_enemy and environment:
            best_cover = None
            best_cover_score = 0

            for obj in environment:
                if isinstance(obj, Tree):
                    # Проверяем, может ли это дерево быть укрытием
                    tree_to_unit = math.sqrt((obj.x - self.x) ** 2 + (obj.y - self.y) ** 2)
                    tree_to_enemy = math.sqrt((obj.x - closest_enemy.x) ** 2 + (obj.y - closest_enemy.y) ** 2)

                    # Угол между юнитом, деревом и врагом
                    angle = math.atan2(closest_enemy.y - obj.y, closest_enemy.x - obj.x) - \
                            math.atan2(self.y - obj.y, self.x - obj.x)
                    angle = (angle + math.pi) % (2 * math.pi) - math.pi  # Нормализуем угол

                    # Оценка пригодности укрытия
                    if (tree_to_unit < COVER_RADIUS and
                            abs(angle) > math.pi / 2 and  # Дерево должно быть между юнитом и врагом
                            tree_to_enemy > obj.size / 2):  # Враг не должен быть слишком близко к дереву

                        # Чем больше дерево и чем лучше оно закрывает, тем выше оценка
                        score = (obj.size / 10) * (1 - tree_to_unit / COVER_RADIUS) * (abs(angle) / (math.pi))

                        if score > best_cover_score:
                            best_cover_score = score
                            best_cover = obj

            # Если нашли хорошее укрытие
            if best_cover and best_cover_score > 0.3:
                # Вектор к укрытию (позиция за деревом относительно врага)
                cover_dx = best_cover.x - closest_enemy.x
                cover_dy = best_cover.y - closest_enemy.y
                cover_dist = max(1, math.sqrt(cover_dx ** 2 + cover_dy ** 2))

                # Нормализуем и немного уменьшаем расстояние, чтобы встать прямо за деревом
                cover_dx = cover_dx / cover_dist * (best_cover.size / 2 + GRID_SIZE * 2)
                cover_dy = cover_dy / cover_dist * (best_cover.size / 2 + GRID_SIZE * 2)

                target_x = best_cover.x + cover_dx
                target_y = best_cover.y + cover_dy

                # Вектор движения к укрытию
                cover_force[0] = (target_x - self.x) * 0.1
                cover_force[1] = (target_y - self.y) * 0.1

        # 3. Обход препятствий (если не движемся к укрытию)
        if math.sqrt(cover_force[0] ** 2 + cover_force[1] ** 2) < 0.5:  # Если нет сильного стремления к укрытию
            closest_obstacle = None
            min_obstacle_distance = float('inf')

            if environment:
                for obj in environment:
                    if isinstance(obj, (House, Tree)):
                        dx = (self.x + GRID_SIZE / 2) - obj.x
                        dy = (self.y + GRID_SIZE / 2) - obj.y
                        distance = math.sqrt(dx * dx + dy * dy)
                        obstacle_radius = obj.size / 2 if isinstance(obj, Tree) else obj.size * 0.7

                        if distance < obstacle_radius + OBSTACLE_DETECTION_RANGE:
                            if distance < min_obstacle_distance:
                                min_obstacle_distance = distance
                                closest_obstacle = obj

            if closest_obstacle:
                obstacle_dx = (self.x + GRID_SIZE / 2) - closest_obstacle.x
                obstacle_dy = (self.y + GRID_SIZE / 2) - closest_obstacle.y
                obstacle_distance = max(1, math.sqrt(obstacle_dx ** 2 + obstacle_dy ** 2))
                obstacle_dx /= obstacle_distance
                obstacle_dy /= obstacle_distance
                obstacle_radius = closest_obstacle.size / 2 if isinstance(closest_obstacle,
                                                                          Tree) else closest_obstacle.size * 0.7

                if obstacle_distance < obstacle_radius + GRID_SIZE:
                    push_force = OBSTACLE_AVOIDANCE_FORCE * 2
                    avoidance_force[0] += obstacle_dx * push_force
                    avoidance_force[1] += obstacle_dy * push_force
                else:
                    desired_dx = math.cos(desired_direction)
                    desired_dy = math.sin(desired_direction)
                    projection = desired_dx * obstacle_dx + desired_dy * obstacle_dy

                    if projection > 0:
                        perp_dx = -obstacle_dy
                        perp_dy = obstacle_dx
                        cross_product = desired_dx * obstacle_dy - desired_dy * obstacle_dx
                        if cross_product > 0:
                            perp_dx, perp_dy = obstacle_dy, -obstacle_dx

                        avoidance_strength = OBSTACLE_AVOIDANCE_FORCE * (
                                1 - min(1, (obstacle_distance - obstacle_radius) / OBSTACLE_DETECTION_RANGE))

                        obstacle_circle_force[0] = perp_dx * avoidance_strength * 2
                        obstacle_circle_force[1] = perp_dy * avoidance_strength * 2
                        avoidance_force[0] += obstacle_dx * avoidance_strength * 0.5
                        avoidance_force[1] += obstacle_dy * avoidance_strength * 0.5

        # 4. Избегание союзников (с более сильным отталкиванием)
        ally_avoidance = self.calculate_avoidance(allies)
        avoidance_force[0] += ally_avoidance[0]
        avoidance_force[1] += ally_avoidance[1]

        # Комбинируем все силы (приоритет у укрытия)
        final_move = [
            desired_move[0] + avoidance_force[0] + obstacle_circle_force[0] +
            cover_force[0] + river_current[0],  # Добавляем течение реки
            desired_move[1] + avoidance_force[1] + obstacle_circle_force[1] +
            cover_force[1] + river_current[1]  # Добавляем течение реки
        ]

        # Нормализуем вектор
        move_length = math.sqrt(final_move[0] ** 2 + final_move[1] ** 2)
        if move_length > 0:
            final_move = [
                final_move[0] / move_length * actual_speed,
                final_move[1] / move_length * actual_speed
            ]

        # Применяем движение
        new_x = self.x + final_move[0]
        new_y = self.y + final_move[1]

        # Ограничиваем позицию
        self.x = max(0, min(new_x, SCREEN_WIDTH - GRID_SIZE))
        self.y = max(TOP_PANEL_HEIGHT, min(new_y, SCREEN_HEIGHT - GRID_SIZE))

        # Обновляем направление
        if move_length > 0:
            new_angle = math.atan2(final_move[1], final_move[0])
            if self.temporary_direction is not None:
                angle_diff = (new_angle - self.temporary_direction + math.pi) % (2 * math.pi) - math.pi
                self.temporary_direction += angle_diff * 0.25
            else:
                self.target_direction = new_angle

        self.update_attack_cooldown()

    def calculate_avoidance(self, allies):
        avoidance_x, avoidance_y = 0, 0
        for ally in allies:
            if ally == self or ally.health <= 0:
                continue

            distance = math.sqrt((self.x - ally.x) ** 2 + (self.y - ally.y) ** 2)
            if distance < self.formation_spacing:
                dx = self.x - ally.x
                dy = self.y - ally.y
                if dx == 0 and dy == 0:
                    dx, dy = random.random() - 0.5, random.random() - 0.5

                force = (self.formation_spacing - distance) / 5.0
                avoidance_x += dx * force
                avoidance_y += dy * force
        return avoidance_x, avoidance_y

    def find_target_in_direction(self, enemies):
        best_target = None
        best_score = -1

        for enemy in enemies:
            if enemy.health <= 0:  # Пропускаем мертвых врагов
                continue

            dx = enemy.x - self.x
            dy = enemy.y - self.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > self.stats['detection_range']:
                continue

            angle_to_enemy = math.atan2(dy, dx)
            angle_diff = abs(((angle_to_enemy - self.target_direction) + math.pi) % (2 * math.pi) - math.pi)

            direction_score = max(0, 1 - angle_diff / (math.pi / 2))
            proximity_score = 1 - min(1, distance / self.stats['detection_range'])

            total_score = direction_score * 0.7 + proximity_score * 0.3

            if total_score > best_score:
                best_score = total_score
                best_target = enemy

        self.current_target = best_target if best_score > 0.3 else None

    def can_attack(self):
        return self.attack_cooldown <= 0

    def update_attack_cooldown(self):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def check_enemies_in_direction(self, enemies):
        """Проверяет, есть ли враги в текущем направлении движения"""
        if self.direction is None:
            return False

        for enemy in enemies:
            if enemy.health <= 0:
                continue

            # Вектор от юнита к врагу
            dx = enemy.x - self.x
            dy = enemy.y - self.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > self.stats['detection_range']:
                continue

            # Угол к врагу
            angle_to_enemy = math.atan2(dy, dx)
            angle_diff = abs(((angle_to_enemy - self.direction) + math.pi) % (2 * math.pi) - math.pi)

            # Если враг в пределах 45 градусов от направления движения
            if angle_diff < math.pi / 4 and distance <= self.stats['range']:
                return True

        return False
#----------------------------------------------КЛАСС АРМИИ----------------------------------------------
class Army:
    def __init__(self, team, cavalry_count, infantry_count, artillery_count=0, custom_positions=None, formation_positions=None):
        self.team = team
        self.soldiers = []
        self.cavalry_count = cavalry_count
        self.infantry_count = infantry_count
        self.artillery_count = artillery_count

        if team == 'enemy' and global_enemy_positions:
            # Используем сохраненные позиции для врага
            used_positions = set()
            for pos, unit_type in global_enemy_positions:
                x, y = pos
                if unit_type == 'cavalry' and len(
                        [s for s in self.soldiers if s.type == UnitType.CAVALRY]) < cavalry_count:
                    self.soldiers.append(Soldier(x, y, team, UnitType.CAVALRY))
                    used_positions.add((x, y))
                elif unit_type == 'infantry' and len(
                        [s for s in self.soldiers if s.type == UnitType.INFANTRY]) < infantry_count:
                    self.soldiers.append(Soldier(x, y, team, UnitType.INFANTRY))
                    used_positions.add((x, y))
                elif unit_type == 'artillery' and len(
                        [s for s in self.soldiers if s.type == UnitType.ARTILLERY]) < artillery_count:
                    self.soldiers.append(Soldier(x, y, team, UnitType.ARTILLERY))
                    used_positions.add((x, y))

            # Добавляем оставшихся юнитов, если нужно
            remaining_cavalry = cavalry_count - len([s for s in self.soldiers if s.type == UnitType.CAVALRY])
            remaining_infantry = infantry_count - len([s for s in self.soldiers if s.type == UnitType.INFANTRY])
            remaining_artillery = artillery_count - len([s for s in self.soldiers if s.type == UnitType.ARTILLERY])

            if remaining_cavalry > 0 or remaining_infantry > 0 or remaining_artillery > 0:
                # Генерируем дополнительные позиции для оставшихся юнитов
                additional_positions = self.generate_squad_formation(remaining_cavalry, remaining_infantry, remaining_artillery)
                for pos, unit_type in additional_positions:
                    x, y = pos
                    if unit_type == 'cavalry' and len(
                            [s for s in self.soldiers if s.type == UnitType.CAVALRY]) < cavalry_count:
                        self.soldiers.append(Soldier(x, y, team, UnitType.CAVALRY))
                    elif unit_type == 'infantry' and len(
                            [s for s in self.soldiers if s.type == UnitType.INFANTRY]) < infantry_count:
                        self.soldiers.append(Soldier(x, y, team, UnitType.INFANTRY))
                    elif unit_type == 'artillery' and len(
                            [s for s in self.soldiers if s.type == UnitType.ARTILLERY]) < artillery_count:
                        self.soldiers.append(Soldier(x, y, team, UnitType.ARTILLERY))
        elif custom_positions:
            # Старая логика для игрока
            for unit_type, positions in custom_positions.items():
                for pos in positions:
                    x, y = pos
                    if unit_type == 'cavalry' and len(
                            [s for s in self.soldiers if s.type == UnitType.CAVALRY]) < cavalry_count:
                        self.soldiers.append(Soldier(x, y, team, UnitType.CAVALRY))
                    elif unit_type == 'infantry' and len(
                            [s for s in self.soldiers if s.type == UnitType.INFANTRY]) < infantry_count:
                        self.soldiers.append(Soldier(x, y, team, UnitType.INFANTRY))
                    elif unit_type == 'artillery' and len(
                            [s for s in self.soldiers if s.type == UnitType.ARTILLERY]) < artillery_count:
                        self.soldiers.append(Soldier(x, y, team, UnitType.ARTILLERY))
        elif formation_positions:
            # Старая логика для формирования
            for pos, unit_type in formation_positions:
                x, y = pos
                if unit_type == 'cavalry':
                    self.soldiers.append(Soldier(x, y, team, UnitType.CAVALRY))
                elif unit_type == 'infantry':
                    self.soldiers.append(Soldier(x, y, team, UnitType.INFANTRY))
                elif unit_type == 'artillery':
                    self.soldiers.append(Soldier(x, y, team, UnitType.ARTILLERY))
        elif team == 'enemy':
            # Генерация позиций для врага и сохранение их в глобальную переменную
            positions = self.generate_squad_formation(cavalry_count, infantry_count, artillery_count)
            global_enemy_positions.clear()  # Очищаем старые позиции
            for pos, unit_type in positions:
                x, y = pos
                if unit_type == 'cavalry' and len(
                        [s for s in self.soldiers if s.type == UnitType.CAVALRY]) < cavalry_count:
                    self.soldiers.append(Soldier(x, y, team, UnitType.CAVALRY))
                    global_enemy_positions.append(((x, y), 'cavalry'))
                elif unit_type == 'infantry' and len(
                        [s for s in self.soldiers if s.type == UnitType.INFANTRY]) < infantry_count:
                    self.soldiers.append(Soldier(x, y, team, UnitType.INFANTRY))
                    global_enemy_positions.append(((x, y), 'infantry'))
                elif unit_type == 'artillery' and len(
                        [s for s in self.soldiers if s.type == UnitType.ARTILLERY]) < artillery_count:
                    self.soldiers.append(Soldier(x, y, team, UnitType.ARTILLERY))
                    global_enemy_positions.append(((x, y), 'artillery'))

    def set_temporary_direction(self, angle, duration):
        """Устанавливает временное направление движения для всех выбранных юнитов"""
        current_time = pygame.time.get_ticks()
        for soldier in self.soldiers:
            if soldier.selected and soldier.health > 0:
                # Для артиллерии устанавливаем только направление стрельбы
                if soldier.type == UnitType.ARTILLERY:
                    soldier.direction = angle
                    soldier.target_direction = angle
                else:
                    soldier.temporary_direction = angle
                    soldier.temporary_movement_end_time = current_time + duration
                    soldier.current_target = None  # Сбрасываем текущую цель

    def generate_squad_formation(self, cavalry_count, infantry_count, artillery_count=0):
        """Генерация построения с уменьшенными интервалами между юнитами"""
        formation = []
        used_positions = set()
        squad_zones = []  # Для хранения зон взводов

        # Размеры взводов
        squad_sizes = {
            'infantry': 16,
            'cavalry': 8,
            'artillery': 4
        }

        # Границы спавна (верхняя часть экрана)
        spawn_area_top = int(TOP_PANEL_HEIGHT + 20)
        spawn_area_bottom = int(SCREEN_HEIGHT // 2.5)
        spawn_area_left = int(SCREEN_WIDTH // 4)
        spawn_area_right = int(SCREEN_WIDTH - 50)

        # Уменьшенные интервалы между юнитами
        UNIT_SPACING = GRID_SIZE + 2
        CAVALRY_SPACING = GRID_SIZE + 3
        ARTILLERY_SPACING = GRID_SIZE * 3  # Больше места для артиллерии

        # Функция проверки позиции
        def is_position_valid(x, y, unit_type, squad_rect=None):
            # Проверка границ
            if (x < 0 or x > SCREEN_WIDTH - GRID_SIZE or
                    y < TOP_PANEL_HEIGHT or y > SCREEN_HEIGHT - GRID_SIZE):
                return False

            # Проверка препятствий
            for obj in global_environment:
                if obj.contains(x + GRID_SIZE / 2, y + GRID_SIZE / 2):
                    return False

            # Проверка на пересечение с другими юнитами
            pos_key = (round(x), round(y))
            if pos_key in used_positions:
                return False

            # Проверка пересечения с зонами других взводов
            if squad_rect:
                for zone in squad_zones:
                    if squad_rect.colliderect(zone):
                        return False

            return True

        # Функция поиска позиции для взвода
        def find_squad_position(squad_size, unit_type):
            spacing = CAVALRY_SPACING if unit_type == 'cavalry' else (
                ARTILLERY_SPACING if unit_type == 'artillery' else UNIT_SPACING)
            rows = min(2, squad_size)
            cols = (squad_size + rows - 1) // rows

            squad_width = int(cols * spacing)
            squad_height = int(rows * spacing)

            attempts = 0
            while attempts < 50:
                try:
                    base_x = random.randint(spawn_area_left, max(spawn_area_left, spawn_area_right - squad_width))
                    base_y = random.randint(spawn_area_top, max(spawn_area_top, spawn_area_bottom - squad_height))
                except ValueError:
                    attempts += 1
                    continue

                squad_rect = pygame.Rect(base_x, base_y, squad_width, squad_height)

                # Проверяем все позиции в зоне
                valid_positions = []
                for i in range(squad_size):
                    row = i // cols
                    col = i % cols
                    x = int(base_x + col * spacing)
                    y = int(base_y + row * spacing)

                    if not is_position_valid(x, y, unit_type, squad_rect):
                        break
                    valid_positions.append((x, y))
                else:
                    squad_zones.append(squad_rect)
                    return valid_positions

                attempts += 1
            return None

        # Сначала размещаем артиллерию (ей нужно больше места)
        if artillery_count > 0:
            num_squads = (artillery_count + squad_sizes['artillery'] - 1) // squad_sizes['artillery']
            remaining_artillery = artillery_count

            for _ in range(num_squads):
                squad_size = min(squad_sizes['artillery'], remaining_artillery)
                positions = find_squad_position(squad_size, 'artillery')

                if positions:
                    for x, y in positions:
                        formation.append(((x, y), 'artillery'))
                        used_positions.add((round(x), round(y)))
                    remaining_artillery -= squad_size

        # Затем размещаем кавалерию
        if cavalry_count > 0:
            num_squads = (cavalry_count + squad_sizes['cavalry'] - 1) // squad_sizes['cavalry']
            remaining_cavalry = cavalry_count

            for _ in range(num_squads):
                squad_size = min(squad_sizes['cavalry'], remaining_cavalry)
                positions = find_squad_position(squad_size, 'cavalry')

                if positions:
                    for x, y in positions:
                        formation.append(((x, y), 'cavalry'))
                        used_positions.add((round(x), round(y)))
                    remaining_cavalry -= squad_size

        # Затем размещаем пехоту
        if infantry_count > 0:
            num_squads = (infantry_count + squad_sizes['infantry'] - 1) // squad_sizes['infantry']
            remaining_infantry = infantry_count

            for _ in range(num_squads):
                squad_size = min(squad_sizes['infantry'], remaining_infantry)
                positions = find_squad_position(squad_size, 'infantry')

                if positions:
                    for x, y in positions:
                        formation.append(((x, y), 'infantry'))
                        used_positions.add((round(x), round(y)))
                    remaining_infantry -= squad_size

        return formation

    def find_nearest_valid_position(self, x, y, used_positions, is_valid_func, max_offset=100):
        """Находит ближайшую валидную позицию"""
        for radius in range(0, max_offset, 5):
            for angle in range(0, 360, 15):
                rad = math.radians(angle)
                test_x = int(x + radius * math.cos(rad))
                test_y = int(y + radius * math.sin(rad))
                pos_key = (test_x, test_y)

                if pos_key not in used_positions and is_valid_func(test_x, test_y):
                    return pos_key
        return None

    def draw(self):
        for soldier in self.soldiers:
            soldier.draw()

    def select_in_rect(self, rect):
        for soldier in self.soldiers:
            if soldier.health > 0:
                soldier.selected = rect.collidepoint(soldier.x, soldier.y)

    def deselect_all(self):
        for soldier in self.soldiers:
            if soldier.health > 0:
                soldier.selected = False

    def update_movement(self, enemies, environment=None):
        for soldier in self.soldiers:
            if soldier.health > 0:
                soldier.update_movement(enemies, [s for s in self.soldiers if s.health > 0], environment)

    def attack_enemy(self, enemy_army):
        for soldier in self.soldiers:
            if soldier.health > 0 and soldier.current_target and soldier.current_target.health > 0:
                distance = math.sqrt((soldier.x - soldier.current_target.x) ** 2 +
                                     (soldier.y - soldier.current_target.y) ** 2)
                if distance <= soldier.stats['range'] and soldier.can_attack():
                    soldier.attack(soldier.current_target)

    def get_unit_counts(self):
        cavalry = sum(1 for s in self.soldiers if s.type == UnitType.CAVALRY and s.health > 0)
        infantry = sum(1 for s in self.soldiers if s.type == UnitType.INFANTRY and s.health > 0)
        artillery = sum(1 for s in self.soldiers if s.type == UnitType.ARTILLERY and s.health > 0)
        return cavalry, infantry, artillery
#----------------------------------------------ИИ ВОИНОВ ИГРОКА----------------------------------------------
class SmartArmyController:
    def __init__(self, army, enemy_army):
        self.army = army
        self.enemy_army = enemy_army
        self.last_update_time = 0
        self.update_interval = 200
        self.border_margin = 50  # Минимальное расстояние до границы экрана

    def update(self, current_time):
        if current_time - self.last_update_time < self.update_interval:
            return

        self.last_update_time = current_time

        for soldier in self.army.soldiers:
            if soldier.health <= 0:
                continue

            # Проверка границ мира и корректировка направления
            self.check_world_borders(soldier)

            # Если есть команда на движение - выполняем ее
            if (soldier.temporary_direction is not None and
                    current_time < soldier.temporary_movement_end_time):
                self.check_enemies_while_moving(soldier)
                continue

            self.combat_ai(soldier, current_time)

    def combat_ai(self, soldier, current_time):
        # 1. Если есть текущая цель, атакуем ее
        if soldier.current_target and soldier.current_target.health > 0:
            distance = self.calculate_distance(soldier, soldier.current_target)

            if distance <= soldier.stats['range']:
                if soldier.can_attack():
                    soldier.attack(soldier.current_target)
                return
            elif distance <= soldier.stats['detection_range'] * 1.5:
                # Преследуем цель
                dx = soldier.current_target.x - soldier.x
                dy = soldier.current_target.y - soldier.y
                soldier.target_direction = math.atan2(dy, dx)
                return
            else:
                soldier.current_target = None  # Цель слишком далеко

        # 2. Ищем новую цель
        best_target = None
        best_score = -1

        for enemy in self.enemy_army.soldiers:
            if enemy.health <= 0:
                continue

            distance = self.calculate_distance(soldier, enemy)
            if distance > soldier.stats['detection_range']:
                continue

            # Система оценки целей
            score = 0

            # Приоритет ближайшим целям
            score += (1 - distance / soldier.stats['detection_range']) * 0.6

            # Приоритет слабым целям
            score += (1 - enemy.health / 100) * 0.4

            # Бонусы по типу юнита
            if soldier.type == UnitType.INFANTRY and enemy.type == UnitType.CAVALRY:
                score += 0.5
            elif soldier.type == UnitType.CAVALRY and enemy.type == UnitType.INFANTRY:
                score -= 0.2

            if score > best_score:
                best_score = score
                best_target = enemy

        if best_target:
            soldier.current_target = best_target
            dx = best_target.x - soldier.x
            dy = best_target.y - soldier.y
            soldier.target_direction = math.atan2(dy, dx)

    def check_enemies_while_moving(self, soldier):
        """Проверяет врагов во время движения"""
        closest_enemy = None
        min_distance = float('inf')

        for enemy in self.enemy_army.soldiers:
            if enemy.health <= 0:
                continue

            distance = self.calculate_distance(soldier, enemy)
            if distance < soldier.stats['range'] and distance < min_distance:
                min_distance = distance
                closest_enemy = enemy

        if closest_enemy:
            soldier.current_target = closest_enemy
            soldier.temporary_direction = None  # Прерываем движение для боя

    def calculate_distance(self, a, b):
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

    def check_world_borders(self, soldier):
        """Корректирует направление движения при приближении к границам"""
        turn_angle = math.pi / 4  # Угол поворота при приближении к границе

        # Проверяем каждую границу
        if soldier.x < self.border_margin:  # Левая граница
            if soldier.target_direction is not None:
                if math.pi / 2 < soldier.target_direction < 3 * math.pi / 2:
                    soldier.target_direction += turn_angle
        elif soldier.x > SCREEN_WIDTH - self.border_margin:  # Правая граница
            if soldier.target_direction is not None:
                if -math.pi / 2 < soldier.target_direction < math.pi / 2:
                    soldier.target_direction -= turn_angle

        if soldier.y < self.border_margin:  # Верхняя граница
            if soldier.target_direction is not None:
                if math.pi < soldier.target_direction or soldier.target_direction < 0:
                    soldier.target_direction = -soldier.target_direction
        elif soldier.y > SCREEN_HEIGHT - self.border_margin:  # Нижняя граница
            if soldier.target_direction is not None:
                if 0 < soldier.target_direction < math.pi:
                    soldier.target_direction = -soldier.target_direction

    def calculate_distance(self, a, b):
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
#----------------------------------------------ИИ ВОИНОВ ПРОТИВНИКА----------------------------------------------
class AI:
    def __init__(self, army, enemy_army):
        self.army = army
        self.enemy_army = enemy_army
        self.last_decision_time = 0
        self.decision_interval = 1000
        self.last_artillery_decision = 0
        self.artillery_interval = 3000  # Реже принимаем решения для артиллерии

    def update(self, current_time):
        if current_time - self.last_decision_time < self.decision_interval:
            return

        self.last_decision_time = current_time

        # Обновляем обычных юнитов
        for soldier in self.army.soldiers:
            if soldier.health <= 0:
                continue

            if soldier.type == UnitType.ARTILLERY:
                # Для артиллерии отдельная логика
                if current_time - self.last_artillery_decision >= self.artillery_interval:
                    self.update_artillery(soldier, current_time)
                continue

            closest_enemy = None
            min_distance = float('inf')

            for enemy in self.enemy_army.soldiers:
                if enemy.health <= 0:
                    continue

                distance = math.sqrt((soldier.x - enemy.x) ** 2 + (soldier.y - enemy.y) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    closest_enemy = enemy

            if closest_enemy:
                dx = closest_enemy.x - soldier.x
                dy = closest_enemy.y - soldier.y
                angle = math.atan2(dy, dx)

                if min_distance < soldier.stats['range']:
                    soldier.target_direction = None
                    soldier.current_target = closest_enemy
                    soldier.direction = angle  # Добавляем направление даже при атаке
                else:
                    soldier.target_direction = angle
                    soldier.direction = angle  # Вот ключевое: добавляем направление
                    soldier.current_target = closest_enemy
            else:
                target_y = SCREEN_HEIGHT - 100 if self.army.team == 'enemy' else 100
                dx = SCREEN_WIDTH // 2 - soldier.x
                dy = target_y - soldier.y
                soldier.target_direction = math.atan2(dy, dx)
                soldier.current_target = None

        # Обновляем время последнего решения артиллерии
        if current_time - self.last_artillery_decision >= self.artillery_interval:
            self.last_artillery_decision = current_time

    def update_artillery(self, artillery, current_time):
        """Обновление логики для артиллерии"""
        if artillery.health <= 0:
            return

        # Ищем скопление врагов
        best_target = None
        max_enemies = 0
        max_damage_potential = 0

        for enemy in self.enemy_army.soldiers:
            if enemy.health <= 0:
                continue

            # Проверяем расстояние до врага
            dx = enemy.x - artillery.x
            dy = enemy.y - artillery.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > artillery.stats['range']:
                continue

            # Считаем сколько врагов попадет в радиус взрыва
            enemies_in_radius = 0
            for other_enemy in self.enemy_army.soldiers:
                if other_enemy.health <= 0:
                    continue

                other_dx = other_enemy.x - enemy.x
                other_dy = other_enemy.y - enemy.y
                other_dist = math.sqrt(other_dx * other_dx + other_dy * other_dy)

                if other_dist <= artillery.stats['splash_radius']:
                    enemies_in_radius += 1

            # Выбираем цель с максимальным потенциальным уроном
            damage_potential = enemies_in_radius * artillery.stats['power']

            if damage_potential > max_damage_potential:
                max_damage_potential = damage_potential
                max_enemies = enemies_in_radius
                best_target = enemy

        # Если нашли хорошую цель - стреляем
        if best_target and max_enemies >= 1:
            artillery.direction = math.atan2(best_target.y - artillery.y, best_target.x - artillery.x)
            artillery.artillery_attack(best_target.x + GRID_SIZE // 2, best_target.y + GRID_SIZE // 2,
                                       self.enemy_army.soldiers)
#----------------------------------------------КНОПКИ----------------------------------------------
class Button:
    def __init__(self, x, y, width, height, text, font_size=24):  # Уменьшен размер шрифта по умолчанию
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.is_hovered = False
        self.font_size = font_size
        self.font = pygame.font.SysFont(None, font_size)  # Создаем шрифт один раз

    def draw(self):
        color = COLORS['button_hover'] if self.is_hovered else COLORS['button']
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, COLORS['text'], self.rect, 2)

        # Автоматическое уменьшение шрифта, если текст не помещается
        text_surface = self.font.render(self.text, True, COLORS['text'])
        while text_surface.get_width() > self.rect.width - 10 and self.font_size > 10:
            self.font_size -= 1
            self.font = pygame.font.SysFont(None, self.font_size)
            text_surface = self.font.render(self.text, True, COLORS['text'])

        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False
#----------------------------------------------ОКНО ВВОДА----------------------------------------------
class InputBox:
    def __init__(self, x, y, width, height, text='', font_size=24):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = COLORS['button']
        self.text = text
        self.font = pygame.font.SysFont(None, font_size)
        self.txt_surface = self.font.render(text, True, COLORS['text'])
        self.active = False
        self.value = text

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Если кликнули по input box
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
            # Изменение цвета поля ввода
            self.color = COLORS['button_hover'] if self.active else COLORS['button']

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                try:
                    self.value = int(self.text)
                except ValueError:
                    self.value = 0
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                # Проверяем, что вводится цифра
                if event.unicode.isdigit():
                    self.text += event.unicode
            # Перерисовка текста
            self.txt_surface = self.font.render(self.text, True, COLORS['text'])
        return False

    def update(self):
        # Изменение размера поля, если текст слишком длинный
        width = max(100, self.txt_surface.get_width() + 10)
        self.rect.w = width

    def draw(self, screen):
        # Рисуем текст
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        # Рисуем прямоугольник
        pygame.draw.rect(screen, self.color, self.rect, 2)

    def get_value(self):
        try:
            return int(self.text)
        except ValueError:
            return 0
#----------------------------------------------ПОРЯДОК ОТРИСОВКИ----------------------------------------------
def draw_all_armies(player_army, enemy_army, terrain_texture, environment):
    """Функция отрисовки всех армий и окружения в правильном порядке"""
    # 1. Рисуем текстуру местности
    screen.blit(terrain_texture, (0, 0))

    # 2. Рисуем окружение - сначала дороги (нижний слой)
    for obj in environment:
        if isinstance(obj, Road):  # Сначала рисуем дороги
            obj.draw(screen)

    # 3. Затем остальные объекты окружения (реки, деревья, дома)
    for obj in environment:
        if not isinstance(obj, Road):  # Все кроме дорог
            obj.draw(screen)

    # 4. Рисуем ВСЕ мертвые юниты (и игрока, и врага) как фон
    for soldier in player_army.soldiers + enemy_army.soldiers:
        if soldier.health <= 0:
            soldier.draw(layer="background")

    # 5. Рисуем живых юнитов, скрытых под деревьями
    for soldier in player_army.soldiers + enemy_army.soldiers:
        if soldier.health > 0:
            under_tree = False
            for tree in (obj for obj in environment if isinstance(obj, Tree)):
                if tree.contains(soldier.x, soldier.y):
                    under_tree = True
                    break

            if not under_tree:
                soldier.draw(layer="foreground")

    # 6. Рисуем кроны деревьев поверх некоторых юнитов
    for tree in (obj for obj in environment if isinstance(obj, Tree)):
        tree.draw(screen)
#----------------------------------------------ПАНЕЛИ----------------------------------------------
def draw_stats_panel(soldier, x, y):
    panel_width, panel_height = 225, 210  # Увеличили размер панели для артиллерии
    pygame.draw.rect(screen, COLORS['panel_bg'], (x, y, panel_width, panel_height))
    pygame.draw.rect(screen, COLORS['panel_border'], (x, y, panel_width, panel_height), 2)

    font = pygame.font.SysFont(None, 24)

    # Основные характеристики
    type_map = {
        UnitType.INFANTRY: "Пехота",
        UnitType.CAVALRY: "Кавалерия",
        UnitType.ARTILLERY: "Артиллерия"
    }
    lines = [
        f"Тип: {type_map[soldier.type]}",
        f"Сила: {soldier.stats['power']}",
        f"Броня: {soldier.stats['armor']}",
        f"Скорость: {soldier.stats['speed']:.1f}",
        f"Дальность: {soldier.stats['range']}",
        f"Здоровье: {soldier.health}"
    ]

    # Добавляем специальные характеристики для артиллерии
    if soldier.type == UnitType.ARTILLERY:
        lines.extend([
            f"Радиус взрыва: {soldier.stats['splash_radius']}",
            f"Скорострельность: {soldier.stats['attack_speed'] / FPS:.1f} сек"
        ])

    for i, line in enumerate(lines):
        text = font.render(line, True, COLORS['text'])
        screen.blit(text, (x + 10, y + 10 + i * 25))

def draw_top_panel(player_counts, enemy_counts):
    """Отрисовка верхней панели с информацией о юнитах"""
    panel_height = 30
    pygame.draw.rect(screen, COLORS['top_panel'], (0, 0, SCREEN_WIDTH, panel_height))

    font = pygame.font.SysFont(None, 24)

    # Текст для игрока
    player_text = font.render(
        f"Вы: Кав.{player_counts[0]} Пех.{player_counts[1]} Арт.{player_counts[2]}",
        True, COLORS['text'])
    screen.blit(player_text, (20, 5))

    # Текст для врага
    enemy_text = font.render(
        f"Враг: Кав.{enemy_counts[0]} Пех.{enemy_counts[1]} Арт.{enemy_counts[2]}",
        True, COLORS['text'])
    screen.blit(enemy_text, (SCREEN_WIDTH - enemy_text.get_width() - 20, 5))


def show_victory_screen(winner, player_army, enemy_army):
    """Показывает экран победы/поражения/ничьи с цветной статистикой"""
    clock = pygame.time.Clock()
    running = True

    # Подсчет статистики для игрока
    player_initial_cav = player_army.cavalry_count
    player_initial_inf = player_army.infantry_count
    player_initial_art = player_army.artillery_count
    player_initial_total = player_initial_cav + player_initial_inf + player_initial_art

    player_survived_cav = sum(1 for s in player_army.soldiers if s.health > 0 and s.type == UnitType.CAVALRY)
    player_survived_inf = sum(1 for s in player_army.soldiers if s.health > 0 and s.type == UnitType.INFANTRY)
    player_survived_art = sum(1 for s in player_army.soldiers if s.health > 0 and s.type == UnitType.ARTILLERY)
    player_survived_total = player_survived_cav + player_survived_inf + player_survived_art

    player_dead_cav = player_initial_cav - player_survived_cav
    player_dead_inf = player_initial_inf - player_survived_inf
    player_dead_art = player_initial_art - player_survived_art
    player_dead_total = player_dead_cav + player_dead_inf + player_dead_art

    # Подсчет статистики для врага
    enemy_initial_cav = enemy_army.cavalry_count
    enemy_initial_inf = enemy_army.infantry_count
    enemy_initial_art = enemy_army.artillery_count
    enemy_initial_total = enemy_initial_cav + enemy_initial_inf + enemy_initial_art

    enemy_survived_cav = sum(1 for s in enemy_army.soldiers if s.health > 0 and s.type == UnitType.CAVALRY)
    enemy_survived_inf = sum(1 for s in enemy_army.soldiers if s.health > 0 and s.type == UnitType.INFANTRY)
    enemy_survived_art = sum(1 for s in enemy_army.soldiers if s.health > 0 and s.type == UnitType.ARTILLERY)
    enemy_survived_total = enemy_survived_cav + enemy_survived_inf + enemy_survived_art

    enemy_dead_cav = enemy_initial_cav - enemy_survived_cav
    enemy_dead_inf = enemy_initial_inf - enemy_survived_inf
    enemy_dead_art = enemy_initial_art - enemy_survived_art
    enemy_dead_total = enemy_dead_cav + enemy_dead_inf + enemy_dead_art

    # Проверяем условие ничьи (только кавалерия с обеих сторон)
    if (player_survived_cav > 0 and player_survived_inf == 0 and player_survived_art == 0 and
            enemy_survived_cav > 0 and enemy_survived_inf == 0 and enemy_survived_art == 0):
        winner = 'draw'

    # Текст статистики с цветами
    stats = [
        {"text": "=== Ваши войска ===", "color": COLORS['text']},
        {"text": f"Кавалерия: {player_survived_cav}/{player_initial_cav} (погибло: {player_dead_cav})", "color": COLORS['player_cavalry']},
        {"text": f"Пехота:    {player_survived_inf}/{player_initial_inf} (погибло: {player_dead_inf})", "color": COLORS['player_infantry']},
        {"text": f"Артиллерия: {player_survived_art}/{player_initial_art} (погибло: {player_dead_art})", "color": COLORS['player_artillery']},
        {"text": f"Всего:     {player_survived_total}/{player_initial_total} (погибло: {player_dead_total})", "color": COLORS['text']},
        {"text": "", "color": COLORS['text']},
        {"text": "=== Войска врага ===", "color": COLORS['text']},
        {"text": f"Кавалерия: {enemy_survived_cav}/{enemy_initial_cav} (погибло: {enemy_dead_cav})", "color": COLORS['enemy_cavalry']},
        {"text": f"Пехота:    {enemy_survived_inf}/{enemy_initial_inf} (погибло: {enemy_dead_inf})", "color": COLORS['enemy_infantry']},
        {"text": f"Артиллерия: {enemy_survived_art}/{enemy_initial_art} (погибло: {enemy_dead_art})", "color": COLORS['enemy_artillery']},
        {"text": f"Всего:     {enemy_survived_total}/{enemy_initial_total} (погибло: {enemy_dead_total})", "color": COLORS['text']},
        {"text": "", "color": COLORS['text']},
        {
            "text": f"Общие потери: {player_initial_total - player_survived_total + enemy_initial_total - enemy_survived_total} юнитов",
            "color": (255, 200, 100)}  # Оранжевый для общих потерь
    ]

    while running:
        mouse_pos = pygame.mouse.get_pos()

        # Затемнение экрана
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        screen.blit(s, (0, 0))

        # Размеры панели
        panel_width, panel_height = 700, 500
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = (SCREEN_HEIGHT - panel_height) // 2

        # Цвет панели в зависимости от результата
        if winner == 'player':
            panel_color = COLORS['victory_panel']
        elif winner == 'enemy':
            panel_color = COLORS['defeat_panel']
        else:  # Ничья
            panel_color = (60, 60, 30)  # Специальный цвет для ничьи

        pygame.draw.rect(screen, panel_color, (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(screen, COLORS['panel_border'], (panel_x, panel_y, panel_width, panel_height), 3)

        # Текст результата
        font_large = pygame.font.SysFont(None, 72)
        if winner == 'player':
            result_text = "ПОБЕДА!"
        elif winner == 'enemy':
            result_text = "ПОРАЖЕНИЕ"
        else:
            result_text = "НИЧЬЯ!"

        text_surf = font_large.render(result_text, True, COLORS['text'])
        screen.blit(text_surf, (panel_x + (panel_width - text_surf.get_width()) // 2, panel_y + 30))

        # Контейнер для статистики
        stats_container_x = panel_x + 50
        stats_container_y = panel_y + 100
        stats_container_width = panel_width - 100
        stats_container_height = panel_height - 180

        # Фон контейнера
        pygame.draw.rect(screen, (40, 40, 40),
                         (stats_container_x, stats_container_y,
                          stats_container_width, stats_container_height))
        pygame.draw.rect(screen, COLORS['panel_border'],
                         (stats_container_x, stats_container_y,
                          stats_container_width, stats_container_height), 2)

        # Автоматический подбор размера шрифта
        max_font_size = 28
        font = pygame.font.SysFont(None, max_font_size)

        # Проверяем, помещается ли текст
        while max_font_size > 16:
            test_font = pygame.font.SysFont(None, max_font_size)
            line_height = max_font_size + 5
            total_height = len(stats) * line_height

            if total_height <= stats_container_height - 20:
                font = test_font
                break
            max_font_size -= 1

        # Отрисовка статистики с цветами
        current_y = stats_container_y + 20
        for stat in stats:
            text = font.render(stat["text"], True, stat["color"])
            screen.blit(text, (stats_container_x + 20, current_y))
            current_y += line_height

        # Кнопка возврата в меню
        menu_button = Button(panel_x + (panel_width - 200) // 2, panel_y + panel_height - 70,
                             200, 50, "В главное меню")
        menu_button.check_hover(mouse_pos)
        menu_button.draw()

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if menu_button.rect.collidepoint(mouse_pos):
                    return True

        clock.tick(FPS)

def draw_unit_counts(player_counts, enemy_counts):
    font = pygame.font.SysFont(None, 36)

    player_text = font.render(f"Вы: Кав.{player_counts[0]} Пех.{player_counts[1]}", True, COLORS['text'])
    enemy_text = font.render(f"Враг: Кав.{enemy_counts[0]} Пех.{enemy_counts[1]}", True, COLORS['text'])

    screen.blit(player_text, (20, 20))
    screen.blit(enemy_text, (SCREEN_WIDTH - 220, 20))
#----------------------------------------------ГЛАВНОЕ МЕНЮ----------------------------------------------
def main_menu():
    play_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, 200, 50, "Играть", 40)
    exit_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 20, 200, 50, "Выход", 40)

    clock = pygame.time.Clock()
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(COLORS['menu_bg'])

        # Заголовок
        font = pygame.font.SysFont(None, 72)
        title = font.render("Пиксельные Армии", True, COLORS['text'])
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))

        # Кнопки
        play_button.check_hover(mouse_pos)
        exit_button.check_hover(mouse_pos)
        play_button.draw()
        exit_button.draw()

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False

            if play_button.is_clicked(mouse_pos, event):
                return battle_setup()
            if exit_button.is_clicked(mouse_pos, event):
                pygame.quit()
                return False

        clock.tick(FPS)
#----------------------------------------------ПАНЕЛЬ НАСТРОЕК БИТВЫ----------------------------------------------
def battle_setup():
    global global_player_cavalry, global_player_infantry, global_player_artillery
    global global_enemy_cavalry, global_enemy_infantry, global_enemy_artillery
    global global_player_cavalry_positions, global_player_infantry_positions, global_player_artillery_positions
    global global_enemy_positions, global_environment

    # Генерируем окружение только если оно еще не создано
    if global_environment is None:
        global_environment = generate_environment(SCREEN_WIDTH, SCREEN_HEIGHT)

    clock = pygame.time.Clock()
    # Генерируем окружение
    environment = global_environment

    # Инициализируем custom_positions с сохраненными позициями
    custom_positions = {
        'cavalry': [pos for pos in global_player_cavalry_positions],
        'infantry': [pos for pos in global_player_infantry_positions],
        'artillery': [pos for pos in global_player_artillery_positions]
    }

    # Используем глобальные значения по умолчанию
    player_cavalry = global_player_cavalry if not custom_positions['cavalry'] else len(custom_positions['cavalry'])
    player_infantry = global_player_infantry if not custom_positions['infantry'] else len(custom_positions['infantry'])
    player_artillery = global_player_artillery if not custom_positions['artillery'] else len(
        custom_positions['artillery'])
    enemy_cavalry = global_enemy_cavalry
    enemy_infantry = global_enemy_infantry
    enemy_artillery = global_enemy_artillery

    # Области интерфейса
    CONTROL_PANEL = pygame.Rect(0, SCREEN_HEIGHT - 150, SCREEN_WIDTH, 150)

    # Текстура рельефа
    terrain_texture = create_terrain_texture(SCREEN_WIDTH, SCREEN_HEIGHT)

    # Элементы управления
    font = pygame.font.SysFont(None, 24)

    # Создаем поля ввода
    player_cavalry_input = InputBox(120, SCREEN_HEIGHT - 120, 50, 30, str(player_cavalry))
    player_infantry_input = InputBox(120, SCREEN_HEIGHT - 80, 50, 30, str(player_infantry))
    player_artillery_input = InputBox(120, SCREEN_HEIGHT - 40, 50, 30, str(player_artillery))
    enemy_cavalry_input = InputBox(350, SCREEN_HEIGHT - 120, 50, 30, str(enemy_cavalry))
    enemy_infantry_input = InputBox(350, SCREEN_HEIGHT - 80, 50, 30, str(enemy_infantry))
    enemy_artillery_input = InputBox(350, SCREEN_HEIGHT - 40, 50, 30, str(enemy_artillery))

    # Кнопки
    infantry_button = Button(450, SCREEN_HEIGHT - 80, 100, 30, "Пехота")
    cavalry_button = Button(450, SCREEN_HEIGHT - 120, 100, 30, "Кавалерия")
    artillery_button = Button(450, SCREEN_HEIGHT - 40, 100, 30, "Артиллерия")
    delete_button = Button(600, SCREEN_HEIGHT - 80, 100, 30, "Удалить")
    random_enemy_button = Button(600, SCREEN_HEIGHT - 120, 150, 30, "Случайный враг")
    start_button = Button(SCREEN_WIDTH - 220, SCREEN_HEIGHT - 120, 200, 50, "Начать битву", 30)

    placing_units = False
    deleting_units = False
    start_pos = None
    current_type = 'infantry'
    show_controls = True
    delete_mode = False
    enemy_positions = []

    # Предпросмотр врага
    enemy_preview = Army('enemy', enemy_cavalry_input.get_value(),
                         enemy_infantry_input.get_value(), enemy_artillery_input.get_value())

    running = True
    input_boxes = [player_cavalry_input, player_infantry_input, player_artillery_input,
                   enemy_cavalry_input, enemy_infantry_input, enemy_artillery_input]

    while running:
        mouse_pos = pygame.mouse.get_pos()

        # Отрисовка фона с текстурой
        screen.blit(terrain_texture, (0, 0))

        # Отрисовка окружения
        # 1. Сначала рисуем дороги (самый нижний слой окружения)
        for obj in environment:
            if isinstance(obj, Road):
                obj.draw(screen)

        # 2. Затем остальные объекты окружения (реки, дома)
        for obj in environment:
            if not isinstance(obj, (Road, Tree)):
                obj.draw(screen)

        # 3. Затем деревья (поверх домов)
        for obj in environment:
            if isinstance(obj, Tree):
                obj.draw(screen)

        # Отрисовка предпросмотра врага
        for soldier in enemy_preview.soldiers:
            s = soldier
            color = (*s.color[:3], 100)
            surf = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(surf, color, (0, 0, GRID_SIZE, GRID_SIZE))
            screen.blit(surf, (s.x, s.y))

        # Отрисовка размещенных юнитов игрока
        for pos in custom_positions['cavalry']:
            pygame.draw.rect(screen, COLORS['player_cavalry'], (pos[0], pos[1], GRID_SIZE, GRID_SIZE))
        for pos in custom_positions['infantry']:
            pygame.draw.rect(screen, COLORS['player_infantry'], (pos[0], pos[1], GRID_SIZE, GRID_SIZE))
        for pos in custom_positions['artillery']:
            pygame.draw.rect(screen, COLORS['player_artillery'], (pos[0], pos[1], GRID_SIZE, GRID_SIZE))

        # Отрисовка выделения для удаления
        if deleting_units and start_pos:
            selection_rect = pygame.Rect(
                min(start_pos[0], mouse_pos[0]),
                min(start_pos[1], mouse_pos[1]),
                abs(mouse_pos[0] - start_pos[0]),
                abs(mouse_pos[1] - start_pos[1])
            )
            pygame.draw.rect(screen, (255, 0, 0, 150), selection_rect, 2)

        # Отрисовка линии размещения
        if placing_units and start_pos:
            pygame.draw.line(screen, COLORS['highlight'], start_pos, mouse_pos, 2)

        # Отрисовка панели управления
        if show_controls:
            pygame.draw.rect(screen, COLORS['panel_bg'], CONTROL_PANEL)
            pygame.draw.rect(screen, COLORS['panel_border'], CONTROL_PANEL, 2)

            # Отрисовка текста перед полями ввода
            font = pygame.font.SysFont(None, 24)
            player_text = font.render("Ваши войска:", True, COLORS['text'])
            enemy_text = font.render("Войска врага:", True, COLORS['text'])
            screen.blit(player_text, (20, SCREEN_HEIGHT - 140))
            screen.blit(enemy_text, (250, SCREEN_HEIGHT - 140))

            # Отрисовка подписей к полям ввода
            cavalry_label = font.render("Кавалерия:", True, COLORS['text'])
            infantry_label = font.render("Пехота:", True, COLORS['text'])
            artillery_label = font.render("Артиллерия:", True, COLORS['text'])
            screen.blit(cavalry_label, (10, SCREEN_HEIGHT - 120))
            screen.blit(infantry_label, (10, SCREEN_HEIGHT - 80))
            screen.blit(artillery_label, (10, SCREEN_HEIGHT - 40))
            screen.blit(cavalry_label, (240, SCREEN_HEIGHT - 120))
            screen.blit(infantry_label, (240, SCREEN_HEIGHT - 80))
            screen.blit(artillery_label, (240, SCREEN_HEIGHT - 40))

            # Отрисовка полей ввода
            for box in input_boxes:
                box.draw(screen)

            # Отрисовка кнопок
            for btn in [infantry_button, cavalry_button, artillery_button,
                        delete_button, random_enemy_button, start_button]:
                btn.check_hover(mouse_pos)
                btn.draw()

            # Отображение счетчиков размещенных юнитов
            count_text = font.render(
                f"Размещено: Кав. {len(custom_positions['cavalry'])}/{player_cavalry_input.get_value()} "
                f"Пех. {len(custom_positions['infantry'])}/{player_infantry_input.get_value()} "
                f"Арт. {len(custom_positions['artillery'])}/{player_artillery_input.get_value()}",
                True, COLORS['text'])
            screen.blit(count_text, (20, TOP_PANEL_HEIGHT + 10))

        pygame.draw.rect(screen, COLORS['top_panel'], (0, 0, SCREEN_WIDTH, TOP_PANEL_HEIGHT))
        title_text = font.render("Настройка битвы", True, COLORS['text'])
        screen.blit(title_text, (10, 5))

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False

            # Обработка полей ввода
            for box in input_boxes:
                if box.handle_event(event):
                    # Обновляем предпросмотр
                    enemy_preview = Army('enemy',
                                         enemy_cavalry_input.get_value(),
                                         enemy_infantry_input.get_value(),
                                         enemy_artillery_input.get_value())

            # Обработка кнопок
            if infantry_button.is_clicked(mouse_pos, event):
                current_type = 'infantry'
                delete_mode = False
                placing_units = False
            if cavalry_button.is_clicked(mouse_pos, event):
                current_type = 'cavalry'
                delete_mode = False
                placing_units = False
            if artillery_button.is_clicked(mouse_pos, event):
                current_type = 'artillery'
                delete_mode = False
                placing_units = False

            if delete_button.is_clicked(mouse_pos, event):
                delete_mode = not delete_mode
                placing_units = False

            if random_enemy_button.is_clicked(mouse_pos, event):
                enemy_cavalry_input.text = str(random.randint(5, 50))
                enemy_infantry_input.text = str(random.randint(10, 100))
                enemy_artillery_input.text = str(random.randint(0, 10))
                enemy_cavalry_input.txt_surface = enemy_cavalry_input.font.render(enemy_cavalry_input.text, True,
                                                                                  COLORS['text'])
                enemy_infantry_input.txt_surface = enemy_infantry_input.font.render(enemy_infantry_input.text, True,
                                                                                    COLORS['text'])
                enemy_artillery_input.txt_surface = enemy_artillery_input.font.render(enemy_artillery_input.text, True,
                                                                                      COLORS['text'])

                enemy_preview = Army('enemy',
                                     int(enemy_cavalry_input.text),
                                     int(enemy_infantry_input.text),
                                     int(enemy_artillery_input.text))

            if start_button.is_clicked(mouse_pos, event):
                if (len(custom_positions['cavalry']) == player_cavalry_input.get_value() and
                        len(custom_positions['infantry']) == player_infantry_input.get_value() and
                        len(custom_positions['artillery']) == player_artillery_input.get_value()):
                    # Сохраняем значения в глобальные переменные
                    global_player_cavalry = player_cavalry_input.get_value()
                    global_player_infantry = player_infantry_input.get_value()
                    global_player_artillery = player_artillery_input.get_value()
                    global_enemy_cavalry = enemy_cavalry_input.get_value()
                    global_enemy_infantry = enemy_infantry_input.get_value()
                    global_enemy_artillery = enemy_artillery_input.get_value()

                    # Создаем армии
                    player_army = Army('player',
                                       global_player_cavalry,
                                       global_player_infantry,
                                       global_player_artillery,
                                       {'cavalry': custom_positions['cavalry'],
                                        'infantry': custom_positions['infantry'],
                                        'artillery': custom_positions['artillery']})
                    enemy_army = Army('enemy',
                                      global_enemy_cavalry,
                                      global_enemy_infantry,
                                      global_enemy_artillery)

                    # Сохраняем текущие позиции ВСЕХ живых юнитов перед выходом
                    global_player_cavalry_positions = [(s.x, s.y) for s in player_army.soldiers
                                                       if s.type == UnitType.CAVALRY and s.health > 0]
                    global_player_infantry_positions = [(s.x, s.y) for s in player_army.soldiers
                                                        if s.type == UnitType.INFANTRY and s.health > 0]
                    global_player_artillery_positions = [(s.x, s.y) for s in player_army.soldiers
                                                         if s.type == UnitType.ARTILLERY and s.health > 0]

                    battle_result = run_battle(player_army, enemy_army, terrain_texture)
                    if battle_result == 'menu':
                        return True
                    else:
                        return False

            # Остальная обработка событий (размещение/удаление юнитов)
            if delete_mode and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not show_controls or (mouse_pos[1] < CONTROL_PANEL.y and mouse_pos[1] > TOP_PANEL_HEIGHT):
                    deleting_units = True
                    start_pos = mouse_pos

            if delete_mode and event.type == pygame.MOUSEBUTTONUP and event.button == 1 and deleting_units:
                end_pos = mouse_pos
                deleting_units = False

                # Удаление юнитов в выделенной области
                selection_rect = pygame.Rect(
                    min(start_pos[0], end_pos[0]),
                    min(start_pos[1], end_pos[1]),
                    abs(end_pos[0] - start_pos[0]),
                    abs(end_pos[1] - start_pos[1])
                )

                for unit_type in ['cavalry', 'infantry', 'artillery']:
                    custom_positions[unit_type] = [
                        pos for pos in custom_positions[unit_type]
                        if not selection_rect.collidepoint(pos)
                    ]

            if not delete_mode and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not show_controls or (mouse_pos[1] < CONTROL_PANEL.y and mouse_pos[1] > TOP_PANEL_HEIGHT):
                    placing_units = True
                    start_pos = mouse_pos

            if not delete_mode and event.type == pygame.MOUSEBUTTONUP and event.button == 1 and placing_units:
                end_pos = mouse_pos
                placing_units = False
                max_units = (player_infantry_input.get_value() if current_type == 'infantry' else
                             (player_cavalry_input.get_value() if current_type == 'cavalry' else
                              player_artillery_input.get_value()))
                current_units = len(custom_positions[current_type])

                if current_units < max_units and end_pos[1] > TOP_PANEL_HEIGHT:
                    dx = end_pos[0] - start_pos[0]
                    dy = end_pos[1] - start_pos[1]
                    distance = max(1, math.sqrt(dx * dx + dy * dy))
                    steps = min(max_units - current_units, int(distance / (GRID_SIZE + 2)))

                    for i in range(steps):
                        ratio = i / steps
                        x = start_pos[0] + dx * ratio
                        y = start_pos[1] + dy * ratio
                        if y > TOP_PANEL_HEIGHT:
                            custom_positions[current_type].append((x, y))

        pygame.display.flip()
        clock.tick(FPS)
#----------------------------------------------ГЕНЕРАЦИЯ МЕСТНОСТИ----------------------------------------------
def create_terrain_texture(width, height):
    """Создает текстуру с крупным рельефом для пересеченной местности"""
    texture = pygame.Surface((width, height))

    # Цвета рельефа (от высокого к низкому)
    colors = [
        (90, 190, 120),  # Средние склоны
        (70, 160, 110),  # Нижние склоны
    ]

    # Генерация базового шума с очень крупными деталями
    noise_grid = [[0 for _ in range(width)] for _ in range(height)]

    # Заполняем крупные области случайными значениями
    chunk_size = 3  # Размер крупных блоков
    for y in range(0, height, chunk_size):
        for x in range(0, width, chunk_size):
            val = random.random()
            for dy in range(chunk_size):
                for dx in range(chunk_size):
                    if y + dy < height and x + dx < width:
                        noise_grid[y + dy][x + dx] = val

    # Сглаживаем резкие границы между блоками
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            noise_grid[y][x] = (
                    noise_grid[y][x] * 0.5 +
                    noise_grid[y - 1][x] * 0.1 +
                    noise_grid[y + 1][x] * 0.1 +
                    noise_grid[y][x - 1] * 0.1 +
                    noise_grid[y][x + 1] * 0.1 +
                    noise_grid[y - 1][x - 1] * 0.05 +
                    noise_grid[y - 1][x + 1] * 0.05 +
                    noise_grid[y + 1][x - 1] * 0.05 +
                    noise_grid[y + 1][x + 1] * 0.05
            )

    # Нормализуем значения
    min_val = min(min(row) for row in noise_grid)
    max_val = max(max(row) for row in noise_grid)

    # Раскрашиваем текстуру
    for y in range(height):
        for x in range(width):
            # Нормализованная высота (0-1)
            h = (noise_grid[y][x] - min_val) / (max_val - min_val)

            # Определяем цвет по высоте
            color_idx = min(int(h * (len(colors) - 1)), len(colors) - 2)
            ratio = h * (len(colors) - 1) - color_idx

            # Интерполяция между цветами
            r = int(colors[color_idx][0] + ratio * (colors[color_idx + 1][0] - colors[color_idx][0]))
            g = int(colors[color_idx][1] + ratio * (colors[color_idx + 1][1] - colors[color_idx][1]))
            b = int(colors[color_idx][2] + ratio * (colors[color_idx + 1][2] - colors[color_idx][2]))

            texture.set_at((x, y), (r, g, b))

    return texture

class Tree:
    def __init__(self, x, y, size):
        self.x = x  # Теперь это координата основания ствола
        self.y = y
        self.size = size
        self.trunk_height = int(size * 0.6)  # Увеличиваем высоту ствола
        self.crown_radius = int(size * 0.5)  # Размер кроны
        # Цвета
        self.leaves_color = (34, 139, 34)  # Зеленый для листьев
        self.trunk_color = (59, 46, 28)   # Коричневый для ствола
        self.branch_color = (59, 46, 28)  # Тот же цвет для ветвей

    def draw(self, screen):
        # Размеры и параметры
        trunk_height = int(self.size * 0.4)  # длиннее ствол
        trunk_base_width = int(self.size * 0.2)  # ширина у основания

        top_x = self.x
        top_y = self.y - trunk_height

        # Рисуем сужающийся ствол как трапецию
        trunk_top_width = int(trunk_base_width * 0.4)
        points = [
            (self.x - trunk_base_width // 2, self.y),
            (self.x + trunk_base_width // 2, self.y),
            (top_x + trunk_top_width // 2, top_y),
            (top_x - trunk_top_width // 2, top_y)
        ]

        # Крона — круг чуть выше вершины ствола
        main_radius = int(self.size * 0.4)
        crown_center_y = top_y - main_radius // 2
        pygame.draw.circle(screen, self.leaves_color,
                           (self.x, crown_center_y),
                           main_radius)

        # Дополнительные слои листьев для объема
        offsets = [(-main_radius // 1.5, -main_radius // 3),
                   (main_radius // 1.5, -main_radius // 4),
                   (0, -main_radius)]
        for dx, dy in offsets:
            radius = int(main_radius / 1.5)
            pygame.draw.circle(screen, self.leaves_color,
                               (self.x + dx, crown_center_y + dy),
                               radius)

        # Ветви: начинаются у вершины ствола и идут вверх под углами
        branch_length = int(self.size * 0.3)
        branch_thickness_start = max(3, int(self.size * 0.04))  # увеличил толщину веток

        angles_deg = [60, 90, 120]  # углы в градусах: все вверх или чуть в стороны
        for angle_deg in angles_deg:
            rad = math.radians(angle_deg)
            end_x = self.x + branch_length * math.cos(rad)
            end_y = top_y - branch_length * math.sin(rad)   # вверх и в стороны

            num_segments = 10
            for i in range(num_segments):
                t1 = i / num_segments
                t2 = (i +1) / num_segments

                start_x_line = self.x + t1 * branch_length * math.cos(rad)
                start_y_line = top_y - t1 * branch_length * math.sin(rad)

                end_x_line = self.x + t2 * branch_length * math.cos(rad)
                end_y_line = top_y - t2 * branch_length * math.sin(rad)

                thickness = int(branch_thickness_start * (1 - t1))
                if thickness <1:
                    thickness=1

                pygame.draw.line(screen,
                                 self.branch_color,
                                 (start_x_line,start_y_line),
                                 (end_x_line,end_y_line),
                                 thickness)
        pygame.draw.polygon(screen, self.trunk_color, points)

    def contains(self, x, y):
        # Проверяем попадание в крону (основание теперь внизу)
        crown_center_y = self.y - self.trunk_height - self.crown_radius//2
        dist = math.sqrt((x - self.x)**2 + (y - crown_center_y)**2)
        return dist <= self.crown_radius

class House:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size
        # Более реалистичные цвета
        self.wall_color = (139, 69, 19)  # Коричневый
        self.roof_color = (100, 30, 22)  # Темно-красный
        self.window_color = (200, 200, 150)  # Светло-желтый
        self.rect = pygame.Rect(x - size // 2, y - size // 2, size, size)

    def draw(self, screen):
        # Основание дома
        house_width = self.size
        house_height = self.size * 0.7
        base_rect = pygame.Rect(
            self.x - house_width // 2,
            self.y - house_height // 2,
            house_width, house_height
        )
        pygame.draw.rect(screen, self.wall_color, base_rect)

        # Крыша (треугольная)
        roof_points = [
            (self.x - house_width // 2, self.y - house_height // 2),
            (self.x + house_width // 2, self.y - house_height // 2),
            (self.x, self.y - house_height)
        ]
        pygame.draw.polygon(screen, self.roof_color, roof_points)

        # Окна
        window_size = house_width // 4
        pygame.draw.rect(screen, self.window_color,
                         (self.x - window_size, self.y - window_size // 2,
                          window_size, window_size))


    def contains(self, x, y):
        return self.rect.collidepoint(x, y)

class River:
    def __init__(self, points, width):
        self.points = points  # Список точек, через которые проходит река
        self.width = width
        self.color = (64, 164, 223)  # Голубой
        self.color2 = (70, 160, 110)
        self.current_directions = []  # Направления течения для каждого сегмента
        self.current_speeds = []  # Скорости течения

        # Инициализируем направления и скорости течения
        for i in range(len(points) - 1):
            dx = points[i + 1][0] - points[i][0]
            dy = points[i + 1][1] - points[i][1]
            length = max(1, math.sqrt(dx * dx + dy * dy))

            # Основное направление течения (по реке)
            main_dir = (dx / length, dy / length)

            # Добавляем случайное отклонение (до 45 градусов)
            angle = random.uniform(-math.pi / 4, math.pi / 4)
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            dir_x = main_dir[0] * cos_a - main_dir[1] * sin_a
            dir_y = main_dir[0] * sin_a + main_dir[1] * cos_a

            self.current_directions.append((dir_x, dir_y))
            self.current_speeds.append(random.uniform(0, 0))  # Случайная скорость

    def draw(self, screen):
        # Рисуем реку как набор соединенных многоугольников и кругов в изгибах
        for i in range(len(self.points) - 1):
            start = self.points[i]
            end = self.points[i + 1]

            # Вычисляем вектор направления
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = max(1, math.sqrt(dx * dx + dy * dy))

            # Нормализуем и поворачиваем на 90 градусов для перпендикуляра
            nx = -dy / length
            ny = dx / length

            # Точки для основной голубой реки
            points = [
                (start[0] + nx * self.width // 2, start[1] + ny * self.width // 2),
                (start[0] - nx * self.width // 2, start[1] - ny * self.width // 2),
                (end[0] - nx * self.width // 2, end[1] - ny * self.width // 2),
                (end[0] + nx * self.width // 2, end[1] + ny * self.width // 2)
            ]

            # Рисуем голубую реку
            pygame.draw.polygon(screen, self.color, points)

            # Добавляем круг в моменте поворота, если это не последний сегмент
            if i < len(self.points) - 2:
                next_start = self.points[i + 2]
                # Вычисляем угол поворота
                next_dx = next_start[0] - end[0]
                next_dy = next_start[1] - end[1]
                next_length = max(1, math.sqrt(next_dx * next_dx + next_dy * next_dy))

                # Угол между текущим и следующим сегментами
                angle = math.acos((dx * next_dx + dy * next_dy) / (length * next_length))

                # Если угол значителен, рисуем круг
                if angle > 0.1:  # Порог для определения "изгиба"
                    circle_center = (end[0], end[1])
                    pygame.draw.circle(screen, self.color, circle_center, self.width // 2)

    def contains(self, x, y):
        """Проверяет, находится ли точка (x,y) в реке"""
        for i in range(len(self.points) - 1):
            start = self.points[i]
            end = self.points[i + 1]

            # Вектор сегмента реки
            seg_vec = (end[0] - start[0], end[1] - start[1])
            # Вектор от точки до начала сегмента
            pt_vec = (x - start[0], y - start[1])

            # Проекция точки на сегмент
            seg_len = seg_vec[0] ** 2 + seg_vec[1] ** 2
            if seg_len == 0:
                continue

            t = max(0, min(1, (pt_vec[0] * seg_vec[0] + pt_vec[1] * seg_vec[1]) / seg_len))
            proj = (start[0] + t * seg_vec[0], start[1] + t * seg_vec[1])

            # Расстояние до сегмента
            dist = math.sqrt((x - proj[0]) ** 2 + (y - proj[1]) ** 2)
            if dist < self.width / 2:
                return True
        return False

    def get_current_force(self, x, y):
        """Возвращает вектор силы течения в точке (x,y)"""
        for i in range(len(self.points) - 1):
            start = self.points[i]
            end = self.points[i + 1]

            # Проверяем, находится ли точка в этом сегменте реки
            seg_vec = (end[0] - start[0], end[1] - start[1])
            pt_vec = (x - start[0], y - start[1])

            seg_len = math.sqrt(seg_vec[0] ** 2 + seg_vec[1] ** 2)
            if seg_len == 0:
                continue

            t = (pt_vec[0] * seg_vec[0] + pt_vec[1] * seg_vec[1]) / (seg_len * seg_len)

            if 0 <= t <= 1:  # Точка проекции внутри сегмента
                proj_dist = math.sqrt((x - (start[0] + t * seg_vec[0])) ** 2 +
                                      (y - (start[1] + t * seg_vec[1])) ** 2)

                if proj_dist <= self.width / 2:  # Точка в реке
                    force_x = self.current_directions[i][0] * self.current_speeds[i]
                    force_y = self.current_directions[i][1] * self.current_speeds[i]

                    # Уменьшаем силу у берегов
                    edge_factor = 1 - (proj_dist / (self.width / 2)) ** 2
                    return (force_x * edge_factor, force_y * edge_factor)

        return (0, 0)  # Точка не в реке

def generate_environment(width, height, center_clear_radius=200):
    objects = []

    # Варианты путей реки
    river_paths = [
        [(0, 0), (width // 3, height // 3), (2 * width // 3, 2 * height // 3), (width, height)],
        [(0, height // 2), (width // 4, height // 3), (width // 2, height // 2),
         (3 * width // 4, 2 * height // 3), (width, height // 2)],
        [(width // 2, 0), (width // 3, height // 4), (width // 2, height // 2),
         (2 * width // 3, 3 * height // 4), (width // 2, height)],
        [(0, height), (width // 3, 2 * height // 3), (2 * width // 3, height // 3), (width, 0)]
    ]

    # Выбираем случайный путь для реки
    river_points = random.choice(river_paths)
    river = River(river_points, 30)
    objects.append(river)

    # Генерация домов
    houses = []
    house_count = random.randint(8, 15)
    for _ in range(house_count):
        attempts = 0
        placed = False
        while attempts < 100 and not placed:
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(25, 40)

            dist_to_center = math.sqrt((x - width // 2) ** 2 + (y - height // 2) ** 2)
            if (dist_to_center > center_clear_radius and
                    not river.contains(x, y) and
                    not any(obj.contains(x, y) for obj in objects if isinstance(obj, (Tree, House)))):
                house = House(x, y, size)
                objects.append(house)
                houses.append(house)
                placed = True
            attempts += 1

    # Генерация дорог между домами (только если есть хотя бы 2 дома)
    if len(houses) > 1:
        connected = [houses[0]]
        unconnected = houses[1:]

        while unconnected:
            closest_pair = None
            min_distance = float('inf')

            # Находим ближайшую пару соединенный-несоединенный дом
            for connected_house in connected:
                for unconnected_house in unconnected:
                    dx = connected_house.x - unconnected_house.x
                    dy = connected_house.y - unconnected_house.y
                    distance = dx * dx + dy * dy

                    if distance < min_distance:
                        # Проверяем, не пересекает ли дорога реку
                        road_clear = True
                        for i in range(len(river.points) - 1):
                            p1 = river.points[i]
                            p2 = river.points[i + 1]
                            p3 = (connected_house.x, connected_house.y)
                            p4 = (unconnected_house.x, unconnected_house.y)

                            def ccw(A, B, C):
                                return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

                            intersect = ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

                            if intersect:
                                road_clear = False
                                break

                        if road_clear:
                            closest_pair = (connected_house, unconnected_house)
                            min_distance = distance

            if closest_pair:
                src, dst = closest_pair
                # Создаем дорогу
                road_points = [(src.x, src.y), (dst.x, dst.y)]
                road = Road(road_points, 8)
                objects.append(road)
                connected.append(dst)
                unconnected.remove(dst)
            else:
                # Если не удалось найти соединение без пересечения реки, пропускаем этот дом
                unconnected.pop(0)

        # Затем деревья с проверкой на дома
        tree_count = random.randint(30, 50)
        for _ in range(tree_count):
            attempts = 0
            placed = False
            while attempts < 100 and not placed:
                x = random.randint(0, width)
                y = random.randint(0, height)
                size = random.randint(15, 30)

                dist_to_center = math.sqrt((x - width // 2) ** 2 + (y - height // 2) ** 2)
                if (dist_to_center > center_clear_radius and
                        not river.contains(x, y) and
                        not any(h.rect.collidepoint(x, y) for h in houses) and  # Проверка на дома
                        not any(t.contains(x, y) for t in objects if isinstance(t, Tree))):
                    tree = Tree(x, y, size)
                    objects.append(tree)
                    placed = True
                attempts += 1

    return objects

class Road:
    def __init__(self, points, width):
        self.points = points
        self.width = width
        self.color = (240, 230, 140) # Бледно-желтый цвет дороги

    def draw(self, screen):
        # Рисуем дорогу как толстую линию
        if len(self.points) >= 2:
            pygame.draw.line(screen, self.color,
                             self.points[0], self.points[1],
                             self.width)

    def contains(self, x, y):
        # Проверка попадания точки в дорогу (для коллизий)
        x1, y1 = self.points[0]
        x2, y2 = self.points[1]

        # Расстояние от точки до линии
        line_length = math.hypot(x2 - x1, y2 - y1)
        if line_length == 0:
            return False

        # Нормализованные проекции
        u = ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / (line_length * line_length)

        if u < 0 or u > 1:
            return False

        # Ближайшая точка на линии
        closest_x = x1 + u * (x2 - x1)
        closest_y = y1 + u * (y2 - y1)

        # Расстояние до линии
        distance = math.hypot(x - closest_x, y - closest_y)

        return distance <= self.width / 2
#----------------------------------------------ЛОГИКА БИТВЫ----------------------------------------------
def run_battle(player_army, enemy_army, terrain_texture):
    global global_environment
    environment = global_environment if global_environment else generate_environment(SCREEN_WIDTH, SCREEN_HEIGHT)

    ai = AI(enemy_army, player_army)
    player_controller = SmartArmyController(player_army, enemy_army)
    clock = pygame.time.Clock()
    running = True
    selecting = False
    selection_start = (0, 0)
    selection_end = (0, 0)
    drawing_path = False
    path_start = (0, 0)
    path_end = (0, 0)
    show_stats = False
    stats_soldier = None
    artillery_target = None  # Цель для артиллерии игрока

    while running:
        current_time = pygame.time.get_ticks()

        # Отрисовка фона с текстурой и окружением
        draw_all_armies(player_army, enemy_army, terrain_texture, environment)

        # Обновление логики игры
        player_controller.update(current_time)
        player_army.update_movement(enemy_army.soldiers, environment)
        enemy_army.update_movement(player_army.soldiers, environment)
        ai.update(current_time)
        player_army.attack_enemy(enemy_army)
        enemy_army.attack_enemy(player_army)

        # Отрисовка верхней панели
        draw_top_panel(player_army.get_unit_counts(), enemy_army.get_unit_counts())

        # Проверка условий победы
        player_alive = [s for s in player_army.soldiers if s.health > 0]
        enemy_alive = [s for s in enemy_army.soldiers if s.health > 0]

        # Проверяем, остались ли у игрока только артиллерия
        player_only_artillery = (len(player_alive) > 0 and
                               all(s.type == UnitType.ARTILLERY for s in player_alive))

        # Проверяем, остались ли у врага только артиллерия
        enemy_only_artillery = (len(enemy_alive) > 0 and
                              all(s.type == UnitType.ARTILLERY for s in enemy_alive))

        # Если у одной из сторон не осталось юнитов или ничья (только артиллерия с обеих сторон)
        if (len(player_alive) == 0 or len(enemy_alive) == 0 or
                (player_only_artillery and enemy_only_artillery)):

            # Определяем победителя
            if len(enemy_alive) == 0:
                winner = 'player'
            elif len(player_alive) == 0:
                winner = 'enemy'
            else:  # Только кавалерия с обеих сторон
                winner = 'draw'

            if show_victory_screen(winner, player_army, enemy_army):
                return 'menu'
            else:
                return False

        # Обработка событий
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'menu'

                elif event.key == pygame.K_SPACE:
                    current_time = pygame.time.get_ticks()
                    for soldier in player_army.soldiers:
                        if soldier.selected:
                            soldier.target_direction = None
                            soldier.temporary_direction = None
                            soldier.current_target = None
                            soldier.temporary_movement_end_time = current_time

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:  # ПКМ
                    selecting = True
                    selection_start = mouse_pos
                    selection_end = mouse_pos
                    player_army.deselect_all()
                    show_stats = False
                    artillery_target = None

                elif event.button == 1:  # ЛКМ
                    mouse_pressed = True
                    clicked_soldier = None
                    for soldier in player_army.soldiers + enemy_army.soldiers:
                        if (abs(soldier.x - mouse_pos[0]) < GRID_SIZE and
                                abs(soldier.y - mouse_pos[1]) < GRID_SIZE):
                            clicked_soldier = soldier
                            break

                    if clicked_soldier:
                        show_stats = True
                        stats_soldier = clicked_soldier
                    else:
                        drawing_path = True
                        path_start = mouse_pos
                        path_end = mouse_pos
                        show_stats = False
                        artillery_target = mouse_pos

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3 and selecting:  # ПКМ отпущена
                    selecting = False
                    selection_end = mouse_pos
                    selection_rect = pygame.Rect(
                        min(selection_start[0], selection_end[0]),
                        min(selection_start[1], selection_end[1]),
                        abs(selection_end[0] - selection_start[0]),
                        abs(selection_end[1] - selection_start[1])
                    )
                    player_army.select_in_rect(selection_rect)

                elif event.button == 1:  # ЛКМ отпущена
                    if drawing_path:
                        drawing_path = False
                        path_end = mouse_pos
                        if path_start != path_end:
                            dx = path_end[0] - path_start[0]
                            dy = path_end[1] - path_start[1]
                            angle = math.atan2(dy, dx)
                            player_army.set_temporary_direction(angle, 1000)

                            # Если выбрана артиллерия - стреляем
                            for soldier in player_army.soldiers:
                                if soldier.selected and soldier.type == UnitType.ARTILLERY and artillery_target:
                                    soldier.artillery_attack(artillery_target[0], artillery_target[1],
                                                             enemy_army.soldiers)
                    show_stats = False

            elif event.type == pygame.MOUSEMOTION:
                if selecting and pygame.mouse.get_pressed()[2]:  # Перетаскивание ПКМ
                    selection_end = mouse_pos

                if drawing_path and pygame.mouse.get_pressed()[0]:  # Перетаскивание ЛКМ
                    path_end = mouse_pos
                    artillery_target = mouse_pos

        # Отрисовка выделения
        if selecting:
            selection_rect = pygame.Rect(
                min(selection_start[0], selection_end[0]),
                min(selection_start[1], selection_end[1]),
                abs(selection_end[0] - selection_start[0]),
                abs(selection_end[1] - selection_start[1])
            )
            pygame.draw.rect(screen, COLORS['selection'], selection_rect, 2)

        # Отрисовка пути и цели артиллерии
        if drawing_path:
            pygame.draw.line(screen, COLORS['path_line'], path_start, path_end, 3)

            # Рисуем стрелку в конце линии
            angle = math.atan2(path_end[1] - path_start[1], path_end[0] - path_start[0])
            arrow_len = 15
            pygame.draw.line(screen, COLORS['path_line'], path_end,
                             (path_end[0] - arrow_len * math.cos(angle - math.pi / 6),
                              path_end[1] - arrow_len * math.sin(angle - math.pi / 6)), 2)
            pygame.draw.line(screen, COLORS['path_line'], path_end,
                             (path_end[0] - arrow_len * math.cos(angle + math.pi / 6),
                              path_end[1] - arrow_len * math.sin(angle + math.pi / 6)), 2)

            # Для артиллерии показываем радиус взрыва
            for soldier in player_army.soldiers:
                if soldier.selected and soldier.type == UnitType.ARTILLERY:
                    pygame.draw.circle(screen, (255, 100, 100, 50),
                                       artillery_target, soldier.stats['splash_radius'], 1)

        if show_stats and stats_soldier and pygame.mouse.get_pressed()[0]:
            draw_stats_panel(stats_soldier, mouse_pos[0], mouse_pos[1])

        pygame.display.flip()
        clock.tick(FPS)
#----------------------------------------------ГЛАВНЫЙ ИГРОВОЙ ЦИКЛ----------------------------------------------
def main_game(params):
    # Создаем текстуру рельефа
    terrain_texture = create_terrain_texture(SCREEN_WIDTH, SCREEN_HEIGHT)
    # Инициализация армий
    player_army = Army('player', params['player_cavalry'], params['player_infantry'], params['custom_positions'])
    enemy_army = Army('enemy', params['enemy_cavalry'], params['enemy_infantry'])
    ai = AI(enemy_army, player_army)

    # Переменные управления
    selecting = False
    selection_start = (0, 0)
    selection_end = (0, 0)
    show_stats = False
    stats_soldier = None
    drawing_path = False
    path_start = (0, 0)
    path_end = (0, 0)

    clock = pygame.time.Clock()
    running = True

    while running:
        current_time = pygame.time.get_ticks()
        screen.blit(terrain_texture, (0, 0))

        # Обработка событий
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:  # ПКМ - выделение
                    selecting = True
                    selection_start = mouse_pos
                    player_army.deselect_all()

                elif event.button == 1:  # ЛКМ - направление
                    drawing_path = True
                    path_start = path_end = mouse_pos

                    # Проверка клика по солдату
                    for soldier in player_army.soldiers + enemy_army.soldiers:
                        if (abs(soldier.x - mouse_pos[0]) < GRID_SIZE and abs(soldier.y - mouse_pos[1]) < GRID_SIZE):
                            show_stats = True
                            stats_soldier = soldier
                            break

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3 and selecting:
                    selecting = False
                    selection_end = mouse_pos
                    selection_rect = pygame.Rect(
                        min(selection_start[0], selection_end[0]),
                        min(selection_start[1], selection_end[1]),
                        abs(selection_end[0] - selection_start[0]),
                        abs(selection_end[1] - selection_start[1])
                    )
                    player_army.select_in_rect(selection_rect)

                elif event.button == 1 and drawing_path:
                    drawing_path = False
                    if path_start != path_end:
                        dx = path_end[0] - path_start[0]
                        dy = path_end[1] - path_start[1]
                        angle = math.atan2(dy, dx)
                        player_army.set_direction_for_selected(angle, enemy_army.soldiers)
                    show_stats = False

            elif event.type == pygame.MOUSEMOTION:
                if selecting and pygame.mouse.get_pressed()[2]:
                    selection_end = mouse_pos

                if drawing_path and pygame.mouse.get_pressed()[0]:
                    path_end = mouse_pos

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:  # Стоп
                    for soldier in player_army.soldiers:
                        if soldier.selected:
                            soldier.target_direction = None
                            soldier.direction = None

            # Добавляем отображение последних значений юнитов
            font = pygame.font.SysFont(None, 28)
            last_units_text = font.render(
                f"Последние значения: Вы - Кав.{global_player_cavalry} Пех.{global_player_infantry}, "
                f"Враг - Кав.{global_enemy_cavalry} Пех.{global_enemy_infantry}",
                True, COLORS['text'])
            screen.blit(last_units_text, (SCREEN_WIDTH // 2 - last_units_text.get_width() // 2, 250))

        # Обновление ИИ
        ai.update(current_time)

        # Обновление движения
        player_army.update_movement(enemy_army.soldiers)
        enemy_army.update_movement(player_army.soldiers)

        # Боевая система
        player_army.attack_enemy(enemy_army)
        enemy_army.attack_enemy(player_army)

        # Отрисовка
        player_army.draw()
        enemy_army.draw()

        # Отрисовка выделения
        if selecting:
            selection_rect = pygame.Rect(
                min(selection_start[0], selection_end[0]),
                min(selection_start[1], selection_end[1]),
                abs(selection_end[0] - selection_start[0]),
                abs(selection_end[1] - selection_start[1])
            )
            pygame.draw.rect(screen, COLORS['selection'], selection_rect, 1)

        # Отрисовка пути
        if drawing_path:
            pygame.draw.line(screen, COLORS['path_line'], path_start, path_end, 2)

        # Панель характеристик
        if show_stats and stats_soldier and pygame.mouse.get_pressed()[0]:
            draw_stats_panel(stats_soldier, mouse_pos[0], mouse_pos[1])

        # Счетчики юнитов
        draw_unit_counts(player_army.get_unit_counts(), enemy_army.get_unit_counts())

        pygame.display.flip()
        clock.tick(FPS)

    return True
#----------------------------------------------ЗАПУСК----------------------------------------------
def main():
    # Инициализация глобальных переменных для артиллерии
    global global_player_artillery, global_enemy_artillery, global_player_artillery_positions
    global_player_artillery = 0
    global_enemy_artillery = 0
    global_player_artillery_positions = []

    while True:
        result = main_menu()
        if not result:
            break
        if result is True:
            continue
        result = main_game(result)
        if not result:
            break

if __name__ == "__main__":
    main()
    pygame.quit()