#!/usr/bin/env python3

import sys
import math
import base64
import tkinter

from io import BytesIO
from PIL import Image as Image

# NO ADDITIONAL IMPORTS ALLOWED!


def get_pixel(image, x, y):
    if x < 0:
        x = 0
    elif x > image['width'] - 1:
        x = image['width'] - 1
    if y < 0:
        y = 0
    elif y > image['height'] - 1:
        y = image['height'] - 1
    return image['pixels'][y * image['width'] + x] # list index has to be int or slice


def set_pixel(image, x, y, c):
    image['pixels'][y * image['width'] + x] = c # list index has to be int or slice


def apply_per_pixel(image, func):
    result = {
        'height': image['height'],
        'width': image['width'],
        'pixels': [None] * (image['height'] * image['width']), # initialize w x h size array
    }
    for x in range(image['width']):
        for y in range(image['height']):
            color = get_pixel(image, x , y)
            newcolor = func(color)
            set_pixel(result, x, y, newcolor) # y, x to x, y and indentation
    return result


def inverted(image):
    return apply_per_pixel(image, lambda c: 255-c) # 256 to 255



# HELPER FUNCTIONS

def correlate(image, kernel):
    """
    Compute the result of correlating the given image with the given kernel.

    The output of this function should have the same form as a 6.009 image (a
    dictionary with 'height', 'width', and 'pixels' keys), but its pixel values
    do not necessarily need to be in the range [0,255], nor do they need to be
    integers (they should not be clipped or rounded at all).

    This process should not mutate the input image; rather, it should create a
    separate structure to represent the output.

    The kernel is a square with an odd number of rows and columns and
    is represented as a 1-D list containing n*n elements.
    """
    
    # Initialize new image    
    new_image = {
            'height': image['height'], 
            'width': image['width'], 
            'pixels': [i for i in image['pixels']]
                }
    
    # Modify pixels (x corresponds to height/rows, y corresponds to width/columns)
    for x in range(image['width']):
        for y in range(image['height']):
            
            # Get size of kernel
            n = int(math.sqrt(len(kernel)))
            image_portion = []
            half_length = n // 2
            for i in range(-half_length, half_length + 1):
                for j in range(-half_length, half_length + 1):
                    image_portion.append(get_pixel(image, x + j, y + i))
                    
            # Compute correlate values for each pixel
            correlate_values = [a*b for a,b in zip(image_portion, kernel)]          
            new_pixel_value = sum(correlate_values)
            set_pixel(new_image, x, y, new_pixel_value)
            
    return new_image
  

def round_and_clip_image(image):
    """
    Given a dictionary, ensure that the values in the 'pixels' list are all
    integers in the range [0, 255].

    All values should be converted to integers using Python's `round` function.

    Any locations with values higher than 255 in the input should have value
    255 in the output; and any locations with values lower than 0 in the input
    should have value 0 in the output.
    """
    
    new_pixels = []
    
    # Clip out of range values
    for p in image['pixels']:
        if p > 255:
            p = 255   
        elif p < 0:
            p = 0
        
        # Round final values
        new_pixels.append(round(p))
        
    return {'height': image['height'], 
            'width': image['width'], 
            'pixels': new_pixels}
        

def box_blur_kernel(n):
    return [1 / (n**2)] * n**2

# FILTERS

def blurred(image, n):
    """
    Return a new image representing the result of applying a box blur (with
    kernel size n) to the given input image.

    This process should not mutate the input image; rather, it should create a
    separate structure to represent the output.
    """
    # first, create a representation for the appropriate n-by-n kernel (you may
    # wish to define another helper function for this)
    kernel = box_blur_kernel(n)

    # then compute the correlation of the input image with that kernel
    blurred_image = correlate(image, kernel) # shouldn't mutate because i copy in correlate, right?

    # and, finally, make sure that the output is a valid image (using the
    # helper function from above) before returning it.
    return round_and_clip_image(blurred_image)


def sharpened(i, n):
    """
    Return a new image representing the result of applying 2I−B 
    (where I is the original pixel value and B is the blurred version of it), 
    with kernel size n, to the given input image.
    """
    # Blur the image, but do not round/clip values
    kernel = box_blur_kernel(n)
    blurred_i = correlate(i, kernel)
    
    # Apply formula to each pixel
    sharpened_color_list = []
    for p in range(len(i['pixels'])):
        color = i['pixels'][p]
        sharpened_color = (2 * color) - blurred_i['pixels'][p]
        sharpened_color_list.append(sharpened_color)
    result = {'height': i['height'], 
            'width': i['width'], 
            'pixels': sharpened_color_list}
    
    # Round and clip 
    return round_and_clip_image(result)



def edges(i):
    Kx = [-1, 0, 1,
          -2, 0, 2,
          -1, 0, 1]
    Ky = [-1, -2, -1,
          0, 0, 0,
          1, 2, 1]
    i_Kx = correlate(i, Kx)
    i_Ky = correlate(i, Ky)
    
    # Apply formula to each pixel
    new_color_list = []
    for p in range(len(i['pixels'])):
        new_color = round(math.sqrt((i_Kx['pixels'][p] ** 2) + (i_Ky['pixels'][p] ** 2)))
        new_color_list.append(new_color)
        
    result = {'height': i['height'], 
            'width': i['width'], 
            'pixels': new_color_list}
    
    # Round and clip 
    return round_and_clip_image(result)
    

# HELPER FUNCTIONS FOR LOADING AND SAVING IMAGES

def load_image(filename):
    """
    Loads an image from the given file and returns a dictionary
    representing that image.  This also performs conversion to greyscale.

    Invoked as, for example:
       i = load_image('test_images/cat.png')
    """
    with open(filename, 'rb') as img_handle:
        img = Image.open(img_handle)
        img_data = img.getdata()
        if img.mode.startswith('RGB'):
            pixels = [round(.299 * p[0] + .587 * p[1] + .114 * p[2])
                      for p in img_data]
        elif img.mode == 'LA':
            pixels = [p[0] for p in img_data]
        elif img.mode == 'L':
            pixels = list(img_data)
        else:
            raise ValueError('Unsupported image mode: %r' % img.mode)
        w, h = img.size
        return {'height': h, 'width': w, 'pixels': pixels}


def save_image(image, filename, mode='PNG'):
    """
    Saves the given image to disk or to a file-like object.  If filename is
    given as a string, the file type will be inferred from the given name.  If
    filename is given as a file-like object, the file type will be determined
    by the 'mode' parameter.
    """
    out = Image.new(mode='L', size=(image['width'], image['height']))
    out.putdata(image['pixels'])
    if isinstance(filename, str):
        out.save(filename)
    else:
        out.save(filename, mode)
    out.close()


if __name__ == '__main__':
    # code in this block will only be run when you explicitly run your script,
    # and not when the tests are being run.  this is a good place for
    # generating images, etc.
    
    #### 2.2 Test: Testing load and save functions ####
#    i = load_image('test_images/tree.png')
#    new_i = save_image(i, 'test_images/bwtree.png', mode='PNG')
    
  #######################################################
      
    #### 3.3 Test: Testing the inversion filter ####
#     i = load_image('test_images/bluegill.png')
#     inverted_i = inverted(i)
#     new_i = save_image(inverted_i, 'test_images/inverted_bluegill.png', mode='PNG')
    
  #######################################################
  
    #### 4.3 and 4.4 Tests: Testing the correlate function with different kernels ####
#    
#    test_kernel = [0, 0, 0, 0, 1, 0, 0, 0, 0] # identity_kernel
#    
#    test_kernel = [0.0, 0.2, 0.0, 0.2, 0.2, 0.2, 0.0, 0.2, 0.0] # average_kernel
#    
#    test_kernel = [
#    0, 0, 0, 0, 0, 0, 0, 0, 0, 
#    0, 0, 0, 0, 0, 0, 0, 0, 0, 
#    1, 0, 0, 0, 0, 0, 0, 0, 0, 
#    0, 0, 0, 0, 0, 0, 0, 0, 0, 
#    0, 0, 0, 0, 0, 0, 0, 0, 0,
#    0, 0, 0, 0, 0, 0, 0, 0, 0,
#    0, 0, 0, 0, 0, 0, 0, 0, 0,
#    0, 0, 0, 0, 0, 0, 0, 0, 0,
#    0, 0, 0, 0, 0, 0, 0, 0, 0]
#    
#    i = load_image('test_images/pigbird.png')
#    new_i = correlate(i, test_kernel) 
#    new_i = round_and_clip_image(new_i)
#    save_image(new_i, 'test_images/correlated_pigbird.png', mode='PNG')
    
  #######################################################
  
    #### 5.1.1 Test: Testing the blurred function with kernel of size 5 ####
#     i = load_image('test_images/cat.png')
#     n = 5
#     blurred_i = blurred(i, n)
#     new_i = save_image(blurred_i, 'test_images/blurred_cat.png', mode='PNG')
    
  #######################################################
  
    #### 5.2.1 Test: Testing the sharpened function with kernel of size 11 #### 
    # test_images/python.png
#    i = load_image('test_images/python.png')
#    n = 11
#    sharpened_i = sharpened(i, n)
#    new_i = save_image(sharpened_i, 'test_images/sharpened_python.png', mode='PNG')
    
  #######################################################
   
    #### 6.1 Test: Testing the edges function #### 
    i = load_image('test_images/construct.png')
    edges_i = edges(i)
    new_i = save_image(edges_i, 'test_images/edges_construct.png', mode='PNG')
        
  #######################################################
   
    
#    i = {'height': 3, 'width': 3, 'pixels': [0] * 9}
#    i['pixels'][1] = 5
#    kernel = [1] * 9
#    new_i = correlate(i, kernel) 
#    print(new_i)
    
    pass