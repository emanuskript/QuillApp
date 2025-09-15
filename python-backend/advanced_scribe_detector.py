# advanced_scribe_detector.py
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import logging
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from datetime import datetime
import json

log = logging.getLogger(__name__)

class AdvancedScribeDetector:
    """
    Advanced scribe detection with multiple algorithms and confidence scoring
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=10)
        self.features_cache = {}
        
    def extract_writing_features(self, line_image: np.ndarray) -> Dict[str, float]:
        """
        Extract comprehensive writing features from a line image
        """
        if line_image is None or line_image.size == 0:
            return self._default_features()
            
        # Convert to grayscale if needed
        if len(line_image.shape) == 3:
            gray = cv2.cvtColor(line_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = line_image.copy()
            
        # Ensure we have content
        if np.sum(gray < 128) < 10:  # Less than 10 dark pixels
            return self._default_features()
            
        features = {}
        
        try:
            # 1. Stroke width analysis
            features.update(self._analyze_stroke_width(gray))
            
            # 2. Curvature and angularity
            features.update(self._analyze_curvature(gray))
            
            # 3. Spacing analysis
            features.update(self._analyze_spacing(gray))
            
            # 4. Slant analysis
            features.update(self._analyze_slant(gray))
            
            # 5. Pressure simulation (ink density)
            features.update(self._analyze_pressure(gray))
            
            # 6. Letter size consistency
            features.update(self._analyze_size_consistency(gray))
            
            # 7. Baseline analysis
            features.update(self._analyze_baseline(gray))
            
        except Exception as e:
            log.warning(f"Feature extraction failed: {e}")
            return self._default_features()
            
        return features
    
    def _default_features(self) -> Dict[str, float]:
        """Return default features when extraction fails"""
        return {
            'avg_stroke_width': 2.0,
            'stroke_width_variance': 0.5,
            'curvature_avg': 0.3,
            'angularity_score': 0.5,
            'letter_spacing': 8.0,
            'word_spacing': 20.0,
            'slant_angle': 0.0,
            'slant_consistency': 0.8,
            'pressure_avg': 0.6,
            'pressure_variance': 0.2,
            'letter_height_avg': 15.0,
            'letter_height_variance': 2.0,
            'baseline_straightness': 0.9
        }
    
    def _analyze_stroke_width(self, gray: np.ndarray) -> Dict[str, float]:
        """Analyze stroke width characteristics"""
        # Distance transform to find stroke widths
        binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        if np.sum(binary) == 0:
            return {'avg_stroke_width': 2.0, 'stroke_width_variance': 0.5}
            
        dist_transform = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
        stroke_widths = dist_transform[dist_transform > 0] * 2  # Diameter
        
        if len(stroke_widths) == 0:
            return {'avg_stroke_width': 2.0, 'stroke_width_variance': 0.5}
            
        return {
            'avg_stroke_width': float(np.mean(stroke_widths)),
            'stroke_width_variance': float(np.var(stroke_widths))
        }
    
    def _analyze_curvature(self, gray: np.ndarray) -> Dict[str, float]:
        """Analyze curvature and angularity of strokes"""
        binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {'curvature_avg': 0.3, 'angularity_score': 0.5}
            
        curvatures = []
        angular_points = 0
        total_points = 0
        
        for contour in contours:
            if len(contour) < 5:
                continue
                
            # Approximate contour to find angular points
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            angular_points += len(approx)
            total_points += len(contour)
            
            # Calculate curvature for longer contours
            if len(contour) > 10:
                for i in range(1, len(contour) - 1):
                    p1 = contour[i-1][0]
                    p2 = contour[i][0]
                    p3 = contour[i+1][0]
                    
                    # Calculate angle
                    v1 = p2 - p1
                    v2 = p3 - p2
                    
                    if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                        cos_angle = np.clip(cos_angle, -1, 1)
                        curvature = 1 - abs(cos_angle)  # 0 = straight, 1 = very curved
                        curvatures.append(curvature)
        
        return {
            'curvature_avg': float(np.mean(curvatures)) if curvatures else 0.3,
            'angularity_score': float(angular_points / max(total_points, 1))
        }
    
    def _analyze_spacing(self, gray: np.ndarray) -> Dict[str, float]:
        """Analyze letter and word spacing"""
        binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        
        # Find connected components (potential letters)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)
        
        if num_labels < 3:  # Background + at least 2 components
            return {'letter_spacing': 8.0, 'word_spacing': 20.0}
        
        # Sort components by x-coordinate
        components = []
        for i in range(1, num_labels):  # Skip background
            x, y, w, h, area = stats[i]
            if area > 20:  # Filter out noise
                components.append((x, x + w, area))
        
        if len(components) < 2:
            return {'letter_spacing': 8.0, 'word_spacing': 20.0}
            
        components.sort(key=lambda x: x[0])  # Sort by x position
        
        # Calculate gaps between components
        gaps = []
        for i in range(len(components) - 1):
            gap = components[i+1][0] - components[i][1]  # Start of next - end of current
            if gap > 0:
                gaps.append(gap)
        
        if not gaps:
            return {'letter_spacing': 8.0, 'word_spacing': 20.0}
            
        gaps = np.array(gaps)
        
        # Distinguish between letter spacing and word spacing
        gap_threshold = np.percentile(gaps, 75)  # Top 25% are likely word spaces
        letter_gaps = gaps[gaps <= gap_threshold]
        word_gaps = gaps[gaps > gap_threshold]
        
        return {
            'letter_spacing': float(np.mean(letter_gaps)) if len(letter_gaps) > 0 else 8.0,
            'word_spacing': float(np.mean(word_gaps)) if len(word_gaps) > 0 else 20.0
        }
    
    def _analyze_slant(self, gray: np.ndarray) -> Dict[str, float]:
        """Analyze writing slant angle and consistency"""
        binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        
        # Find vertical strokes using morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
        vertical_strokes = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # Find lines using HoughLines
        lines = cv2.HoughLines(vertical_strokes, 1, np.pi/180, threshold=20)
        
        if lines is None or len(lines) == 0:
            return {'slant_angle': 0.0, 'slant_consistency': 0.8}
        
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = (theta - np.pi/2) * 180 / np.pi  # Convert to degrees from vertical
            if abs(angle) < 45:  # Only consider reasonable slants
                angles.append(angle)
        
        if not angles:
            return {'slant_angle': 0.0, 'slant_consistency': 0.8}
        
        return {
            'slant_angle': float(np.mean(angles)),
            'slant_consistency': float(1.0 / (1.0 + np.var(angles)))  # Higher consistency = lower variance
        }
    
    def _analyze_pressure(self, gray: np.ndarray) -> Dict[str, float]:
        """Simulate pressure analysis using ink density"""
        binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        ink_pixels = gray[binary > 0]
        
        if len(ink_pixels) == 0:
            return {'pressure_avg': 0.6, 'pressure_variance': 0.2}
        
        # Normalize intensities (darker = more pressure)
        pressure_values = (255 - ink_pixels) / 255.0
        
        return {
            'pressure_avg': float(np.mean(pressure_values)),
            'pressure_variance': float(np.var(pressure_values))
        }
    
    def _analyze_size_consistency(self, gray: np.ndarray) -> Dict[str, float]:
        """Analyze consistency of letter sizes"""
        binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)
        
        if num_labels < 2:
            return {'letter_height_avg': 15.0, 'letter_height_variance': 2.0}
        
        heights = []
        for i in range(1, num_labels):  # Skip background
            x, y, w, h, area = stats[i]
            if area > 20 and h > 5:  # Filter noise and very small components
                heights.append(h)
        
        if not heights:
            return {'letter_height_avg': 15.0, 'letter_height_variance': 2.0}
        
        return {
            'letter_height_avg': float(np.mean(heights)),
            'letter_height_variance': float(np.var(heights))
        }
    
    def _analyze_baseline(self, gray: np.ndarray) -> Dict[str, float]:
        """Analyze baseline straightness"""
        binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        
        # Find bottom points of each connected component
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)
        
        bottom_points = []
        for i in range(1, num_labels):  # Skip background
            x, y, w, h, area = stats[i]
            if area > 20:  # Filter noise
                bottom_y = y + h
                center_x = x + w // 2
                bottom_points.append((center_x, bottom_y))
        
        if len(bottom_points) < 3:
            return {'baseline_straightness': 0.9}
        
        # Fit a line to bottom points
        points = np.array(bottom_points)
        if len(points) > 1:
            # Calculate variance from best-fit line
            x_coords = points[:, 0]
            y_coords = points[:, 1]
            
            # Simple linear regression
            A = np.vstack([x_coords, np.ones(len(x_coords))]).T
            m, b = np.linalg.lstsq(A, y_coords, rcond=None)[0]
            
            # Calculate deviations from line
            predicted_y = m * x_coords + b
            deviations = np.abs(y_coords - predicted_y)
            avg_deviation = np.mean(deviations)
            
            # Convert to straightness score (0-1, higher is straighter)
            straightness = 1.0 / (1.0 + avg_deviation / 5.0)
        else:
            straightness = 0.9
        
        return {'baseline_straightness': float(straightness)}
    
    def detect_scribe_changes_advanced(self, line_images: List[np.ndarray], 
                                     window_size: int = 5, 
                                     sensitivity: float = 0.7) -> List[Dict]:
        """
        Advanced scribe change detection with multiple features and algorithms
        """
        if len(line_images) < 2:
            return []
        
        # Extract features for all lines
        all_features = []
        feature_names = None
        
        for i, img in enumerate(line_images):
            features = self.extract_writing_features(img)
            if feature_names is None:
                feature_names = list(features.keys())
            
            feature_vector = [features[name] for name in feature_names]
            all_features.append(feature_vector)
        
        if len(all_features) < 2:
            return []
        
        # Normalize features
        all_features = np.array(all_features)
        all_features = self.scaler.fit_transform(all_features)
        
        # Apply PCA for dimensionality reduction
        if all_features.shape[1] > 10:
            all_features = self.pca.fit_transform(all_features)
        
        # Detect changes using multiple methods
        changes = []
        
        # Method 1: Sliding window comparison
        changes.extend(self._detect_changes_sliding_window(all_features, window_size, sensitivity))
        
        # Method 2: Clustering-based detection
        changes.extend(self._detect_changes_clustering(all_features, sensitivity))
        
        # Method 3: Statistical change point detection
        changes.extend(self._detect_changes_statistical(all_features, sensitivity))
        
        # Merge and rank changes
        changes = self._merge_and_rank_changes(changes, len(line_images))
        
        return changes
    
    def _detect_changes_sliding_window(self, features: np.ndarray, 
                                     window_size: int, 
                                     sensitivity: float) -> List[Dict]:
        """Detect changes using sliding window approach"""
        changes = []
        
        for i in range(window_size, len(features) - window_size):
            before_window = features[i-window_size:i]
            after_window = features[i:i+window_size]
            
            # Calculate distance between windows
            before_mean = np.mean(before_window, axis=0)
            after_mean = np.mean(after_window, axis=0)
            
            distance = np.linalg.norm(before_mean - after_mean)
            
            # Calculate significance
            before_var = np.var(before_window, axis=0)
            after_var = np.var(after_window, axis=0)
            combined_var = np.mean(before_var + after_var)
            
            if combined_var > 0:
                significance = distance / np.sqrt(combined_var)
            else:
                significance = distance
            
            confidence = min(significance / 2.0, 1.0)  # Normalize to 0-1
            
            if confidence >= sensitivity:
                changes.append({
                    'line_number': i + 1,
                    'confidence': confidence,
                    'method': 'sliding_window',
                    'distance': distance
                })
        
        return changes
    
    def _detect_changes_clustering(self, features: np.ndarray, sensitivity: float) -> List[Dict]:
        """Detect changes using clustering approach"""
        if len(features) < 4:
            return []
        
        # Try different numbers of clusters
        changes = []
        max_clusters = min(len(features) // 2, 5)
        
        for n_clusters in range(2, max_clusters + 1):
            try:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                labels = kmeans.fit_predict(features)
                
                # Find cluster boundaries
                for i in range(1, len(labels)):
                    if labels[i] != labels[i-1]:
                        # Calculate confidence based on cluster separation
                        center1 = kmeans.cluster_centers_[labels[i-1]]
                        center2 = kmeans.cluster_centers_[labels[i]]
                        distance = np.linalg.norm(center1 - center2)
                        
                        confidence = min(distance / 3.0, 1.0)  # Normalize
                        
                        if confidence >= sensitivity:
                            changes.append({
                                'line_number': i + 1,
                                'confidence': confidence,
                                'method': 'clustering',
                                'distance': distance
                            })
            except:
                continue
        
        return changes
    
    def _detect_changes_statistical(self, features: np.ndarray, sensitivity: float) -> List[Dict]:
        """Detect changes using statistical change point detection"""
        changes = []
        
        # Simple change point detection using cumulative sum
        for feature_idx in range(features.shape[1]):
            feature_values = features[:, feature_idx]
            
            # Calculate cumulative sum of deviations from mean
            mean_val = np.mean(feature_values)
            deviations = feature_values - mean_val
            cumsum = np.cumsum(deviations)
            
            # Find points where cumsum changes direction significantly
            for i in range(2, len(cumsum) - 2):
                before_trend = cumsum[i] - cumsum[i-2]
                after_trend = cumsum[i+2] - cumsum[i]
                
                if before_trend * after_trend < 0:  # Sign change
                    trend_change = abs(before_trend - after_trend)
                    confidence = min(trend_change / np.std(deviations) / 2.0, 1.0)
                    
                    if confidence >= sensitivity:
                        changes.append({
                            'line_number': i + 1,
                            'confidence': confidence,
                            'method': 'statistical',
                            'distance': trend_change
                        })
        
        return changes
    
    def _merge_and_rank_changes(self, changes: List[Dict], total_lines: int) -> List[Dict]:
        """Merge nearby changes and rank by confidence"""
        if not changes:
            return []
        
        # Group changes by proximity (within 2 lines)
        grouped_changes = []
        changes.sort(key=lambda x: x['line_number'])
        
        current_group = [changes[0]]
        
        for change in changes[1:]:
            if change['line_number'] - current_group[-1]['line_number'] <= 2:
                current_group.append(change)
            else:
                grouped_changes.append(current_group)
                current_group = [change]
        
        grouped_changes.append(current_group)
        
        # Merge each group
        merged_changes = []
        for group in grouped_changes:
            # Take the change with highest confidence, but average the position
            best_change = max(group, key=lambda x: x['confidence'])
            avg_line = int(np.mean([c['line_number'] for c in group]))
            avg_confidence = np.mean([c['confidence'] for c in group])
            
            # Generate explanation
            methods = list(set([c['method'] for c in group]))
            explanation = self._generate_explanation(best_change, methods)
            
            merged_changes.append({
                'line_number': avg_line,
                'confidence': avg_confidence,
                'explanation': explanation,
                'distance': best_change['distance'],
                'z_score': (best_change['distance'] - 1.0) / 0.5,  # Simplified z-score
                'methods_detected': methods
            })
        
        # Sort by confidence and return top changes
        merged_changes.sort(key=lambda x: x['confidence'], reverse=True)
        return merged_changes[:5]  # Return top 5 changes
    
    def _generate_explanation(self, change: Dict, methods: List[str]) -> str:
        """Generate human-readable explanation for the change"""
        confidence = change['confidence']
        distance = change['distance']
        
        confidence_level = "high" if confidence > 0.8 else "medium" if confidence > 0.6 else "moderate"
        
        explanations = [
            f"A {confidence_level} confidence scribe change was detected.",
            f"Multiple detection methods ({', '.join(methods)}) identified this transition.",
            f"The writing characteristics show significant variation (distance: {distance:.3f})."
        ]
        
        if distance > 2.0:
            explanations.append("The change appears to be quite pronounced, suggesting a clear transition between different writing styles.")
        elif distance > 1.0:
            explanations.append("The change shows moderate variation in writing characteristics.")
        else:
            explanations.append("The change is subtle but statistically significant.")
        
        return " ".join(explanations)
