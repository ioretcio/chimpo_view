import os
import argparse
import math
import cv2
import hashlib
import shutil
from pathlib import Path

window_description = 'press w-if image contains target objects, a-if image does not contains target objects, d-if image broken (out of context),\
    z-to UNDO, x-to EXIT, arrowKeys - NAVIGATE'
cv2.namedWindow(window_description, cv2.WINDOW_NORMAL) 



text = """
                ......:::......                                       ..
              ...-=+======+++=:....                                     
            ..:=+=============++=.......                                
          ...=++===============++++=++=-...                             
     ......-+++=================++++++*#+=..                            
    ..:=+*++++===================+++++==*+=.                            
   ..=+#++++++===============++++++++*==+*=.                            
   .-+#+=+++++++++++=============--=+++==+=.                            
   .-+*==++++=-================------++++=:.                            
   .:=*==+++-----=====-----==%+#+-----+++=..                            
   ..:=+=++-----%=*%----:---=@@@@-:---+++..                             
    ..:=+++----:@@@@---:::---%%%%::::-+++-.                .........    
     ...+++--:::#%%@----:-----+*-:::-=+++=.              ...:-===-:.... 
       .++++-::::-=--==*==#==--:::-==+++*-.            ..:===+++++++=-..
       .=++++==-:::-------------==+++++++...          ..+==+*******++++.
       ..++++++===---------=+*=-=+*****#*++-...       .:*==*......:+*++:
        ..**++++++=--#@@%%%%%==+*++++++*#*++++:..     .-*+=+..    ......
         ..=**+++++-----++=--+**+++=====+**+++++:..   .:*+==:.          
          ...-*****+========+*#*++=======+**++++++:.. ..+*+==:..        
             ........:-=++++*##**++=======+*==++++*+.. ..+*+==:.        
                     .......=###*+++======+*====++++*:. ..+*+==:..      
              ....:--=++**+++=============+*=====++++*=....+*+==-..     
             ..:===++++++++++++++==========*+=====++++*=....+*++=-..    
             ..=+++**+==========++++++=====*+======+++**-....=*++=-..   
             .:=+++=*++============**+++++++*======++++**:.  .=*+==:.   
             ..=+*:*++++=============*######+=====+++++**=.  ..=*+==... 
              .....*+++++++++++=======+*####*====++++++***..  ..**+=+.. 
                  .++++=++++++++++======++**++++++++++***#:.   .:*+==:. 
                  .:*++====+**+++++++===++++++++++++++***#:.   ..**==+. 
                  ..=*+++====++**++++++++++++++++++++***#*..    .+*+=+..
                   ..-*+++====++*#*+++++++++++++++++****#-.    ..*+==+..
                    ...**++++==++*##*+++++++++++++++***#+..    ..*+==+..
                      ..:*+++++=+++##*++++++++++++++**#*..    ..=+==++. 
                        ..:+++++++++##*++++++++++++**##:..   ..=+===+.. 
                          ...++++++++##*++++++++++**##*:....:======+:.. 
                            ...=++++++***++++++++**#**+*++==--==++*..   
                         .......:=====++************++++=====++*+:..    
                       ..:==--===========******#***+++++++**+-:...      
..                     .:+++++++++++++++++*##**++==--::........         
"""
# Розділіть текст на рядки та виведіть кожен рядок окремо
lines = text.split('\n')
for line in lines:
    print(line)

global _Total
global _Left
global _Empty
global _Delete
global _Valid
_Total = 0
_Left = 0
_Empty = 0
_Delete = 0
_Valid = 0



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

    if not classes:
        return key
    
    
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


def draw_boxes(labels_array, image, classes, file):
    print(labels_array)
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
        
        alpha = 0.50
        
        
        global _Total
        global _Left
        global _Empty
        global _Delete
        global _Valid
        text = f"Total={_Total}\nLeft={_Left}\nValid={_Valid}\nEmpty={_Empty}\nDelete={_Delete}"
        y0, dy = 40, 25
        cv2.putText(image, f"File: {file}", (2, 15 ), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        for i, line in enumerate(text.split('\n')):
            y = y0 + i*dy
            cv2.putText(image, line, (2+1, y+1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            cv2.putText(image, line, (2-1, y-1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(image, line, (2, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        
        overlay = image.copy()
        
        
        cv2.line(overlay, (int(a[0]), int(a[1])), (int(b[0]), int(
            b[1])), generateColorByText(getClass(label[0], classes)), 2)
        cv2.line(overlay, (int(b[0]), int(b[1])), (int(c[0]), int(
            c[1])), generateColorByText(getClass(label[0], classes)), 2)
        cv2.line(overlay, (int(c[0]), int(c[1])), (int(d[0]), int(
            d[1])), generateColorByText(getClass(label[0], classes)), 2)
        cv2.line(overlay, (int(a[0]), int(a[1])), (int(d[0]), int(
            d[1])), generateColorByText(getClass(label[0], classes)), 2)
        
        image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
        
        
    return cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)


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
    image_files = sorted([file for file in os.listdir(image_folder) if file.endswith(('.jpg', '.jpeg', '.png', '.gif'))])
    global _Total
    global _Left
    global _Empty
    global _Delete
    global _Valid
    
    _Total = len(image_files)
    _Left = len(image_files)
    actions_queue = []
    
    file_index = 0
    while True:
        file_index = min(len(image_files)-1, file_index)
        if len(image_files)==0: break
        
        file = image_files[file_index]
        possible_label_file = os.path.join(
            label_folder,  os.path.splitext(file)[0] + ".txt")
        if os.path.exists(possible_label_file):
            words = read_label_file(possible_label_file)
            if not words:
                continue
            img = cv2.imread(os.path.join(image_folder, file))
            if img is None:
                image_files.remove(file)
                continue
            img = draw_boxes(words, img, classes,file)
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
        elif k == 97 or k == 244:#a
            actions_queue.append([os.path.join(image_folder, file),
                        os.path.join(empty_path, file)])
            _Left -=1
            _Empty +=1
            shutil.move(os.path.join(image_folder,file),os.path.join(empty_path,file))
            image_files.remove(file)
        elif k == 119 or k == 246:#w
            actions_queue.append([os.path.join(image_folder, file),
                        os.path.join(valid_path, file)])
            shutil.move(os.path.join(image_folder,file),os.path.join(valid_path,file))
            _Left-=1
            _Valid+=1
            image_files.remove(file)
        elif k == 101 or k == 243:#e
            actions_queue.append([os.path.join(image_folder, file),
                        os.path.join(alt_valid_path, file)])
            shutil.move(os.path.join(image_folder,file),os.path.join(alt_valid_path,file))
            _Left-=1
            _Valid+=1
            image_files.remove(file)
        
        elif k == 100 or k == 226:#d 
            actions_queue.append([os.path.join(image_folder, file),
                        os.path.join(deleted_path, file)])
            shutil.move(os.path.join(image_folder,file),os.path.join(deleted_path,file))
            _Left-=1
            _Delete+=1
            image_files.remove(file)
            
            
        elif k == 122 or k == 255:#z
            if (len(actions_queue) > 0):
                shutil.move(actions_queue[-1][1], actions_queue[-1][0])
                file_name = os.path.basename(actions_queue[-1][0])
                image_files.insert(0, file_name)
                file_index = max(0, file_index-1)
                actions_queue.remove(actions_queue[-1])  # z button
                _Left+=1
        elif k == 2555904:#>
            file_index = min(file_index+1, len(image_files)-1)
        elif k == 2424832:#<
            file_index = max(0, file_index-1)
        elif k == -1:
            break
        else:
            print(f"Unhandled {k} key")


def process_classes_file(path):
    with open(path, 'r') as f:
        classes = {}
        lines = f.readlines()
        print(lines)
        for index in range(len(lines)):
            classes[index] = lines[index].strip()
        print("> Classes:")
        for index, label in classes.items():
            print(f"    {index}: {label}")
        return classes



if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description='Suppa chimpa view.')
    parser.add_argument('--label_folder','-l', help='Folder containing label files')
    parser.add_argument('--image_folder','-i', help='Folder containing image files')
    
    args = parser.parse_args()
    labels = args.label_folder
    images = args.image_folder

    path = Path(os.path.abspath(images))
    parent_path = path.parent.absolute()
    valid_path = os.path.join(parent_path, "valid")
    alt_valid_path = os.path.join(parent_path, "alt_valid")
    empty_path = os.path.join(parent_path, "empty")
    deleted_path = os.path.join(parent_path, "deleted")
    
    user_permitted = False
    
    
    if not os.path.exists(valid_path):
        user_permission = input("Allow to create 4 new folders (for valid, alt_valid, empty and deleted images) (Y/N)?")
        if user_permission.lower() in ['y', 'yes']:
            user_permitted = True
        else:
            exit()
        os.makedirs(valid_path)
    if not os.path.exists(empty_path):
        if not user_permitted:
            user_permission = input("Allow to create 4 new folders (for valid, alt_valid, empty and deleted images) (Y/N)?")
            if user_permission.lower() in ['y', 'yes']:
                user_permitted = True
            else:
                exit()
        os.makedirs(empty_path)
    if not os.path.exists(alt_valid_path):
        if not user_permitted:
            user_permission = input("Allow to create 4 new folders (for valid, alt_valid, empty and deleted images) (Y/N)?")
            if user_permission.lower() in ['y', 'yes']:
                user_permitted = True
            else:
                exit()
        os.makedirs(alt_valid_path)
    if not os.path.exists(deleted_path):
        if not user_permitted:
            user_permission = input("Allow to create 4 new folders (for valid, alt_valid, empty and deleted images) (Y/N)?")
            if user_permission.lower() in ['y', 'yes']:
                user_permitted = True
            else:
                exit()
        os.makedirs(deleted_path)

    if not os.path.exists(os.path.join(labels, "classes.txt")):
        print("> No classes.txt file, i searching for predefined.txt in app folder...")
        predefined_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "predefined.txt")
        if os.path.exists(predefined_path):
            print("> predefined.txt file found, i will use it.")
            classes = process_classes_file(predefined_path)
        else:
            classes = None
    else:
        print("> classes.txt file found, i will use it.")
        classes = process_classes_file(os.path.join(labels, "classes.txt"))
    
    
    
    
    
    
    print("starting...")
    
    
    tutorpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources\\tutor.png")
    cv2.imshow(window_description, cv2.imread(tutorpath))
    cv2.waitKey(0)
    
    iterative_viewer(images, labels, classes, valid_path,
                    empty_path, deleted_path)
