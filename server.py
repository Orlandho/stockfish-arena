"""
Servidor FastAPI con WebSockets para la GUI de Stockfish.
Controla el estado oficial de la partida mediante python-chess y
gestiona la comunicación en tiempo real con Stockfish 19.
"""

import asyncio
import os
import json
from typing import Dict, Any, List, Optional
import chess
import chess.pgn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from stockfish_engine import StockfishEngine

app = FastAPI(title="Stockfish 19 Web GUI")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

ENGINE_PATH = os.path.join(os.path.dirname(__file__), "stockfish-windows-x86-64-universal.exe")
engine: Optional[StockfishEngine] = None

class GameManager:
    def __init__(self):
        self.board = chess.Board()
        self.moves_uci: List[str] = []
        self.moves_san: List[str] = []
        self.player_color = "white"
        self.difficulty = "intermedio"
        self.custom_elo = 1800
        self.active_websocket: Optional[WebSocket] = None
        self.is_game_over = False
        self.game_result = ""
        self.eval_data = {"cp": 0, "mate": None, "depth": 0, "win_chance": 50.0}

    def reset_game(self, player_color="white", difficulty="intermedio", custom_elo=1800):
        self.board = chess.Board()
        self.moves_uci = []
        self.moves_san = []
        self.player_color = player_color
        self.difficulty = difficulty
        self.custom_elo = custom_elo
        self.is_game_over = False
        self.game_result = ""
        self.eval_data = {"cp": 0, "mate": None, "depth": 0, "win_chance": 50.0}

    def get_legal_moves_dict(self) -> Dict[str, List[str]]:
        """Retorna un diccionario {casilla_origen: [casillas_destino_legales]}."""
        legal_dict: Dict[str, List[str]] = {}
        for move in self.board.legal_moves:
            from_sq = chess.square_name(move.from_square)
            to_sq = chess.square_name(move.to_square)
            if from_sq not in legal_dict:
                legal_dict[from_sq] = []
            if to_sq not in legal_dict[from_sq]:
                legal_dict[from_sq].append(to_sq)
        return legal_dict

    def get_captured_pieces(self) -> Dict[str, Any]:
        """Calcula las piezas capturadas por cada bando y la diferencia de material."""
        initial_counts = {
            chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2,
            chess.ROOK: 2, chess.QUEEN: 1
        }
        piece_values = {
            chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
            chess.ROOK: 5, chess.QUEEN: 9
        }

        white_captured = []  # Piezas negras capturadas por las blancas
        black_captured = []  # Piezas blancas capturadas por las negras

        white_material = 0
        black_material = 0

        for pt in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            w_count = len(self.board.pieces(pt, chess.WHITE))
            b_count = len(self.board.pieces(pt, chess.BLACK))

            white_material += w_count * piece_values[pt]
            black_material += b_count * piece_values[pt]

            w_lost = initial_counts[pt] - w_count
            b_lost = initial_counts[pt] - b_count

            symbol = chess.piece_symbol(pt)
            black_captured.extend([symbol.upper()] * max(0, w_lost))
            white_captured.extend([symbol.lower()] * max(0, b_lost))

        diff = white_material - black_material  # Positivo = blancas tienen ventaja de material
        return {
            "white_captured": white_captured,
            "black_captured": black_captured,
            "white_material": white_material,
            "black_material": black_material,
            "diff": diff
        }

    def get_state(self) -> Dict[str, Any]:
        """Empaqueta el estado completo para el cliente."""
        turn = "white" if self.board.turn == chess.WHITE else "black"
        is_check = self.board.is_check()

        # Detección de fin de juego
        game_over = False
        winner = None
        reason = ""

        if self.board.is_checkmate():
            game_over = True
            winner = "black" if self.board.turn == chess.WHITE else "white"
            reason = "Jaque mate"
        elif self.board.is_stalemate():
            game_over = True
            winner = "draw"
            reason = "Tablas por rey ahogado"
        elif self.board.is_insufficient_material():
            game_over = True
            winner = "draw"
            reason = "Tablas por material insuficiente"
        elif self.board.can_claim_threefold_repetition():
            game_over = True
            winner = "draw"
            reason = "Tablas por triple repetición"
        elif self.board.can_claim_fifty_moves():
            game_over = True
            winner = "draw"
            reason = "Tablas por la regla de los 50 movimientos"

        self.is_game_over = game_over
        if game_over:
            self.game_result = reason

        return {
            "type": "state",
            "fen": self.board.fen(),
            "turn": turn,
            "player_color": self.player_color,
            "difficulty": self.difficulty,
            "custom_elo": self.custom_elo,
            "is_check": is_check,
            "game_over": game_over,
            "winner": winner,
            "reason": reason,
            "moves_san": self.moves_san,
            "moves_uci": self.moves_uci,
            "legal_moves": self.get_legal_moves_dict(),
            "captured": self.get_captured_pieces(),
            "eval": self.eval_data
        }

    def apply_move(self, uci_str: str) -> Optional[str]:
        """Aplica una jugada UCI y retorna su representación SAN."""
        try:
            move = chess.Move.from_uci(uci_str)
            if move in self.board.legal_moves:
                san = self.board.san(move)
                self.board.push(move)
                self.moves_uci.append(uci_str)
                self.moves_san.append(san)
                return san
            return None
        except Exception:
            return None

    def undo_last_move_pair(self) -> bool:
        """Deshace la última jugada del motor y del jugador."""
        undone = False
        # Si es el turno del jugador y hay al menos 2 jugadas en el historial:
        # Deshace jugada del motor y jugada del jugador
        if len(self.board.move_stack) >= 2:
            self.board.pop()
            self.board.pop()
            self.moves_uci = self.moves_uci[:-2]
            self.moves_san = self.moves_san[:-2]
            undone = True
        elif len(self.board.move_stack) == 1:
            self.board.pop()
            self.moves_uci = self.moves_uci[:-1]
            self.moves_san = self.moves_san[:-1]
            undone = True
        return undone

game = GameManager()

@app.on_event("startup")
async def startup_event():
    global engine
    engine = StockfishEngine(ENGINE_PATH)
    await engine.start()
    await engine.set_difficulty(game.difficulty, custom_elo=game.custom_elo)

@app.on_event("shutdown")
async def shutdown_event():
    global engine
    if engine:
        await engine.close()

@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    game.active_websocket = websocket

    # Enviar estado inicial
    await websocket.send_json(game.get_state())

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "new_game":
                player_color = data.get("player_color", "white")
                difficulty = data.get("difficulty", "intermedio")
                custom_elo = data.get("custom_elo", 1800)

                if engine:
                    await engine.new_game()
                    await engine.set_difficulty(difficulty, custom_elo=custom_elo)

                game.reset_game(player_color=player_color, difficulty=difficulty, custom_elo=custom_elo)
                await websocket.send_json(game.get_state())

                # Si el jugador eligió Negras, Stockfish mueve primero
                if player_color == "black" and not game.is_game_over:
                    asyncio.create_task(run_engine_move(websocket))

            elif msg_type == "player_move":
                from_sq = data.get("from")
                to_sq = data.get("to")
                promotion = data.get("promotion", "")

                uci_move = f"{from_sq}{to_sq}{promotion}"
                san = game.apply_move(uci_move)

                if san:
                    # Enviar estado actualizado con la jugada del jugador
                    await websocket.send_json(game.get_state())

                    # Si el juego no terminó, disparar la respuesta de Stockfish
                    if not game.is_game_over:
                        asyncio.create_task(run_engine_move(websocket))
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Jugada ilegal: {uci_move}"
                    })

            elif msg_type == "undo":
                if game.undo_last_move_pair():
                    # Recalcular evaluación de la posición restaurada
                    if engine:
                        asyncio.create_task(run_eval_update(websocket))
                    await websocket.send_json(game.get_state())

            elif msg_type == "hint":
                # Solicitar mejor jugada a Stockfish
                if engine and not game.is_game_over:
                    is_white = game.board.turn == chess.WHITE
                    eval_res = await engine.evaluate_position(game.moves_uci, turn_is_white=is_white, depth=14)
                    best_uci = eval_res.get("bestmove")
                    if best_uci:
                        try:
                            move = chess.Move.from_uci(best_uci)
                            san = game.board.san(move)
                            await websocket.send_json({
                                "type": "hint_result",
                                "uci": best_uci,
                                "from": chess.square_name(move.from_square),
                                "to": chess.square_name(move.to_square),
                                "san": san
                            })
                        except Exception:
                            pass

            elif msg_type == "set_difficulty":
                difficulty = data.get("difficulty", "intermedio")
                custom_elo = data.get("custom_elo", 1800)
                game.difficulty = difficulty
                game.custom_elo = custom_elo
                if engine:
                    await engine.set_difficulty(difficulty, custom_elo=custom_elo)
                await websocket.send_json(game.get_state())

    except WebSocketDisconnect:
        game.active_websocket = None
    except Exception as e:
        print(f"Error WebSocket: {e}")
        game.active_websocket = None

async def run_engine_move(ws: WebSocket):
    """Calcula y aplica la jugada de Stockfish mientras envía telemetría de evaluación."""
    if not engine or game.is_game_over:
        return

    is_white = game.board.turn == chess.WHITE

    async def on_eval(eval_data: Dict[str, Any]):
        game.eval_data = eval_data
        try:
            await ws.send_json({
                "type": "eval",
                "eval": eval_data
            })
        except Exception:
            pass

    # Calcular jugada
    result = await engine.compute_move(
        moves_uci=game.moves_uci,
        turn_is_white=is_white,
        eval_callback=on_eval
    )

    best_move_uci = result.get("bestmove")
    if best_move_uci and not game.is_game_over:
        san = game.apply_move(best_move_uci)
        if san:
            state = game.get_state()
            state["last_engine_move"] = {
                "uci": best_move_uci,
                "san": san
            }
            try:
                await ws.send_json(state)
            except Exception:
                pass

async def run_eval_update(ws: WebSocket):
    """Actualiza la barra de evaluación tras un retroceso de jugada."""
    if not engine or game.is_game_over:
        return
    is_white = game.board.turn == chess.WHITE
    eval_res = await engine.evaluate_position(game.moves_uci, turn_is_white=is_white, depth=12)
    game.eval_data = eval_res
    try:
        await ws.send_json({
            "type": "eval",
            "eval": eval_res
        })
    except Exception:
        pass
