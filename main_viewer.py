import os
import argparse
import math
import cv2
import hashlib
import shutil
from pathlib import Path
import re

window_description = 'press w-if image contains tech, a-if image does not contains tech, d-if image broken,\
    z-to undo (but they return in next session), x-to EXIT, arrowKeys - NAVIGATE'

parser = argparse.ArgumentParser()


def translit(text):
    cyrillic_to_latin = {
        'а': 'a',         'б': 'b',        'в': 'v',        'г': 'h',        'ґ': 'g',
        'д': 'd',        'е': 'e',        'є': 'ie',        'ж': 'zh',        'з': 'z',
        'и': 'y',        'і': 'i',        'ї': 'i',        'й': 'i',        'к': 'k',
        'л': 'l',        'м': 'm',        'н': 'n',        'о': 'o',        'п': 'p',
        'р': 'r',        'с': 's',        'т': 't',        'у': 'u',        'ф': 'f',
        'х': 'kh',        'ц': 'ts',        'ч': 'ch',        'ш': 'sh',        'щ': 'shch',
        'ь': '_',        'ъ': '_',        'ю': 'iu',        'я': 'ia',        'А': 'A',
        'Б': 'B',        'В': 'V',        'Г': 'H',        'Ґ': 'G',        'Д': 'D',
        'Е': 'E',        'Є': 'Ie',        'Ж': 'Zh',        'З': 'Z',        'И': 'Y',
        'І': 'I',        'Ї': 'I',        'Й': 'I',        'К': 'K',        'Л': 'L',
        'М': 'M',        'Н': 'N',        'О': 'O',        'П': 'P',        'Р': 'R',
        'С': 'S',        'Т': 'T',        'У': 'U',        'Ф': 'F',        'Х': 'Kh',
        'Ц': 'Ts',        'Ч': 'Ch',        'Ш': 'Sh',        'Щ': 'Shch',        'Ь': '_',
        'Ъ': '_',        'Ю': 'Iu',        'Я': 'Ia', 'Ñ':'N'
    }

    for key in cyrillic_to_latin.keys():
        text = text.replace(key, cyrillic_to_latin[key])
    
    text = text.replace('\u0096', '')
    text = text.replace('\u0094', '')

    return text


def read_label_file(label_path):
    words = []
    with open(label_path, 'r') as label_file:
        lines = label_file.readlines()
        for line in lines:
            line = line.strip().split(' ')
            words.append(line)
        if (words[0][0] != 'YOLO_OBB'):
            return None
    return words


def generateColorByText(text):
    s = str(text)
    hashCode = int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16)
    r = int((hashCode / 255) % 255)
    g = int((hashCode / 65025) % 255)
    b = int((hashCode / 16581375) % 255)
    return (b, g, r)


def getClass(key, classes):
    key = int(key)

    if key in classes.keys():
        return classes[key]
    else:
        return key


def rotate_point(origin, point, angle):
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy


def draw_boxes(labels_array, image, classes):
    for label in labels_array:
        if label[0] == 'YOLO_OBB':
            continue
        centerX = float(label[1])
        centerY = float(label[2])
        width = float(label[3])
        height = float(label[4])
        angle = -(math.pi*float(label[5])/180)
        a = (centerX-width/2, centerY-height/2)
        b = (centerX+width/2, centerY-height/2)
        c = (centerX+width/2, centerY+height/2)
        d = (centerX-width/2, centerY+height/2)
        a = rotate_point((centerX, centerY), a, angle)
        b = rotate_point((centerX, centerY), b, angle)
        c = rotate_point((centerX, centerY), c, angle)
        d = rotate_point((centerX, centerY), d, angle)
        cv2.line(image, (int(a[0]), int(a[1])), (int(b[0]), int(
            b[1])), generateColorByText(getClass(label[0], classes)), 2)
        cv2.line(image, (int(b[0]), int(b[1])), (int(c[0]), int(
            c[1])), generateColorByText(getClass(label[0], classes)), 2)
        cv2.line(image, (int(c[0]), int(c[1])), (int(d[0]), int(
            d[1])), generateColorByText(getClass(label[0], classes)), 2)
        cv2.line(image, (int(a[0]), int(a[1])), (int(d[0]), int(
            d[1])), generateColorByText(getClass(label[0], classes)), 2)


def latinize_all(image_folder, label_folder):
    for image in os.listdir(image_folder):
        if(image != translit(image)):
            shutil.move(os.path.join(image_folder, image),
                        os.path.join(image_folder, translit(image)))
    for label in os.listdir(label_folder):
        if(label != translit(label)):
            shutil.move(os.path.join(label_folder, label),
                        os.path.join(label_folder, translit(label)))


def iterative_viewer(image_folder, label_folder, classes, valid_path, empty_path, deleted_path):
    latinize_all(image_folder, label_folder)
    image_files = [file for file in os.listdir(image_folder) if file.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
    last = []
    cv2.namedWindow(window_description)
    file_index = 0
    while True:
        file = image_files[file_index]
        possible_label_file = os.path.join(
            label_folder,  os.path.splitext(file)[0] + ".txt")
        if os.path.exists(possible_label_file):
            words = read_label_file(possible_label_file)
            if not words:
                continue
            img = cv2.imread(os.path.join(image_folder, file))
            draw_boxes(words, img, classes)
            try:
                cv2.imshow(window_description, img)
            except Exception as E:
                for char in file:
                    print(char, ord(char))
            if cv2.getWindowProperty(window_description, cv2.WND_PROP_VISIBLE) <1:
                break
            k = cv2.waitKeyEx(0)
            if k == 120 or k == 247:
                exit()  # x button
            elif k == 97 or k == 244:
                last.append([os.path.join(image_folder, file),
                            os.path.join(empty_path, file)])
                # a button
                print(
                    f"Image does not contain tech {shutil.move(os.path.join(image_folder,file),os.path.join(empty_path,file))}")
                image_files.remove(file)
                file_index = min(file_index+1, len(image_files)-1)
            elif k == 119 or k == 246:
                last.append([os.path.join(image_folder, file),
                            os.path.join(valid_path, file)])
                # w button
                print(
                    f"Image contains tech {shutil.move(os.path.join(image_folder,file),os.path.join(valid_path,file))}")
                image_files.remove(file)
                file_index = min(file_index+1, len(image_files)-1)
            elif k == 100 or k == 226:
                last.append([os.path.join(image_folder, file),
                            os.path.join(deleted_path, file)])
                # d button
                print(
                    f"Broken image {shutil.move(os.path.join(image_folder,file), os.path.join(deleted_path,file))}")
                image_files.remove(file)
                file_index = min(file_index+1, len(image_files)-1)
            elif k == 122 or k == 255:
                if (len(last) > 0):
                    print(f"Undo {shutil.move(last[-1][1], last[-1][0])}")
                    last.remove(last[-1])  # z button
                file_index = min(file_index+1, len(image_files)-1)
            elif k == 2555904:
                file_index = min(file_index+1, len(image_files)-1)
            elif k == 2424832:
                print("prev")
                file_index = max(0, file_index-1)
            elif k == -1:
                break
            else:
                print(f"Unhandled {k} key")


if __name__ == "__main__":

    parser.add_argument('label_folder', help='Folder containing label files')
    parser.add_argument('image_folder', help='Folder containing image files')
    labels = parser.parse_args().label_folder
    images = parser.parse_args().image_folder

    path = Path(os.path.abspath(images))
    parent_path = path.parent.absolute()
    valid_path = os.path.join(parent_path, "valid")
    empty_path = os.path.join(parent_path, "empty")
    deleted_path = os.path.join(parent_path, "deleted")
    
    user_permission = input("Allow to create 3 new folders (for valid, empty and deleted images) (Y/N)?")
    if user_permission.lower() == 'y' or user_permission.lower() == 'yes':
        pass
    else:
        exit()
    
    
    if not os.path.exists(valid_path):
        os.makedirs(valid_path)
    if not os.path.exists(empty_path):
        os.makedirs(empty_path)
    if not os.path.exists(deleted_path):
        os.makedirs(deleted_path)

    if not os.path.exists(os.path.join(labels, "classes.txt")):
        print("> No classes.txt file, i will use numbers.")
    else:
        print("> classes.txt file found, i will use it.")
    classes = {}
    with open(os.path.join(labels, "classes.txt"), 'r') as f:
        lines = f.readlines()
        for index in range(len(lines)):
            classes[index] = lines[index].strip()
    print("> Classes:")
    for index, label in classes.items():
        print(f"    {index}: {label}")
    print("starting...")
    iterative_viewer(images, labels, classes, valid_path,
                    empty_path, deleted_path)
