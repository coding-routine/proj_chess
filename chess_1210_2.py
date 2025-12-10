import pygame

pygame.init()
# ⭐ 1. 화면 크기 변경 (턴 표시를 위해)
screen_height = 480 + 40 # 40픽셀 추가
screen = pygame.display.set_mode((480, screen_height))
pygame.display.set_caption("Easy Chess for Kids")

font = pygame.font.SysFont("Arial", 30) # 폰트 크기 조금 줄임
clock = pygame.time.Clock()

TILE = 60

# ⭐ 2. 이미지 로딩 섹션 추가
PIECE_IMAGES = {}
# 체스 말 심볼과 파일 이름 매핑
piece_symbols = {"R": "Rook", "N": "Knight", "B": "Bishop", "Q": "Queen", "K": "King", "P": "Pawn"}

for team in ["white", "black"]:
    for sym, name in piece_symbols.items():
        try:
            # 이미지가 'images' 폴더에 있다고 가정
            image_path = f"/Users/eunbi/Desktop/coding_lesson/project_chess/{team}_{name}.png" 
            image = pygame.image.load(image_path)
            # TILE 크기에 맞게 이미지 크기 조정
            scaled_image = pygame.transform.scale(image, (TILE, TILE))
            PIECE_IMAGES[(sym, team)] = scaled_image
        except pygame.error:
            # 이미지가 없을 경우 폰트 렌더링을 위해 None 저장
            # print(f"Warning: Could not load image {image_path}. Using text fallback.")
            PIECE_IMAGES[(sym, team)] = None
            

# ---------------------------------------------------
# 1) 모든 체스 말 32개 자동 배치 (기존과 동일)
# ---------------------------------------------------
pieces = []

# Pawn 16개
for col in range(8):
    pieces.append({"symbol": "P", "team": "white", "x": col*TILE, "y": 6*TILE})
    pieces.append({"symbol": "P", "team": "black", "x": col*TILE, "y": 1*TILE})

# 백 / 흑 주요 말 (R N B Q K B N R)
back_rank = ["R","N","B","Q","K","B","N","R"]

for col, sym in enumerate(back_rank):
    pieces.append({"symbol": sym, "team": "white", "x": col*TILE, "y": 7*TILE})
    pieces.append({"symbol": sym, "team": "black", "x": col*TILE, "y": 0*TILE})


# ---------------------------------------------------
# 2) 보조 함수들 (기존과 동일)
# ---------------------------------------------------
def draw_board():
    # 보드 영역 (480x480)만 그립니다.
    colors = [(240, 217, 181), (181, 136, 99)]
    for r in range(8):
        for c in range(8):
            pygame.draw.rect(screen, colors[(r+c)%2], (c*TILE, r*TILE, TILE, TILE))

def get_piece_at(col, row):
    x = col * TILE
    y = row * TILE
    for p in pieces:
        if p["x"] == x and p["y"] == y:
            return p
    return None

def remove_piece(piece):
    if piece in pieces:
        pieces.remove(piece)


# ---------------------------------------------------
# 3) 이동 규칙 함수들 (Pawn에 첫 2칸 이동 규칙 추가)
# ---------------------------------------------------
def can_pawn_move(piece, col, row, dest_col, dest_row):
    team = piece["team"]
    direction = -1 if team == "white" else 1

    # 1) 앞 한 칸
    if dest_col == col and dest_row == row + direction:
        if get_piece_at(dest_col, dest_row) is None:
            return True

    # 2) 대각선 먹기
    if abs(dest_col - col) == 1 and dest_row == row + direction:
        target = get_piece_at(dest_col, dest_row)
        if target and target["team"] != team:
            return True

    # 3) 첫 이동 시 두 칸 이동 (추가된 부분)
    is_initial_position = (team == "white" and row == 6) or (team == "black" and row == 1)
    if is_initial_position and dest_col == col and dest_row == row + 2 * direction:
        # 중간 칸 (행: row + direction)이 비어있는지 확인
        mid_row = row + direction
        if get_piece_at(col, mid_row) is None and get_piece_at(dest_col, dest_row) is None:
            return True
        
    return False


def path_clear(col, row, dest_col, dest_row):
    # ... (기존과 동일)
    step_col = 0 if dest_col == col else (1 if dest_col > col else -1)
    step_row = 0 if dest_row == row else (1 if dest_row > row else -1)

    c, r = col + step_col, row + step_row
    while (c, r) != (dest_col, dest_row):
        if get_piece_at(c, r):
            return False
        c += step_col
        r += step_row
    return True


def can_rook_move(piece, col, row, dest_col, dest_row):
    if col != dest_col and row != dest_row:
        return False
    if not path_clear(col, row, dest_col, dest_row):
        return False
    target = get_piece_at(dest_col, dest_row)
    if target and target["team"] == piece["team"]:
        return False
    return True


def can_bishop_move(piece, col, row, dest_col, dest_row):
    if abs(dest_col - col) != abs(dest_row - row):
        return False
    if not path_clear(col, row, dest_col, dest_row):
        return False
    target = get_piece_at(dest_col, dest_row)
    if target and target["team"] == piece["team"]:
        return False
    return True


def can_knight_move(piece, col, row, dest_col, dest_row):
    dc = abs(dest_col - col)
    dr = abs(dest_row - row)

    # L자 이동 : (2,1) 또는 (1,2)
    if not ((dc == 2 and dr == 1) or (dc == 1 and dr == 2)):
        return False

    target = get_piece_at(dest_col, dest_row)
    if target and target["team"] == piece["team"]:
        return False

    return True


def can_king_move(piece, col, row, dest_col, dest_row):
    if max(abs(dest_col - col), abs(dest_row - row)) != 1:
        return False
    target = get_piece_at(dest_col, dest_row)
    if target and target["team"] == piece["team"]:
        return False
    return True


def can_queen_move(piece, col, row, dest_col, dest_row):
    # 퀸 = 룩(직선) + 비숍(대각선)
    straight = (col == dest_col or row == dest_row)
    diagonal = abs(dest_col - col) == abs(dest_row - row)

    if not (straight or diagonal):
        return False

    if not path_clear(col, row, dest_col, dest_row):
        return False

    target = get_piece_at(dest_col, dest_row)
    if target and target["team"] == piece["team"]:
        return False

    return True


def can_move(piece, dest_col, dest_row):
    col = piece["x"] // TILE
    row = piece["y"] // TILE
    sym = piece["symbol"]

    # 이동하려는 칸이 현재 칸과 같으면 이동 불가 (제자리 클릭)
    if col == dest_col and row == dest_row:
        return False
    
    if sym == "P": return can_pawn_move(piece, col, row, dest_col, dest_row)
    if sym == "R": return can_rook_move(piece, col, row, dest_col, dest_row)
    if sym == "N": return can_knight_move(piece, col, row, dest_col, dest_row)
    if sym == "B": return can_bishop_move(piece, col, row, dest_col, dest_row)
    if sym == "Q": return can_queen_move(piece, col, row, dest_col, dest_row)
    if sym == "K": return can_king_move(piece, col, row, dest_col, dest_row)
    return False


# ---------------------------------------------------
# 4) 메인 루프 (턴제 및 이미지 그리기 적용)
# ---------------------------------------------------
selected_piece = None
# ⭐ 턴제 로직 변수 추가
current_turn = "white" 
running = True

while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        elif e.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            dest_col = mx // TILE
            dest_row = my // TILE

            # 보드 밖 클릭 무시
            if not (0 <= dest_col < 8 and 0 <= dest_row < 8):
                continue
            
            if selected_piece is None:
                clicked = get_piece_at(dest_col, dest_row)
                # ⭐ 턴 체크: 현재 턴의 말만 선택 가능
                if clicked and clicked["team"] == current_turn:
                    selected_piece = clicked
            else:
                if can_move(selected_piece, dest_col, dest_row):
                    target = get_piece_at(dest_col, dest_row)
                    
                    # 캡처 (잡기): 타겟이 있고, 타겟 팀이 내 팀이 아니면
                    if target and target["team"] != selected_piece["team"]:
                        remove_piece(target)
                        
                    # 이동 실행
                    selected_piece["x"] = dest_col * TILE
                    selected_piece["y"] = dest_row * TILE
                    
                    # ⭐ 턴 전환
                    current_turn = "black" if current_turn == "white" else "white"
                    
                # 이동했든 안 했든 (또는 유효하지 않은 이동이든) 선택 해제
                selected_piece = None

    # 화면 그리기
    screen.fill((200, 200, 200)) # 배경색
    draw_board()

    # 선택 표시
    if selected_piece:
        pygame.draw.rect(screen, (255,255,0),
            (selected_piece["x"], selected_piece["y"], TILE, TILE), 3)

    # ⭐ 턴 정보 표시
    turn_color = (255, 255, 255) if current_turn == "white" else (0, 0, 0)
    turn_text = font.render(f"TURN: {current_turn.upper()}", True, turn_color)
    # 화면 아래 중앙에 표시
    screen.blit(turn_text, (480 // 2 - turn_text.get_width() // 2, 480 + 5)) 

    # ⭐ 말 그리기 (이미지 우선)
    for p in pieces:
        image = PIECE_IMAGES.get((p["symbol"], p["team"]))
        if image:
            # 이미지 사용
            screen.blit(image, (p["x"], p["y"]))
        else:
            # 이미지가 없으면 텍스트(폰트)로 대체
            color = (255,255,255) if p["team"]=="white" else (0,0,0)
            text = font.render(p["symbol"], True, color)
            # 텍스트를 타일 중앙에 가깝게 배치
            screen.blit(text, (p["x"] + TILE//2 - text.get_width()//2, p["y"] + TILE//2 - text.get_height()//2))


    pygame.display.flip()
    clock.tick(30)

pygame.quit()