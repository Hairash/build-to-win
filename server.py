import os
import random

from flask import Flask, request, session, render_template, redirect
from flask_socketio import SocketIO, emit

from flask_sqlalchemy import SQLAlchemy

from game import Field

app = Flask('build_to_win')
app.secret_key = os.getenv('SECRET_KEY', 'somesecretkey')
socketio = SocketIO(app, cors_allowed_origins='*')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)


with app.app_context():
    db.create_all()

FIELD_SIZE = 10


class GAME_STATES:
    LOBBY = 'lobby'
    PLAYING = 'playing'
    END = 'end'


class GameData:
    state = GAME_STATES.LOBBY
    players = set()
    players_queue = []
    current_player_idx = 0
    turn_ctr = 0
    winner = None
    end_turn_ctr = 0

    field = None  # 2d list of Cell objects

    @classmethod
    def end_turn(cls):
        cls.current_player_idx = (cls.current_player_idx + 1) % len(cls.players_queue)
        if cls.current_player_idx == 0:
            cls.turn_ctr += 1
        while not cls.field.is_in_game(cls.players_queue[cls.current_player_idx], cls.turn_ctr):
            cls.current_player_idx = (cls.current_player_idx + 1) % len(cls.players_queue)
            if cls.current_player_idx == 0:
                cls.turn_ctr += 1
        cls.field.update_resources(cls.players_queue[cls.current_player_idx])

    @classmethod
    def check_end_game(cls):
        winner = cls.field.is_end_game(cls.players, cls.turn_ctr, cls.end_turn_ctr)
        if winner:
            cls.state = GAME_STATES.END
            cls.winner = winner
            return True
        return False

    @classmethod
    def to_dict(cls):
        return {
            'state': cls.state,
            'players': cls.players_queue if cls.players_queue else list(cls.players),
            'current_player': cls.players_queue[cls.current_player_idx] if cls.players_queue else None,
            'turn_ctr': cls.turn_ctr,
            'end_turn_ctr': cls.end_turn_ctr,
            'field': cls.field.to_dict() if cls.field else None,
        }

    @classmethod
    def reset(cls):
        cls.state = GAME_STATES.LOBBY
        cls.players_queue = []
        cls.current_player_idx = 0
        cls.turn_ctr = 0
        cls.winner = None
        cls.end_turn_ctr = 0
        cls.field = None


#### Pages
@app.route('/')
def index():
    return render_template('login.html')


@app.route('/game')
def game():
    if 'username' in session:
        print(f'User {session["username"]} connected')
        GameData.players.add(session['username'])
        return render_template('game.html')
    return redirect('/')


#### Websocket events
@socketio.on('connect')
def handle_connect():
    if 'username' not in session:
        emit('connected', {'error': 'Not logged in'})

    print(f'User {session["username"]} connected')
    GameData.players.add(session['username'])
    emit('connected', {'event': 'Connected', 'name': session['username']})
    socketio.emit('players', {'players': list(GameData.players)})
    if GameData.state in [GAME_STATES.PLAYING, GAME_STATES.END]:
        emit('game_started', {**GameData.to_dict()})
        emit('game_updated', {
            'current_player': GameData.players_queue[GameData.current_player_idx],
            'turn_ctr': GameData.turn_ctr,
            'field': GameData.field.to_dict(),
        })
        if GameData.state == GAME_STATES.END:
            emit('game_over', {'winner': GameData.winner})


@socketio.on('disconnect')
def handle_disconnect():
    if 'username' in session:
        print(f'User {session["username"]} disconnected')
        GameData.players.discard(session['username'])
        print(f'GameData players: {GameData.players}')
        socketio.emit('players', {'players': list(GameData.players)})

        if GameData.state in [GAME_STATES.PLAYING, GAME_STATES.END]:
            GameData.field.remove_player(session['username'])

            # TODO: Cannot be properly handled on the 1st turn
            if not any([GameData.field.is_in_game(player, GameData.turn_ctr) for player in GameData.players_queue]):
                GameData.reset()
                socketio.emit('go_to_lobby')
                return

            if GameData.players_queue[GameData.current_player_idx] == session['username']:
                GameData.end_turn()

            socketio.emit('game_updated', {
                'current_player': GameData.players_queue[GameData.current_player_idx],
                'turn_ctr': GameData.turn_ctr,
                'field': GameData.field.to_dict(),
            })

            if GameData.check_end_game():
                socketio.emit('game_over', {'winner': GameData.winner,})


@socketio.on('build')
def handle_build(data):
    if (
        'username' in session and GameData.state == GAME_STATES.PLAYING and
        GameData.players_queue[GameData.current_player_idx] == session['username']
    ):
        print('Building request received', data)
        player = session['username']
        x = int(data.get('x'))
        y = int(data.get('y'))
        if not GameData.field.is_build_possible(x, y):
            emit('error', {'error': 'Cannot build here'})
            return

        building_type = data.get('type')
        print(x, y, building_type)
        if not GameData.field.is_enough_resources(player, building_type):
            emit('error', {'error': 'Not enough resources'})
            return

        if GameData.turn_ctr < 2 and building_type == 'tower':
            emit('error', {
                'error': 'Cannot build tower during first 2 turns',
            })
            return

        GameData.field.build(x, y, building_type, player)
        # TODO: Send build event with the specific cells to change
        socketio.emit('game_updated', {
            'current_player': GameData.players_queue[GameData.current_player_idx],
            'turn_ctr': GameData.turn_ctr,
            'field': GameData.field.to_dict(),
        })
        # TODO: Add "you lose" check
        GameData.end_turn_ctr = 0
        if GameData.check_end_game():
            socketio.emit('game_over', {'winner': GameData.winner})
            return
        # socketio.emit('building_placed', {
        #     'x': x,
        #     'y': y,
        #     'type': building_type,
        #     'player': player,
        # })
        # socketio.emit('update_field', {
        #     'field': GameData.field.to_dict(),
        # })
        GameData.end_turn()
        socketio.emit('game_updated', {
            'current_player': GameData.players_queue[GameData.current_player_idx],
            'turn_ctr': GameData.turn_ctr,
            'field': GameData.field.to_dict(),
        })
    else:
        emit('error', {'error': 'Wait for your turn'})


@socketio.on('end_turn')
def handle_end_turn():
    if (
        'username' in session and GameData.state == GAME_STATES.PLAYING and
        GameData.players_queue[GameData.current_player_idx] == session['username']
    ):
        if GameData.turn_ctr < 1:
            emit('error', {'error': 'Cannot skip first turn'})
            return
        GameData.end_turn_ctr += 1
        if GameData.check_end_game():
            socketio.emit('game_over', {'winner': GameData.winner})
            return

        GameData.end_turn()
        socketio.emit('game_updated', {
            'current_player': GameData.players_queue[GameData.current_player_idx],
            'turn_ctr': GameData.turn_ctr,
            'field': GameData.field.to_dict(),
        })
    else:
        emit('error', {'error': 'Wait for your turn'})


@socketio.on('restart_game')
def handle_restart_game():
    if (
        'username' in session and GameData.state == GAME_STATES.END
    ):
        GameData.reset()
        socketio.emit('go_to_lobby')
    else:
        emit('error', {'error': 'Not logged in'})


@socketio.on('start_game')
def handle_start_game():
    if 'username' in session and GameData.state == GAME_STATES.LOBBY:
        GameData.state = GAME_STATES.PLAYING
        GameData.players_queue = list(GameData.players)
        random.shuffle(GameData.players_queue)

        GameData.field = Field(FIELD_SIZE, GameData.players_queue)

        socketio.emit('game_started', {**GameData.to_dict()})
    else:
        emit('error', {'error': 'Game not started'})


#### Authentication
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(name=username).first()
    if user and user.password == password:
        session['username'] = username
        return {'event': 'Login successful', 'success': True}

    return {'event': 'Login failed', 'success': False, 'error': 'Invalid credentials'}


@app.route('/register', methods=['GET', 'POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    print()
    for user in User.query.all():
        print(user.name)
    if User.query.filter_by(name=username).first():
        user = User.query.filter_by(name=username).first()
        print(user)
        print(user.name)
        return {'event': 'Registration failed', 'success': False, 'error': 'User already exists'}

    new_user = User(name=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    return {'event': 'Registration successful', 'success': True}


@app.route('/logout', methods=['POST'])
def logout():
    # TODO: Add logout functionality
    session.pop('username', None)


if __name__ == '__main__':
    # socketio.run(app, host='0.0.0.0', port=8080)
    socketio.run(app, port=8080, allow_unsafe_werkzeug=True)
