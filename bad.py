import cv2
import numpy as np
import math
from skimage.draw import line
from matplotlib import image as Image


def loadImg(path):
    return cv2.imread(path)


def calc(img, result):
    suma = 0
    count = 0
    for i in range(len(img)):
        for j in range(len(img[i])):
            suma += (img[i][j][0] / 255 - result[i][j][0]) ** 2
            count += 1
    print("Suma = ", suma)
    print("Count = ", count)
    print("Błąd = ", suma / count)
    return suma / count


def generate(size):
    tab = []
    for i in range(size):
        if i == size // 2:
            tab.append(1)
        else:
            if abs(i - size / 2) % 2 == 0:
                tab.append(0)
            else:
                tab.append(-4 / math.pi ** 2 * (1 / (abs(i - size // 2) ** 2)))
    return tab


def generateSinogram(img, imgSize, alpha, n, l, name, f):
    steps = int(360 / alpha) + 1
    r = (imgSize[0] ** 2 + imgSize[1] ** 2) ** 0.5 / 2
    print(imgSize)
    result = np.zeros(imgSize)
    sinogram = np.zeros((steps, n, 3))
    stepsTabs = []
    kernel = generate(n)
    for i in range(steps):
        fi = i * alpha
        x0 = int(r * math.cos(math.radians(fi)) + imgSize[1] / 2)
        y0 = int(r * math.sin(math.radians(fi)) + imgSize[0] / 2)

        sumTab = []
        xTabs = []
        yTabs = []
        for j in range(n):

            x1 = int(r * math.cos(math.radians(fi) + math.pi - (math.radians(l) / 2) +
                                  j * (math.radians(l) / (n - 1))) + imgSize[1] / 2)
            y1 = int(r * math.sin(math.radians(fi) + math.pi - (math.radians(l) / 2) +
                                  j * (math.radians(l) / (n - 1))) + imgSize[0] / 2)

            xtab, ytab = line(x0, y0, x1, y1)

            suma = 0
            count = 0
            for k in range(len(xtab)):
                point = (xtab[k], ytab[k])
                if 0 <= point[0] < imgSize[1] and 0 <= point[1] < imgSize[0]:
                    suma += img[point[1]][point[0]][0]
                    count += 1
            if count != 0:
                suma /= count
            sumTab.append(suma)
            xTabs.append(xtab)
            yTabs.append(ytab)
        if f:
            sumTab1 = np.convolve(sumTab, kernel, "same")
        else:
            sumTab1 = sumTab
        for a in range(len(sumTab)):
            suma = sumTab[a] / 255
            sinogram[i][a] += [suma, suma, suma]
            suma = sumTab1[a] / 255
            suma = suma
            xtab = xTabs[a]
            ytab = yTabs[a]
            for k in range(len(xtab)):
                point = (xtab[k], ytab[k])
                if imgSize[1] > point[0] >= 0 <= point[1] < imgSize[0]:
                    result[point[1]][point[0]] += [suma, suma, suma]
                    """if result[point[1]][point[0]][0] > 1:
                        result[point[1]][point[0]] = [1, 1, 1]
                    if result[point[1]][point[0]][0] < 0:
                        result[point[1]][point[0]] = [0, 0, 0]"""
        if fi % 1 == 0:
            print("Angle = ", fi, " n = ", n, " alpha = ", alpha, " l = ", l)
    result = normalizeAll(result)
    if alpha % 1 != 0:
        alpha = steps
    Image.imsave('bad/' + name +'/result_no_correction_' + str(n) + '_' + str(alpha) + '_' + str(l) + '.png', result)
    result = filter(result, 3, 3)
    sinogram = normalizeAll(sinogram)
    Image.imsave('bad/' + name + '/sinogram_' + str(n) + '_' + str(alpha) + '_' + str(l) + '.png', sinogram)
    Image.imsave('bad/' + name +'/result_filtered_' + str(n) + '_' + str(alpha) + '_' + str(l) + '.png', result)
    error = calc(img, result)
    print("Error = ", error, " n = ", n, " alpha = ", alpha, " l = ", l)
    f = open("bad/" + name + "/wyniki.txt", "a+")
    wyn = str(n) + '; ' + str(alpha) + '; ' + str(l) + '; ' + str(error) + "\n"
    f.write(wyn)
    f.close()
    return


def normalizeAll(sumTab):
    mX = 0
    mI = 255
    for i in sumTab:
        for j in i:
            mX = max(mX, j[0])
            mI = min(mI, j[0])
    print("Max = ", mX, " Min = ", mI)
    if mX != 0:
        for i in range(len(sumTab)):
            for j in range(len(sumTab[i])):
                for a in range(3):
                    sumTab[i][j][a] = (sumTab[i][j][a] - mI) / (mX - mI)
    return sumTab

def filter(result, n, size):
    mask = np.ones((size, size))
    l = 0
    for i in mask:
        for j in i:
            l += j
    if l == 0:
        return
    for a in range(n):
        for i in range(len(result)):
            for j in range(len(result[0])):
                if i - int(len(mask) / 2) >= 0 and i + int(len(mask) / 2) < len(result) \
                        and j - int(len(mask[0]) / 2) >= 0 and j + int(len(mask[0]) / 2) < len(result[0]):
                    sum = 0
                    for a in range(-int(len(mask) / 2), int(len(mask) / 2) + 1):
                        for b in range(-int(len(mask) / 2), int(len(mask) / 2) + 1):
                            sum += result[i + a][j + b][0] * mask[a + 1][b + 1]
                    result[i][j] = sum / l
    return result



if __name__ == '__main__':

    img = loadImg("zdj/Shepp_logan.jpg")
    imgSize = (len(img), len(img[0]), len(img[0][0]))
    generateSinogram(img, imgSize, 1, 360, 270, "filter", True)

    img = loadImg("zdj/Shepp_logan.jpg")
    imgSize = (len(img), len(img[0]), len(img[0][0]))
    generateSinogram(img, imgSize, 1, 360, 270, 'nonfilter', False)

    """f = open("bad/alpha/wyniki.txt", "w+")
    wyn = 'n; alpha; l; error\n'
    f.write(wyn)
    f.close()
    #todo poprawic 360/540, 360/630
    tab = [360 / 540, 360 / 630]
    #tab = [4, 2, 1, 0.5]
    for alpha in tab:
        img = loadImg("zdj/Shepp_logan.jpg")
        imgSize = (len(img), len(img[0]), len(img[0][0]))
        generateSinogram(img, imgSize, alpha, 180, 180, "alpha")

    f = open("bad/n/wyniki.txt", "w+")
    f.write(wyn)
    f.close()

    for n in range(720, 721, 90):
        img = loadImg("zdj/Shepp_logan.jpg")
        imgSize = (len(img), len(img[0]), len(img[0][0]))
        generateSinogram(img, imgSize, 2, n, 180, "n")"""

    """f = open("bad/l/wyniki.txt", "w+")
    f.write(wyn)
    f.close()"""

    """for l in range(270, 271, 45):
        img = loadImg("zdj/Shepp_logan.jpg")
        imgSize = (len(img), len(img[0]), len(img[0][0]))
        generateSinogram(img, imgSize, 2, 180, l, "l")"""