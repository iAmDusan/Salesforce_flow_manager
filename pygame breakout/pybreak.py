# simple breakout clone with collision detection, bricks, ball, and paddle

import pygame
import sys

# Initialize Pygame
pygame.init()

# Inititalize Clock
clock = pygame.time.Clock()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 10
BALL_SIZE = 10
BRICK_WIDTH = 60
BRICK_HEIGHT = 20

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Breakout Clone")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)


# Paddle object
class Paddle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((PADDLE_WIDTH, PADDLE_HEIGHT))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.x = (SCREEN_WIDTH - PADDLE_WIDTH) // 2
        self.rect.y = SCREEN_HEIGHT - PADDLE_HEIGHT - 10

    def update(self):
        mouse_x, _ = pygame.mouse.get_pos()
        self.rect.x = mouse_x - (PADDLE_WIDTH // 2)
        self.rect.clamp_ip(screen.get_rect())

# Ball object
class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((BALL_SIZE, BALL_SIZE))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = (SCREEN_WIDTH - BALL_SIZE) // 2
        self.rect.y = (SCREEN_HEIGHT - BALL_SIZE) // 2
        self.dx = 5
        self.dy = -5

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy

        if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.dx = -self.dx
        if self.rect.top < 0:
            self.dy = -self.dy

        # New collision detection for the paddle
        if self.rect.colliderect(paddle.rect):
            # Calculate the distance between ball and paddle centers along the x-axis
            offset_x = (self.rect.centerx - paddle.rect.centerx) / (paddle.rect.width / 2)

            # Scaling factor to control the maximum angle change
            scaling_factor = 5

            # Apply the calculated angle change to the ball's x-direction
            self.dx += offset_x * scaling_factor
            self.dy = -abs(self.dy)
            
# Brick object
class Brick(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((BRICK_WIDTH, BRICK_HEIGHT))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


# Game objects
paddle = Paddle()
ball = Ball()
bricks = pygame.sprite.Group()

# Create bricks
for i in range(5):
    for j in range(10):
        brick_x = j * (BRICK_WIDTH + 10) + 30
        brick_y = i * (BRICK_HEIGHT + 10) + 50
        brick = Brick(brick_x, brick_y)
        bricks.add(brick)

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Update game objects
    paddle.update()
    ball.update()

    # Collision detection
    if ball.rect.colliderect(paddle.rect):
        ball.dy = -abs(ball.dy)

    collided_bricks = pygame.sprite.spritecollide(ball, bricks, True)
    if collided_bricks:
        ball.dy = -ball.dy
        # You can also add scoring logic here, e.g., increase the score for each brick hit

    if ball.rect.bottom > SCREEN_HEIGHT:
        # Ball went out of the screen, you can handle the game over or life loss logic here
        ball.rect.x = (SCREEN_WIDTH - BALL_SIZE) // 2
        ball.rect.y = (SCREEN_HEIGHT - BALL_SIZE) // 2
        ball.dy = -abs(ball.dy)

    # Draw screen
    screen.fill(BLACK)
    pygame.draw.rect(screen, WHITE, paddle.rect)
    pygame.draw.ellipse(screen, RED, ball.rect)
    bricks.draw(screen)

    pygame.display.flip()

    # Limit the frame rate
    clock.tick(60)
