import pygame
import sys
import game # 기존 game.py의 변수와 클래스를 가져옵니다.

# --- AI 제어 함수 ---

def control_player_ai(player, ball, side):
    """
    단순한 AI 로직으로 플레이어를 제어하는 함수
    - player: 제어할 플레이어 객체 (player1 or player2)
    - ball: 공 객체
    - side: 플레이어의 진영 ('left' or 'right')
    """
    # 1. 수평 이동 로직
    # 공이 자기 진영에 있을 때 공을 따라 이동
    is_ball_on_my_side = (side == 'left' and ball.x < game.SCREEN_WIDTH / 2) or \
                         (side == 'right' and ball.x > game.SCREEN_WIDTH / 2)

    if is_ball_on_my_side:
        # 공보다 왼쪽에 있으면 오른쪽으로 이동
        if player.rect.centerx < ball.x - 10:
            player.move(game.PLAYER_SPEED)
        # 공보다 오른쪽에 있으면 왼쪽으로 이동
        elif player.rect.centerx > ball.x + 10:
            player.move(-game.PLAYER_SPEED)
    else:
        # 공이 상대 진영에 있으면 자기 진영의 중앙으로 복귀
        target_x = game.SCREEN_WIDTH // 4 if side == 'left' else game.SCREEN_WIDTH * 3 // 4
        if player.rect.centerx < target_x - game.PLAYER_SPEED:
            player.move(game.PLAYER_SPEED)
        elif player.rect.centerx > target_x + game.PLAYER_SPEED:
            player.move(-game.PLAYER_SPEED)

    # 2. 점프 로직
    # 공이 자기 진영에 있고, 플레이어보다 위에 있으며, 가까이 있을 때 점프
    horizontal_distance = abs(player.rect.centerx - ball.x)
    is_ball_above = ball.y < player.rect.top

    if is_ball_on_my_side and is_ball_above and horizontal_distance < 80:
        player.jump()

# --- 게임 초기화 ---
pygame.init()
screen = pygame.display.set_mode((game.SCREEN_WIDTH, game.SCREEN_HEIGHT))
pygame.display.set_caption("AI vs AI Volleyball")
clock = pygame.time.Clock()

# game.py의 초기화 함수를 호출하여 게임 상태를 설정합니다.
game.reset_game()

# --- 메인 루프 ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # 스페이스바를 누르면 게임 재시작
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                game.reset_game()

    # AI로 각 플레이어 제어
    control_player_ai(game.player1, game.ball, 'left')
    control_player_ai(game.player2, game.ball, 'right')

    # 게임 로직 업데이트 (env.py의 step 함수 로직과 동일)
    game.player1.update()
    game.player2.update()
    game.ball.update()
    
    # 충돌 처리
    for player in [game.player1, game.player2]:
        dist_x = game.ball.x - player.rect.centerx
        dist_y = game.ball.y - player.rect.centery
        distance = (dist_x**2 + dist_y**2)**0.5
        if distance < game.BALL_RADIUS + game.PLAYER_WIDTH / 2:
            game.ball.y_velocity = -10
            game.ball.x_velocity = (dist_x / 20) * 5

    if pygame.Rect(game.ball.x - game.ball.radius, game.ball.y - game.ball.radius, game.ball.radius*2, game.ball.radius*2).colliderect(game.net_rect):
        game.ball.x_velocity *= -1
        
    # 득점 처리
    if game.ball.y + game.ball.radius > game.SCREEN_HEIGHT:
        if game.ball.x < game.SCREEN_WIDTH // 2:
            game.score2 += 1
            game.ball.reset(-1)
        else:
            game.score1 += 1
            game.ball.reset(1)
            
    # 승리 조건 확인 및 게임오버 처리
    if game.score1 >= game.WINNING_SCORE:
        game.message = "Player 1 Wins!"
        game.game_over = True
    elif game.score2 >= game.WINNING_SCORE:
        game.message = "Player 2 Wins!"
        game.game_over = True

    # --- 화면 그리기 ---
    screen.fill(game.BLUE)
    game.player1.draw()
    game.player2.draw()
    game.ball.draw()
    pygame.draw.rect(screen, game.BLACK, game.net_rect)

    score1_text = game.score_font.render(str(game.score1), True, game.WHITE)
    score2_text = game.score_font.render(str(game.score2), True, game.WHITE)
    screen.blit(score1_text, (game.SCREEN_WIDTH // 4, 20))
    screen.blit(score2_text, (game.SCREEN_WIDTH * 3 // 4 - score2_text.get_width(), 20))

    if game.game_over:
        msg_text = game.message_font.render(game.message, True, game.YELLOW)
        restart_text = game.message_font.render("Press SPACE to Restart", True, game.WHITE)
        screen.blit(msg_text, (game.SCREEN_WIDTH // 2 - msg_text.get_width() // 2, game.SCREEN_HEIGHT // 2 - 50))
        screen.blit(restart_text, (game.SCREEN_WIDTH // 2 - restart_text.get_width() // 2, game.SCREEN_HEIGHT // 2 + 10))


    pygame.display.flip()
    clock.tick(60)