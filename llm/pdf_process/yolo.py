import os
import torch
import math

import numpy as np
from PIL import Image

class Paper:
    def __init__(self):
        self.pages = []  # 实例属性，每个 Paper 对象有独立的 pages 列表

    class Page:
        def __init__(self):
            self.figures = []  # 每个 Page 对象有独立的 figures 列表
            self.graphs = []   # 每个 Page 对象有独立的 graphs 列表
            self.formulas = [] # 每个 Page 对象有独立的 formulas 列表

        class Caption:
            def __init__(self):
                self.bbox = []
                self.iamge = []
                self.location = []

        class Figure:
            def __init__(self):
                self.image = None  # 初始化为 None 或其他适当类型
                self.bbox = []
                self.caption = []

        class Graph:
            def __init__(self):
                self.image = None  # 初始化为 None 或其他适当类型
                self.bbox = []
                self.caption = []

        class Formula:
            def __init__(self):
                self.image = None  # 初始化为 None 或其他适当类型
                self.bbox = []
    
class LayoutDetectionYOLO:

    def __init__(self, model_path):
        """
        Initialize the LayoutDetectionYOLO class.

        Args:
            config (dict): Configuration dictionary containing model parameters.
        """
        # Mapping from class IDs to class names
        self.id_to_names = {
            0: 'title', 
            1: 'plain text',
            2: 'abandon', 
            3: 'figure', 
            4: 'figure_caption', 
            5: 'table', 
            6: 'table_caption', 
            7: 'table_footnote', 
            8: 'isolate_formula', 
            9: 'formula_caption'
        }

        # Load the YOLO model from the specified path
        try:
            from doclayout_yolo import YOLOv10
            self.model = YOLOv10(model_path)
        except AttributeError:
            from ultralytics import YOLO
            self.model = YOLO(model_path)

        # Set model parameters
        self.img_size = 1280
        self.conf_thres = 0.25
        self.iou_thres = 0.45
        self.visualize = True
        self.nc = 10
        self.workers = 8
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu' 
        if self.iou_thres > 0:
            import torchvision
            self.nms_func = torchvision.ops.nms

    def predict(self, images, image_ids=None):
        """
        Predict formulas in images.

        Args:
            images (list): List of images to be predicted.
            result_path (str): Path to save the prediction results.
            image_ids (list, optional): List of image IDs corresponding to the images.

        Returns:
            list: List of prediction results.
        """
        this_paper=Paper()
        results = []
        for idx, image in enumerate(images):
            this_page=this_paper.Page()
            result = self.model.predict(image, imgsz=self.img_size, conf=self.conf_thres, iou=self.iou_thres, verbose=False, device=self.device)[0]
            if self.visualize:
                boxes = result.__dict__['boxes'].xyxy
                classes = result.__dict__['boxes'].cls
                scores = result.__dict__['boxes'].conf

                if self.iou_thres > 0:
                    indices = self.nms_func(boxes=torch.Tensor(boxes), scores=torch.Tensor(scores),iou_threshold=self.iou_thres)
                    boxes, scores, classes = boxes[indices], scores[indices], classes[indices]
                    if len(boxes.shape) == 1:
                        boxes = np.expand_dims(boxes, 0)
                        scores = np.expand_dims(scores, 0)
                        classes = np.expand_dims(classes, 0)
                # Determine the base name of the image
                if image_ids:
                    base_name = image_ids[idx]
                else:
                    # base_name = os.path.basename(image)
                    base_name = os.path.splitext(os.path.basename(image))[0]  # Remove file extension
                
                result_name = f"{base_name}_layout.png"
                fig=[]
                fig_cap=[]
                graph=[]
                graph_cap=[]
                formula=[]
                formula_cap=[]
                
                for i in range(0,len(boxes)):
                    if int(classes[i].item())==3 or int(classes[i].item())==4:
                        if int(classes[i].item())==3 :
                            this_figure= this_page.Figure()
                            this_page.figures.append(this_figure)
                            fig.append(list(map(int, boxes[i])))
                        if int(classes[i].item())==4 :
                            fig_cap.append(list(map(int, boxes[i])))
                    elif int(classes[i].item())==5 or int(classes[i].item())==6 or int(classes[i].item())==7:
                        if int(classes[i].item())==5 :
                            this_figure= this_page.Graph()
                            this_page.graphs.append(this_figure)
                            graph.append(list(map(int, boxes[i])))
                        if int(classes[i].item())==6 or  int(classes[i].item())==7:
                            graph_cap.append(list(map(int, boxes[i])))
                    if int(classes[i].item())==8 or int(classes[i].item())==9:
                        if int(classes[i].item())==8 :
                            this_figure= this_page.Formula()
                            this_figure.bbox=list(map(int, boxes[i]))
                            this_page.formulas.append(this_figure)
                            formula.append(list(map(int, boxes[i])))
                        if int(classes[i].item())==9 :
                            formula_cap.append(list(map(int, boxes[i])))                    
                if len(fig_cap)>0:
                    for id,item in enumerate(fig_cap):
                        mid = []
                        x_min, y_min, x_max, y_max= map(int, item)
                        for figs in fig:
                            mid.append(((figs[0]+figs[2])/2,(figs[1]+figs[3])/2,math.sqrt((figs[2]-figs[0])**2+(figs[3]-figs[1])**2)))
                        if len(fig)>0:
                            mins=math.sqrt((mid[0][0]-(x_max+x_min)/2)**2+(mid[0][1]-(y_max+y_min)/2)**2)-mid[0][2]
                            ptr=0
                            
                            for i in range(1,len(mid)):
                                temp=math.sqrt((mid[i][0]-(x_max+x_min)/2)**2+(mid[i][1]-(y_max+y_min)/2)**2)-mid[i][2]
                                if temp<mins:
                                    mins=temp
                                    this_page.figures[i]
                                    ptr=i
                            pos=1
                            if y_max<fig[ptr][1]: pos=1
                            if y_min>fig[ptr][3]: pos=0
                            if x_min<fig[ptr][0]: fig[ptr][0]=x_min
                            if y_min<fig[ptr][1]: fig[ptr][1]=y_min
                            if x_max>fig[ptr][2]: fig[ptr][2]=x_max
                            if y_max>fig[ptr][3]: fig[ptr][3]=y_max  
                            captions=this_page.Caption()   
                            captions.bbox=list(map(int, item))
                            captions.location=[id,pos]
                            this_page.figures[ptr].caption.append(captions)
                            this_page.figures[ptr].bbox=fig[ptr]                
                if len(graph_cap)>0:
                    for id,item in enumerate(graph_cap):
                        mid = []
                        x_min, y_min, x_max, y_max= map(int, item)
                        for figs in graph:
                            mid.append(((figs[0]+figs[2])/2,(figs[1]+figs[3])/2,math.sqrt((figs[2]-figs[0])**2+(figs[3]-figs[1])**2)))
                        if len(graph)>0:
                            mins=math.sqrt((mid[0][0]-(x_max+x_min)/2)**2+(mid[0][1]-(y_max+y_min)/2)**2)-mid[0][2]
                            ptr=0
                            for i in range(1,len(mid)):
                                temp=math.sqrt((mid[i][0]-(x_max+x_min)/2)**2+(mid[i][1]-(y_max+y_min)/2)**2)-mid[i][2]
                                if temp<mins:
                                    mins=temp
                                    ptr=i
                            pos=1
                            if y_max<graph[ptr][1]: pos=1
                            if y_min>graph[ptr][3] or y_min>graph[ptr][1]: pos=0
                            if x_min<graph[ptr][0]: graph[ptr][0]=x_min
                            if y_min<graph[ptr][1]: graph[ptr][1]=y_min
                            if x_max>graph[ptr][2]: graph[ptr][2]=x_max
                            if y_max>graph[ptr][3]: graph[ptr][3]=y_max    
                            captions=this_page.Caption()   
                            captions.bbox=list(map(int, item))
                            captions.location=[id,pos]                            
                            this_page.graphs[ptr].caption.append(captions)
                            this_page.graphs[ptr].bbox=graph[ptr]                 
                if len(fig)>0:
                    for id,item  in enumerate(fig):
                        figs = image.crop(item)
                        this_page.figures[id].image=figs
                if len(graph)>0:
                    for id,item in enumerate(graph):
                        figs = image.crop(item)
                        this_page.graphs[id].image=figs
                if len(formula)>0:
                    for id,item in enumerate(formula):
                        figs = image.crop(item)
                        this_page.formulas[id].image=figs
                # 按任意键退出显示imshow("Cropped Masked Region", graph)        
                # 按任意键退出显示
                
            this_paper.pages.append(this_page)
        return this_paper
    
    def create_mask(self,image_shape, top_left, bottom_right):
        """
        创建一个给定区域的掩码。
        
        :param image_shape: 图像尺寸 (height, width)
        :param top_left: 左上角坐标 (x1, y1)
        :param bottom_right: 右下角坐标 (x2, y2)
        :return: 掩码 (numpy array)
        """
        height, width = image_shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        
        x1, y1 = top_left
        x2, y2 = bottom_right
        
        mask[y1:y2, x1:x2] = 1  # 设置区域为 1
        return mask
