#!/usr/bin/env python3
# YouTube Music Playlist Downloader
version = "1.4.0"

import os
import json
from pathlib import Path
from typing import Dict, Any
from yt_dlp import YoutubeDL
from .downloader import setup_config, generate_playlist

class MusicDownloadPipeline:
    def __init__(self, config_path: str):
        """
        Initialize the music download pipeline
        
        Args:
            config_path (str): Path to JSON config file containing playlist URLs and genres
        """
        self.config_path = config_path
        self.downloads_dir = Path(os.path.dirname(os.path.dirname(__file__))) / "downloads"
        self.downloads_dir.mkdir(exist_ok=True)

    def load_config(self) -> Dict[str, Any]:
        """Load and validate the configuration file"""
        try:
            with open(self.config_path) as f:
                config = json.load(f)
                
            required_fields = ["playlists"]
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field '{field}' in config")
                    
            for playlist in config["playlists"]:
                if "url" not in playlist or "genre" not in playlist:
                    raise ValueError("Each playlist must have 'url' and 'genre' fields")
                    
            return config
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in config file")
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

    def setup_download_config(self, playlist_config: Dict[str, str]) -> Dict[str, Any]:
        """
        Set up the download configuration for a playlist
        
        Args:
            playlist_config (dict): Configuration for a single playlist
            
        Returns:
            dict: Complete download configuration
        """
        download_config = {
            "url": playlist_config["url"],
            "reverse_playlist": False,
            "use_title": True,
            "use_uploader": True,
            "use_playlist_name": True
        }
        return setup_config(download_config)

    def process_playlist(self, playlist_config: Dict[str, str]) -> None:
        """
        Process and download a single playlist
        
        Args:
            playlist_config (dict): Configuration for the playlist
        """
        genre = playlist_config["genre"]
        genre_dir = self.downloads_dir / genre
        genre_dir.mkdir(exist_ok=True)

        # Change to genre directory for download
        original_dir = os.getcwd()
        os.chdir(str(genre_dir))

        try:
            download_config = self.setup_download_config(playlist_config)
            generate_playlist(
                download_config,
                ".playlist_config.json",
                update=False,
                force_update=False,
                regenerate_metadata=False,
                single_playlist=True,
                current_playlist_name=None,
                track_num_to_update=None
            )
        finally:
            os.chdir(original_dir)

    def run(self) -> None:
        """Run the complete download pipeline"""
        config = self.load_config()
        
        for playlist in config["playlists"]:
            print(f"\nProcessing playlist for genre: {playlist['genre']}")
            print(f"URL: {playlist['url']}")
            try:
                self.process_playlist(playlist)
                print(f"Successfully downloaded playlist for {playlist['genre']}")
            except Exception as e:
                print(f"Error processing playlist: {str(e)}")

def main():
    """Main entry point for the download pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download music playlists by genre")
    parser.add_argument(
        "--config", 
        required=True,
        help="Path to JSON config file containing playlist URLs and genres"
    )
    
    args = parser.parse_args()
    
    pipeline = MusicDownloadPipeline(args.config)
    pipeline.run()

if __name__ == "__main__":
    main()