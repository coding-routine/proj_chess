import pygame
import copy

pygame.init()
# 1. 화면 설정 (턴 표시를 위해 아래 40픽셀 추가)
screen_height = 480 + 40 
screen = pygame.display.set_mode((480, screen_height))
pygame.display.set_caption("Chess with Hint & Promotion")

font = pygame.font.SysFont("Arial", 25)
clock = pygame.time.Clock()
TILE = 60

# 2. 이미지 로딩 (기존 경로 유지)
PIECE_IMAGES = {}
piece_symbols = {"R": "Rook", "N": "Knight", "B": "Bishop", "Q": "Queen", "K": "King", "P": "Pawn"}
for team in ["white", "black"]:
    for sym, name in piece_symbols.items():
        try:
            image_path = f"/Users/eunbi/Desktop/coding_lesson/project_chess/{team}_{name}.png" 
            image = pygame.image.load(image_path)
            PIECE_IMAGES[(sym, team)] = pygame.transform.scale(image, (TILE, TILE))
        except:
            PIECE_IMAGES[(sym, team)] = None

# ---------------------------------------------------
# 데이터 초기화 및 보조 함수 (이전 코드와 동일)
# ---------------------------------------------------
pieces = []
def reset_game():
    global pieces, current_turn
    pieces = []
    current_turn = "white"
    for col in range(8):
        pieces.append({"symbol": "P", "team": "white", "x": col*TILE, "y": 6*TILE, "has_moved": False})
        pieces.append({"symbol": "P", "team": "black", "x": col*TILE, "y": 1*TILE, "has_moved": False})
    back_rank = ["R","N","B","Q","K","B","N","R"]
    for col, sym in enumerate(back_rank):
        pieces.append({"symbol": sym, "team": "white", "x": col*TILE, "y": 7*TILE, "has_moved": False})
        pieces.append({"symbol": sym, "team": "black", "x": col*TILE, "y": 0*TILE, "has_moved": False})

reset_game()

def get_piece_at(col, row, current_pieces):
    for p in current_pieces:
        if p["x"] == col * TILE and p["y"] == row * TILE:
            return p
    return None

# 길 막힘 검사
def is_path_clear(c1, r1, c2, r2, current_pieces):
    step_c = 0 if c1 == c2 else (1 if c2 > c1 else -1)
    step_r = 0 if r1 == r2 else (1 if r2 > r1 else -1)
    curr_c, curr_r = c1 + step_c, r1 + step_r
    while (curr_c, curr_r) != (c2, r2):
        if get_piece_at(curr_c, curr_r, current_pieces): return False
        curr_c += step_c; curr_r += step_r
    return True

# ---------------------------------------------------
# 규칙 검사 로직 (체크/체크메이트 포함)
# ---------------------------------------------------
def can_move_basic(piece, d_col, d_row, current_pieces):
    col, row = piece["x"]//TILE, piece["y"]//TILE
    sym, team = piece["symbol"], piece["team"]
    target = get_piece_at(d_col, d_row, current_pieces)
    if target and target["team"] == team: return False
    
    if sym == "P":
        dir = -1 if team == "white" else 1
        if d_col == col and d_row == row + dir and not target: return True
        if d_col == col and d_row == row + 2*dir and not piece["has_moved"] and not target:
            if not get_piece_at(col, row + dir, current_pieces): return True
        if abs(d_col - col) == 1 and d_row == row + dir and target: return True
        return False
    if sym == "R": return (col == d_col or row == d_row) and is_path_clear(col, row, d_col, d_row, current_pieces)
    if sym == "B": return abs(d_col-col) == abs(d_row-row) and is_path_clear(col, row, d_col, d_row, current_pieces)
    if sym == "N": return (abs(d_col-col), abs(d_row-row)) in [(1,2),(2,1)]
    if sym == "Q": return (col == d_col or row == d_row or abs(d_col-col) == abs(d_row-row)) and is_path_clear(col, row, d_col, d_row, current_pieces)
    if sym == "K": return max(abs(d_col-col), abs(d_row-row)) == 1
    return False

def is_in_check(team, current_pieces):
    king = next(p for p in current_pieces if p["symbol"] == "K" and p["team"] == team)
    k_col, k_row = king["x"]//TILE, king["y"]//TILE
    for p in current_pieces:
        if p["team"] != team and can_move_basic(p, k_col, k_row, current_pieces): return True
    return False

def is_legal_move(piece, d_col, d_row, current_pieces):
    if not can_move_basic(piece, d_col, d_row, current_pieces): return False
    test_pieces = copy.deepcopy(current_pieces)
    me = next(tp for tp in test_pieces if tp["x"] == piece["x"] and tp["y"] == piece["y"])
    target = get_piece_at(d_col, d_row, test_pieces)
    if target: test_pieces.remove(target)
    me["x"], me["y"] = d_col * TILE, d_row * TILE
    return not is_in_check(piece["team"], test_pieces)

# ---------------------------------------------------
# 메인 루프
# ---------------------------------------------------
selected_piece = None
running = True

while running:
    screen.fill((200, 200, 200))
    # 보드 그리기
    colors = [(240, 217, 181), (181, 136, 99)]
    for r in range(8):
        for c in range(8):
            pygame.draw.rect(screen, colors[(r+c)%2], (c*TILE, r*TILE, TILE, TILE))

    # ⭐ [기능 1] 힌트 시스템: 선택된 말이 갈 수 있는 곳에 점 그리기
    if selected_piece:
        for r in range(8):
            for c in range(8):
                if is_legal_move(selected_piece, c, r, pieces):
                    cx, cy = c * TILE + TILE // 2, r * TILE + TILE // 2
                    target = get_piece_at(c, r, pieces)
                    # 잡을 수 있는 적이 있으면 빨간 테두리, 빈 곳은 초록 점
                    if target:
                        pygame.draw.circle(screen, (255, 0, 0), (cx, cy), 20, 3)
                    else:
                        pygame.draw.circle(screen, (0, 255, 0), (cx, cy), 8)

    for e in pygame.event.get():
        if e.type == pygame.QUIT: running = False
        if e.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            c, r = mx//TILE, my//TILE
            if r >= 8: continue

            if selected_piece is None:
                p = get_piece_at(c, r, pieces)
                if p and p["team"] == current_turn: selected_piece = p
            else:
                if is_legal_move(selected_piece, c, r, pieces):
                    target = get_piece_at(c, r, pieces)
                    if target: pieces.remove(target)
                    selected_piece["x"], selected_piece["y"] = c*TILE, r*TILE
                    selected_piece["has_moved"] = True
                    
                    # ⭐ [기능 2] 폰 승진: 끝에 도달하면 퀸으로 변신
                    if selected_piece["symbol"] == "P":
                        if (selected_piece["team"] == "white" and r == 0) or \
                           (selected_piece["team"] == "black" and r == 7):
                            selected_piece["symbol"] = "Q"

                    current_turn = "black" if current_turn == "white" else "white"
                selected_piece = None

    # 말 그리기
    for p in pieces:
        img = PIECE_IMAGES.get((p["symbol"], p["team"]))
        if img: screen.blit(img, (p["x"], p["y"]))
        else: # 이미지 없을 때 대비 텍스트
            txt = font.render(p["symbol"], True, (255,255,255) if p["team"]=="white" else (0,0,0))
            screen.blit(txt, (p["x"]+15, p["y"]+15))
    
    # 선택 사각형
    if selected_piece:
        pygame.draw.rect(screen, (255,255,0), (selected_piece["x"], selected_piece["y"], TILE, TILE), 3)

    # 턴 표시
    msg = f"TURN: {current_turn.upper()}"
    if is_in_check(current_turn, pieces): msg += " (CHECK!)"
    txt = font.render(msg, True, (0,0,0) if current_turn=='black' else (255,255,255))
    screen.blit(txt, (240 - txt.get_width()//2, 485))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()