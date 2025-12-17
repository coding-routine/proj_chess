import pygame
import copy

pygame.init()
screen_height = 480 + 40 
screen = pygame.display.set_mode((480, screen_height))
pygame.display.set_caption("Chess: Castling & Checkmate")

font = pygame.font.SysFont("Arial", 25)
clock = pygame.time.Clock()
TILE = 60

# 1. 이미지 로드 (기존과 동일)
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
# 데이터 초기화 (has_moved 추가)
# ---------------------------------------------------
pieces = []
def reset_game():
    global pieces, current_turn, game_over_msg
    pieces = []
    current_turn = "white"
    game_over_msg = None
    for col in range(8):
        pieces.append({"symbol": "P", "team": "white", "x": col*TILE, "y": 6*TILE, "has_moved": False})
        pieces.append({"symbol": "P", "team": "black", "x": col*TILE, "y": 1*TILE, "has_moved": False})
    back_rank = ["R","N","B","Q","K","B","N","R"]
    for col, sym in enumerate(back_rank):
        pieces.append({"symbol": sym, "team": "white", "x": col*TILE, "y": 7*TILE, "has_moved": False})
        pieces.append({"symbol": sym, "team": "black", "x": col*TILE, "y": 0*TILE, "has_moved": False})

reset_game()

# ---------------------------------------------------
# 보조 함수 및 규칙 (이동 규칙은 기존 유지하되 King/Castling 수정)
# ---------------------------------------------------
def get_piece_at(col, row, current_pieces):
    for p in current_pieces:
        if p["x"] == col * TILE and p["y"] == row * TILE:
            return p
    return None

def is_path_clear(c1, r1, c2, r2, current_pieces):
    step_c = 0 if c1 == c2 else (1 if c2 > c1 else -1)
    step_r = 0 if r1 == r2 else (1 if r2 > r1 else -1)
    curr_c, curr_r = c1 + step_c, r1 + step_r
    while (curr_c, curr_r) != (c2, r2):
        if get_piece_at(curr_c, curr_r, current_pieces): return False
        curr_c += step_c
        curr_r += step_r
    return True

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
    if sym == "R":
        return (col == d_col or row == d_row) and is_path_clear(col, row, d_col, d_row, current_pieces)
    if sym == "B":
        return abs(d_col-col) == abs(d_row-row) and is_path_clear(col, row, d_col, d_row, current_pieces)
    if sym == "N":
        return (abs(d_col-col), abs(d_row-row)) in [(1,2),(2,1)]
    if sym == "Q":
        return (col == d_col or row == d_row or abs(d_col-col) == abs(d_row-row)) and is_path_clear(col, row, d_col, d_row, current_pieces)
    if sym == "K":
        if max(abs(d_col-col), abs(d_row-row)) == 1: return True
        # 캐슬링 기본 조건 (왕이 2칸 이동)
        if not piece["has_moved"] and d_row == row and abs(d_col - col) == 2:
            return True # 상세 체크는 is_legal_move에서 수행
    return False

# ---------------------------------------------------
# 체크 및 체크메이트 핵심 로직
# ---------------------------------------------------
def find_king(team, current_pieces):
    for p in current_pieces:
        if p["symbol"] == "K" and p["team"] == team: return p
    return None

def is_in_check(team, current_pieces):
    king = find_king(team, current_pieces)
    if not king: return False
    k_col, k_row = king["x"]//TILE, king["y"]//TILE
    for p in current_pieces:
        if p["team"] != team:
            if can_move_basic(p, k_col, k_row, current_pieces): return True
    return False

def is_legal_move(piece, d_col, d_row, current_pieces):
    # 1. 기본 이동 규칙 확인
    if not can_move_basic(piece, d_col, d_row, current_pieces): return False
    
    # 2. 캐슬링 특수 검사
    col, row = piece["x"]//TILE, piece["y"]//TILE
    if piece["symbol"] == "K" and abs(d_col - col) == 2:
        if is_in_check(piece["team"], current_pieces): return False
        rook_col = 7 if d_col == 6 else 0
        step = 1 if d_col == 6 else -1
        # 경로 확인
        if not is_path_clear(col, row, rook_col, row, current_pieces): return False
        # 왕이 지나가는 칸이 공격받는지 확인
        for s in [1, 2]:
            test_pieces = copy.deepcopy(current_pieces)
            tp = get_piece_at(col, row, test_pieces)
            tp["x"] = (col + s*step) * TILE
            if is_in_check(piece["team"], test_pieces): return False
        return True

    # 3. 이동 후 내가 체크 상태가 되는지 확인
    test_pieces = copy.deepcopy(current_pieces)
    p_idx = current_pieces.index(piece)
    tp = test_pieces[p_idx]
    target = get_piece_at(d_col, d_row, test_pieces)
    if target: test_pieces.remove(target)
    tp["x"], tp["y"] = d_col * TILE, d_row * TILE
    return not is_in_check(piece["team"], test_pieces)

def is_checkmate(team, current_pieces):
    if not is_in_check(team, current_pieces): return False
    for p in current_pieces:
        if p["team"] == team:
            for r in range(8):
                for c in range(8):
                    if is_legal_move(p, c, r, current_pieces): return False
    return True

# ---------------------------------------------------
# 메인 루프
# ---------------------------------------------------
selected_piece = None
game_over_msg = None

while True:
    screen.fill((200, 200, 200))
    # 보드 그리기
    colors = [(240, 217, 181), (181, 136, 99)]
    for r in range(8):
        for c in range(8):
            pygame.draw.rect(screen, colors[(r+c)%2], (c*TILE, r*TILE, TILE, TILE))

    for e in pygame.event.get():
        if e.type == pygame.QUIT: pygame.quit(); exit()
        if game_over_msg:
            if e.type == pygame.MOUSEBUTTONDOWN: reset_game()
            continue

        if e.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            c, r = mx//TILE, my//TILE
            if r >= 8: continue

            if selected_piece is None:
                p = get_piece_at(c, r, pieces)
                if p and p["team"] == current_turn: selected_piece = p
            else:
                if is_legal_move(selected_piece, c, r, pieces):
                    # 캐슬링 실행 시 룩도 이동
                    if selected_piece["symbol"] == "K" and abs(c - selected_piece["x"]//TILE) == 2:
                        rook_src_c = 7 if c == 6 else 0
                        rook_dest_c = 5 if c == 6 else 3
                        rook = get_piece_at(rook_src_c, r, pieces)
                        rook["x"] = rook_dest_c * TILE
                        rook["has_moved"] = True
                    
                    target = get_piece_at(c, r, pieces)
                    if target: pieces.remove(target)
                    selected_piece["x"], selected_piece["y"] = c*TILE, r*TILE
                    selected_piece["has_moved"] = True
                    current_turn = "black" if current_turn == "white" else "white"
                    
                    if is_checkmate(current_turn, pieces):
                        game_over_msg = f"CHECKMATE! {('BLACK' if current_turn=='white' else 'WHITE')} WINS!"
                selected_piece = None

    # 말 그리기
    for p in pieces:
        img = PIECE_IMAGES.get((p["symbol"], p["team"]))
        if img: screen.blit(img, (p["x"], p["y"]))
    
    if selected_piece:
        pygame.draw.rect(screen, (255,255,0), (selected_piece["x"], selected_piece["y"], TILE, TILE), 3)

    # 하단 텍스트
    msg = game_over_msg if game_over_msg else f"TURN: {current_turn.upper()}"
    if not game_over_msg and is_in_check(current_turn, pieces): msg += " (CHECK!)"
    txt = font.render(msg, True, (0,0,0) if current_turn == 'black' and not game_over_msg else (255,0,0) if game_over_msg else (255,255,255))
    screen.blit(txt, (240 - txt.get_width()//2, 485))

    pygame.display.flip()
    clock.tick(30)