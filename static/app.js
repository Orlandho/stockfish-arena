// Cliente de Ajedrez Interactivo con WebSocket para Stockfish 19
// Soporta Drag & Drop, Click-to-Move, Barra de Evaluación, Audio y Dificultad Dinámica.

class ChessApp {
    constructor() {
        this.ws = null;
        this.state = null;
        this.selectedSquare = null;
        this.orientation = 'white'; // 'white' o 'black' en la base
        this.isDragging = false;
        this.draggedSquare = null;
        this.ghostPiece = null;
        this.pendingPromotion = null;
        this.hintSquares = [];

        // Elementos del DOM
        this.boardEl = document.getElementById('chessboard');
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        this.evalBarFill = document.getElementById('evalBarFill');
        this.evalTextWhite = document.getElementById('evalTextWhite');
        this.evalTextBlack = document.getElementById('evalTextBlack');
        this.movesListEl = document.getElementById('movesList');
        this.gameOverBanner = document.getElementById('gameOverBanner');
        this.promoModal = document.getElementById('promoModal');
        this.playerCapturedEl = document.getElementById('playerCaptured');
        this.engineCapturedEl = document.getElementById('engineCaptured');
        this.engineEloLabel = document.getElementById('engineEloLabel');
        this.difficultySelect = document.getElementById('difficultySelect');
        this.eloSlider = document.getElementById('eloSlider');
        this.eloSliderLabel = document.getElementById('eloSliderLabel');

        this.init();
    }

    init() {
        this.connectWebSocket();
        this.setupEventListeners();
        this.renderBoardSkeleton();
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        this.updateStatus('connecting', 'Conectando a Stockfish...');

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this.updateStatus('ready', 'Listo para jugar');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleServerMessage(data);
        };

        this.ws.onclose = () => {
            this.updateStatus('disconnected', 'Desconectado. Reintentando...');
            setTimeout(() => this.connectWebSocket(), 2000);
        };

        this.ws.onerror = (err) => {
            console.error('Error WebSocket:', err);
        };
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    updateStatus(type, message) {
        this.statusText.textContent = message;
        this.statusDot.className = 'status-dot';
        if (type === 'thinking') {
            this.statusDot.classList.add('thinking');
        } else if (type === 'disconnected') {
            this.statusDot.style.backgroundColor = '#e53935';
            this.statusDot.style.boxShadow = '0 0 8px #e53935';
        } else {
            this.statusDot.style.backgroundColor = '';
            this.statusDot.style.boxShadow = '';
        }
    }

    handleServerMessage(data) {
        if (data.type === 'state') {
            const previousFen = this.state ? this.state.fen : null;
            const previousTurn = this.state ? this.state.turn : null;
            this.state = data;
            this.hintSquares = [];

            this.renderPieces();
            this.renderMoveHistory();
            this.renderCapturedPieces();
            this.updateEvalBar(data.eval);

            // Gestionar audio y estado del turno
            if (previousFen && previousFen !== data.fen) {
                this.triggerMoveAudio(data);
            }

            if (data.game_over) {
                this.showGameOver(data.winner, data.reason);
                this.updateStatus('ready', data.reason);
            } else if (data.turn === data.player_color) {
                this.updateStatus('ready', data.is_check ? '¡Estás en Jaque! Tu turno' : 'Tu turno');
            } else {
                this.updateStatus('thinking', 'Stockfish 19 pensando...');
            }

        } else if (data.type === 'eval') {
            this.updateEvalBar(data.eval);

        } else if (data.type === 'hint_result') {
            this.showHint(data.from, data.to, data.san);
        }
    }

    triggerMoveAudio(state) {
        if (state.is_check) {
            window.chessAudio.playCheck();
        } else {
            const lastSan = state.moves_san[state.moves_san.length - 1] || '';
            if (lastSan.includes('O-O') || lastSan.includes('O-O-O')) {
                window.chessAudio.playCastle();
            } else if (lastSan.includes('x')) {
                window.chessAudio.playCapture();
            } else {
                window.chessAudio.playMove();
            }
        }
    }

    renderBoardSkeleton() {
        this.boardEl.innerHTML = '';
        const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
        const ranks = ['8', '7', '6', '5', '4', '3', '2', '1'];

        const displayRanks = this.orientation === 'white' ? ranks : [...ranks].reverse();
        const displayFiles = this.orientation === 'white' ? files : [...files].reverse();

        for (let r = 0; r < 8; r++) {
            for (let f = 0; f < 8; f++) {
                const rank = displayRanks[r];
                const file = displayFiles[f];
                const sqName = `${file}${rank}`;
                const isLight = (f + r) % 2 === 0;

                const sq = document.createElement('div');
                sq.className = `square ${isLight ? 'light' : 'dark'}`;
                sq.dataset.square = sqName;

                // Coordenadas en los bordes
                if (f === 0) {
                    const rankCoord = document.createElement('span');
                    rankCoord.className = 'coord rank';
                    rankCoord.textContent = rank;
                    sq.appendChild(rankCoord);
                }
                if (r === 7) {
                    const fileCoord = document.createElement('span');
                    fileCoord.className = 'coord file';
                    fileCoord.textContent = file;
                    sq.appendChild(fileCoord);
                }

                this.boardEl.appendChild(sq);
            }
        }
    }

    parseFen(fen) {
        const boardMap = {};
        const rows = fen.split(' ')[0].split('/');
        const ranks = ['8', '7', '6', '5', '4', '3', '2', '1'];
        const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];

        for (let r = 0; r < 8; r++) {
            let col = 0;
            for (let c = 0; c < rows[r].length; c++) {
                const ch = rows[r][c];
                if (ch >= '1' && ch <= '8') {
                    col += parseInt(ch, 10);
                } else {
                    const sq = `${files[col]}${ranks[r]}`;
                    boardMap[sq] = ch;
                    col++;
                }
            }
        }
        return boardMap;
    }

    renderPieces() {
        if (!this.state) return;
        const boardMap = this.parseFen(this.state.fen);

        // Limpiar todas las casillas
        const squares = this.boardEl.querySelectorAll('.square');
        squares.forEach(sq => {
            const sqName = sq.dataset.square;
            sq.classList.remove('selected', 'last-move', 'in-check', 'hint');

            // Quitar indicadores de legalidad y piezas
            const dot = sq.querySelector('.legal-dot, .legal-capture-ring');
            if (dot) dot.remove();

            const oldPiece = sq.querySelector('.piece');
            if (oldPiece) oldPiece.remove();

            // Resaltar última jugada
            if (this.state.moves_uci && this.state.moves_uci.length > 0) {
                const lastMove = this.state.moves_uci[this.state.moves_uci.length - 1];
                const fromSq = lastMove.substring(0, 2);
                const toSq = lastMove.substring(2, 4);
                if (sqName === fromSq || sqName === toSq) {
                    sq.classList.add('last-move');
                }
            }

            // Resaltar casilla seleccionada
            if (sqName === this.selectedSquare) {
                sq.classList.add('selected');
            }

            // Resaltar pistas
            if (this.hintSquares.includes(sqName)) {
                sq.classList.add('hint');
            }

            // Resaltar rey en jaque
            if (this.state.is_check) {
                const piece = boardMap[sqName];
                const isCheckWhiteKing = this.state.turn === 'white' && piece === 'K';
                const isCheckBlackKing = this.state.turn === 'black' && piece === 'k';
                if (isCheckWhiteKing || isCheckBlackKing) {
                    sq.classList.add('in-check');
                }
            }

            // Insertar pieza
            const pieceChar = boardMap[sqName];
            if (pieceChar && PIECES_SVG[pieceChar]) {
                const pieceDiv = document.createElement('div');
                pieceDiv.className = 'piece';
                pieceDiv.innerHTML = PIECES_SVG[pieceChar];
                pieceDiv.dataset.square = sqName;
                pieceDiv.dataset.piece = pieceChar;
                sq.appendChild(pieceDiv);
            }
        });

        // Mostrar puntos legales si hay casilla seleccionada
        if (this.selectedSquare && this.state.legal_moves) {
            const destinations = this.state.legal_moves[this.selectedSquare] || [];
            destinations.forEach(destSq => {
                const sqEl = this.boardEl.querySelector(`[data-square="${destSq}"]`);
                if (sqEl) {
                    const isCapture = !!boardMap[destSq];
                    const marker = document.createElement('div');
                    marker.className = isCapture ? 'legal-capture-ring' : 'legal-dot';
                    sqEl.appendChild(marker);
                }
            });
        }
    }

    setupEventListeners() {
        // Clics e interacción en el tablero
        this.boardEl.addEventListener('click', (e) => this.handleBoardClick(e));
        this.boardEl.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        window.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        window.addEventListener('mouseup', (e) => this.handleMouseUp(e));

        // Pestañas
        document.getElementById('tabMovesBtn').addEventListener('click', () => this.switchTab('moves'));
        document.getElementById('tabSettingsBtn').addEventListener('click', () => this.switchTab('settings'));

        // Botones de acción
        document.getElementById('btnNewGame').addEventListener('click', () => this.startNewGame());
        document.getElementById('btnUndo').addEventListener('click', () => this.undoMove());
        document.getElementById('btnHint').addEventListener('click', () => this.requestHint());
        document.getElementById('btnFlip').addEventListener('click', () => this.flipBoard());
        document.getElementById('btnCopyPgn').addEventListener('click', () => this.copyPgn());
        document.getElementById('btnMute').addEventListener('click', (e) => this.toggleMute(e.target));

        // Selector de color
        document.getElementById('btnColorWhite').addEventListener('click', () => this.selectColor('white'));
        document.getElementById('btnColorBlack').addEventListener('click', () => this.selectColor('black'));

        // Dificultad
        this.difficultySelect.addEventListener('change', () => this.handleDifficultyChange());
        this.eloSlider.addEventListener('input', (e) => {
            this.eloSliderLabel.textContent = `Ajuste Fino de Elo: ${e.target.value}`;
        });
        this.eloSlider.addEventListener('change', () => this.handleDifficultyChange());

        // Modal de Promoción
        this.promoModal.querySelectorAll('.promo-piece-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const promo = btn.dataset.promo;
                if (this.pendingPromotion) {
                    this.executeMove(this.pendingPromotion.from, this.pendingPromotion.to, promo);
                    this.pendingPromotion = null;
                    this.promoModal.style.display = 'none';
                }
            });
        });
    }

    handleBoardClick(e) {
        if (this.isDragging) return;
        const squareEl = e.target.closest('.square');
        if (!squareEl || !this.state || this.state.game_over) return;

        // Comprobar que sea el turno del jugador
        if (this.state.turn !== this.state.player_color) return;

        const clickedSquare = squareEl.dataset.square;
        const boardMap = this.parseFen(this.state.fen);
        const pieceOnClicked = boardMap[clickedSquare];

        // Si ya teníamos una casilla seleccionada y se hace clic en un destino legal:
        if (this.selectedSquare) {
            const destinations = this.state.legal_moves[this.selectedSquare] || [];
            if (destinations.includes(clickedSquare)) {
                this.tryMove(this.selectedSquare, clickedSquare);
                this.selectedSquare = null;
                this.renderPieces();
                return;
            }
        }

        // Selección de pieza propia
        const isOwnPiece = pieceOnClicked && (
            (this.state.player_color === 'white' && pieceOnClicked === pieceOnClicked.toUpperCase()) ||
            (this.state.player_color === 'black' && pieceOnClicked === pieceOnClicked.toLowerCase())
        );

        if (isOwnPiece) {
            this.selectedSquare = (this.selectedSquare === clickedSquare) ? null : clickedSquare;
        } else {
            this.selectedSquare = null;
        }

        this.renderPieces();
    }

    handleMouseDown(e) {
        if (e.button !== 0 || !this.state || this.state.game_over) return;
        if (this.state.turn !== this.state.player_color) return;

        const pieceEl = e.target.closest('.piece');
        if (!pieceEl) return;

        const square = pieceEl.dataset.square;
        const pieceChar = pieceEl.dataset.piece;

        // Validar que sea pieza propia
        const isOwnPiece = (
            (this.state.player_color === 'white' && pieceChar === pieceChar.toUpperCase()) ||
            (this.state.player_color === 'black' && pieceChar === pieceChar.toLowerCase())
        );
        if (!isOwnPiece) return;

        this.isDragging = true;
        this.draggedSquare = square;
        this.selectedSquare = square;
        this.renderPieces();

        // Crear ghost piece
        this.ghostPiece = document.createElement('div');
        this.ghostPiece.className = 'ghost-piece';
        this.ghostPiece.innerHTML = PIECES_SVG[pieceChar];
        this.ghostPiece.style.left = `${e.clientX}px`;
        this.ghostPiece.style.top = `${e.clientY}px`;
        document.body.appendChild(this.ghostPiece);

        const currentPieceDiv = this.boardEl.querySelector(`[data-square="${square}"] .piece`);
        if (currentPieceDiv) currentPieceDiv.classList.add('dragging');
    }

    handleMouseMove(e) {
        if (this.isDragging && this.ghostPiece) {
            this.ghostPiece.style.left = `${e.clientX}px`;
            this.ghostPiece.style.top = `${e.clientY}px`;
        }
    }

    handleMouseUp(e) {
        if (!this.isDragging) return;

        this.isDragging = false;
        if (this.ghostPiece) {
            this.ghostPiece.remove();
            this.ghostPiece = null;
        }

        const dropTarget = document.elementFromPoint(e.clientX, e.clientY);
        const squareEl = dropTarget ? dropTarget.closest('.square') : null;

        if (squareEl && this.draggedSquare) {
            const targetSquare = squareEl.dataset.square;
            const destinations = this.state.legal_moves[this.draggedSquare] || [];

            if (destinations.includes(targetSquare)) {
                this.tryMove(this.draggedSquare, targetSquare);
                this.selectedSquare = null;
            }
        }

        this.draggedSquare = null;
        this.renderPieces();
    }

    tryMove(fromSq, toSq) {
        const boardMap = this.parseFen(this.state.fen);
        const piece = boardMap[fromSq];

        // Comprobar si es coronación de peón
        const isPawnPromotion = (
            (piece === 'P' && toSq[1] === '8') ||
            (piece === 'p' && toSq[1] === '1')
        );

        if (isPawnPromotion) {
            this.pendingPromotion = { from: fromSq, to: toSq };
            this.showPromotionModal(piece === 'P' ? 'white' : 'black');
        } else {
            this.executeMove(fromSq, toSq);
        }
    }

    showPromotionModal(color) {
        const pieces = {
            'q': color === 'white' ? 'Q' : 'q',
            'r': color === 'white' ? 'R' : 'r',
            'b': color === 'white' ? 'B' : 'b',
            'n': color === 'white' ? 'N' : 'n'
        };

        this.promoModal.querySelectorAll('.promo-piece-btn').forEach(btn => {
            const promoType = btn.dataset.promo;
            btn.innerHTML = PIECES_SVG[pieces[promoType]];
        });

        this.promoModal.style.display = 'flex';
    }

    executeMove(fromSq, toSq, promotion = '') {
        this.send({
            type: 'player_move',
            from: fromSq,
            to: toSq,
            promotion: promotion
        });
    }

    startNewGame() {
        const color = document.querySelector('.color-btn.active').dataset.color;
        const difficulty = this.difficultySelect.value;
        const customElo = parseInt(this.eloSlider.value, 10);

        this.gameOverBanner.style.display = 'none';
        this.orientation = color;
        this.selectedSquare = null;
        this.hintSquares = [];
        this.renderBoardSkeleton();

        this.send({
            type: 'new_game',
            player_color: color,
            difficulty: difficulty,
            custom_elo: customElo
        });
    }

    undoMove() {
        this.selectedSquare = null;
        this.hintSquares = [];
        this.send({ type: 'undo' });
    }

    requestHint() {
        if (!this.state || this.state.game_over || this.state.turn !== this.state.player_color) return;
        this.updateStatus('thinking', 'Buscando mejor jugada...');
        this.send({ type: 'hint' });
    }

    showHint(fromSq, toSq, san) {
        this.hintSquares = [fromSq, toSq];
        this.renderPieces();
        this.updateStatus('ready', `Pista sugerida: ${san} (${fromSq} ➔ ${toSq})`);
    }

    flipBoard() {
        this.orientation = this.orientation === 'white' ? 'black' : 'white';
        this.renderBoardSkeleton();
        this.renderPieces();
    }

    selectColor(color) {
        document.getElementById('btnColorWhite').classList.toggle('active', color === 'white');
        document.getElementById('btnColorBlack').classList.toggle('active', color === 'black');
    }

    handleDifficultyChange() {
        const diff = this.difficultySelect.value;
        const elo = parseInt(this.eloSlider.value, 10);

        const eloMap = {
            'principiante': 1320,
            'aficionado': 1500,
            'intermedio': 1800,
            'avanzado': 2100,
            'maestro': 2500,
            'maximo': 3190
        };

        if (eloMap[diff] && this.eloSlider.value == 1800) {
            this.eloSlider.value = eloMap[diff];
            this.eloSliderLabel.textContent = `Ajuste Fino de Elo: ${eloMap[diff]}`;
        }

        const labels = {
            'principiante': 'Elo 1320 (Principiante)',
            'aficionado': 'Elo 1500 (Aficionado)',
            'intermedio': 'Elo 1800 (Intermedio)',
            'avanzado': 'Elo 2100 (Avanzado)',
            'maestro': 'Elo 2500 (Gran Maestro)',
            'maximo': 'Elo +3500 (Máxima Potencia NNUE)'
        };
        this.engineEloLabel.textContent = labels[diff] || `Elo ${elo}`;

        this.send({
            type: 'set_difficulty',
            difficulty: diff,
            custom_elo: parseInt(this.eloSlider.value, 10)
        });
    }

    updateEvalBar(evalData) {
        if (!evalData) return;
        const winChance = evalData.win_chance !== undefined ? evalData.win_chance : 50.0;
        this.evalBarFill.style.height = `${winChance}%`;

        let label = '';
        if (evalData.mate !== null && evalData.mate !== undefined) {
            label = evalData.mate > 0 ? `M${evalData.mate}` : `-M${Math.abs(evalData.mate)}`;
        } else if (evalData.cp !== null && evalData.cp !== undefined) {
            const pawnVal = (evalData.cp / 100).toFixed(1);
            label = evalData.cp >= 0 ? `+${pawnVal}` : `${pawnVal}`;
        }

        if (winChance >= 50) {
            this.evalTextWhite.textContent = label;
            this.evalTextBlack.textContent = '';
        } else {
            this.evalTextBlack.textContent = label;
            this.evalTextWhite.textContent = '';
        }
    }

    renderMoveHistory() {
        if (!this.state || !this.state.moves_san) return;
        this.movesListEl.innerHTML = '';

        const moves = this.state.moves_san;
        for (let i = 0; i < moves.length; i += 2) {
            const moveNum = Math.floor(i / 2) + 1;
            const whiteMove = moves[i];
            const blackMove = moves[i + 1] || '';

            const numSpan = document.createElement('span');
            numSpan.className = 'move-num';
            numSpan.textContent = `${moveNum}.`;

            const whiteSpan = document.createElement('span');
            whiteSpan.className = `move-san ${i === moves.length - 1 ? 'active' : ''}`;
            whiteSpan.textContent = whiteMove;

            const blackSpan = document.createElement('span');
            blackSpan.className = `move-san ${i + 1 === moves.length - 1 ? 'active' : ''}`;
            blackSpan.textContent = blackMove;

            this.movesListEl.appendChild(numSpan);
            this.movesListEl.appendChild(whiteSpan);
            this.movesListEl.appendChild(blackSpan);
        }

        this.movesListEl.scrollTop = this.movesListEl.scrollHeight;
    }

    renderCapturedPieces() {
        if (!this.state || !this.state.captured) return;
        const captured = this.state.captured;

        // Piezas capturadas por las blancas (piezas negras caídas)
        this.playerCapturedEl.innerHTML = '';
        captured.white_captured.forEach(p => {
            const span = document.createElement('span');
            span.className = 'captured-mini';
            span.innerHTML = PIECES_SVG[p];
            this.playerCapturedEl.appendChild(span);
        });
        if (captured.diff > 0) {
            const diffSpan = document.createElement('span');
            diffSpan.className = 'material-diff';
            diffSpan.textContent = `+${captured.diff}`;
            this.playerCapturedEl.appendChild(diffSpan);
        }

        // Piezas capturadas por las negras (piezas blancas caídas)
        this.engineCapturedEl.innerHTML = '';
        captured.black_captured.forEach(p => {
            const span = document.createElement('span');
            span.className = 'captured-mini';
            span.innerHTML = PIECES_SVG[p];
            this.engineCapturedEl.appendChild(span);
        });
        if (captured.diff < 0) {
            const diffSpan = document.createElement('span');
            diffSpan.className = 'material-diff';
            diffSpan.textContent = `+${Math.abs(captured.diff)}`;
            this.engineCapturedEl.appendChild(diffSpan);
        }
    }

    showGameOver(winner, reason) {
        this.gameOverBanner.style.display = 'block';
        this.gameOverBanner.className = 'game-over-banner';

        let text = '';
        if (winner === 'draw') {
            this.gameOverBanner.classList.add('draw');
            text = `½ - ½ Tablas: ${reason}`;
            window.chessAudio.playGameOver(false);
        } else if (winner === this.state.player_color) {
            text = `🏆 ¡Victoria! Has ganado por ${reason}`;
            window.chessAudio.playGameOver(true);
        } else {
            this.gameOverBanner.classList.add('defeat');
            text = `Stockfish 19 ha ganado por ${reason}`;
            window.chessAudio.playGameOver(false);
        }
        this.gameOverBanner.textContent = text;
    }

    switchTab(tab) {
        const movesBtn = document.getElementById('tabMovesBtn');
        const settingsBtn = document.getElementById('tabSettingsBtn');
        const movesContent = document.getElementById('tabMovesContent');
        const settingsContent = document.getElementById('tabSettingsContent');

        if (tab === 'moves') {
            movesBtn.classList.add('active');
            settingsBtn.classList.remove('active');
            movesContent.style.display = 'flex';
            settingsContent.style.display = 'none';
        } else {
            settingsBtn.classList.add('active');
            movesBtn.classList.remove('active');
            settingsContent.style.display = 'flex';
            movesContent.style.display = 'none';
        }
    }

    copyPgn() {
        if (!this.state || !this.state.moves_san || this.state.moves_san.length === 0) {
            alert('No hay jugadas para exportar aún.');
            return;
        }

        let pgn = '[Event "Partida contra Stockfish 19"]\n';
        pgn += `[White "${this.state.player_color === 'white' ? 'Orlando Dorival' : 'Stockfish 19'}"]\n`;
        pgn += `[Black "${this.state.player_color === 'black' ? 'Orlando Dorival' : 'Stockfish 19'}"]\n`;
        pgn += `[Result "${this.state.game_over ? (this.state.winner === 'white' ? '1-0' : this.state.winner === 'black' ? '0-1' : '1/2-1/2') : '*'}"]\n\n`;

        const moves = this.state.moves_san;
        for (let i = 0; i < moves.length; i += 2) {
            const moveNum = Math.floor(i / 2) + 1;
            pgn += `${moveNum}. ${moves[i]} ${moves[i + 1] || ''} `;
        }

        navigator.clipboard.writeText(pgn.trim()).then(() => {
            alert('PGN copiado al portapapeles con éxito.');
        }).catch(() => {
            prompt('Copia tu PGN:', pgn);
        });
    }

    toggleMute(btn) {
        window.chessAudio.muted = !window.chessAudio.muted;
        btn.textContent = window.chessAudio.muted ? '🔇 Mute' : '🔊 Sonido';
    }
}

// Iniciar aplicación al cargar el DOM
window.addEventListener('DOMContentLoaded', () => {
    window.chessApp = new ChessApp();
});
