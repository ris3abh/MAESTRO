from music_download.download_pipeline import MusicDownloadPipeline
from music_download.metadata_processor import MetadataProcessor
from music_download.quality_validator import AudioQualityValidator
from music_download.audio_preprocessor import AudioPreprocessor
from music_download.feature_extractor import FeatureExtractor
from pathlib import Path
import json
import time

def save_pipeline_summary(summary_path: Path, pipeline_stats: dict):
    """Save complete pipeline summary"""
    with open(summary_path, 'w') as f:
        json.dump(pipeline_stats, f, indent=4)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Music Dataset Pipeline")
    parser.add_argument(
        "--config", 
        required=True,
        help="Path to JSON config file containing playlist URLs and genres"
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip download phase and only process existing files"
    )
    parser.add_argument(
        "--skip-preprocessing",
        action="store_true",
        help="Skip audio preprocessing"
    )
    parser.add_argument(
        "--skip-features",
        action="store_true",
        help="Skip feature extraction"
    )
    
    args = parser.parse_args()
    
    # Setup paths
    project_root = Path(__file__).parent
    downloads_dir = project_root / "downloads"
    processed_dir = project_root / "processed"
    features_dir = project_root / "features"
    
    # Create necessary directories
    processed_dir.mkdir(exist_ok=True)
    features_dir.mkdir(exist_ok=True)
    
    # Initialize pipeline statistics
    pipeline_stats = {
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "phases": {},
        "summary": {
            "total_tracks_processed": 0,
            "failed_tracks": 0,
            "total_duration": 0
        }
    }
    
    try:
        # 1. Download Phase
        if not args.skip_download:
            print("\n=== Starting Download Phase ===")
            start_time = time.time()
            
            pipeline = MusicDownloadPipeline(args.config)
            pipeline.run()
        
            # Extract metadata and validate quality
            print("\n=== Extracting Metadata ===")
            metadata_processor = MetadataProcessor(downloads_dir)
            metadata = metadata_processor.run()
            
            print("\n=== Validating Audio Quality ===")
            validator = AudioQualityValidator()
            validation_results = validator.validate_dataset(downloads_dir)
            
            with open(downloads_dir / "validation_results.json", "w") as f:
                json.dump(validation_results, f, indent=4)
            
            pipeline_stats["phases"]["download"] = {
                "duration": time.time() - start_time,
                "tracks_downloaded": len(metadata["tracks"]),
                "validation_summary": validation_results["summary"]
            }
        
        # 2. Preprocessing Phase
        if not args.skip_preprocessing:
            print("\n=== Starting Preprocessing Phase ===")
            start_time = time.time()
            
            preprocessor = AudioPreprocessor()
            preprocessing_stats = preprocessor.process_dataset(downloads_dir, processed_dir)
            
            with open(processed_dir / "preprocessing_stats.json", "w") as f:
                json.dump(preprocessing_stats, f, indent=4)
            
            pipeline_stats["phases"]["preprocessing"] = {
                "duration": time.time() - start_time,
                "tracks_processed": preprocessing_stats["processed_files"],
                "failed_tracks": preprocessing_stats["failed_files"]
            }
        
        # 3. Feature Extraction Phase
        if not args.skip_features:
            print("\n=== Starting Feature Extraction Phase ===")
            start_time = time.time()
            
            extractor = FeatureExtractor()
            source_dir = processed_dir if not args.skip_preprocessing else downloads_dir
            features = extractor.process_dataset(source_dir)
            
            with open(features_dir / "features.json", "w") as f:
                json.dump(features, f, indent=4)
            
            pipeline_stats["phases"]["feature_extraction"] = {
                "duration": time.time() - start_time,
                "tracks_analyzed": features["statistics"]["processed_files"],
                "failed_tracks": features["statistics"]["failed_files"]
            }
        
        # Update pipeline summary
        pipeline_stats["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        pipeline_stats["total_duration"] = time.time() - start_time
        
        # Save pipeline summary
        save_pipeline_summary(project_root / "pipeline_summary.json", pipeline_stats)
        
        print("\n=== Pipeline Execution Complete ===")
        print(f"Total execution time: {pipeline_stats['total_duration']:.2f} seconds")
        print("Check pipeline_summary.json for detailed statistics")
        
    except Exception as e:
        print(f"\nError in pipeline execution: {str(e)}")
        pipeline_stats["error"] = str(e)
        save_pipeline_summary(project_root / "pipeline_summary.json", pipeline_stats)
        raise

if __name__ == "__main__":
    main()


# # Run complete pipeline
# python main.py --config playlists.json

# # Skip download and only process existing files
# python main.py --config playlists.json --skip-download

# # Run specific phases
# python main.py --config playlists.json --skip-download --skip-preprocessing