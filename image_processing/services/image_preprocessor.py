import os
import numpy as np
import yaml
from PIL import Image
import tensorflow as tf


class ImagePreprocessor:
    """
    Handles image preprocessing for the image recognition system.
    Prepares images for model inference by resizing, normalizing, etc.
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
        
        # Extract preprocessing parameters
        self.input_size = self.config['model']['input_size']
        self.channels = self.config['model']['channels']
        self.normalize = self.config['model']['preprocessing']['normalize']
        self.resize_method = self.config['model']['preprocessing']['resize_method']
    
    def preprocess_image(self, image_path):
        """
        Preprocess a single image file.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            numpy.ndarray: Preprocessed image ready for model inference
        """
        # Load image
        try:
            img = Image.open(image_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize image
            img = img.resize((self.input_size, self.input_size), Image.BILINEAR)
            
            # Convert to numpy array
            img_array = np.array(img)
            
            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)
            
            # Normalize if required
            if self.normalize:
                img_array = img_array / 255.0
                
            return img_array
            
        except Exception as e:
            print(f"Error preprocessing image {image_path}: {str(e)}")
            raise
    
    def preprocess_image_bytes(self, image_bytes):
        """
        Preprocess image from bytes data.
        
        Args:
            image_bytes (bytes): Image data as bytes
            
        Returns:
            numpy.ndarray: Preprocessed image ready for model inference
        """
        try:
            # Create image from bytes
            img = Image.open(tf.io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize image
            img = img.resize((self.input_size, self.input_size), Image.BILINEAR)
            
            # Convert to numpy array
            img_array = np.array(img)
            
            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)
            
            # Normalize if required
            if self.normalize:
                img_array = img_array / 255.0
                
            return img_array
            
        except Exception as e:
            print(f"Error preprocessing image bytes: {str(e)}")
            raise
    
    def preprocess_batch(self, image_paths):
        """
        Preprocess a batch of images.
        
        Args:
            image_paths (list): List of paths to image files
            
        Returns:
            numpy.ndarray: Batch of preprocessed images
        """
        preprocessed_images = []
        
        for path in image_paths:
            try:
                img_array = self.preprocess_image(path)
                preprocessed_images.append(img_array[0])  # Remove batch dimension
            except Exception as e:
                print(f"Error preprocessing image {path}: {str(e)}")
                continue
        
        if not preprocessed_images:
            raise ValueError("No images were successfully preprocessed")
        
        # Stack images into a batch
        return np.stack(preprocessed_images) 