#!/usr/bin/env python3
"""
Simple test script to generate a test base64 image and test if our HTML can display it
"""
from PIL import Image, ImageDraw, ImageFont
import base64
import io
import json

def create_test_image():
    """Create a simple test image with text"""
    # Create a test image
    width, height = 400, 100
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Add some text
    try:
        # Try to use a system font
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    text = "Test Line Screenshot - This should be visible!"
    draw.text((10, 30), text, fill='black', font=font)
    
    # Add a border
    draw.rectangle([0, 0, width-1, height-1], outline='red', width=2)
    
    # Convert to base64
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return img_data

def create_test_html_with_image():
    """Create test HTML with actual base64 image"""
    test_image = create_test_image()
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Display Test</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            padding: 20px;
            background-color: #f0f0f0;
        }}
        .test-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .image-test {{
            border: 2px solid #ccc;
            padding: 10px;
            margin: 10px 0;
            background: #fafafa;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
        }}
        .failure {{
            background-color: #ffebee;
            border: 2px solid #f44336;
            color: #d32f2f;
        }}
        .success {{
            background-color: #e8f5e8;
            border: 2px solid #4caf50;
            color: #2e7d32;
        }}
    </style>
</head>
<body>
    <h1>🔍 Image Display Test - Debugging Grey Rectangle Issue</h1>
    
    <div class="test-container">
        <h2>Test 1: Direct Base64 Image</h2>
        <p>This should show a white rectangle with red border and black text:</p>
        <div class="image-test">
            <img src="data:image/png;base64,{test_image}" alt="Test Image" style="display: block; margin: 10px 0;">
        </div>
    </div>

    <div class="test-container">
        <h2>Test 2: Dynamic Image Creation</h2>
        <p>This will create the same image dynamically via JavaScript:</p>
        <div class="image-test" id="dynamic-container">
            <p>Loading...</p>
        </div>
    </div>

    <div class="test-container">
        <h2>Test 3: Error Simulation</h2>
        <p>Testing what happens with invalid base64:</p>
        <div class="image-test">
            <img src="data:image/png;base64,invalid" alt="Invalid Image" style="display: block; margin: 10px 0;" 
                 onerror="this.parentElement.innerHTML='<div class=\\"failure\\">❌ Invalid base64 detected</div>'">
        </div>
    </div>

    <script>
        // Test dynamic image creation (similar to Vue.js approach)
        const testBase64 = "{test_image}";
        
        setTimeout(() => {{
            const container = document.getElementById('dynamic-container');
            
            // Clear loading message
            container.innerHTML = '';
            
            // Create image element
            const img = document.createElement('img');
            img.src = `data:image/png;base64,${{testBase64}}`;
            img.alt = 'Dynamic Test Image';
            img.style.display = 'block';
            img.style.margin = '10px 0';
            img.style.border = '1px solid #ddd';
            
            // Add error handler
            img.onerror = function() {{
                container.innerHTML = '<div class="failure">❌ Dynamic image failed to load</div>';
            }};
            
            // Add success handler
            img.onload = function() {{
                console.log('✅ Dynamic image loaded successfully');
                const successDiv = document.createElement('div');
                successDiv.className = 'success';
                successDiv.textContent = '✅ Dynamic image loaded successfully';
                container.appendChild(successDiv);
            }};
            
            container.appendChild(img);
        }}, 1000);

        // Test if we can detect image load failures
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('🔍 Testing image display capabilities...');
            console.log('Base64 length:', testBase64.length);
            console.log('Base64 prefix:', testBase64.substring(0, 50));
        }});
    </script>
</body>
</html>"""
    
    return html_content

if __name__ == "__main__":
    # Create the test HTML
    html_content = create_test_html_with_image()
    
    # Save it
    with open('/Users/mobasuony/Desktop/QuillApp/image_test_with_data.html', 'w') as f:
        f.write(html_content)
    
    print("✅ Created test HTML with real image data")
    print("📄 Saved to: /Users/mobasuony/Desktop/QuillApp/image_test_with_data.html")
    print("🌐 Open this file in browser to test image display")
    
    # Also create JSON with test data for manual testing
    test_data = {
        "scribe_changes": [
            {
                "start_line": 1,
                "end_line": 3,
                "confidence": 0.95,
                "line_screenshots": [
                    {
                        "line_number": 1,
                        "text": "Test Line 1 - Generated image",
                        "image_data": create_test_image(),
                        "bbox": [10, 10, 400, 110]
                    },
                    {
                        "line_number": 2,
                        "text": "Test Line 2 - Another generated image", 
                        "image_data": create_test_image(),
                        "bbox": [10, 120, 400, 220]
                    }
                ]
            }
        ]
    }
    
    with open('/Users/mobasuony/Desktop/QuillApp/test_backend_response.json', 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print("📋 Created test backend response: /Users/mobasuony/Desktop/QuillApp/test_backend_response.json")
