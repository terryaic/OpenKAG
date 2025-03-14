from .pdf_process import yolo
from .pdf_process import task
from settings import PDF_MODEL_PATH

def pdf_process(input_file):
    # get input and output path from config
    dect=task.LayoutDetectionTask(yolo.LayoutDetectionYOLO(PDF_MODEL_PATH))
    detection_results = dect.predict_pdfs(input_file)

    return detection_results
    
if __name__ == "__main__":
    result = pdf_process("/home/turing/Downloads/resnet-1.pdf")
    print("结果是：")
    print(result)

