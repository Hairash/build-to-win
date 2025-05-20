const GAME_STATES = {
  LOBBY: 'lobby',
  PLAYING: 'playing',
  END: 'end',
};
let gameState = GAME_STATES.LOBBY;
let selectedBuilding = null;
let currentUser = null;
let getDataLoop = true;
const COLORS = [
  'red',
  'blue',
  'green',
  'yellow',  // Yellow is not visible
  'purple',
  'orange',
  'pink',
  'brown',
  'cyan',
  'lime',
  'teal',
  'navy',
  'maroon',
  'olive',
  'silver',
  'gold',
]
let playersColors = null;


window.onload = function () {
  document.getElementById('start-game-btn').addEventListener('click', sendStartGame);
  document.getElementById('end-turn-btn').addEventListener('click', sendEndTurn);
  const actionButtons = document.getElementsByClassName('action building');
  // Iterate over all action buttons and add event listeners
  for (let i = 0; i < actionButtons.length; i++) {
    actionButtons[i].addEventListener('click', handleActionClick);
  }
  document.getElementById('restart-game-btn').addEventListener('click', sendRestartGame);
  // TODO: Check this
  document.getElementById('game-message').addEventListener('click', function () {
    this.style.display = 'none';
    this.classList.remove('fade-in');
  });
}


// ---- Game logic ----
function initColors(players) {
  playersColors = {};
  for (let i = 0; i < players.length; i++) {
    playersColors[players[i]] = COLORS[i];
  }

  if (currentUser in playersColors) {
    document.getElementById('player-name').className = `player-label ${playersColors[currentUser]}`;
  }
}

function updateGameStatus(data) {
  const currentPlayerEl = document.getElementById('current-player');
  currentPlayerEl.textContent = data.current_player;
  currentPlayerEl.className = `player-label ${playersColors[data.current_player]}`;
  if (currentUser in data.field.resources) {
    document.getElementById('wood-resource').textContent = data.field.resources[currentUser].wood;
  }

  if (data.current_player === currentUser ) {
    enableButtons(data);
  }
  else {
    disableButtons();
  }
}

function startGame(data) {
  document.getElementById('lobby').style.display = 'none';
  document.getElementById('game').style.display = 'block'; // Show the game
  document.getElementById('restart-game-container').style.display = 'none';
  document.getElementById('game-message').style.display = 'none';
  document.getElementById('game-message').classList.remove('fade-in');

  initColors(data.players);
  createField(data.field.field);
  updateGameStatus(data);
}

function goToLobby() {
  document.getElementById('field').innerHTML = ''; // Clear the field
  document.getElementById('game').style.display = 'none';
  document.getElementById('lobby').style.display = 'block'; // Show the lobby
  document.getElementById('player-name').className = 'player-label';
  playersColors = null;
}

function handleActionClick() {
  document.querySelector('.action.building.selected')?.classList.remove('selected');
  this.classList.add('selected');
  selectedBuilding = this.dataset.type;
}

function handleCellClick() {
  if (selectedBuilding) {
    const x = this.dataset.x;
    const y = this.dataset.y;
    console.log('Sending building action:', selectedBuilding, x, y);
    sendBuildingAction(selectedBuilding, x, y);
  }
}

function outputPlayersInLobby(data) {
  console.log(data);
  const lobbyPlayersEl = document.getElementById('lobby-players');
  lobbyPlayersEl.innerHTML = ''; // Clear the list before updating
  data.players.forEach(player => {
    const p = document.createElement('p');
    p.textContent = player;
    lobbyPlayersEl.appendChild(p);
  });

  if (data.players.length >= 2) {
    document.getElementById('game-start-condition-label').style.display = 'none';
    enableElement(document.getElementById('start-game-btn'));
  }
  else {
    document.getElementById('game-start-condition-label').style.display = 'block';
    disableElement(document.getElementById('start-game-btn'));
  }
}

function createField(field) {
  const fieldEl = document.getElementById('field');
  document.getElementById('field').innerHTML = '';
  for (let x = 0; x < field.length; x++) {
    const rowEl = document.createElement('div');
    rowEl.id = `row-${x}`;
    rowEl.className = 'cell-row';
    for (let y = 0; y < field[x].length; y++) {
      const cellData = field[x][y];
      const cellEl = document.createElement('span');
      cellEl.id = `cell-${x}-${y}`;
      cellEl.className = 'cell';
      cellEl.classList.add(cellData.resource);
      cellEl.dataset.x = x;
      cellEl.dataset.y = y;
      cellEl.addEventListener('click', handleCellClick);
      rowEl.appendChild(cellEl);
    }
    fieldEl.appendChild(rowEl);
  }
}

function updateField(field) {
  for (let x = 0; x < field.length; x++) {
    const rowEl = document.getElementById(`row-${x}`);
    for (let y = 0; y < field[x].length; y++) {
      const cellData = field[x][y];
      const cellEl = document.getElementById(`cell-${x}-${y}`);
      cellEl.className = `cell ${cellData.resource}`;
      const buildingEl = cellEl.querySelector('.building');
      if (cellData.building && buildingEl) {
        buildingEl.className = `building ${cellData.building.type} ${playersColors[cellData.building.player]}`;
        buildingEl.dataset.player = cellData.building.player;
      } else if (cellData.building) {
        const newBuildingEl = document.createElement('span');
        newBuildingEl.className = `building ${cellData.building.type} ${playersColors[cellData.building.player]}`;
        newBuildingEl.dataset.player = cellData.building.player;
        cellEl.appendChild(newBuildingEl);
      } else if (!cellData.building && buildingEl) {
        buildingEl.remove();
      }
    }
  }
}

function disableElement(element) {
  element.disabled = true;
  // Add class disabled only if it's not already there
  if (!element.classList.contains('disabled')) {
    element.classList.add('disabled');
  }
}

function enableElement(element) {
  element.disabled = false;
  // Remove class disabled only if it's there
  if (element.classList.contains('disabled')) {
    element.classList.remove('disabled');
  }
}

function disableButtons() {
  const actionButtons = document.getElementsByClassName('action building');
  for (let i = 0; i < actionButtons.length; i++) {
    disableElement(actionButtons[i]);
  }
  disableElement(document.getElementById('end-turn-btn'));
}

function enableButtons(data) {
  const actionButtons = document.getElementsByClassName('action building');
  console.log(data.field.resources[currentUser].wood);
  for (let i = 0; i < actionButtons.length; i++) {
    console.log(actionButtons[i].dataset.cost);
    if (data.field.resources[currentUser].wood >= actionButtons[i].dataset.cost) {
      enableElement(actionButtons[i]);
    }
  }
  if (data.turn_ctr >= 1) {
    enableElement(document.getElementById('end-turn-btn'));
  }
  if (data.turn_ctr < 2) {
    disableElement(document.querySelector('.action.building[data-type="tower"]'));
  }
}


// ---- Send requests to server ----
function sendStartGame() {
  socket.emit('start_game');
}

function sendBuildingAction(buildingType, x, y) {
  socket.emit('build', { type: buildingType, x: x, y: y });
}

function sendEndTurn() {
  socket.emit('end_turn');
}

function sendRestartGame() {
  socket.emit('restart_game');
}


// ---- Start client ----
const socket = io();

socket.on('connected', (data) => {
  console.log('Connected to server');
  currentUser = data.name;
  const playerName = document.getElementById('player-name');
  playerName.textContent = data.name;
});

socket.on('players', (data) => {
  console.log('Players:', data);
  outputPlayersInLobby(data);
});

socket.on('game_started', (data) => {
  console.log('Game started:', data);
  gameState = GAME_STATES.PLAYING;
  disableButtons();
  startGame(data);
});

socket.on('game_updated', (data) => {
  console.log('Turn ended:', data);
  updateField(data.field.field);
  updateGameStatus(data);
})

socket.on('game_over', (data) => {
  console.log('Game over:', data);
  gameState = GAME_STATES.END;
  document.getElementById('game-message').textContent = `Game Over! ${data.winner} wins!`;
  document.getElementById('game-message').style.display = 'block';
  document.getElementById('game-message').classList.add('fade-in');
  if (currentUser in playersColors) {
    document.getElementById('restart-game-container').style.display = 'flex';
  }
});

socket.on('go_to_lobby', () => {
  console.log('Going to lobby');
  gameState = GAME_STATES.LOBBY;
  goToLobby();
});


socket.on('error', (data) => {
  console.error('Error:', data);
  document.getElementById('error-message').textContent = data.error;
  document.getElementById('error-message').style.display = 'block';
  document.getElementById('error-message').classList.add('fade-in');
  setTimeout(() => {
    document.getElementById('error-message').style.display = 'none';
    document.getElementById('error-message').classList.remove('fade-in');
  }, 3000);
});