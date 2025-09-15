# line_segmentor.py
import cv2 as cv
import numpy as np
from typing import List, Tuple

class LineSegmentor:
    
    def __init__(self, gray_img: np.ndarray, bin_img: np.ndarray):
        """
        Constructs a new line segmentation object for the given handwritten paragraph image.

        :param gray_img:    the handwritten paragraph image in gray scale.
        :param bin_img:     the handwritten paragraph image after binarization.
        """
        
        # Store references to the page images.
        self.gray_img = gray_img
        self.bin_img = bin_img
        
        # Get horizontal histogram.
        self.hor_hist = np.sum(bin_img, axis=1, dtype=int) // 255
        
        # Get line density thresholds.
        self.threshold_high = int(np.max(self.hor_hist) // 3)
        self.threshold_low = 25
        
        # Initialize empty lists.
        self.peaks = []
        self.valleys = []
        self.lines_boundaries = []
        
        # Calculate peaks and valleys of the page.
        self.detect_peaks()
        if len(self.peaks) > 1:
            self.avg_peaks_dist = int((self.peaks[-1] - self.peaks[0]) // len(self.peaks))
        else:
            self.avg_peaks_dist = 50  # default value
        self.detect_valleys()
        
        # Detect missing peaks and valleys in a second iteration.
        self.detect_missing_peaks_valleys()
        
        # Detect line boundaries.
        self.detect_line_boundaries()
    
    def segment(self):
        """
        Segments the handwritten paragraph into list of lines.

        :return:    two lists of lines:
                    one from the gray image and the other from the binary image.
        """
        
        # Initialize lines lists.
        gray_lines, bin_lines = [], []
        
        # Loop on every line boundary.
        for l, u, r, d in self.lines_boundaries:
            # Crop gray line.
            g_line = self.gray_img[u:d + 1, l:r + 1]
            gray_lines.append(g_line)
            
            # Crop binary line.
            b_line = self.bin_img[u:d + 1, l:r + 1]
            bin_lines.append(b_line)
        
        # Return list of separated lines.
        return gray_lines, bin_lines
    
    def detect_peaks(self):
        """
        Detects the peak rows of the image and update self.peaks in correspondence.

        The peak rows are the ones with the highest black pixel density.
        """
        
        self.peaks = []
        
        i = 0
        while i < len(self.hor_hist):
            # If the black pixels density of the row is below than threshold
            # then continue to the next row.
            if self.hor_hist[i] < self.threshold_high:
                i += 1
                continue
            
            # Get the row with the maximum density from the following
            # probable row lines.
            peak_idx = i
            while i < len(self.hor_hist) and self.is_probable_peak(i):
                if self.hor_hist[i] > self.hor_hist[peak_idx]:
                    peak_idx = i
                i += 1
            
            # Add peak row index to the list.
            self.peaks.append(peak_idx)
    
    def detect_valleys(self):
        """
        Detects the valleys rows of the image and update self.valleys in correspondence.

        The valleys rows are the ones with the lowest black pixel density
        between two consecutive peaks.
        """
        
        self.valleys = [0]
        
        i = 1
        while i < len(self.peaks):
            u = self.peaks[i - 1]
            d = self.peaks[i]
            i += 1
            
            expected_valley = d - self.avg_peaks_dist // 2
            valley_idx = u
            
            while u < d:
                dist1 = np.abs(u - expected_valley)
                dist2 = np.abs(valley_idx - expected_valley)
                
                cond1 = self.hor_hist[u] < self.hor_hist[valley_idx]
                cond2 = self.hor_hist[u] == self.hor_hist[valley_idx] and dist1 < dist2
                
                if cond1 or cond2:
                    valley_idx = u
                
                u += 1
            
            self.valleys.append(valley_idx)
        
        self.valleys.append(len(self.hor_hist) - 1)
    
    def detect_missing_peaks_valleys(self):
        """
        Detects the missing peaks and valleys after the first detection trial
        using functions self.detect_peaks and self.detect_valleys.

        And updates self.peaks and self.valleys in correspondence.
        """
        
        i = 1
        found = False
        
        while i < len(self.valleys):
            # Calculate distance between two consecutive valleys.
            up, down = self.valleys[i - 1], self.valleys[i]
            dis = down - up
            
            i += 1
            
            # If the distance is about twice the average distance between
            # two consecutive peaks, then it is most probable that we are missing
            # a line in between these two valleys.
            if dis < 1.5 * self.avg_peaks_dist:
                continue
            
            u = up + self.avg_peaks_dist
            d = min(down, u + self.avg_peaks_dist)
            
            while (d - u) * 2 > self.avg_peaks_dist:
                if self.is_probable_valley(u) and self.is_probable_valley(d):
                    peak = self.get_peak_in_range(u, d)
                    if self.hor_hist[peak] > self.threshold_low:
                        self.peaks.append(self.get_peak_in_range(u, d))
                        found = True
                
                u = u + self.avg_peaks_dist
                d = min(down, u + self.avg_peaks_dist)
        
        # Re-distribute peaks and valleys if new ones are found.
        if found:
            self.peaks.sort()
            self.detect_valleys()
    
    def detect_line_boundaries(self):
        """
        Detects handwritten lines of the image using the peaks and valleys.

        And updates self.lines_boundaries in correspondence.
        """
        
        # Get image dimensions.
        height, width = self.bin_img.shape
        
        self.lines_boundaries = []
        
        i = 1
        while i < len(self.valleys):
            u = self.valleys[i - 1]
            d = self.valleys[i]
            l = 0
            r = width - 1
            i += 1
            
            while u < d and self.hor_hist[u] == 0:
                u += 1
            while d > u and self.hor_hist[d] == 0:
                d -= 1
            
            ver_hist = np.sum(self.bin_img[u:d + 1, :], axis=0) // 255
            
            while l < r and ver_hist[l] == 0:
                l += 1
            while r > l and ver_hist[r] == 0:
                r -= 1
            
            self.lines_boundaries.append((l, u, r, d))
    
    def get_peak_in_range(self, up: int, down: int) -> int:
        """
        Get the peak row index within the given range.
        """
        max_density = 0
        peak_idx = up
        
        for i in range(up, down + 1):
            if i < len(self.hor_hist) and self.hor_hist[i] > max_density:
                max_density = self.hor_hist[i]
                peak_idx = i
        
        return peak_idx
    
    def is_probable_peak(self, row: int) -> bool:
        """
        Check if the given row is a probable peak.
        """
        return row < len(self.hor_hist) and self.hor_hist[row] >= self.threshold_high
    
    def is_probable_valley(self, row: int) -> bool:
        """
        Check if the given row is a probable valley.
        """
        return row < len(self.hor_hist) and self.hor_hist[row] <= self.threshold_low
