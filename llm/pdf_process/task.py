from .base_task import BaseTask
from .yolo import LayoutDetectionYOLO

__all__ = [
    "LayoutDetectionYOLO",
    # "LayoutDetectionLayoutlmv3",
]
class LayoutDetectionTask(BaseTask):
    def __init__(self, model):
        super().__init__(model)

    def predict_images(self, input_data, result_path):
        """
        Predict layouts in images.

        Args:
            input_data (str): Path to a single image file or a directory containing image files.
            result_path (str): Path to save the prediction results.

        Returns:
            list: List of prediction results.
        """
        images = self.load_images(input_data)
        # Perform detection
        return self.model.predict(images, result_path)

    def predict_pdfs(self, input_data):
        """
        Predict layouts in PDF files.

        Args:
            input_data (str): Path to a single PDF file or a directory containing PDF files.
            result_path (str): Path to save the prediction results.

        Returns:
            list: List of prediction results.
        """
        pdf_images = self.load_pdf_images(input_data)
        # Perform detection
        return self.model.predict(list(pdf_images.values()), list(pdf_images.keys()))
