from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chat_pro_secret'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

socketio = SocketIO(app, cors_allowed_origins="*")

# 数据文件
USER_FILE = "awa.txt"
MSG_FILE = "msg_history.txt"

# 用户结构：用户名: {pwd, nick, avatar, friends, mute, role}
def load_users():
    users = {}
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                parts = line.split("|")
                if len(parts) == 6:
                    user, pwd, nick, avatar, friends, mute = parts
                    users[user] = {
                        "pwd": pwd,
                        "nick": nick,
                        "avatar": avatar,
                        "friends": friends.split(",") if friends else [],
                        "mute": mute == "1",
                        "role": "admin" if user == "114514" else "user"
                    }
    return users

def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        for u, d in users.items():
            friends_str = ",".join(d["friends"])
            mute_str = "1" if d["mute"] else "0"
            f.write(f"{u}|{d['pwd']}|{d['nick']}|{d['avatar']}|{friends_str}|{mute_str}\n")

# 消息记录
def save_msg(msg_type, from_user, to_user, content, t):
    with open(MSG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{msg_type}|{from_user}|{to_user}|{content}|{t}\n")

def load_msgs():
    msgs = []
    if os.path.exists(MSG_FILE):
        with open(MSG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                parts = line.split("|")
                if len(parts) == 5:
                    msgs.append({
                        "type": parts[0],
                        "from": parts[1],
                        "to": parts[2],
                        "content": parts[3],
                        "time": parts[4]
                    })
    return msgs

# 初始化默认管理员
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        f.write("114514|123|管理员|default.png||0\n")
        f.write("123|123|用户1|default.png||0\n")

# 路由
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

# 注册
@app.route("/api/register", methods=["POST"])
def register():
    user = request.form.get("username")
    pwd = request.form.get("password")
    nick = request.form.get("nickname")
    users = load_users()
    if user in users:
        return jsonify({"code":1,"msg":"用户名已存在"})
    users[user] = {
        "pwd": pwd, "nick": nick, "avatar": "default.png",
        "friends": [], "mute": False, "role": "user"
    }
    save_users(users)
    return jsonify({"code":0,"msg":"注册成功"})

# 登录
@app.route("/api/login", methods=["POST"])
def login():
    user = request.form.get("username")
    pwd = request.form.get("password")
    users = load_users()
    if user in users and users[user]["pwd"] == pwd:
        return jsonify({
            "code":0, "msg":"成功",
            "role": users[user]["role"],
            "nick": users[user]["nick"],
            "avatar": users[user]["avatar"]
        })
    return jsonify({"code":1,"msg":"账号或密码错误"})

# 上传头像
@app.route("/api/upload_avatar", methods=["POST"])
def upload_avatar():
    user = request.form.get("username")
    file = request.files.get("avatar")
    if not file:
        return jsonify({"code":1,"msg":"未选择文件"})
    filename = secure_filename(f"{user}_{int(time.time())}.png")
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    users = load_users()
    users[user]["avatar"] = filename
    save_users(users)
    return jsonify({"code":0,"avatar":filename})

# 获取好友
@app.route("/api/get_friends", methods=["POST"])
def get_friends():
    user = request.form.get("username")
    users = load_users()
    friends = users.get(user, {}).get("friends", [])
    data = []
    for f in friends:
        if f in users:
            data.append({
                "user": f,
                "nick": users[f]["nick"],
                "avatar": users[f]["avatar"],
                "mute": users[f]["mute"]
            })
    return jsonify({"code":0,"friends":data})

# 添加好友
@app.route("/api/add_friend", methods=["POST"])
def add_friend():
    user = request.form.get("username")
    friend = request.form.get("friend")
    users = load_users()
    if friend not in users:
        return jsonify({"code":1,"msg":"用户不存在"})
    if friend in users[user]["friends"]:
        return jsonify({"code":1,"msg":"已是好友"})
    users[user]["friends"].append(friend)
    save_users(users)
    return jsonify({"code":0,"msg":"添加成功"})

# 管理员：禁言/解禁
@app.route("/api/mute_user", methods=["POST"])
def mute_user():
    admin = request.form.get("admin")
    target = request.form.get("target")
    status = request.form.get("status") == "1"
    users = load_users()
    if users.get(admin, {}).get("role") != "admin":
        return jsonify({"code":1,"msg":"无权限"})
    if target in users:
        users[target]["mute"] = status
        save_users(users)
        return jsonify({"code":0,"msg":"操作成功"})
    return jsonify({"code":1,"msg":"用户不存在"})

# Socket 群聊
@socketio.on("group_msg")
def handle_group(data):
    user = data["user"]
    msg = data["msg"]
    users = load_users()
    if users[user]["mute"]:
        emit("mute_notice", {"msg":"你已被禁言"}, to=request.sid)
        return
    t = time.strftime("%H:%M:%S")
    save_msg("group", user, "all", msg, t)
    emit("new_group_msg", {
        "user": user,
        "nick": users[user]["nick"],
        "avatar": users[user]["avatar"],
        "msg": msg,
        "time": t
    }, broadcast=True)

# Socket 私聊
@socketio.on("private_msg")
def handle_private(data):
    from_u = data["from"]
    to_u = data["to"]
    msg = data["msg"]
    users = load_users()
    if users[from_u]["mute"]:
        emit("mute_notice", {"msg":"你已被禁言"}, to=request.sid)
        return
    t = time.strftime("%H:%M:%S")
    save_msg("private", from_u, to_u, msg, t)
    emit("new_private_msg", {
        "from": from_u,
        "nick": users[from_u]["nick"],
        "avatar": users[from_u]["avatar"],
        "msg": msg,
        "time": t
    }, room=to_u)
    emit("new_private_msg", {
        "from": from_u,
        "nick": users[from_u]["nick"],
        "avatar": users[from_u]["avatar"],
        "msg": msg,
        "time": t
    }, room=from_u)

# 获取历史消息
@app.route("/api/get_history", methods=["GET"])
def get_history():
    return jsonify({"code":0,"msgs":load_msgs()})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
