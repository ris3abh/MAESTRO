import librosa
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

@dataclass
class AudioFeatures:
    # Temporal features
    tempo: float
    beats: List[float]
    
    # Spectral features
    spectral_centroid: List[float]
    spectral_bandwidth: List[float]
    spectral_rolloff: List[float]
    
    # Harmonic features
    chromagram: List[List[float]]
    key_strength: List[float]
    
    # Rhythmic features
    onset_strength: List[float]
    tempo_confidence: float
    
    # Energy features
    rms_energy: List[float]
    zero_crossing_rate: List[float]

class FeatureExtractor:
    def __init__(self, 
                frame_size: float = 0.05,  # 50ms frames
                hop_length: int = 512):
        """
        Initialize feature extractor
        
        Args:
            frame_size: Size of analysis frames in seconds
            hop_length: Number of samples between frames
        """
        self.frame_size = frame_size
        self.hop_length = hop_length
    
    def extract_temporal_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract temporal features (tempo, beats)"""
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=self.hop_length)
        beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=self.hop_length)
        
        return {
            "tempo": float(tempo),
            "beats": beat_times.tolist()
        }
    
    def extract_spectral_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract spectral features"""
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=self.hop_length)[0]
        spectral_bandwidths = librosa.feature.spectral_bandwidth(y=y, sr=sr, hop_length=self.hop_length)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=self.hop_length)[0]
        
        return {
            "spectral_centroid": spectral_centroids.tolist(),
            "spectral_bandwidth": spectral_bandwidths.tolist(),
            "spectral_rolloff": spectral_rolloff.tolist()
        }
    
    def extract_harmonic_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract harmonic features"""
        chromagram = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=self.hop_length)
        key_strengths = np.max(chromagram, axis=1)
        
        return {
            "chromagram": chromagram.tolist(),
            "key_strength": key_strengths.tolist()
        }
    
    def extract_rhythmic_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract rhythmic features"""
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=self.hop_length)
        tempo, confidence = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        
        return {
            "onset_strength": onset_env.tolist(),
            "tempo_confidence": float(confidence)
        }
    
    def extract_energy_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract energy-based features"""
        rms = librosa.feature.rms(y=y, hop_length=self.hop_length)[0]
        zcr = librosa.feature.zero_crossing_rate(y=y, hop_length=self.hop_length)[0]
        
        return {
            "rms_energy": rms.tolist(),
            "zero_crossing_rate": zcr.tolist()
        }
    
    def extract_features(self, audio_path: Path) -> AudioFeatures:
        """Extract all features from an audio file"""
        # Load audio
        y, sr = librosa.load(audio_path, sr=None)
        
        # Extract all feature types
        temporal = self.extract_temporal_features(y, sr)
        spectral = self.extract_spectral_features(y, sr)
        harmonic = self.extract_harmonic_features(y, sr)
        rhythmic = self.extract_rhythmic_features(y, sr)
        energy = self.extract_energy_features(y, sr)
        
        # Combine all features
        return AudioFeatures(
            **temporal,
            **spectral,
            **harmonic,
            **rhythmic,
            **energy
        )
    
    def process_dataset(self, input_dir: Path) -> Dict[str, Any]:
        """Process entire dataset"""
        dataset_features = {
            "features": {},
            "statistics": {
                "total_files": 0,
                "processed_files": 0,
                "failed_files": 0,
                "average_features": {}
            }
        }
        
        all_features = []
        
        # Process each genre directory
        for genre_dir in input_dir.iterdir():
            if not genre_dir.is_dir():
                continue
                
            print(f"\nExtracting features from {genre_dir.name} tracks...")
            
            # Process each audio file
            for audio_file in genre_dir.glob("*.mp3"):
                dataset_features["statistics"]["total_files"] += 1
                
                try:
                    features = self.extract_features(audio_file)
                    dataset_features["features"][str(audio_file)] = asdict(features)
                    all_features.append(features)
                    
                    dataset_features["statistics"]["processed_files"] += 1
                    print(f"Processed: {audio_file.name}")
                    
                except Exception as e:
                    dataset_features["statistics"]["failed_files"] += 1
                    print(f"Error processing {audio_file.name}: {str(e)}")
        
        # Calculate average features
        if all_features:
            dataset_features["statistics"]["average_features"] = {
                "tempo": np.mean([f.tempo for f in all_features]),
                "spectral_centroid": np.mean([np.mean(f.spectral_centroid) for f in all_features]),
                "spectral_bandwidth": np.mean([np.mean(f.spectral_bandwidth) for f in all_features]),
                "rms_energy": np.mean([np.mean(f.rms_energy) for f in all_features])
            }
        
        return dataset_features