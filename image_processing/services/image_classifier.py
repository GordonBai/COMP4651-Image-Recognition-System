import os
import numpy as np
import yaml
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2, ResNet50
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_preprocess
from tensorflow.keras.applications.resnet50 import preprocess_input as resnet_preprocess
from image_processing.services.image_preprocessor import ImagePreprocessor


class ImageClassifier:
    """
    Handles image classification using TensorFlow models.
    """
    def __init__(self, config_path=None):
        if config_path is None:
            # Default configuration path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.join(os.path.dirname(current_dir), 'configs')
            config_path = os.path.join(config_dir, 'model_config.yaml')
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Extract model parameters
        self.model_name = self.config['model']['name']
        self.input_size = self.config['model']['input_size']
        self.confidence_threshold = self.config['inference']['confidence_threshold']
        self.top_k = self.config['inference']['top_k']
        
        # Initialize preprocessor
        self.preprocessor = ImagePreprocessor(config_path)
        
        # Load labels
        labels_path = self.config['labels']['path']
        if os.path.exists(labels_path):
            with open(labels_path, 'r') as f:
                self.labels = [line.strip() for line in f.readlines()]
        else:
            self.labels = None
        
        # Load model
        self.model = self._load_model()
    
    def _load_model(self):
        """
        Load the appropriate model based on configuration.
        
        Returns:
            tensorflow.keras.Model: The loaded model
        """
        if self.model_name.lower() == 'mobilenet_v2':
            model = MobileNetV2(weights='imagenet', include_top=True)
            self.preprocess_func = mobilenet_preprocess
        elif self.model_name.lower() == 'resnet50':
            model = ResNet50(weights='imagenet', include_top=True)
            self.preprocess_func = resnet_preprocess
        else:
            # Load custom model from weights path if specified
            weights_path = self.config['model']['weights_path']
            if os.path.exists(weights_path):
                model = tf.keras.models.load_model(weights_path)
            else:
                raise ValueError(f"Model {self.model_name} not supported and no weights path found")
        
        return model
    
    def classify_image(self, image_path):
        """
        Classify a single image.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            list: Top k predictions with class labels and confidences
        """
        # Preprocess the image
        img_array = self.preprocessor.preprocess_image(image_path)
        
        # Apply model-specific preprocessing
        if hasattr(self, 'preprocess_func'):
            img_array = self.preprocess_func(img_array)
        
        # Perform prediction
        predictions = self.model.predict(img_array)
        
        # Process results
        return self._process_predictions(predictions[0])
    
    def classify_image_bytes(self, image_bytes):
        """
        Classify an image from bytes data.
        
        Args:
            image_bytes (bytes): Image data as bytes
            
        Returns:
            list: Top k predictions with class labels and confidences
        """
        # Preprocess the image
        img_array = self.preprocessor.preprocess_image_bytes(image_bytes)
        
        # Apply model-specific preprocessing
        if hasattr(self, 'preprocess_func'):
            img_array = self.preprocess_func(img_array)
        
        # Perform prediction
        predictions = self.model.predict(img_array)
        
        # Process results
        return self._process_predictions(predictions[0])
    
    def classify_batch(self, image_paths):
        """
        Classify a batch of images.
        
        Args:
            image_paths (list): List of paths to image files
            
        Returns:
            list: List of prediction results for each image
        """
        # Preprocess the batch
        img_batch = self.preprocessor.preprocess_batch(image_paths)
        
        # Apply model-specific preprocessing
        if hasattr(self, 'preprocess_func'):
            img_batch = self.preprocess_func(img_batch)
        
        # Perform prediction
        predictions = self.model.predict(img_batch)
        
        # Process results
        return [self._process_predictions(pred) for pred in predictions]
    
    def _process_predictions(self, predictions):
        """
        Process raw model predictions into readable results.
        
        Args:
            predictions (numpy.ndarray): Raw model predictions
            
        Returns:
            list: Top k predictions with class labels and confidences
        """
        # Get indices of top k predictions
        top_indices = predictions.argsort()[-self.top_k:][::-1]
        
        results = []
        for i in top_indices:
            confidence = float(predictions[i])
            
            # Skip if below confidence threshold
            if confidence < self.confidence_threshold:
                continue
            
            # Get class label if available
            if self.labels and i < len(self.labels):
                label = self.labels[i]
            else:
                label = f"class_{i}"
            
            results.append({
                "label": label,
                "confidence": confidence,
                "class_id": int(i)
            })
        
        return results 