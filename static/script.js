const socket = io();
const user = localStorage.getItem("user");
const role = localStorage.getItem("role");
let currentTab = "group";
let currentPrivate = null;

// 登录
async function login() {
  const u = document.getElementById("user").value;
  const p = document.getElementById("pwd").value;
  const fd = new FormData();
  fd.append("username", u);
  fd.append("password", p);
  const r = await fetch("/api/login", {method:"POST", body:fd});
  const data = await r.json();
  if (data.code === 0) {
    localStorage.setItem("user", u);
    localStorage.setItem("nick", data.nick);
    localStorage.setItem("avatar", data.avatar);
    localStorage.setItem("role", data.role);
    location.href = "chat.html";
  } else {
    document.getElementById("msg").textContent = data.msg;
  }
}

// 注册
async function register() {
  const u = document.getElementById("user").value;
  const p = document.getElementById("pwd").value;
  const n = document.getElementById("nick").value;
  const fd = new FormData();
  fd.append("username", u);
  fd.append("password", p);
  fd.append("nickname", n);
  const r = await fetch("/api/register", {method:"POST", body:fd});
  const data = await r.json();
  document.getElementById("msg").textContent = data.msg;
  if (data.code === 0) setTimeout(()=>location.href="index.html", 1000);
}

// 聊天室初始化
if (location.pathname.includes("chat")) {
  document.getElementById("nick").textContent = localStorage.getItem("nick");
  document.getElementById("avatar").src = "uploads/"+localStorage.getItem("avatar");
  if (role === "admin") document.getElementById("adminPanel").style.display = "block";
  loadFriends();
  loadHistory();

  // 群聊消息
  socket.on("new_group_msg", (data) => {
    addMsg("groupBox", data);
  });

  // 私聊消息
  socket.on("new_private_msg", (data) => {
    addMsg("privateBox", data);
  });

  // 禁言提示
  socket.on("mute_notice", (data) => alert(data.msg));
}

// 切换标签
function showTab(tab) {
  currentTab = tab;
  document.getElementById("groupBox").style.display = tab==="group"?"block":"none";
  document.getElementById("privateBox").style.display = tab==="private"?"block":"none";
}

// 发送消息
function sendMsg() {
  const msg = document.getElementById("msgInput").value.trim();
  if (!msg) return;
  if (currentTab === "group") {
    socket.emit("group_msg", {user: user, msg: msg});
  } else {
    if (!currentPrivate) return alert("选择私聊对象");
    socket.emit("private_msg", {from: user, to: currentPrivate, msg: msg});
  }
  document.getElementById("msgInput").value = "";
}

// 添加消息到界面
function addMsg(boxId, data) {
  const box = document.getElementById(boxId);
  const div = document.createElement("div");
  div.className = "msg-item";
  div.innerHTML = `
    <img src="uploads/${data.avatar}">
    <div class="msg-content">
      <div><b>${data.nick}</b> <span class="msg-time">${data.time}</span></div>
      <div>${data.msg}</div>
    </div>
  `;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

// 上传头像
async function uploadAvatar() {
  const file = document.getElementById("avatarFile").files[0];
  if (!file) return alert("选择图片");
  const fd = new FormData();
  fd.append("username", user);
  fd.append("avatar", file);
  const r = await fetch("/api/upload_avatar", {method:"POST", body:fd});
  const data = await r.json();
  if (data.code === 0) {
    localStorage.setItem("avatar", data.avatar);
    document.getElementById("avatar").src = "uploads/"+data.avatar;
  }
}

// 加载好友
async function loadFriends() {
  const fd = new FormData();
  fd.append("username", user);
  const r = await fetch("/api/get_friends", {method:"POST", body:fd});
  const data = await r.json();
  const list = document.getElementById("friendList");
  list.innerHTML = "";
  data.friends.forEach(f => {
    const div = document.createElement("div");
    div.className = "friend-item" + (f.mute ? " mute" : "");
    div.innerText = `${f.nick} (${f.user})`;
    div.onclick = () => { currentPrivate = f.user; showTab("private"); };
    list.appendChild(div);
  });
}

// 添加好友
async function addFriend() {
  const f = document.getElementById("addFriend").value.trim();
  const fd = new FormData();
  fd.append("username", user);
  fd.append("friend", f);
  const r = await fetch("/api/add_friend", {method:"POST", body:fd});
  const data = await r.json();
  alert(data.msg);
  loadFriends();
}

// 管理员禁言
async function muteUser(status) {
  const target = document.getElementById("muteUser").value.trim();
  const fd = new FormData();
  fd.append("admin", user);
  fd.append("target", target);
  fd.append("status", status);
  const r = await fetch("/api/mute_user", {method:"POST", body:fd});
  const data = await r.json();
  alert(data.msg);
  loadFriends();
}

// 加载历史消息
async function loadHistory() {
  const r = await fetch("/api/get_history");
  const data = await r.json();
  data.msgs.forEach(msg => {
    if (msg.type === "group") {
      addMsg("groupBox", {
        nick: msg.from, avatar: "default.png",
        msg: msg.content, time: msg.time
      });
    }
  });
}
