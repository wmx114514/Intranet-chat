# 内网聊天室（完整版）
- 管理员：114514 / 123
- 功能：注册、登录、昵称、头像、群聊、私聊、消息记录、好友、管理员禁言
- 数据：awa.txt（用户）、msg_history.txt（消息）

## 运行
1. pip install -r requirements.txt
2. python app.py
3. 访问 http://127.0.0.1:5000
4. 内网访问：http://你的IP:5000

## 手机Termux运行
1. pkg update && pkg upgrade -y更新
2. pkg install python -y安装pip
3. pip install flask安装flask(核心)
4. 下载到手机
5. 进入Termus
6. cd (你下载此项目的目录)
7. 如果是压缩包就解压
8. python app.py
9. 成功后会提示 :
* Serving Flask app 'app'
 * Debug mode: on
 * Running on all addresses (0.0.0.0)
   WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5000
 * Running on http://xxx.xxx.xxx.xxx:5000
10. 浏览器进入http://127.0.0.1:5000
