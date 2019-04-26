# Usage: python gplust_ensemble.py -i /home/images -o /home/output
# import the necessary packages
from PIL import Image
import pytesseract
import io
import argparse
import cv2
import os
import glob
import numpy as np
from pytesseract import Output

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="My_First_Project.json"

def detect_text(path):
    """Detects text in the file."""
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)
    response = client.document_text_detection(image=image)
    document = response.full_text_annotation
    transcripts = ""
    count = 0
    confidences = []
    numChars = []
    avg_confidence = -1
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    count = count + 1
                    word_text = ''.join([
                        symbol.text for symbol in word.symbols
                        ])
                    if( count == 1 or Slash_Flag == 1 or word_text == "/" or word_text == "-" ):
                        transcripts = transcripts + word_text
                    else:
                        transcripts = transcripts + " " + word_text
                    if( word_text == "/" or word_text == "-"):
                        Slash_Flag = 1;
                    else:
                        Slash_Flag = 0;
                    confidences.append(word.confidence)
                    numChars.append(len(word_text))

    if confidences != []:
        avg_confidence = np.average(confidences, weights=numChars)
    return (transcripts, avg_confidence);

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input_dir", help="Input directory for the files to be modified")
ap.add_argument("-o", "--output_dir", help="Output directory for the files to be modified")
args = vars(ap.parse_args())

input_dir = args["input_dir"]
output_dir = args["output_dir"]

im_names = sorted(glob.glob(os.path.join(input_dir, '*.png')))

# load the image as a PIL/Pillow image, apply OCR, and then delete
# the temporary file

langs = ['5x5_Dots_FT_500', 'dotOCRDData1', 'Dotrice_FT_500', 'DotMatrix_FT_500'] 

for im_name in im_names:
    file_name = os.path.basename(im_name).split('.')[0]
    file_name = file_name.split()[0]
    print(file_name)
    print('\n')
    avg_confidences = []
    (G_text, G_avg_confidence) = detect_text(im_name)
    G_avg_confidence = 100*G_avg_confidence
    avg_confidences.append(G_avg_confidence)
    for i in range(len(langs)):
        data = pytesseract.image_to_data(Image.open(im_name), lang = langs[i], config='--psm 7', output_type=Output.DICT)
        debug = pytesseract.image_to_data(Image.open(im_name), lang = langs[i], config='--psm 7')
        text = data['text']
        confidences = []
        numChars = []

        for j in range(len(text)):
            if int(data['conf'][j]) > -1:
                confidences.append(int(data['conf'][j]))
                numChars.append(len(text[j]))

        if confidences != []:
            avg_confidences.append(np.average(confidences, weights=numChars))
        else:
            avg_confidences.append(-1)
    save_path = os.path.join(output_dir, file_name + ".txt")
    best = avg_confidences.index(max(avg_confidences))
    if best > 0:
        text = pytesseract.image_to_string(Image.open(im_name), lang = langs[best-1], config='--psm 7')
    else:
        text = G_text
    f = open(save_path, "w")
    f.write(text)
    f.write('\n')
    print(text)
    print('\n')
    print(best)
    print('\n')
    print(avg_confidences[best])
    print('\n')
