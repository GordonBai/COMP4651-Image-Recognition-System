import os
import sys
import argparse
import json

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Import the image classifier
from image_processing.services.image_classifier import ImageClassifier


def test_classifier(image_path):
    """
    Test the image classifier with a local image.
    
    Args:
        image_path (str): Path to the test image
    """
    print(f"Testing image classification on: {image_path}")
    
    # Create classifier
    classifier = ImageClassifier()
    
    # Classify the image
    try:
        results = classifier.classify_image(image_path)
        
        print("\nClassification Results:")
        print(json.dumps(results, indent=2))
        
        # Check if any results were found
        if not results:
            print("No classification results found.")
            return False
        
        print(f"\nTop prediction: {results[0]['label']} with confidence {results[0]['confidence']:.4f}")
        return True
        
    except Exception as e:
        print(f"Error during classification: {str(e)}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test image classification")
    parser.add_argument("image_path", help="Path to the image file to classify")
    args = parser.parse_args()
    
    if not os.path.exists(args.image_path):
        print(f"Error: Image file not found: {args.image_path}")
        sys.exit(1)
    
    success = test_classifier(args.image_path)
    
    if success:
        print("\nTest completed successfully.")
        sys.exit(0)
    else:
        print("\nTest failed.")
        sys.exit(1) 