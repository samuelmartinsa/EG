from PIL import Image, ImageDraw

def channel(i, c, size, startFill, stopFill):
    """calculate the value of a single color channel for a single pixel"""
    return startFill[c] + int((i * 1.0 / size) * (stopFill[c] - startFill[c]))

def color(i, size, startFill, stopFill):
    """calculate the RGB value of a single pixel"""
    return tuple([channel(i, c, size, startFill, stopFill) for c in range(3)])

def round_corner(radius):
    """Draw a round corner"""
    corner = Image.new('RGBA', (radius, radius), (0, 0, 0, 0))
    draw = ImageDraw.Draw(corner)
    draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill="blue")
    return corner

def apply_grad_to_corner(corner, gradient, backwards = False, topBottom = False):
    width, height = corner.size
    widthIter = range(width)

    if backwards:
        widthIter.reverse()

    for i in xrange(height):
        gradPos = 0
    for j in widthIter:
                if topBottom:
                    pos = (i,j)
                else:
                    pos = (j,i)
        pix = corner.getpixel(pos)
            gradPos+=1
        if pix[3] != 0:
            corner.putpixel(pos,gradient[gradPos])

    return corner

def round_rectangle(size, radius, startFill, stopFill, runTopBottom = False):
    """Draw a rounded rectangle"""
    width, height = size
    rectangle = Image.new('RGBA', size)

    if runTopBottom:
      si = height
    else:
      si = width

    gradient = [ color(i, width, startFill, stopFill) for i in xrange(si) ]

    if runTopBottom:
        modGrad = []
        for i in xrange(height):
           modGrad += [gradient[i]] * width
        rectangle.putdata(modGrad)
    else:
        rectangle.putdata(gradient*height)

    origCorner = round_corner(radius)

    # upper left
    corner = origCorner
    apply_grad_to_corner(corner,gradient,False,runTopBottom)
    rectangle.paste(corner, (0, 0))

    # lower left
    if runTopBottom: 
        gradient.reverse()
        backwards = True
    else:
        backwards = False


    corner = origCorner.rotate(90)
    apply_grad_to_corner(corner,gradient,backwards,runTopBottom)
    rectangle.paste(corner, (0, height - radius))

    # lower right
    if not runTopBottom: 
        gradient.reverse()

    corner = origCorner.rotate(180)
    apply_grad_to_corner(corner,gradient,True,runTopBottom)
    rectangle.paste(corner, (width - radius, height - radius))

    # upper right
    if runTopBottom: 
        gradient.reverse()
        backwards = False
    else:
        backwards = True

    corner = origCorner.rotate(270)
    apply_grad_to_corner(corner,gradient,backwards,runTopBottom)
    rectangle.paste(corner, (width - radius, 0))

    return rectangle

img = round_rectangle((200, 200), 70, (255,0,0), (0,255,0), True)
img.save("test.png", 'PNG')