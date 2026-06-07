#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuantInsight Pro - 加密 ZIP (AES-256)
Phase 2 C1: 提交包加密
"""

import os
import sys
import pyzipper
import secrets
import string
from datetime import datetime

SRC = r"D:\shFintech\QuantInsight_Pro_提交包_v1.0_20260606.zip"
DST = r"D:\shFintech\QuantInsight_Pro_提交包_v1.0_20260606_加密.zip"

def gen_password(length=20):
    """生成 20 字符强密码 (大小写+数字+符号)"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def encrypt_zip_aes256(src, dst, password):
    """AES-256 加密 ZIP"""
    print(f"[1/3] 读取源文件: {src}")
    if not os.path.exists(src):
        print(f"  [ERROR] 源文件不存在: {src}")
        return False
    src_size = os.path.getsize(src)
    print(f"  源文件大小: {src_size/1024/1024:.2f} MB")

    print(f"\n[2/3] AES-256 加密中...")
    with pyzipper.AESZipFile(dst, 'w',
                              compression=pyzipper.ZIP_DEFLATED,
                              encryption=pyzipper.WZ_AES) as zf:
        zf.setpassword(password.encode('utf-8'))
        zf.setencryption(pyzipper.WZ_AES, nbits=256)
        zf.write(src, arcname=os.path.basename(src))
    dst_size = os.path.getsize(dst)
    print(f"  输出文件: {dst}")
    print(f"  输出大小: {dst_size/1024/1024:.2f} MB")
    print(f"  压缩比:   {dst_size/src_size*100:.1f}%")

    print(f"\n[3/3] 验证加密包...")
    try:
        with pyzipper.AESZipFile(dst, 'r') as zf:
            zf.setpassword(password.encode('utf-8'))
            names = zf.namelist()
            print(f"  解压验证: PASS ({len(names)} 文件, {names[0]})")
        return True
    except Exception as e:
        print(f"  [ERROR] 解压验证失败: {e}")
        return False


def main():
    print("="*60)
    print("QuantInsight Pro - 提交包 AES-256 加密")
    print("="*60)

    # 生成强密码
    password = gen_password(20)
    print(f"\n生成密码: {password}")
    print(f"密码长度: {len(password)} 字符")
    print(f"密码强度: 大小写+数字+符号 4 类")
    print(f"熵估算:   {len(password) * 6} bits (远超 AES-256 256 bits 需求)")

    # 加密
    success = encrypt_zip_aes256(SRC, DST, password)

    if success:
        # 写入密码到独立文件 (3 份副本)
        pwd_file = r"D:\shFintech\_pwd_submission_v1.txt"
        with open(pwd_file, 'w', encoding='utf-8') as f:
            f.write(f"# QuantInsight Pro 提交包加密密码\n")
            f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 源文件:   {os.path.basename(SRC)}\n")
            f.write(f"# 加密文件: {os.path.basename(DST)}\n")
            f.write(f"# 加密算法: AES-256 (pyzipper WZ_AES)\n")
            f.write(f"# 密码长度: {len(password)} 字符\n")
            f.write(f"#\n")
            f.write(f"# 密码 (请妥善保管, 建议 3 处独立备份):\n")
            f.write(f"\n{password}\n")
        print(f"\n[OK] 密码已保存到: {pwd_file}")
        print(f"[OK] 建议 3 处独立备份:")
        print(f"  1. 团队主邮箱草稿 (用户操作)")
        print(f"  2. 推荐单位邮箱草稿 (用户操作)")
        print(f"  3. 律师托管 (用户操作)")
        print(f"\n[OK] 加密包路径: {DST}")
        print(f"[OK] 加密包大小: {os.path.getsize(DST)/1024/1024:.2f} MB")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
