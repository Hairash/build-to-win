import os
from flask import Flask, request, session, render_template, redirect

from flask_sqlalchemy import SQLAlchemy

from game import Field

app = Flask('build_to_win')
app.secret_key = os.getenv('SECRET_KEY', 'somesecretkey')
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


#### API calls
@app.route('/game_data', methods=['GET'])
def game_data():
    if 'username' in session:
        data = {
            'state': GameData.state,
            'players': GameData.players_queue if GameData.players_queue else list(GameData.players),
            'current_player': GameData.players_queue[GameData.current_player_idx] if GameData.players_queue else None,
        }
        if GameData.field:
            data.update(GameData.field.to_dict())
        if GameData.state == GAME_STATES.END:
            data['winner'] = GameData.winner
        return data

    return {'state': GAME_STATES.LOBBY, 'players': []}


@app.route('/current_user', methods=['GET'])
def current_user():
    if 'username' in session:
        return {'name': session['username']}
    return {'name': None}


@app.route('/start_game', methods=['POST'])
def start_game():
    if 'username' in session and GameData.state == GAME_STATES.LOBBY:
        GameData.state = GAME_STATES.PLAYING
        GameData.players_queue = list(GameData.players)  # TODO: Shuffle

        GameData.field = Field(FIELD_SIZE, GameData.players_queue)

        return {'event': 'Game started', 'success': True}
    return {'event': 'Game not started', 'success': False}


@app.route('/build', methods=['POST'])
def build():
    if (
        'username' in session and GameData.state == GAME_STATES.PLAYING and
        GameData.players_queue[GameData.current_player_idx] == session['username']
    ):
        player = session['username']
        x = int(request.json.get('x'))
        y = int(request.json.get('y'))
        if not GameData.field.is_build_possible(x, y):
            return {'event': 'Cannot build here', 'success': False}

        building_type = request.json.get('type')
        print(x, y, building_type)
        if not GameData.field.is_enough_resources(player, building_type):
            return {'event': 'Not enough resources', 'success': False}

        GameData.field.build(x, y, building_type, player)
        GameData.end_turn_ctr = 0
        if GameData.check_end_game():
            return {'event': 'Game over', 'success': True}
        GameData.end_turn()
        return {'event': 'Building placed', 'success': True}
        # TODO: Add winning condition and start new game

    return {'event': 'Wait for your turn', 'success': False}

@app.route('/end_turn', methods=['POST'])
def end_turn():
    if (
        'username' in session and GameData.state == GAME_STATES.PLAYING and
        GameData.players_queue[GameData.current_player_idx] == session['username']
    ):
        # TODO: Not allow to skip first turn
        GameData.end_turn_ctr += 1
        print(GameData.end_turn_ctr)
        if GameData.check_end_game():
            return {'event': 'Game over', 'success': True}

        GameData.end_turn()
        return {'event': 'Turn ended', 'success': True}

    return {'event': 'Not logged in', 'success': False}


@app.route('/restart_game', methods=['POST'])
def restart_game():
    if (
        'username' in session and GameData.state == GAME_STATES.END
    ):
        GameData.state = GAME_STATES.LOBBY
        GameData.players_queue = []
        GameData.current_player_idx = 0
        GameData.turn_ctr = 0
        GameData.winner = None
        GameData.field = None

        return {'event': 'Game restarted', 'success': True}

    return {'event': 'Not logged in', 'success': False}


@app.route('/leave_game', methods=['POST'])
def leave_game():
    if 'username' in session and GameData.state == GAME_STATES.LOBBY:
        GameData.players.discard(session['username'])
        # if session['username'] in GameData.players_queue:
        #     GameData.players_queue.remove(session['username'])
        return {'event': 'Left game', 'success': True}

    return {'event': 'Not logged in', 'success': False}


#### Authentication
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(name=username).first()
    if user and user.password == password:
        session['username'] = username
        return {'event': 'Login successful', 'success': True}

    return {'event': 'Login failed', 'success': False}


@app.route('/register', methods=['GET', 'POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    print(User.query.all())  # Not needed, just for debugging
    if User.query.filter_by(name=username).first():
        return 'User already exists'

    new_user = User(name=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    return 'User registered successfully'


@app.route('/logout', methods=['POST'])
def logout():
    # TODO: Add logout functionality
    session.pop('username', None)


# TODO: Change host
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    # app.run(port=5000)
