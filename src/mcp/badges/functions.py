# from datetime import datetime
import os
from io import BytesIO
from flask.scaffold import F
# from lxml import etree
from bs4 import BeautifulSoup
import base64
from qrcode import QRCode

# from sqlalchemy.exc import PendingRollbackError

from flask import current_app

# from mcp import db
from mcp.users.models import User
# from mcp.config import settings
# from mcp.groups.models import Group
# from mcp.main.tasks import set_task_progress, run_as_task

# from mcp.badges.models import


def makeFileFriendlyName(names):
    for n in names:
        if n != '':
            n.replace(' ', '_')

    name = '_'.join(names)

    return name


def encode_image(image):
    return "data:image/png;base64," + base64.b64encode(image).decode("utf-8")


def generate_badge(user_id, template):
    user = User.query.get(user_id)
    template_path = os.path.join(current_app.root_path, 'badges/static/badge_templates',
                                template)
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics',
                                user.image_file)

    badge_svg = None

    with open(template_path) as template_file:
        soup = BeautifulSoup(template_file, features='lxml')

        first_name = soup.find('tspan', {"id": "tspan3833"})
        last_name = soup.find('tspan', {"id": "tspan3841"})
        photo = soup.find('image', {"id": "image290"})
        qr_code = soup.find('image', {"id": "qr"})

        first_name.contents[0].replace_with(user.first_name)
        last_name.contents[0].replace_with(user.last_name)
        with open(picture_path, 'rb') as picture_file:
            image = picture_file.read()
            photo.attrs['xlink:href'] = encode_image(image)

        qr = QRCode(version=1, box_size=10, border=0)
        name = makeFileFriendlyName([user.first_name, user.last_name])
        qr.add_data(f"http://makeict.org/wiki/User:{name}")
        qr.make(fit=True)

        qr_img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        qr_code.attrs['xlink:href'] = encode_image(buffer.getvalue())

        badge_svg = soup

    return badge_svg