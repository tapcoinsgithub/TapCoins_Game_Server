import os
import socketio
from decouple import config
import json

sio = socketio.Server(cors_allowed_origins=config('ALLOWED_HOSTS'))
app = socketio.WSGIApp(sio)
sid_to_game_clients = {}
sid_to_game_ids = {}
all_game_rooms = {}
all_game_clients = {}

if __name__ == '__main__':
    import eventlet
    eventlet.wsgi.server(eventlet.listen((config('WSGI_HOST'), int(os.getenv('PORT', 8765)))), app)

class GameClient():
    def __init__(self, _username, _socketId, _ready, _streakDash):
        self.username = _username
        self.socketId = _socketId
        self.ready = _ready
        self.streakDash = _streakDash

    def get_username(self):
        return self.username
    
    def get_socketId(self):
        return self.socketId
    
    def get_ready(self):
        return self.ready
    
    def set_ready(self, status):
        self.ready = status

    def get_streak_dash(self):
        return self.streakDash

class GameRoom():
    def __init__(self, _player1, _player2, _gameId):
        self.player1 = _player1
        self.player2 = _player2
        self.gameId = _gameId

    def set_player1(self, _player1):
        self.player1 = _player1

    def set_player2(self, _player2):
        self.player2 = _player2

    def get_player1(self):
        return self.player1

    def get_player2(self):
        return self.player2

    def send_tap(x, y, _to):
        data = x + "|" + y
        print(f"Sending tap to {_to}")
        sio.emit("TAP", data, room=_to)
        # _io.to(_to).emit('TAP', data)

@sio.event
def connect(sid, environ):
    print('Client connected', sid)

@sio.event
def game_id(sid, data):
    data_split = data.split("|")
    print(data_split)
    c_gameId = data_split[0]
    c_username = data_split[1]
    place = data_split[2]
    streakDash = data_split[3]
    # Check if user data is already in server
    new_client = None
    new_game_room = None
    completed_game_room = False
    key = c_gameId + "|" + place
    new_client = GameClient(c_username, sid, False, streakDash)
    all_game_clients[key] = new_client
    sid_to_game_clients[sid] = new_client
    sid_to_game_ids[sid] = c_gameId

    if place == "1":
        try:
            new_game_room = all_game_rooms[c_gameId]
            new_game_room.set_player1(new_client)
            completed_game_room = True
            print("GOT THROUGH THE TRY BLOCK OF GETTING A GAME")
        except:
            new_game_room = GameRoom(new_client, None, c_gameId)
            all_game_rooms[c_gameId] =  new_game_room
            sio.emit("GAMEID", "NOTYET", room=sid)
            print("GOT THROUGH EXCEPT BLOCK OF MAKING A GAME")
    elif place == "2":
        try:
            new_game_room = all_game_rooms[c_gameId]
            new_game_room.set_player2(new_client)
            completed_game_room = True
            print("GOT THROUGH THE TRY BLOCK OF GETTING A GAME PLAYER 2")
        except:
            new_game_room = GameRoom(None, new_client, c_gameId)
            all_game_rooms[c_gameId] =  new_game_room
            sio.emit("GAMEID", "NOTYET", room=sid)
            print("GOT THROUGH THE TRY BLOCK OF MAKING A GAME PLAYER 2")
    if completed_game_room:
        print("COMPLETED THE GAME ROOM")
        print(new_game_room)
        for key in all_game_clients:
            print("***********************")
            print(key)
            print(all_game_clients[key])
            print("***********************")
        player1_message = "SUCCESS|" + new_game_room.get_player2().get_streak_dash() 
        player2_message = "SUCCESS|" + new_game_room.get_player1().get_streak_dash() 
        sio.emit('GAMEID', player1_message, room=new_game_room.get_player1().get_socketId())
        sio.emit('GAMEID', player2_message, room=new_game_room.get_player2().get_socketId())

@sio.event
def ready(sid, data):
    data_split = data.split("|")
    username = data_split[0]
    game_Id = data_split[1]
    print("IN THE READY UP EVENT")
    for key in all_game_clients:
        print("***********************")
        print(key)
        print(all_game_clients[key])
        print("***********************")
    user = all_game_clients[game_Id + "|1"]
    user2 = all_game_clients[game_Id + "|2"]

    if user.get_username() == username:
        user.set_ready(True)
        message = str(user.get_ready()) + "|" + str(user2.get_ready()) + "|" + username
        sio.emit("READY", message, room=user2.get_socketId())
        # io.to(user2.get_socketId()).emit('READY', message)
    elif user2.get_username() == username:
        user2.set_ready(True)
        message = str(user2.get_ready()) + "|" + str(user.get_ready()) + "|" + username
        sio.emit("READY", message, room=user.get_socketId())
        # io.to(user.get_socketId()).emit('READY', message)

@sio.event
def start_game(sid, game_id):
    user1 = all_game_clients[game_id + "|1"]
    user2 = all_game_clients[game_id + "|2"]
    sio.emit("STARTCGAME", room=user1.get_socketId())
    sio.emit("STARTCGAME", room=user2.get_socketId())
    # io.to(user1.get_socketId()).emit('STARTCGAME');
    # io.to(user2.get_socketId()).emit('STARTCGAME');

@sio.event
def tap(sid, index):
    index_split1 = index.split("|")
    index_split2 = index_split1[1].split("*")
    x_index = index_split1[0]
    y_index = index_split2[0]
    game_id = index_split2[1]
    user1 = all_game_clients[game_id + "|1"]
    user2 = all_game_clients[game_id + "|2"]
    reciever = None
    curr_game = all_game_rooms[game_id]
    if (user1.get_socketId() == sid):
        reciever = user2
    elif (user2.get_socketId() == sid):
        reciever = user1
    data = x_index + "|" + y_index
    print(f"Sending tap to {reciever.get_socketId()}")
    sio.emit("TAP", data, room=reciever.get_socketId())
    # curr_game.send_tap(x_index, y_index, reciever.get_socketId())

@sio.event
def remove_game_client(sid, values):
    try:
        values_split = values.split("|")
        value = values_split[0]
        game_id = values_split[1]
        removed_user = get_user(game_id, sid)
        removed_user_position = get_map_position(game_id, sid)
        if (value == "EXIT"):
            del all_game_clients[removed_user_position]
            try:
                if (removed_user_position.split("|")[1] == "1"):
                    user = all_game_clients[removed_user_position.split("|")[0] + "|2"]
                    sio.emit("DISCONNECT", room=user.get_socketId())
                    # io.to(user2.get_socketId()).emit("DISCONNECT")
                elif (removed_user_position.split("|")[1] == "2"):
                    user = all_game_clients[removed_user_position.split("|")[0] + "|1"]
                    sio.emit("DISCONNECT", room=user.get_socketId())
                    # io.to(user.get_socketId()).emit("DISCONNECT")
            except:
                print("ERROR EMITING TO OTHER CLIENT")
        else:
            del all_game_clients[removed_user_position]
            del sid_to_game_clients[sid]
            del sid_to_game_ids[sid]
        if (removed_user != None):
            sio.emit("REMOVEDUSER", value, room=removed_user.get_socketId())
            # io.to(removed_user.get_socketId()).emit("REMOVEDUSER", value);
    except:
        print("Game Client already removed.")

@sio.event
def cancelled(sid, data):
    try:
        data_split = data.split("|")
        canceled_username = data_split[0]
        game_id = data_split[1]
        user1 = all_game_clients[game_id + "|1"]
        user2 = all_game_clients[game_id + "|2"]
        if (user1.get_username() == canceled_username):
            try:
                sio.emit("CANCELLED", canceled_username, room=user2.get_socketId())
                # io.to(user2.get_socketId()).emit('CANCELLED', canceled_username)
            except:
                print("IN THE CANCELLED CATCH BLOCK 1")
        elif (user2.get_username() == canceled_username):
            try:
                sio.emit("CANCELLED", canceled_username, room=user1.get_socketId())
                # io.to(user1.get_socketId()).emit('CANCELLED', canceled_username)
            except:
                print("IN THE CANCELLED CATCH BLOCK 2")
    except:
        print("Client already cancelled.")

@sio.event
def disconnect(sid):
    print("IN DISCONNECT HANDLER")
    try:
        curr_gameId = sid_to_game_ids[sid]
        player1_key = curr_gameId + "|1"
        player2_key = curr_gameId + "|2"
        player1 = all_game_clients[player1_key]
        player2 = all_game_clients[player2_key]
        if (player1.get_socketId() == sid):
            del all_game_clients[player1_key]
            del sid_to_game_clients[player1.get_socketId()]
            del sid_to_game_ids[player1.get_socketId()]
            try:
                sio.emit("OPDISCONNECT", room=player2.get_socketId())
            except:
                print("CANNOT EMIT CANCELLED EVENT")
        if (player2.get_socketId() == sid):
            del all_game_clients[player2_key]
            del sid_to_game_clients[player2.get_socketId()]
            del sid_to_game_ids[player2.get_socketId()]
            try:
                sio.emit("OPDISCONNECT", room=player1.get_socketId())
            except:
                print("CANNOT EMIT CANCELLED EVENT")
    except:
        print("CLIENT ALREADY LEFT")

def get_user(game_id, socket_id):
    try:
        user = all_game_clients[game_id + "|1"]
        if (user.get_socketId() == socket_id):
            return user
        else:
            user = all_game_clients.get[game_id + "|2"]
            if (user.get_socketId() == socket_id):
                return user
            else:
                print("USER NOT IN CLIENTS")
                return None
    except:
        user = all_game_clients[game_id + "|2"]
        if (user.get_socketId() == socket_id):
            return user
        else:
            print("USER NOT IN CLIENTS")
            return None

def get_map_position(game_id, socket_id):
    try:
        user = all_game_clients[game_id + "|1"]
        if (user.get_socketId() == socket_id):
            return game_id + "|1"
        else:
            user = all_game_clients[game_id + "|2"]
            if (user.get_socketId() == socket_id):
                return game_id + "|2"
            else:
                print("USER NOT IN CLIENTS")
                return None
    except:
        user = all_game_clients[game_id + "|2"]
        if (user.get_socketId() == socket_id):
            return game_id + "|2"
        else:
            print("USER NOT IN CLIENTS")
            return None
        