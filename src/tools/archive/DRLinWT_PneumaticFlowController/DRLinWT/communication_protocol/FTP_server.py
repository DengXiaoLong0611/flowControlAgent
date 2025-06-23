from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

def Create_FTP_Server(ip_address, port=21, save_path='.', custom_code=None):
    # 创建用户授权器
    authorizer = DummyAuthorizer()
    authorizer.add_user("ADMIN", "PASSWORD", save_path, perm="elradfmwMT")
    authorizer.add_user("admin", "password", save_path, perm="elradfmwMT")

    # 创建FTP处理程序
    handler = FTPHandler
    handler.authorizer = authorizer

    # 创建FTP服务器
    server = FTPServer((ip_address, port), handler)

    # 启动FTP服务器
    print(f"FTP服务器启动在 {ip_address}:{port}")

    try:
        # 你的FTP服务器代码
        server.serve_forever()
    except Exception as e:
        print(f"An error occurred: {e}")
    return server


if __name__=='__main__':
    Create_FTP_Server('191.30.90.11', 21)

