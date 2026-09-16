"""
Módulo de integración con el motor Stockfish 19 mediante el protocolo UCI asíncrono.
Diseñado para mínima latencia, soporte de niveles de dificultad (Elo y Skill)
y streaming de evaluación en tiempo real para la barra de ventaja.
"""

import asyncio
import os
import re
from typing import Optional, Callable, Dict, Any, List

class StockfishEngine:
    def __init__(self, executable_path: str):
        self.executable_path = executable_path
        self.process: Optional[asyncio.subprocess.Process] = None
        self._lock = asyncio.Lock()
        self.current_difficulty = "intermedio"
        self.current_elo = 1800
        self.current_movetime = 800
        self.is_thinking = False

    async def start(self):
        """Inicia el subproceso de Stockfish y realiza el handshake UCI."""
        if not os.path.exists(self.executable_path):
            raise FileNotFoundError(f"No se encontró el ejecutable de Stockfish en: {self.executable_path}")

        self.process = await asyncio.create_subprocess_exec(
            self.executable_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        await self.send_command("uci")
        while True:
            line = await self.read_line()
            if line.strip() == "uciok":
                break

        # Configuración por defecto: 2 hilos, 32 MB Hash
        await self.send_command("setoption name Threads value 2")
        await self.send_command("setoption name Hash value 32")
        await self.send_command("isready")
        await self._wait_for("readyok")

    async def send_command(self, cmd: str):
        """Envía un comando UCI al proceso con flush inmediato."""
        if self.process and self.process.stdin:
            self.process.stdin.write(f"{cmd}\n".encode("utf-8"))
            await self.process.stdin.drain()

    async def read_line(self) -> str:
        """Lee una línea de salida de Stockfish."""
        if not self.process or not self.process.stdout:
            return ""
        line = await self.process.stdout.readline()
        return line.decode("utf-8", errors="ignore").strip()

    async def _wait_for(self, token: str) -> List[str]:
        """Lee líneas hasta encontrar un token específico."""
        lines = []
        while True:
            line = await self.read_line()
            lines.append(line)
            if token in line:
                break
        return lines

    async def set_difficulty(self, preset: str, custom_elo: Optional[int] = None, movetime_ms: Optional[int] = None):
        """
        Configura el nivel de fuerza y tiempo de respuesta de Stockfish 19.
        Presets:
          - principiante: Elo 1320, Skill Level 1, 400ms
          - aficionado:   Elo 1500, Skill Level 5, 600ms
          - intermedio:   Elo 1800, Skill Level 10, 800ms
          - avanzado:     Elo 2100, Skill Level 15, 1200ms
          - maestro:      Elo 2500, Skill Level 20, 1800ms
          - maximo:       Sin límite de fuerza (Full NNUE), Skill Level 20, 2500ms
        """
        async with self._lock:
            presets = {
                "principiante": {"elo": 1320, "skill": 1, "movetime": 400, "limit": True},
                "aficionado":   {"elo": 1500, "skill": 5, "movetime": 600, "limit": True},
                "intermedio":   {"elo": 1800, "skill": 10, "movetime": 800, "limit": True},
                "avanzado":     {"elo": 2100, "skill": 15, "movetime": 1200, "limit": True},
                "maestro":      {"elo": 2500, "skill": 20, "movetime": 1800, "limit": True},
                "maximo":       {"elo": 3190, "skill": 20, "movetime": 2500, "limit": False},
            }

            cfg = presets.get(preset.lower(), presets["intermedio"])
            elo = custom_elo if custom_elo is not None else cfg["elo"]
            elo = max(1320, min(3190, elo))
            movetime = movetime_ms if movetime_ms is not None else cfg["movetime"]

            if cfg["limit"]:
                await self.send_command("setoption name UCI_LimitStrength value true")
                await self.send_command(f"setoption name UCI_Elo value {elo}")
                await self.send_command(f"setoption name Skill Level value {cfg['skill']}")
            else:
                await self.send_command("setoption name UCI_LimitStrength value false")
                await self.send_command("setoption name Skill Level value 20")

            await self.send_command("isready")
            await self._wait_for("readyok")

            self.current_difficulty = preset
            self.current_elo = elo
            self.current_movetime = movetime

    async def new_game(self):
        """Reinicia la memoria interna del motor para una nueva partida."""
        async with self._lock:
            if self.is_thinking:
                await self.send_command("stop")
                self.is_thinking = False
            await self.send_command("ucinewgame")
            await self.send_command("isready")
            await self._wait_for("readyok")

    async def set_position(self, moves_uci: List[str]):
        """Configura la posición actual a partir de la lista de jugadas UCI."""
        if moves_uci:
            moves_str = " ".join(moves_uci)
            await self.send_command(f"position startpos moves {moves_str}")
        else:
            await self.send_command("position startpos")

    async def compute_move(
        self,
        moves_uci: List[str],
        turn_is_white: bool,
        eval_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        movetime: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calcula la mejor jugada para la posición dada y transmite
        actualizaciones de evaluación en tiempo real mediante eval_callback.
        """
        async with self._lock:
            self.is_thinking = True
            await self.set_position(moves_uci)

            time_to_think = movetime or self.current_movetime
            await self.send_command(f"go movetime {time_to_think}")

            best_move = None
            ponder_move = None
            last_eval: Dict[str, Any] = {"cp": 0, "mate": None, "depth": 0}

            try:
                while True:
                    line = await self.read_line()
                    if not line:
                        continue

                    if line.startswith("info "):
                        parsed_eval = self._parse_info_line(line, turn_is_white)
                        if parsed_eval:
                            last_eval = parsed_eval
                            if eval_callback:
                                try:
                                    if asyncio.iscoroutinefunction(eval_callback):
                                        await eval_callback(parsed_eval)
                                    else:
                                        eval_callback(parsed_eval)
                                except Exception:
                                    pass

                    elif line.startswith("bestmove"):
                        parts = line.split()
                        best_move = parts[1] if len(parts) > 1 else None
                        if len(parts) > 3 and parts[2] == "ponder":
                            ponder_move = parts[3]
                        break

            finally:
                self.is_thinking = False

            return {
                "bestmove": best_move,
                "ponder": ponder_move,
                "eval": last_eval
            }

    async def evaluate_position(
        self,
        moves_uci: List[str],
        turn_is_white: bool,
        depth: int = 14
    ) -> Dict[str, Any]:
        """Evalúa rápidamente una posición estática a una profundidad fija."""
        async with self._lock:
            self.is_thinking = True
            await self.set_position(moves_uci)
            await self.send_command(f"go depth {depth}")

            last_eval = {"cp": 0, "mate": None, "depth": depth, "win_chance": 50.0}

            try:
                while True:
                    line = await self.read_line()
                    if line.startswith("info "):
                        parsed = self._parse_info_line(line, turn_is_white)
                        if parsed:
                            last_eval = parsed
                    elif line.startswith("bestmove"):
                        parts = line.split()
                        last_eval["bestmove"] = parts[1] if len(parts) > 1 else None
                        break
            finally:
                self.is_thinking = False

            return last_eval

    def _parse_info_line(self, line: str, turn_is_white: bool) -> Optional[Dict[str, Any]]:
        """
        Extrae la evaluación en centipeones o mate forzado y la normaliza
        a la perspectiva de las Blancas (positivo = ventaja Blanca, negativo = ventaja Negra).
        """
        # Debe contener score
        if " score " not in line:
            return None

        result: Dict[str, Any] = {
            "cp": None,
            "mate": None,
            "depth": 0,
            "nodes": 0,
            "nps": 0,
            "pv": [],
            "win_chance": 50.0
        }

        # Profundidad
        depth_match = re.search(r"depth (\d+)", line)
        if depth_match:
            result["depth"] = int(depth_match.group(1))

        # Nodos y NPS
        nodes_match = re.search(r"nodes (\d+)", line)
        if nodes_match:
            result["nodes"] = int(nodes_match.group(1))
        nps_match = re.search(r"nps (\d+)", line)
        if nps_match:
            result["nps"] = int(nps_match.group(1))

        # Score (cp o mate)
        score_cp_match = re.search(r"score cp (-?\d+)", line)
        score_mate_match = re.search(r"score mate (-?\d+)", line)

        # En UCI, score es relativo al bando que mueve:
        multiplier = 1 if turn_is_white else -1

        if score_cp_match:
            raw_cp = int(score_cp_match.group(1))
            white_cp = raw_cp * multiplier
            result["cp"] = white_cp
            # Fórmula sigmoide estándar de Lichess para probabilidad de victoria de blancas:
            # win_chance = 50 + 50 * (2 / (1 + exp(-0.003682 * cp)) - 1)
            try:
                import math
                val = 2.0 / (1.0 + math.exp(-0.003682 * white_cp)) - 1.0
                result["win_chance"] = round(50.0 + 50.0 * val, 1)
            except OverflowError:
                result["win_chance"] = 100.0 if white_cp > 0 else 0.0

        elif score_mate_match:
            raw_mate = int(score_mate_match.group(1))
            white_mate = raw_mate * multiplier
            result["mate"] = white_mate
            result["win_chance"] = 100.0 if white_mate > 0 else 0.0

        # Principal Variation (PV)
        pv_match = re.search(r" pv (.+)$", line)
        if pv_match:
            result["pv"] = pv_match.group(1).split()[:5]

        return result

    async def stop(self):
        """Detiene inmediatamente cualquier cálculo activo."""
        if self.is_thinking:
            await self.send_command("stop")
            self.is_thinking = False

    async def close(self):
        """Cierra el subproceso limpiamente."""
        if self.process:
            try:
                await self.send_command("quit")
                await asyncio.wait_for(self.process.wait(), timeout=2.0)
            except Exception:
                self.process.kill()
            self.process = None
