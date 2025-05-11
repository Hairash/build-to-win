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
  'yellow',
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


window.onload = function() {
  document.getElementById('start-game-btn').addEventListener('click', sendStartGame);
  document.getElementById('end-turn-btn').addEventListener('click', sendEndTurn);
  const actionButtons = document.getElementsByClassName('action building');
  // Iterate over all action buttons and add event listeners
  for (let i = 0; i < actionButtons.length; i++) {
    actionButtons[i].addEventListener('click', handleActionClick);
  }
  document.getElementById('restart-game-btn').addEventListener('click', sendRestartGame);
  // If user leaves the game, send the message to the server
  window.addEventListener('unload', sendLeaveGame);
}


// ---- Game logic ----
function startGame() {
  document.getElementById('lobby').style.display = 'none';
  document.getElementById('game').style.display = 'block'; // Show the game
  document.getElementById('restart-game-btn').style.display = 'none';
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
    const li = document.createElement('li');
    li.textContent = player;
    lobbyPlayersEl.appendChild(li);
  });
}

function processGameData(data) {
  if (!playersColors) {
    playersColors = {};
    for (let i = 0; i < data.players.length; i++) {
      playersColors[data.players[i]] = COLORS[i];
    }
    if (currentUser in playersColors) {
      document.getElementById('player-name').className = `player-label ${playersColors[currentUser]}`;
    }
  }
  const currentPlayerEl = document.getElementById('current-player');
  currentPlayerEl.textContent = data.current_player;
  currentPlayerEl.className = `player-label ${playersColors[data.current_player]}`;
  if (currentUser in data.resources) {
    document.getElementById('wood-resource').textContent = data.resources[currentUser].wood;
  }
  const fieldEl = document.getElementById('field');
  if (fieldEl.children.length > 0) {
    updateField(data.field);
  }
  else {
    createField(data.field);
  }
}

function createField(field) {
  const fieldEl = document.getElementById('field');
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
  const fieldEl = document.getElementById('field');
  for (let x = 0; x < field.length; x++) {
    const rowEl = document.getElementById(`row-${x}`);
    for (let y = 0; y < field[x].length; y++) {
      const cellData = field[x][y];
      const cellEl = document.getElementById(`cell-${x}-${y}`);
      cellEl.classList.add(cellData.resource);
      const buildingEl = cellEl.querySelector('.building');
      if (cellData.building && buildingEl) {
        buildingEl.className = `building ${cellData.building.type} ${playersColors[cellData.building.player]}`;
        buildingEl.dataset.player = cellData.building.player;
      }
      else if (cellData.building) {
        const newBuildingEl = document.createElement('span');
        newBuildingEl.className = `building ${cellData.building.type} ${playersColors[cellData.building.player]}`;
        newBuildingEl.dataset.player = cellData.building.player;
        cellEl.appendChild(newBuildingEl);
      }
      else if (!cellData.building && buildingEl) {
        buildingEl.remove();
      }
    }
  }
}


// ---- Send requests to server ----
function sendStartGame() {
  fetch('/start_game', {
    method: 'POST',
  })
    .then(response => response.json())
    .then(data => {
      console.log('Game started successfully');
    })
    .catch(error => console.error('Error:', error));
}

function getCurrentUser() {
  fetch('/current_user')
    .then(response => response.json())
    .then(data => {
      currentUser = data.name;
      const playerName = document.getElementById('player-name');
      playerName.textContent = data.name;
    })
    .catch(error => console.error('Error fetching current user:', error));
}

function sendBuildingAction(action, x, y) {
  fetch('/build', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      type: selectedBuilding,
      x: x,
      y: y,
    })
  })
    .then(response => response.json())
    .then(data => {
      console.log('Action response:', data);
      // Handle the response from the server if needed
    })
    .catch(error => console.error('Error:', error));
}

function sendEndTurn() {
  fetch('/end_turn', {
    method: 'POST',
  })
    .then(response => response.json())
    .then(data => {
      console.log('Turn ended successfully');
      // Handle the response from the server if needed
    })
    .catch(error => console.error('Error:', error));
}

function sendRestartGame() {
  fetch('/restart_game', {
    method: 'POST',
  })
    .then(response => response.json())
    .then(data => {
      console.log('Game restarted successfully');
    })
    .catch(error => console.error('Error:', error));
}

function sendLeaveGame() {
  navigator.sendBeacon('/leave_game');
}


// ---- Start client ----
getCurrentUser();

setInterval(function() {
  // TODO: Remove
  if (!getDataLoop) return;
  fetch('/game_data')
    .then(response => response.json())
    .then(data => {
      if (gameState === GAME_STATES.LOBBY) {
        outputPlayersInLobby(data);
        if (data.state === GAME_STATES.PLAYING) {
          gameState = GAME_STATES.PLAYING;
          startGame();
        }
      }
      else if (gameState === GAME_STATES.PLAYING) {
        processGameData(data);
        if (data.state === GAME_STATES.END) {
          gameState = GAME_STATES.END;
          alert(`Game Over! ${data.winner} wins!`);
          if (currentUser === data.winner) {
            document.getElementById('restart-game-btn').style.display = 'block';
          }
        }
      }
      else if (gameState === GAME_STATES.END) {
        if (data.state === GAME_STATES.LOBBY) {
          gameState = GAME_STATES.LOBBY;
          goToLobby();
        }
      }
    })
    .catch(error => console.error('Error fetching players:', error));
}, 100);
