import pygame
import copy

LOCALPATH = "/Users/eunbi/Desktop/coding_lesson/project_chess"
pygame.init()
screen_height = 480 + 80 
screen = pygame.display.set_mode((480, screen_height))
pygame.display.set_caption("Chess: Blitz 10min (En Passant/Stalemate Added)")

font = pygame.font.SysFont("Arial", 25)
timer_font = pygame.font.SysFont("Arial", 30, bold=True)
clock = pygame.time.Clock()
TILE = 60

# --- 이미지 로딩 ---
PIECE_IMAGES = {}
piece_symbols = {"R": "Rook", "N": "Knight", "B": "Bishop", "Q": "Queen", "K": "King", "P": "Pawn"}
for team in ["white", "black"]:
    for sym, name in piece_symbols.items():
        try:
            image_path = LOCALPATH + f"/{team}_{name}.png" 
            image = pygame.image.load(image_path)
            PIECE_IMAGES[(sym, team)] = pygame.transform.scale(image, (TILE, TILE))
        except: PIECE_IMAGES[(sym, team)] = None

# --- 게임 설정 ---
TOTAL_GAME_TIME = 10 * 60 
white_time = TOTAL_GAME_TIME
black_time = TOTAL_GAME_TIME
last_ticks = pygame.time.get_ticks()

pieces = []
current_turn = "white"
promoting_pawn = None
promotion_options = ["Q", "R", "B", "N"]
en_passant_target = None  # ⭐ 앙파상 가능 좌표 (col, row)
game_over = False
winner_msg = ""

def reset_game():
    global pieces, current_turn, white_time, black_time, game_over, winner_msg, en_passant_target
    pieces = []
    current_turn = "white"
    white_time = TOTAL_GAME_TIME
    black_time = TOTAL_GAME_TIME
    game_over = False
    winner_msg = ""
    en_passant_target = None
    for col in range(8):
        pieces.append({"symbol": "P", "team": "white", "x": col*TILE, "y": 6*TILE, "has_moved": False})
        pieces.append({"symbol": "P", "team": "black", "x": col*TILE, "y": 1*TILE, "has_moved": False})
    back_rank = ["R","N","B","Q","K","B","N","R"]
    for col, sym in enumerate(back_rank):
        pieces.append({"symbol": sym, "team": "white", "x": col*TILE, "y": 7*TILE, "has_moved": False})
        pieces.append({"symbol": sym, "team": "black", "x": col*TILE, "y": 0*TILE, "has_moved": False})

reset_game()

# --- 로직 함수들 ---
def get_piece_at(col, row, current_pieces):
    for p in current_pieces:
        if p["x"] == col * TILE and p["y"] == row * TILE: return p
    return None

def is_path_clear(c1, r1, c2, r2, current_pieces):
    step_c = 0 if c1 == c2 else (1 if c2 > c1 else -1)
    step_r = 0 if r1 == r2 else (1 if r2 > r1 else -1)
    curr_c, curr_r = c1 + step_c, r1 + step_r
    while (curr_c, curr_r) != (c2, r2):
        if get_piece_at(curr_c, curr_r, current_pieces): return False
        curr_c += step_c; curr_r += step_r
    return True

def can_move_basic(piece, d_col, d_row, current_pieces, ep_target=None):
    col, row = piece["x"]//TILE, piece["y"]//TILE
    sym, team = piece["symbol"], piece["team"]
    target = get_piece_at(d_col, d_row, current_pieces)
    if target and target["team"] == team: return False
    diff_c, diff_r = abs(d_col-col), abs(d_row-row)
    
    if sym == "P":
        direction = -1 if team == "white" else 1
        # 전진
        if d_col == col and d_row == row + direction and not target: return True
        # 2칸 전진
        if d_col == col and d_row == row + 2*direction and not piece["has_moved"] and not target:
            if not get_piece_at(col, row + direction, current_pieces): return True
        # 대각선 공격 (일반 및 앙파상)
        if diff_c == 1 and d_row == row + direction:
            if target: return True
            if (d_col, d_row) == ep_target: return True # ⭐ 앙파상
        return False
    
    # 다른 기물 로직 (동일)
    if sym == "R": return (col == d_col or row == d_row) and is_path_clear(col, row, d_col, d_row, current_pieces)
    if sym == "B": return diff_c == diff_r and is_path_clear(col, row, d_col, d_row, current_pieces)
    if sym == "N": return (diff_c, diff_r) in [(1,2),(2,1)]
    if sym == "Q": return (col == d_col or row == d_row or diff_c == diff_r) and is_path_clear(col, row, d_col, d_row, current_pieces)
    if sym == "K":
        if max(diff_c, diff_r) == 1: return True
        if not piece["has_moved"] and diff_c == 2 and d_row == row: return True
    return False

def is_in_check(team, current_pieces):
    king = next((p for p in current_pieces if p["symbol"] == "K" and p["team"] == team), None)
    if not king: return False
    k_col, k_row = king["x"]//TILE, king["y"]//TILE
    for p in current_pieces:
        if p["team"] != team and can_move_basic(p, k_col, k_row, current_pieces): return True
    return False

def is_legal_move(piece, d_col, d_row, current_pieces, ep_target=None):
    if not can_move_basic(piece, d_col, d_row, current_pieces, ep_target): return False
    col, row = piece["x"]//TILE, piece["y"]//TILE
    
    # 캐슬링 특수 검사 (기존과 동일)
    if piece["symbol"] == "K" and abs(d_col - col) == 2:
        if is_in_check(piece["team"], current_pieces): return False
        rook_col = 7 if d_col == 6 else 0
        step = 1 if d_col == 6 else -1
        if not is_path_clear(col, row, rook_col, row, current_pieces): return False
        rook = get_piece_at(rook_col, row, current_pieces)
        if not rook or rook["symbol"] != "R" or rook["has_moved"]: return False
        for s in [1, 2]:
            test_pieces = copy.deepcopy(current_pieces)
            tp = next(p for p in test_pieces if p["x"] == piece["x"] and p["y"] == piece["y"])
            tp["x"] = (col + s*step) * TILE
            if is_in_check(piece["team"], test_pieces): return False
        return True

    # 가상 이동 후 체크 여부 확인
    test_pieces = copy.deepcopy(current_pieces)
    me = next(tp for tp in test_pieces if tp["x"] == piece["x"] and tp["y"] == piece["y"])
    target = get_piece_at(d_col, d_row, test_pieces)
    
    # 앙파상 시뮬레이션 시 상대 폰 제거
    if piece["symbol"] == "P" and (d_col, d_row) == ep_target and not target:
        enemy_pawn = get_piece_at(d_col, row, test_pieces)
        if enemy_pawn: test_pieces.remove(enemy_pawn)

    if target: test_pieces.remove(target)
    me["x"], me["y"] = d_col * TILE, d_row * TILE
    return not is_in_check(piece["team"], test_pieces)

# ⭐ [체크메이트/스테일메이트 판정]
def check_end_game(team, current_pieces):
    global game_over, winner_msg
    # 합법적인 수가 하나라도 있는지 확인
    has_legal_move = False
    for p in current_pieces:
        if p["team"] == team:
            for r in range(8):
                for c in range(8):
                    if is_legal_move(p, c, r, current_pieces, en_passant_target):
                        has_legal_move = True
                        break
                if has_legal_move: break
        if has_legal_move: break

    if not has_legal_move:
        game_over = True
        if is_in_check(team, current_pieces):
            winner_msg = f"CHECKMATE! {'BLACK' if team == 'white' else 'WHITE'} WINS!"
        else:
            winner_msg = "STALEMATE! IT'S A DRAW."

def switch_turn():
    global current_turn
    current_turn = "black" if current_turn == "white" else "white"
    check_end_game(current_turn, pieces)

# --- 메인 루프 ---
selected_piece = None
running = True

while running:
    t = pygame.time.get_ticks()
    dt = (t - last_ticks) / 1000
    last_ticks = t
    
    if not game_over and not promoting_pawn:
        if current_turn == "white":
            white_time -= dt
            if white_time <= 0: white_time, game_over, winner_msg = 0, True, "TIME OVER! BLACK WINS!"
        else:
            black_time -= dt
            if black_time <= 0: black_time, game_over, winner_msg = 0, True, "TIME OVER! WHITE WINS!"

    screen.fill((200, 200, 200))
    colors = [(240, 217, 181), (181, 136, 99)]
    for r in range(8):
        for c in range(8):
            pygame.draw.rect(screen, colors[(r+c)%2], (c*TILE, r*TILE, TILE, TILE))

    if selected_piece and not game_over:
        for r in range(8):
            for c in range(8):
                if is_legal_move(selected_piece, c, r, pieces, en_passant_target):
                    cx, cy = c * TILE + TILE // 2, r * TILE + TILE // 2
                    target = get_piece_at(c, r, pieces)
                    # 앙파상 자리도 빨간 점으로 표시
                    is_ep = selected_piece["symbol"] == "P" and (c, r) == en_passant_target
                    dot_color = (255, 0, 0) if (target or is_ep) else (0, 255, 0)
                    pygame.draw.circle(screen, dot_color, (cx, cy), 10 if not (target or is_ep) else 20, 0 if not (target or is_ep) else 3)

    for e in pygame.event.get():
        if e.type == pygame.QUIT: running = False
        
        if e.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            if not game_over and my >= 490 and 380 <= mx <= 470:
                game_over = True
                winner_msg = f"{current_turn.upper()} RESIGNED."
                continue

            if game_over: continue 

            if promoting_pawn:
                if 200 <= my <= 280:
                    idx = (mx - 100) // 70
                    if 0 <= idx < 4:
                        promoting_pawn["symbol"] = promotion_options[idx]
                        promoting_pawn = None
                        switch_turn()
                continue

            c, r = mx//TILE, my//TILE
            if r >= 8: continue
            
            if selected_piece is None:
                p = get_piece_at(c, r, pieces)
                if p and p["team"] == current_turn: selected_piece = p
            else:
                if is_legal_move(selected_piece, c, r, pieces, en_passant_target):
                    old_c, old_r = selected_piece["x"]//TILE, selected_piece["y"]//TILE
                    
                    # 앙파상 처리: 상대 폰 제거
                    if selected_piece["symbol"] == "P" and (c, r) == en_passant_target:
                        victim = get_piece_at(c, old_r, pieces)
                        if victim: pieces.remove(victim)

                    # 캐슬링 처리
                    if selected_piece["symbol"] == "K" and abs(c - old_c) == 2:
                        src_col, dst_col = (7, 5) if c == 6 else (0, 3)
                        rook = get_piece_at(src_col, r, pieces)
                        if rook: rook["x"], rook["has_moved"] = dst_col * TILE, True

                    # 앙파상 타겟 설정: 폰이 2칸 전진했을 때만 발생
                    new_ep_target = None
                    if selected_piece["symbol"] == "P" and abs(r - old_r) == 2:
                        new_ep_target = (c, (r + old_r) // 2)
                    
                    target = get_piece_at(c, r, pieces)
                    if target: pieces.remove(target)
                    
                    selected_piece["x"], selected_piece["y"] = c*TILE, r*TILE
                    selected_piece["has_moved"] = True
                    en_passant_target = new_ep_target # ⭐ 타겟 업데이트
                    
                    if selected_piece["symbol"] == "P" and (r == 0 or r == 7):
                        promoting_pawn = selected_piece
                    else:
                        switch_turn()
                selected_piece = None

    for p in pieces:
        img = PIECE_IMAGES.get((p["symbol"], p["team"]))
        if img: screen.blit(img, (p["x"], p["y"]))
    if selected_piece:
        pygame.draw.rect(screen, (255,255,0), (selected_piece["x"], selected_piece["y"], TILE, TILE), 3)

    if promoting_pawn:
        menu_rect = pygame.Rect(100, 200, 280, 80)
        pygame.draw.rect(screen, (255,255,255), menu_rect); pygame.draw.rect(screen, (0,0,0), menu_rect, 2)
        for i, sym in enumerate(promotion_options):
            img = PIECE_IMAGES.get((sym, promoting_pawn["team"]))
            if img: screen.blit(img, (110 + i * 70, 210))

    # --- 하단 UI (기존 유지) ---
    pygame.draw.rect(screen, (50, 50, 50), (0, 480, 480, 80))
    def format_time(seconds):
        return f"{int(seconds//60):02}:{int(seconds%60):02}"

    if not game_over:
        status_text = f"TURN: {current_turn.upper()}"
        if is_in_check(current_turn, pieces): status_text += " (CHECK!)"
        txt = font.render(status_text, True, (255, 255, 255))
        screen.blit(txt, (240 - txt.get_width()//2, 490))
        
        resign_rect = pygame.Rect(380, 505, 90, 35)
        pygame.draw.rect(screen, (150, 50, 50), resign_rect)
        pygame.draw.rect(screen, (255, 255, 255), resign_rect, 2)
        resign_txt = font.render("RESIGN", True, (255, 255, 255))
        screen.blit(resign_txt, (resign_rect.centerx - resign_txt.get_width()//2, resign_rect.centery - resign_txt.get_height()//2))
    else:
        txt = font.render(winner_msg, True, (255, 255, 0))
        screen.blit(txt, (240 - txt.get_width()//2, 490))

    w_color = (255, 255, 0) if current_turn == "white" and not game_over else (255, 255, 255)
    b_color = (255, 255, 0) if current_turn == "black" and not game_over else (255, 255, 255)
    w_txt = timer_font.render(f"W: {format_time(white_time)}", True, w_color)
    b_txt = timer_font.render(f"B: {format_time(black_time)}", True, b_color)
    screen.blit(w_txt, (50, 520)); screen.blit(b_txt, (220, 520))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()