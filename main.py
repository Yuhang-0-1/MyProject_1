from aip import AipOcr
import cv2
import numpy as np
import os

# 保存需要识别图像的绝对路径
path = 'E:/Stowage_1.jpg'

# 保存船舶积载图中甲板以上的列、层号数组
up_row = ['10','08','06','04','02','00','01','03','05','07','09']
up_tier = ['90','88','86','84','82']

# 保存船舶积载图中甲板以下的列、层号数组
down_row = ['08','06','04','02','01','03','05','07']
down_tier = ['10','08','06','04','02']

# 将百度App_ID, API_Key, Secret_Key写入以调用百度光学字符识别引擎
APP_ID = '19635341'
API_KEY = 's6zIhnLEHwveYgEGh9CODyg6'
SECRET_KEY = 'gb3RjkMkLR2RXKlQ2aV02zP1Ehp03wsW'
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

# 定义识别引擎读取图片文件的函数
def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        return fp.read()

# 读取图片文件
image = get_file_content(path)

# 识别图片字符信息，返回格式为字典类型
ret = client.basicGeneral(image)

# 获取目标字符串
text = list(ret['words_result'][0].values())[-1]

# 对目标字符串切片，得到倍号
for i in range(len(text)):
    if text[i] == 'Y':
        i = i + 1
        break
bay_number = text[i + 1]+text[i + 2]

# 判断某位置上是否存在集装箱
def IsExist(text):
    for i in range(len(text)):
        # 若识别到的单元格目标字符串信息含有字符'G'，则表示该位置上存在集装箱
        if (text[i] == 'G'):
            return 1

# 识别列、层号，需确定每个集装箱的相对位置，需将表格图像切割为单元格逐个分析
# 图像处理模块Python-OpenCV读入图片
raw = cv2.imread(path, 1)

# 图片灰度化
gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)

# 图片二值化
binary = cv2.adaptiveThreshold(~gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY, 35, -5)

rows , tiers = binary.shape
# 识别横线(scale = 18)
# 定义识别横线的结构元素
kernel_1 = cv2.getStructuringElement(cv2.MORPH_RECT, (rows // 18, 1))
# 腐蚀，输出的像素值是横线结构元素覆盖下输入图像的最小像素值
eroded_1 = cv2.erode(binary, kernel_1, iterations = 1)
# 膨胀，输出的像素值是横线结构元素覆盖下输入图像的最大像素值
dilated_row = cv2.dilate(eroded_1, kernel_1, iterations = 1)

# 识别竖线(scale = 13)
# 定义识别竖线的结构元素
kernel_2 = cv2.getStructuringElement(cv2.MORPH_RECT, (1,tiers // 13))
# 腐蚀，输出的像素值是竖线结构元素覆盖下输入图像的最小像素值
eroded_2 = cv2.erode(binary, kernel_2, iterations = 1)
# 膨胀，输出的像素值是竖线结构元素覆盖下输入图像的最大像素值
dilated_tier = cv2.dilate(eroded_2, kernel_2, iterations = 1)

# 对图像的每个像素值进行“与”操作，只有1 & 1 = 1，其余皆为0
bitwise_and = cv2.bitwise_and(dilated_row, dilated_tier)

# 将横竖线共同呈现在一张图片中
merge = cv2.add(dilated_row, dilated_tier)

# 两张图片进行减法运算，去掉表格框线
merge2 = cv2.subtract(binary, merge)

# 定义矩形结构元素（滤波器）
new_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
# 滤波，开运算(先腐蚀后膨胀)用于移除由图像噪音形成的斑点（闭运算用来连接被误分为许多小块的对象）
erode_image = cv2.morphologyEx(merge2, cv2.MORPH_OPEN, new_kernel)

# 合并点阵图及滤波过后的图像，便于后续操作
merge3 = cv2.add(erode_image, bitwise_and)
# 保存中间文件，以便后续操作
cv2.imwrite('E:/picture.jpg',merge3)

# 将焦点标识取出来
xs, ys = np.where(bitwise_and > 0)

# 记录各单元格顶点的横、纵坐标数组
x_point = []
y_point = []

# 通过排序，排除掉相近的像素点，只取相近值的最后一点
sort_x_point = np.sort(xs)
sort_y_point = np.sort(ys)

# 得到列号数组
for i in range(0,len(sort_x_point) - 1,1):
    if (sort_x_point[i + 1] - sort_x_point[i] > 10):
        x_point.append(sort_x_point[i])
# 要将最后一个点加入
x_point.append(sort_x_point[i])

#得到层号数组
for j in range(0,len(sort_y_point) - 1,1):
    if (sort_y_point[j + 1] - sort_y_point[j] > 10):
        y_point.append(sort_y_point[j])
# 要将最后一个点加入
y_point.append(sort_y_point[j])
# print(x_point)
# print(y_point)

y1_point = []
y2_point = []
# 得到y1数组
for i in range(0,len(y_point),1):
    if (i == 0):
        y1_point.append(y_point[i])
    elif (i < 10 and i % 2 != 0):
        y1_point.append(y_point[i])
    elif (i > 11 and i % 2 == 0):
        y1_point.append(y_point[i])
y1_point.append(y_point[i])

# 得到y2数组
for i in range(0,len(y_point) - 1):
    if y_point[i] not in y1_point:
        y2_point.append(y_point[i])
# print(y1_point)
# print(y2_point)

# 统计空单元格
count = 0

# 循环x坐标，y坐标分割表格
for i in range(0,len(x_point) - 1,1):
    # 分割集装箱船甲板以上的箱区位置
    if (i < 5):
        for j in range(0,len(y1_point) - 1,1):
            # 在分割时，第一个参数为x坐标，第二个参数为y坐标
            cell = merge3[x_point[i]:x_point[i + 1], y1_point[j]:y1_point[j + 1]]
            # print(bay_number + up_row[j] + up_tier[i])
            # 识别单元格内容
            path = 'E:/box_' + str(i) + str(j) + '.jpg'
            cv2.imwrite(path,cell)
            image = get_file_content(path)
            ret = client.basicGeneral(image)
            try:
                text = list(ret['words_result'][0].values())[-1]
                if (IsExist(text) == 1):
                    print("箱位号：" + bay_number + up_row[j] + up_tier[i])
            except:
                count = count + 1
            # 删除中间图片文件
            os.remove(path)

    # 分割集装箱船甲板以下的箱区位置
    elif (i > 5):
        for j in range(0,len(y2_point) - 1,1):
            # 分割左舷箱区
            if (j < 4):
                # 在分割时，第一个参数为x坐标，第二个参数为y坐标
                cell = merge3[x_point[i]:x_point[i + 1], y2_point[j]:y2_point[j + 1]]
                # print(bay_number + down_row[j] + down_tier[i - 6])
                # 识别单元格内容
                path = 'E:/box_' + str(i) + str(j) + '.jpg'
                cv2.imwrite(path, cell)
                image = get_file_content(path)
                ret = client.basicGeneral(image)
                try:
                    text = list(ret['words_result'][0].values())[-1]
                    if (IsExist(text) == 1):
                        print("箱位号：" + bay_number + down_row[j] + down_tier[i - 6])
                except:
                    count = count  + 1
                # 删除中间图片文件
                os.remove(path)

            # 分割右舷箱区
            elif (j > 4):
                # 在分割时，第一个参数为x坐标，第二个参数为y坐标
                cell = merge3[x_point[i]:x_point[i + 1], y2_point[j]:y2_point[j + 1]]
                # print(bay_number + down_row[j - 1] + down_tier[i - 6])
                # 识别单元格内容
                path = 'E:/box_' + str(i) + str(j) + '.jpg'
                cv2.imwrite(path, cell)
                image = get_file_content(path)
                ret = client.basicGeneral(image)
                try:
                    text = list(ret['words_result'][0].values())[-1]
                    if (IsExist(text) == 1):
                        print("箱位号：" + bay_number + down_row[j - 1] + down_tier[i - 6])
                except:
                    count = count + 1
                # 删除中间图片文件
                os.remove(path)

print(count)
