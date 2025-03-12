import os
import secrets
from PIL import Image
from flask import current_app

def save_avatar(avatar_pic):
    """保存用户头像"""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(avatar_pic.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/avatars', picture_fn)
    
    # 确保目录存在
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    # 调整图像大小
    output_size = (150, 150)
    i = Image.open(avatar_pic)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return 'avatars/' + picture_fn