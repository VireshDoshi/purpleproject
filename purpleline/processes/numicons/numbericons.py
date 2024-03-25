import io
from PIL import Image, ImageDraw, ImageFont
import textwrap
import mimetypes
import requests


def main():
    # fill in your project id below
    create_number_icons()


def create_number_icons():
    for number in range(1,100):
        new_logo: Image = create_logo(text=f'{number}')
        file_name = f"./purpleline/data/numicons/{number}.png"
        # file_type = mimetypes.guess_type(file_name)[0]
        # buffer = io.BytesIO()
        new_logo.save(file_name, format="PNG")


def create_logo(text: str) -> Image:
    # initialize variables
    image_width = 512
    image_height = 471
    font_size = 200
    font = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
    color_mode = "RGB"
    color_definition = (43, 51, 137)
    max_line_length = 16
    fill_color = "red"
    anchor = "mm"
    alignment = "center"

    # create the image
    # image = Image.new(mode=color_mode, size=(image_width, image_height), color=color_definition)
    image = Image.open('./purpleline/data/icons/house-icon-512x471.png')


    # create the canvas
    canvas = ImageDraw.Draw(image)
    font = ImageFont.truetype(font=font, size=font_size)
    # wrap text
    new_lines = []
    lines = text.split("\n")

    for line in lines:
        if len(line) > max_line_length:
            w = textwrap.TextWrapper(width=max_line_length, break_long_words=False)
            line = "\n".join(w.wrap(line))

        new_lines.append(line)

    new_text = "\n".join(new_lines)
    canvas.ellipse((100, 150, 420, 450),
                   outline="black", width=5, fill="yellow")
    # add text to canvas
    canvas.text(
        xy=((image_width) / 2, (image_height + 200) / 2),
        text=new_text,
        fill=fill_color,
        font=font,
        anchor=anchor,
        align=alignment,
    )
    return image


def update_table_logo(table_id: str, table_name: str):
    # create the new logo
    new_logo: Image = create_logo(text=table_name)

    # upload logo to Morta and get URL
    file_name = f"{table_name}.png"
    file_type = mimetypes.guess_type(file_name)[0]
    buffer = io.BytesIO()
    new_logo.save(buffer, format="PNG")
    image_file = buffer.getvalue()

    x = (file_name, image_file, file_type)

    uploaded_file = upload_file(file=file_tuple)
    new_logo_url = uploaded_file["url"]

    # update the table
    update_table(table_id=table_id, params={"logo": new_logo_url})


def upload_file(file: tuple) -> dict:
    headers = {"Authorization": f"Bearer {MORTA_USER_TOKEN}"}
    files = {"file": file}
    endpoint = "/v1/files"
    destination_url = f"{URL}{endpoint}"
    response = requests.post(url=destination_url, files=files, headers=headers)

    return response.json()["data"]


def update_table(table_id: str, params: dict) -> dict:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {MORTA_USER_TOKEN}"}
    endpoint = "/v1/table/"
    destination_url = f"{URL}{endpoint}{table_id}"
    response = requests.put(url=destination_url, headers=headers, json=params)

    return response.json()["data"]


def loop_and_update(project_id: str):
    tables = get_tables(project_id=project_id)
    for table in tables:
        update_table_logo(table_id=table["publicId"], table_name=table["name"])


def get_tables(project_id: str) -> list:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {MORTA_USER_TOKEN}"}
    endpoint = f"/v1/project/{project_id}/tables"
    destination_url = f"{URL}{endpoint}"
    response = requests.get(url=destination_url, headers=headers)

    return response.json()["data"]


if __name__ == "__main__":
    main()
