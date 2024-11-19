import librosa
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

class AudioQualityValidator:
    def __init__(self, 
                 min_duration: float = 60.0,
                 min_sample_rate: int = 44100,
                 min_bit_depth: int = 16,
                 min_dynamic_range: float = 10.0,
                 max_clipping_ratio: float = 0.01):  # Allow 1% clipping
        self.min_duration = min_duration
        self.min_sample_rate = min_sample_rate
        self.min_bit_depth = min_bit_depth
        self.min_dynamic_range = min_dynamic_range
        self.max_clipping_ratio = max_clipping_ratio
        
    def check_audio_quality(self, audio_path: Path) -> Tuple[bool, List[str], Dict[str, float]]:
        """
        Validate audio file quality
        Returns: (passed, list of issues, metrics)
        """
        issues = []
        metrics = {}
        
        try:
            # Load audio file
            y, sr = librosa.load(audio_path, sr=None)
            
            # Check duration
            duration = librosa.get_duration(y=y, sr=sr)
            metrics['duration'] = duration
            if duration < self.min_duration:
                issues.append(f"Duration too short: {duration:.1f}s < {self.min_duration}s")
            
            # Check sample rate
            metrics['sample_rate'] = sr
            if sr < self.min_sample_rate:
                issues.append(f"Sample rate too low: {sr} < {self.min_sample_rate}")
            
            # Check for clipping
            clipping_samples = np.sum(np.abs(y) >= 0.99)  # Use 0.99 as threshold
            clipping_ratio = clipping_samples / len(y)
            metrics['clipping_ratio'] = clipping_ratio
            if clipping_ratio > self.max_clipping_ratio:
                issues.append(f"Excessive clipping: {clipping_ratio*100:.1f}% of samples")
            
            # Check dynamic range
            dynamic_range = 20 * np.log10(np.max(np.abs(y)) / (np.mean(np.abs(y)) + 1e-6))
            metrics['dynamic_range'] = dynamic_range
            if dynamic_range < self.min_dynamic_range:
                issues.append(f"Low dynamic range: {dynamic_range:.1f}dB")
            
            # Calculate RMS energy
            rms = librosa.feature.rms(y=y)[0]
            metrics['rms_mean'] = float(np.mean(rms))
            metrics['rms_std'] = float(np.std(rms))
            
        except Exception as e:
            issues.append(f"Error analyzing file: {str(e)}")
        
        return len(issues) == 0, issues, metrics
    
    def validate_dataset(self, downloads_dir: Path) -> Dict[str, Dict]:
        """Validate all audio files in the dataset"""
        validation_results = {
            "files": {},
            "summary": {
                "total_files": 0,
                "passed_files": 0,
                "failed_files": 0,
                "average_metrics": {}
            }
        }
        
        all_metrics = []
        
        for genre_dir in downloads_dir.iterdir():
            if not genre_dir.is_dir():
                continue
                
            print(f"\nValidating {genre_dir.name} tracks...")
            
            for audio_file in genre_dir.glob("*.mp3"):
                passed, issues, metrics = self.check_audio_quality(audio_file)
                validation_results["summary"]["total_files"] += 1
                
                if not passed:
                    validation_results["files"][str(audio_file)] = {
                        "passed": False,
                        "issues": issues,
                        "metrics": metrics
                    }
                    validation_results["summary"]["failed_files"] += 1
                    print(f"Quality issues in {audio_file.name}:")
                    for issue in issues:
                        print(f"  - {issue}")
                else:
                    validation_results["summary"]["passed_files"] += 1
                    print(f"Validated: {audio_file.name}")
                
                all_metrics.append(metrics)
        
        # Calculate average metrics
        if all_metrics:
            validation_results["summary"]["average_metrics"] = {
                key: np.mean([m[key] for m in all_metrics if key in m])
                for key in all_metrics[0].keys()
            }
        
        return validation_results