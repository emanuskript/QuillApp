import pytesseract
from PIL import Image, ImageEnhance
import base64
import io

def preprocess_image(image):
    """Preprocess the image for better OCR results"""
    # Convert image to grayscale
    gray_image = image.convert('L')

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(gray_image)
    enhanced_image = enhancer.enhance(2.0)  # Increase contrast

    # Apply thresholding to remove noise and make text clearer
    threshold_image = enhanced_image.point(lambda p: p > 128 and 255)

    return threshold_image

def extract_line_screenshots(image_base64):
    """Extract line screenshots using OCR-based detection - GitHub repo approach"""
    try:
        # Decode base64 image
        image_data = base64.b64decode(image_base64.split(',')[1] if ',' in image_base64 else image_base64)
        original_image = Image.open(io.BytesIO(image_data))
        
        # Preprocess the image for better OCR results
        preprocessed_image = preprocess_image(original_image)
        
        # Perform OCR with pytesseract to get bounding boxes
        custom_config = r'--oem 3 --psm 6'  # Default OEM, single uniform block of text
        data = pytesseract.image_to_data(preprocessed_image, config=custom_config, output_type=pytesseract.Output.DICT)
        
        print(f"OCR found {len(data['text'])} text elements")
        
        # Group words by line number to get complete text lines (GitHub approach)
        line_groups = {}
        for i, word in enumerate(data['text']):
            if word.strip() and int(data['conf'][i]) > 30:  # Filter out low confidence text
                line_num = data['line_num'][i]
                if line_num not in line_groups:
                    line_groups[line_num] = {
                        'words': [],
                        'bboxes': [],
                        'confidences': []
                    }
                
                line_groups[line_num]['words'].append(word.strip())
                line_groups[line_num]['bboxes'].append({
                    'left': data['left'][i],
                    'top': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i]
                })
                line_groups[line_num]['confidences'].append(data['conf'][i])
        
        print(f"Grouped into {len(line_groups)} text lines")
        
        # Extract line screenshots with proper bounding boxes (exact GitHub approach)
        line_screenshots = []
        for line_num, line_data in line_groups.items():
            if len(line_data['words']) > 0:  # Only process lines with text
                # Calculate the bounding box for the entire line
                bboxes = line_data['bboxes']
                
                # Get bounding box of the line (GitHub approach)
                left = min(bbox['left'] for bbox in bboxes)
                top = min(bbox['top'] for bbox in bboxes)
                right = max(bbox['left'] + bbox['width'] for bbox in bboxes)
                bottom = max(bbox['top'] + bbox['height'] for bbox in bboxes)
                
                # Add some padding around the line
                padding = 5
                left = max(0, left - padding)
                top = max(0, top - padding)
                right = min(original_image.width, right + padding)
                bottom = min(original_image.height, bottom + padding)
                
                # Create line bounding box
                line_bbox = (left, top, right, bottom)
                
                # Crop the line from the ORIGINAL image (not preprocessed) - key fix!
                cropped_line = original_image.crop(line_bbox)
                
                # Ensure the cropped image is not empty
                if cropped_line.width > 0 and cropped_line.height > 0:
                    # Convert to base64
                    buffer = io.BytesIO()
                    cropped_line.save(buffer, format='PNG')
                    line_base64 = base64.b64encode(buffer.getvalue()).decode()
                    
                    line_text = ' '.join(line_data['words'])
                    avg_confidence = sum(line_data['confidences']) / len(line_data['confidences'])
                    
                    print(f"Extracted line {line_num}: '{line_text}' ({cropped_line.width}x{cropped_line.height})")
                    
                    line_screenshots.append({
                        'lineNumber': line_num,
                        'text': line_text,
                        'bbox': {
                            'left': left,
                            'top': top,
                            'width': right - left,
                            'height': bottom - top
                        },
                        'screenshot': f"data:image/png;base64,{line_base64}",
                        'confidence': avg_confidence / 100.0  # Convert to 0-1 scale
                    })
        
        # Sort by line number
        line_screenshots.sort(key=lambda x: x['lineNumber'])
        
        print(f"Successfully extracted {len(line_screenshots)} line screenshots")
        return line_screenshots
        
    except Exception as e:
        print(f"Error in OCR line extraction: {e}")
        import traceback
        traceback.print_exc()
        return []

def find_lines_with_text(image_base64, search_text):
    """Find specific lines containing search text (GitHub approach)"""
    try:
        # Decode base64 image
        image_data = base64.b64decode(image_base64.split(',')[1] if ',' in image_base64 else image_base64)
        original_image = Image.open(io.BytesIO(image_data))
        
        # Preprocess the image for better OCR results
        preprocessed_image = preprocess_image(original_image)
        
        # Perform OCR with pytesseract
        custom_config = r'--oem 3 --psm 6'
        data = pytesseract.image_to_data(preprocessed_image, config=custom_config, output_type=pytesseract.Output.DICT)
        
        # Find words containing the search text
        matching_lines = []
        for i, word in enumerate(data['text']):
            if search_text.lower() in word.lower():
                # Get the bounding box of the word
                left = data['left'][i]
                top = data['top'][i]
                width = data['width'][i]
                height = data['height'][i]
                line_bbox = (left, top, left + width, top + height)
                
                # Crop the line from original image
                cropped_line = original_image.crop(line_bbox)
                
                # Convert to base64
                buffer = io.BytesIO()
                cropped_line.save(buffer, format='PNG')
                line_base64 = base64.b64encode(buffer.getvalue()).decode()
                
                matching_lines.append({
                    'lineNumber': data['line_num'][i],
                    'text': word,
                    'bbox': {
                        'left': left,
                        'top': top,
                        'width': width,
                        'height': height
                    },
                    'screenshot': f"data:image/png;base64,{line_base64}",
                    'confidence': data['conf'][i] / 100.0
                })
        
        return matching_lines
        
    except Exception as e:
        print(f"Error in line search: {e}")
        return []

def get_all_line_bboxes(image_base64):
    """Get bounding boxes for all detected text lines"""
    try:
        # Decode base64 image
        image_data = base64.b64decode(image_base64.split(',')[1] if ',' in image_base64 else image_base64)
        original_image = Image.open(io.BytesIO(image_data))
        
        # Preprocess the image for better OCR results
        preprocessed_image = preprocess_image(original_image)
        
        # Perform OCR with pytesseract to get bounding boxes
        custom_config = r'--oem 3 --psm 6'
        data = pytesseract.image_to_data(preprocessed_image, config=custom_config, output_type=pytesseract.Output.DICT)
        
        print(f"OCR found {len(data['text'])} text elements for line extraction")
        
        # Group words by line number to get complete text lines
        line_groups = {}
        for i, word in enumerate(data['text']):
            if word.strip() and int(data['conf'][i]) > 30:  # Filter out low confidence text
                line_num = data['line_num'][i]
                if line_num not in line_groups:
                    line_groups[line_num] = {
                        'words': [],
                        'bboxes': [],
                        'confidences': []
                    }
                
                line_groups[line_num]['words'].append(word.strip())
                line_groups[line_num]['bboxes'].append({
                    'left': data['left'][i],
                    'top': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i]
                })
                line_groups[line_num]['confidences'].append(data['conf'][i])
        
        # Process each line group to create line bounding boxes
        all_lines = []
        for line_num, group in line_groups.items():
            if not group['words']:
                continue
                
            # Calculate the overall bounding box for the entire line
            bboxes = group['bboxes']
            min_left = min(bbox['left'] for bbox in bboxes)
            min_top = min(bbox['top'] for bbox in bboxes)
            max_right = max(bbox['left'] + bbox['width'] for bbox in bboxes)
            max_bottom = max(bbox['top'] + bbox['height'] for bbox in bboxes)
            
            line_bbox = [min_left, min_top, max_right - min_left, max_bottom - min_top]
            line_text = ' '.join(group['words'])
            avg_confidence = sum(group['confidences']) / len(group['confidences'])
            
            all_lines.append({
                'lineNumber': line_num,
                'text': line_text,
                'bbox': line_bbox,  # [x, y, width, height]
                'confidence': avg_confidence / 100.0
            })
        
        # Sort by line number
        all_lines.sort(key=lambda x: x['lineNumber'])
        
        print(f"Processed {len(all_lines)} text lines with bounding boxes")
        return all_lines
        
    except Exception as e:
        print(f"Error extracting line bboxes: {e}")
        return []
