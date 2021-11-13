
import os
import secrets
from PIL import Image
from urllib import request
from flask import current_app


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    picture = None
    if(isinstance(form_picture, str)):
        picture_fn = random_hex + '.png'

    else:
        picture = form_picture
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics',
                                picture_fn)
    if(isinstance(form_picture, str)):
        with request.urlopen(form_picture) as response:
            ret = response.read()
        with open(picture_path, "wb") as f:
            f.write(ret)
        picture = open(picture_path, "rb")

    output_size = (600, 600)
    i = Image.open(picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    if(isinstance(form_picture, str)):
        picture.close()

    return picture_fn
