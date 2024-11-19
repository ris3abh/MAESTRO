import json
import librosa
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class TrackMetadata:
    file_path: str
    genre: str
    title: str
    duration: float
    sample_rate: int
    tempo: float
    key: Optional[str]  # Make key optional
    mean_amplitude: float
    rms_energy: float
    zero_crossing_rate: float
    spectral_centroid: float
    spectral_bandwidth: float

class MetadataProcessor:
    def __init__(self, downloads_dir: Path):
        self.downloads_dir = downloads_dir
        self.metadata_file = downloads_dir / "metadata.json"
        
    def estimate_key(self, y: np.ndarray, sr: int) -> Optional[str]:
        """Safely estimate the musical key of the track"""
        try:
            # Use chromagram for key detection
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            key_indices = np.mean(chroma, axis=1)
            key_index = np.argmax(key_indices)
            
            # Map key index to musical notation
            keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            return keys[key_index]
        except Exception as e:
            print(f"Warning: Could not estimate key: {str(e)}")
            return None

    def process_audio_file(self, audio_path: Path, genre: str) -> TrackMetadata:
        """Extract audio features and metadata from a single track"""
        # Load audio file with a standard sample rate
        y, sr = librosa.load(audio_path, sr=22050)  # Fixed sample rate for consistency
        
        # Extract basic metadata
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Extract musical features
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        key = self.estimate_key(y, sr)
        
        # Extract audio characteristics
        mean_amplitude = float(np.mean(np.abs(y)))
        rms_energy = float(np.sqrt(np.mean(y**2)))
        zero_crossing_rate = float(np.mean(librosa.feature.zero_crossing_rate(y)))
        
        # Extract spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        
        return TrackMetadata(
            file_path=str(audio_path),
            genre=genre,
            title=audio_path.stem,
            duration=duration,
            sample_rate=sr,
            tempo=float(tempo),
            key=key,
            mean_amplitude=mean_amplitude,
            rms_energy=rms_energy,
            zero_crossing_rate=zero_crossing_rate,
            spectral_centroid=float(np.mean(spectral_centroids)),
            spectral_bandwidth=float(np.mean(spectral_bandwidth))
        )
    
    def process_all_tracks(self) -> Dict[str, Any]:
        """Process all downloaded tracks and generate metadata"""
        metadata = {
            "tracks": [],
            "statistics": {
                "total_tracks": 0,
                "total_duration": 0,
                "average_tempo": 0,
                "genre_distribution": {}
            }
        }
        
        all_tempos = []
        
        # Process each genre directory
        for genre_dir in self.downloads_dir.iterdir():
            if not genre_dir.is_dir():
                continue
                
            print(f"\nProcessing {genre_dir.name} tracks...")
            genre_count = 0
            
            # Process each audio file in the genre directory
            for audio_file in genre_dir.glob("*.mp3"):
                try:
                    track_metadata = self.process_audio_file(audio_file, genre_dir.name)
                    metadata["tracks"].append(asdict(track_metadata))
                    print(f"Processed: {audio_file.name}")
                    
                    # Update statistics
                    metadata["statistics"]["total_duration"] += track_metadata.duration
                    all_tempos.append(track_metadata.tempo)
                    genre_count += 1
                    
                except Exception as e:
                    print(f"Error processing {audio_file.name}: {str(e)}")
            
            metadata["statistics"]["genre_distribution"][genre_dir.name] = genre_count
        
        # Calculate final statistics
        metadata["statistics"]["total_tracks"] = len(metadata["tracks"])
        if all_tempos:
            metadata["statistics"]["average_tempo"] = sum(all_tempos) / len(all_tempos)
        
        return metadata
    
    def save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save metadata to JSON file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=4)
    
    def run(self) -> None:
        """Run the complete metadata extraction pipeline"""
        print("Starting metadata extraction...")
        metadata = self.process_all_tracks()
        self.save_metadata(metadata)
        print(f"\nMetadata extraction complete. Saved to {self.metadata_file}")
        
        # Print summary
        stats = metadata["statistics"]
        print("\nDataset Summary:")
        print(f"Total tracks: {stats['total_tracks']}")
        print(f"Total duration: {stats['total_duration']/3600:.2f} hours")
        print(f"Average tempo: {stats['average_tempo']:.1f} BPM")
        print("\nGenre distribution:")
        for genre, count in stats['genre_distribution'].items():
            print(f"  {genre}: {count} tracks")