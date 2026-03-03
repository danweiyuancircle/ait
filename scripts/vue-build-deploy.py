#!/usr/bin/env python3
"""
Vue 项目一键打包部署脚本

执行流程：打包 → 压缩 → SSH 上传 → 备份旧文件 → 解压覆盖

使用示例：
    # 密钥认证
    python scripts/deploy.py \
        --project-dir /path/to/vue-project \
        --build-cmd "pnpm build:prod" \
        --host 192.168.1.100 \
        --user root \
        --remote-dir /var/www/html \
        --key ~/.ssh/id_rsa

    # 密码认证
    python scripts/deploy.py \
        --project-dir /path/to/vue-project \
        --build-cmd "pnpm build:prod" \
        --host 192.168.1.100 \
        --user root \
        --remote-dir /var/www/html \
        --password mypassword
"""

import argparse
import os
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

try:
    import paramiko
except ImportError:
    print("错误: 缺少 paramiko 库，请先安装: pip install paramiko")
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Vue 项目一键打包部署脚本：打包 → 压缩 → SSH 上传 → 备份 → 解压覆盖",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 密钥认证
  python deploy.py \\
    --project-dir /path/to/project \\
    --build-cmd "pnpm build:prod" \\
    --host 192.168.1.100 --user root \\
    --remote-dir /var/www/html --key ~/.ssh/id_rsa

  # 密码认证
  python deploy.py \\
    --project-dir /path/to/project \\
    --build-cmd "pnpm build:prod" \\
    --host 192.168.1.100 --user root \\
    --remote-dir /var/www/html --password mypassword
        """,
    )

    # 必填参数
    parser.add_argument("--project-dir", required=True, help="Vue 项目本地路径")
    parser.add_argument("--build-cmd", required=True, help='打包命令（如 "pnpm build:prod"）')
    parser.add_argument("--host", required=True, help="远程服务器地址")
    parser.add_argument("--user", required=True, help="SSH 用户名")
    parser.add_argument("--remote-dir", required=True, help="远程部署目录")

    # 可选参数
    parser.add_argument("--port", type=int, default=22, help="SSH 端口（默认 22）")
    parser.add_argument("--key", help="SSH 私钥文件路径（与 --password 二选一）")
    parser.add_argument("--password", help="SSH 密码（与 --key 二选一）")
    parser.add_argument("--dist-dir", default="dist", help='打包产物目录名（默认 "dist"）')
    parser.add_argument(
        "--backup-dir", default="/tmp/deploy-backups", help="远程备份目录（默认 /tmp/deploy-backups）"
    )

    args = parser.parse_args()

    # 校验项目路径
    project_path = Path(args.project_dir).resolve()
    if not project_path.is_dir():
        parser.error(f"项目目录不存在: {args.project_dir}")

    # 校验 SSH 认证方式
    if not args.key and not args.password:
        parser.error("必须指定 --key 或 --password 中的至少一种 SSH 认证方式")

    if args.key:
        key_path = Path(args.key).expanduser().resolve()
        if not key_path.is_file():
            parser.error(f"SSH 私钥文件不存在: {args.key}")

    return args


def log(msg):
    print(f"[deploy] {msg}")


def run_build(project_dir, build_cmd):
    """进入项目目录执行打包命令"""
    log(f"执行打包命令: {build_cmd}")
    result = subprocess.run(
        build_cmd,
        shell=True,
        cwd=project_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        log("打包失败!")
        sys.exit(1)
    log("打包完成")


def create_zip(project_dir, dist_dir):
    """将 dist 目录压缩为 zip 文件"""
    dist_path = Path(project_dir) / dist_dir
    if not dist_path.is_dir():
        log(f"打包产物目录不存在: {dist_path}")
        sys.exit(1)

    zip_path = Path(project_dir) / f"{dist_dir}.zip"
    log(f"压缩 {dist_path} → {zip_path}")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in dist_path.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(dist_path)
                zf.write(file, arcname)

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    log(f"压缩完成，文件大小: {size_mb:.2f} MB")
    return str(zip_path)


def connect_ssh(host, port, user, key=None, password=None):
    """建立 SSH 连接"""
    log(f"连接远程服务器 {user}@{host}:{port}")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs = {"hostname": host, "port": port, "username": user}
    if key:
        key_path = str(Path(key).expanduser().resolve())
        connect_kwargs["key_filename"] = key_path
    else:
        connect_kwargs["password"] = password

    client.connect(**connect_kwargs)
    log("SSH 连接成功")
    return client


def ssh_exec(client, cmd):
    """执行远程命令并返回输出"""
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if exit_code != 0:
        log(f"远程命令失败: {cmd}")
        if err:
            log(f"错误输出: {err}")
        sys.exit(1)
    return out


def backup_remote(client, remote_dir, backup_dir):
    """备份远程目录下的旧文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}.tar.gz"
    backup_path = f"{backup_dir}/{backup_name}"

    log(f"备份远程目录 {remote_dir} → {backup_path}")

    # 创建备份目录
    ssh_exec(client, f"mkdir -p {backup_dir}")

    # 检查远程目录是否有内容
    check = ssh_exec(client, f'[ -d "{remote_dir}" ] && ls -A "{remote_dir}" | head -1')
    if not check:
        log("远程目录为空，跳过备份")
        return

    ssh_exec(client, f'tar -czf "{backup_path}" -C "{remote_dir}" .')
    log(f"备份完成: {backup_path}")


def upload_and_deploy(client, local_zip, remote_dir):
    """上传 zip 并在远程解压覆盖"""
    remote_zip = f"/tmp/deploy_{os.path.basename(local_zip)}"

    # 上传
    log(f"上传 {local_zip} → {remote_zip}")
    sftp = client.open_sftp()
    sftp.put(local_zip, remote_zip)
    sftp.close()
    log("上传完成")

    # 确保远程目录存在
    ssh_exec(client, f'mkdir -p "{remote_dir}"')

    # 清空远程目录内容并解压
    log(f"解压到 {remote_dir}")
    ssh_exec(client, f'rm -rf "{remote_dir}"/*')
    ssh_exec(client, f'unzip -o "{remote_zip}" -d "{remote_dir}"')

    # 清理远程临时 zip
    ssh_exec(client, f'rm -f "{remote_zip}"')
    log("远程部署完成")


def main():
    args = parse_args()
    project_dir = str(Path(args.project_dir).resolve())

    log("===== 开始部署 =====")

    # 1. 执行打包
    run_build(project_dir, args.build_cmd)

    # 2. 压缩产物
    local_zip = create_zip(project_dir, args.dist_dir)

    try:
        # 3. SSH 连接
        client = connect_ssh(args.host, args.port, args.user, args.key, args.password)

        try:
            # 4. 备份远程旧文件
            backup_remote(client, args.remote_dir, args.backup_dir)

            # 5. 上传并部署
            upload_and_deploy(client, local_zip, args.remote_dir)
        finally:
            client.close()
            log("SSH 连接已关闭")
    finally:
        # 6. 清理本地临时 zip
        if os.path.exists(local_zip):
            os.remove(local_zip)
            log(f"已清理本地临时文件: {local_zip}")

    log("===== 部署完成 =====")


if __name__ == "__main__":
    main()
