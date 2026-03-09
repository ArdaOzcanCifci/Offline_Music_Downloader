#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Music Offline Downloader
PyQt5 based application to download music and listen offline using YouTube Music API
"""

import sys
import os
import threading
import time
from datetime import datetime
from pathlib import Path


# PyQt5 imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLineEdit, QLabel, QListWidget, QListWidgetItem,
    QProgressBar, QFileDialog, QMessageBox, QStatusBar, QMenuBar,
    QMenu, QAction, QTextEdit, QSplitter, QGroupBox, QFormLayout,
    QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QDialog, QSlider
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

# API imports
from ytmusicapi import YTMusic
import yt_dlp
import mutagen
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC, APIC, USLT
from mutagen.mp3 import MP3

import sys
import os

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

ydl_opts = {
    'ffmpeg_location': os.getcwd(),
}


class DownloadThread(QThread):
    """Background thread class for music downloading process"""
    progress_signal = pyqtSignal(int, str)  # progress, message
    finished_signal = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, video_url, output_path, metadata=None):
        super().__init__()
        self.video_url = video_url
        self.output_path = output_path
        self.metadata = metadata or {}
        
    def run(self):
        try:
            self.progress_signal.emit(0, "Downloading video...")
            
            # Check FFmpeg path
            ffmpeg_path = os.environ.get('FFMPEG_PATH', None)
            
            # Audio downloading with yt-dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [self.progress_hook],
                'ffmpeg_location': ffmpeg_path,  # FFmpeg yolunu ayarla
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.video_url, download=True)
                filename = ydl.prepare_filename(info)
                mp3_file = os.path.splitext(filename)[0] + '.mp3'
            
            # Add metadata
            if self.metadata:
                self.add_metadata(mp3_file)
                
            self.progress_signal.emit(100, "Download completed!")
            self.finished_signal.emit(True, f"Downloaded successfully: {mp3_file}")
            
        except Exception as e:
            error_msg = str(e)
            if "ffprobe and ffmpeg not found" in error_msg:
                self.finished_signal.emit(False, "FFmpeg not found. Please install FFmpeg on your system or specify the FFmpeg path in application settings.")
            else:
                self.finished_signal.emit(False, f"Download error: {error_msg}")
    
    def progress_hook(self, d):
        """Download progress hook"""
        if d['status'] == 'downloading':
            try:
                # İlerleme yüzdesini hesapla
                if 'downloaded_bytes' in d and 'total_bytes' in d:
                    progress = int((d['downloaded_bytes'] / d['total_bytes']) * 100)
                    self.progress_signal.emit(progress, f"Downloading: {progress}%")
                elif 'downloaded_bytes' in d and 'total_bytes_estimate' in d:
                    progress = int((d['downloaded_bytes'] / d['total_bytes_estimate']) * 100)
                    self.progress_signal.emit(progress, f"Downloading: {progress}%")
            except:
                pass
        elif d['status'] == 'finished':
            self.progress_signal.emit(95, "Converting to MP3...")
    
    def add_metadata(self, file_path):
        """Add metadata (title, artist, etc.) to MP3 file"""
        try:
            audio = MP3(file_path, ID3=ID3)
            
            # Add required tags
            if 'title' in self.metadata:
                audio.tags.add(TIT2(encoding=3, text=self.metadata['title']))
            if 'artist' in self.metadata:
                audio.tags.add(TPE1(encoding=3, text=self.metadata['artist']))
            if 'album' in self.metadata:
                audio.tags.add(TALB(encoding=3, text=self.metadata['album']))
            if 'genre' in self.metadata:
                audio.tags.add(TCON(encoding=3, text=self.metadata['genre']))
            if 'year' in self.metadata:
                audio.tags.add(TDRC(encoding=3, text=self.metadata['year']))
                
            audio.save()
        except Exception as e:
            print(f"Add metadatame hatası: {e}")

class YouTubeMusicApp(QMainWindow):
    """Main application class"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Music Offline Downloader")
        self.setGeometry(100, 100, 1000, 700)
        
        # Variables
        self.ytmusic = None
        self.download_folder = os.path.join(os.path.expanduser("~"), "Music", "YouTube_Music")
        self.current_downloads = []
        
        # Music player variables
        self.media_player = QMediaPlayer()
        self.media_player.setVolume(30) 
        self.media_player.mediaStatusChanged.connect(self._handle_media_status_changed)
        self.media_player.positionChanged.connect(self._update_time_slider)
        self.media_player.durationChanged.connect(self._update_duration)
        self.current_playlist = []
        self.current_song_index = -1
        self.is_playing = False
        self.is_shuffled = False
        self.is_seeking = False
        
        # Create folders
        os.makedirs(self.download_folder, exist_ok=True)
        
        # Create interface
        self.init_ui()
        
        # Initialize YouTube Music API
        self.init_ytmusic()
        
    def init_ui(self):
        """Initialize interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Top menu
        self.create_menu()
        
        # Search section
        search_group = QGroupBox("Search on YouTube Music")
        search_layout = QFormLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter song, album, or artist to search...")
        self.search_input.returnPressed.connect(self.search_music)
        
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Song", "Album", "Artist", "Video"])
        
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_music)
        
        search_hbox = QHBoxLayout()
        search_hbox.addWidget(self.search_input)
        search_hbox.addWidget(self.search_type_combo)
        search_hbox.addWidget(self.search_button)
        
        search_layout.addRow("Search:", search_hbox)
        search_group.setLayout(search_layout)
        
        # Results list
        results_group = QGroupBox("Search Results")
        results_layout = QVBoxLayout()
        
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.add_to_download_queue)
        
        results_layout.addWidget(self.results_list)
        results_group.setLayout(results_layout)
        
        # Download queue
        queue_group = QGroupBox("Download Queue")
        queue_layout = QVBoxLayout()
        
        queue_controls = QHBoxLayout()
        self.add_to_queue_btn = QPushButton("Add to Queue")
        self.add_to_queue_btn.clicked.connect(self.add_to_download_queue)
        self.remove_from_queue_btn = QPushButton("Remove from Queue")
        self.remove_from_queue_btn.clicked.connect(self.remove_from_queue)
        self.clear_queue_btn = QPushButton("Clear Queue")
        self.clear_queue_btn.clicked.connect(self.clear_queue)
        
        queue_controls.addWidget(self.add_to_queue_btn)
        queue_controls.addWidget(self.remove_from_queue_btn)
        queue_controls.addWidget(self.clear_queue_btn)
        
        self.download_queue_list = QListWidget()
        
        self.start_download_btn = QPushButton("Start Download")
        self.start_download_btn.clicked.connect(self.start_download)
        self.start_download_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        queue_layout.addLayout(queue_controls)
        queue_layout.addWidget(self.download_queue_list)
        queue_layout.addWidget(self.start_download_btn)
        queue_group.setLayout(queue_layout)
        
        # Progress status
        progress_group = QGroupBox("Download Status")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Arial", 10))
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_group.setLayout(progress_layout)
        
        # Right side vertical splitter (Offline music and Music player)
        right_splitter = QSplitter(Qt.Vertical)
        
        # Offline music
        offline_group = QGroupBox("Offline Music")
        offline_layout = QVBoxLayout()
        
        offline_controls = QHBoxLayout()
        self.refresh_offline_btn = QPushButton("Refresh")
        self.refresh_offline_btn.clicked.connect(self.load_offline_music)
        self.open_folder_btn = QPushButton("Music Folder")
        self.open_folder_btn.clicked.connect(self.open_music_folder)
        self.play_selected_btn = QPushButton("Play Selected")
        self.play_selected_btn.clicked.connect(self.select_song_from_list)
        
        offline_controls.addWidget(self.refresh_offline_btn)
        offline_controls.addWidget(self.open_folder_btn)
        offline_controls.addWidget(self.play_selected_btn)
        
        self.offline_list = QListWidget()
        self.offline_list.itemDoubleClicked.connect(self.play_offline_music)
        
        offline_layout.addLayout(offline_controls)
        offline_layout.addWidget(self.offline_list)
        offline_group.setLayout(offline_layout)
        
        # Music player
        player_group = QGroupBox("Music Player")
        player_layout = QVBoxLayout()
        
        # Current song info
        self.current_song_label = QLabel("Currently playing: None")
        self.current_song_label.setAlignment(Qt.AlignCenter)
        self.current_song_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        # Time slider
        self.time_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setRange(0, 100)
        self.time_slider.sliderMoved.connect(self._seek_position)
        
        self.time_layout.addWidget(self.current_time_label)
        self.time_layout.addWidget(self.time_slider)
        self.time_layout.addWidget(self.total_time_label)
        
        # Playback controls
        control_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.clicked.connect(self.play_previous)
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.toggle_play_pause)
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.clicked.connect(self.play_next)
        self.shuffle_btn = QPushButton("🔀 Shuffle")
        self.shuffle_btn.setCheckable(True)
        self.shuffle_btn.clicked.connect(self.toggle_shuffle)
        
        control_layout.addWidget(self.prev_btn)
        control_layout.addWidget(self.play_btn)
        control_layout.addWidget(self.next_btn)
        control_layout.addWidget(self.shuffle_btn)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_label = QLabel("Volume:")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        
        player_layout.addWidget(self.current_song_label)
        player_layout.addLayout(self.time_layout)
        player_layout.addLayout(control_layout)
        player_layout.addLayout(volume_layout)
        player_group.setLayout(player_layout)
        
        # Add to splitter
        right_splitter.addWidget(offline_group)
        right_splitter.addWidget(player_group)
        right_splitter.setSizes([400, 300])
        
        # Left side vertical splitter (Search, Results, Download queue, Progress status)
        left_splitter = QSplitter(Qt.Vertical)
        left_splitter.addWidget(search_group)
        left_splitter.addWidget(results_group)
        left_splitter.addWidget(queue_group)
        left_splitter.addWidget(progress_group)
        left_splitter.setSizes([150, 200, 200, 100])
        
        # Main horizontal splitter (Left and Right panels)
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([500, 500])
        
        main_layout.addWidget(main_splitter)
        
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("YouTube Music Offline Downloader - Ready")
        
        # Load initial offline music
        self.load_offline_music()
        
    def create_menu(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        settings_action = QAction('Settings', self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def init_ytmusic(self):
        """Initialize YouTube Music API"""
        try:
            # Initialize API (requires OAuth authentication)
            # Check headers_auth.json file first
            auth_file = "headers_auth.json"
            if os.path.exists(auth_file):
                self.ytmusic = YTMusic(auth_file)
                self.statusBar.showMessage("YouTube Music API initialized successfully")
            else:
                # Alternative: try initializing with YTMusic()
                self.ytmusic = YTMusic()
                self.statusBar.showMessage("YouTube Music API initialized (anonymous mode)")
        except Exception as e:
            self.statusBar.showMessage(f"API error: {str(e)}")
            QMessageBox.warning(self, "API Error", f"Could not initialize YouTube Music API: {str(e)}\n\nPlease authenticate with ytmusicapi.setup() command first.")
    
    def search_music(self):
        """Perform music search"""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Warning", "Please enter a search term!")
            return
            
        search_type = self.search_type_combo.currentText()
        
        try:
            self.status_label.setText("Searching...")
            
            # Filter by search type
            if search_type == "Song":
                results = self.ytmusic.search(query, filter="songs", limit=20)
            elif search_type == "Album":
                results = self.ytmusic.search(query, filter="albums", limit=20)
            elif search_type == "Artist":
                results = self.ytmusic.search(query, filter="artists", limit=20)
            else:  # Video
                results = self.ytmusic.search(query, filter="videos", limit=20)
            
            self.display_search_results(results, search_type)
            
        except Exception as e:
            error_msg = str(e)
            if "400" in error_msg:
                QMessageBox.critical(self, "API Error", 
                    f"HTTP 400 Bad Request error occurred.\n\n"
                    f"This error is usually caused by:\n"
                    f"1. No access to YouTube Music API\n"
                    f"2. Missing or incorrect authentication file\n"
                    f"3. API usage limit reached\n\n"
                    f"Solutions:\n"
                    f"1. Run ytmusicapi.setup() command to authenticate\n"
                    f"2. Make sure headers_auth.json file is in the correct location\n"
                    f"3. Wait a while and try again")
            else:
                QMessageBox.critical(self, "Search Error", f"Error occurred while searching: {error_msg}")
    
    def display_search_results(self, results, search_type):
        """List search results"""
        self.results_list.clear()
        
        for item in results:
            if search_type == "Song" and 'videoId' in item:
                title = item.get('title', 'Unknown Song')
                artists = ', '.join([artist['name'] for artist in item.get('artists', [])])
                album = item.get('album', {}).get('name', 'Unknown Album') if item.get('album') else 'Unknown Album'
                
                list_item = QListWidgetItem(f"{title} - {artists} ({album})")
                list_item.setData(Qt.UserRole, {
                    'type': 'song',
                    'videoId': item['videoId'],
                    'title': title,
                    'artists': artists,
                    'album': album
                })
                self.results_list.addItem(list_item)
                
            elif search_type == "Album" and 'browseId' in item:
                title = item.get('title', 'Unknown Album')
                artist = item.get('artist', {}).get('name', 'Unknown Artist') if item.get('artist') else 'Unknown Artist'
                
                list_item = QListWidgetItem(f"{title} - {artist}")
                list_item.setData(Qt.UserRole, {
                    'type': 'album',
                    'browseId': item['browseId'],
                    'title': title,
                    'artist': artist
                })
                self.results_list.addItem(list_item)
                
            elif search_type == "Artist" and 'browseId' in item:
                name = item.get('artist', 'Unknown Artist')
                
                list_item = QListWidgetItem(name)
                list_item.setData(Qt.UserRole, {
                    'type': 'artist',
                    'browseId': item['browseId'],
                    'name': name
                })
                self.results_list.addItem(list_item)
                
            elif search_type == "Video" and 'videoId' in item:
                title = item.get('title', 'Unknown Video')
                
                list_item = QListWidgetItem(title)
                list_item.setData(Qt.UserRole, {
                    'type': 'video',
                    'videoId': item['videoId'],
                    'title': title
                })
                self.results_list.addItem(list_item)
        
        self.status_label.setText(f"{len(results)} results found")
    
    def add_to_download_queue(self):
        """Add selected item to download queue"""
        current_item = self.results_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select an item!")
            return
            
        data = current_item.data(Qt.UserRole)
        
        # Check if already in queue
        for i in range(self.download_queue_list.count()):
            queue_item = self.download_queue_list.item(i)
            queue_data = queue_item.data(Qt.UserRole)
            if queue_data.get('videoId') == data.get('videoId'):
                QMessageBox.information(self, "Information", "This item is already in the queue!")
                return
        
        # Add to queue
        queue_item = QListWidgetItem(f"{data.get('title', 'Unknown')} - {data.get('artists', data.get('artist', data.get('name', '')))}")
        queue_item.setData(Qt.UserRole, data)
        self.download_queue_list.addItem(queue_item)
    
    def remove_from_queue(self):
        """Remove selected item from queue"""
        current_row = self.download_queue_list.currentRow()
        if current_row >= 0:
            self.download_queue_list.takeItem(current_row)
    
    def clear_queue(self):
        """Clear download queue"""
        self.download_queue_list.clear()
    
    def start_download(self):
        """Start downloading"""
        if self.download_queue_list.count() == 0:
            QMessageBox.warning(self, "Warning", "Download queue is empty!")
            return
            
        # Disable download button
        self.start_download_btn.setEnabled(False)
        self.status_label.setText("Downloads starting...")
        
        # Download all items in queue
        for i in range(self.download_queue_list.count()):
            queue_item = self.download_queue_list.item(i)
            data = queue_item.data(Qt.UserRole)
            
            if data.get('type') in ['song', 'video'] and 'videoId' in data:
                video_url = f"https://www.youtube.com/watch?v={data['videoId']}"
                
                # Create metadata
                metadata = {
                    'title': data.get('title', ''),
                    'artist': data.get('artists', data.get('artist', data.get('name', ''))),
                    'album': data.get('album', ''),
                    'genre': 'YouTube Music',
                    'year': str(datetime.now().year)
                }
                
                # Start downloading thread
                thread = DownloadThread(video_url, self.download_folder, metadata)
                thread.progress_signal.connect(self.update_download_progress)
                thread.finished_signal.connect(self.download_finished)
                thread.start()
                
                self.current_downloads.append(thread)
    
    def update_download_progress(self, progress, message):
        """Update download progress"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
    
    def download_finished(self, success, message):
        """When download is finished"""
        if success:
            self.statusBar.showMessage(message, 5000)
            self.load_offline_music()  # Update offline list
        else:
            QMessageBox.critical(self, "Download Error", message)
        
        # Re-enable download button
        self.start_download_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Download completed")
    
    def load_offline_music(self):
        """List offline music"""
        self.offline_list.clear()
        
        if not os.path.exists(self.download_folder):
            return
            
        # Find mp3 files
        for file_path in Path(self.download_folder).glob("*.mp3"):
            list_item = QListWidgetItem(file_path.stem)  # File name (without extension)
            list_item.setData(Qt.UserRole, str(file_path))
            self.offline_list.addItem(list_item)
    
    def play_offline_music(self, item):
        """Play offline music"""
        file_path = item.data(Qt.UserRole)
        
        # Update playlist
        self.update_playlist()
        
        # Find selected song index
        for i, song in enumerate(self.current_playlist):
            if song['path'] == file_path:
                self.current_song_index = i
                break
        
        # Play the music
        self.play_current_song()
    
    def select_song_from_list(self):
        """Select a song from list and play"""
        current_item = self.offline_list.currentItem()
        if current_item:
            self.play_offline_music(current_item)
        else:
            QMessageBox.warning(self, "Warning", "Please select a song!")
    
    def update_playlist(self):
        """Update playlist"""
        self.current_playlist = []
        for i in range(self.offline_list.count()):
            item = self.offline_list.item(i)
            file_path = item.data(Qt.UserRole)
            self.current_playlist.append({
                'path': file_path,
                'name': item.text()
            })
    
    def play_current_song(self):
        """Play current song"""
        if self.current_song_index >= 0 and self.current_song_index < len(self.current_playlist):
            song = self.current_playlist[self.current_song_index]
            file_path = song['path']
            
            # Update song info
            self.current_song_label.setText(f"Currently playing: {song['name']}")
            
            # Check if file exists
            if not os.path.exists(file_path):
                QMessageBox.critical(self, "Error", f"Song file not found: {song['name']}\nThe file may have been deleted or moved.")
                self.statusBar.showMessage(f"Song file not found: {song['name']}")
                return
            
            # Stop media player and load new song
            self.media_player.stop()
            url = QUrl.fromLocalFile(file_path)
            self.media_player.setMedia(QMediaContent(url))
            
            # Wait a little bit and play
            QTimer.singleShot(100, self._start_playback)
        else:
            QMessageBox.warning(self, "Warning", "No song to play!")
    
    def _start_playback(self):
        """Start playing the song"""
        # Check media status
        media_status = self.media_player.mediaStatus()
        
        if media_status == QMediaPlayer.LoadedMedia or media_status == QMediaPlayer.BufferedMedia:
            self.media_player.play()
            self.is_playing = True
            self.play_btn.setText("⏸ Pause")
            
            # Show info in status bar
            if self.current_song_index >= 0 and self.current_song_index < len(self.current_playlist):
                song = self.current_playlist[self.current_song_index]
                self.statusBar.showMessage(f"Now playing: {song['name']}")
        elif media_status == QMediaPlayer.InvalidMedia:
            if self.current_song_index >= 0 and self.current_song_index < len(self.current_playlist):
                song = self.current_playlist[self.current_song_index]
                QMessageBox.critical(self, "Error", f"Song cannot be played: {song['name']}\nThe file is corrupted or unsupported.")
                self.statusBar.showMessage(f"Song cannot be played: {song['name']}")
        else:
            # If in another status wait and retry
            QTimer.singleShot(200, self._start_playback)
    
    def _handle_media_status_changed(self, status):
        """When media status changed"""
        if status == QMediaPlayer.EndOfMedia and self.is_playing:
            # Play next song when current song is over
            self.play_next()
        elif status == QMediaPlayer.InvalidMedia and self.is_playing:
            if self.current_song_index >= 0 and self.current_song_index < len(self.current_playlist):
                song = self.current_playlist[self.current_song_index]
                QMessageBox.critical(self, "Error", f"Song cannot be played: {song['name']}\nThe file is corrupted or unsupported.")
                self.statusBar.showMessage(f"Song cannot be played: {song['name']}")
                self.is_playing = False
                self.play_btn.setText("▶ Play")
    
    def _update_duration(self, duration):
        """Adjust time slider when song duration is updated"""
        if duration > 0 and not self.is_seeking:
            self.time_slider.setRange(0, duration)
            self.total_time_label.setText(self._format_time(duration))
    
    def _update_time_slider(self, position):
        """Update time slider when song position changes"""
        if not self.is_seeking:
            self.time_slider.setValue(position)
            self.current_time_label.setText(self._format_time(position))
    
    def _seek_position(self, position):
        """When the position is changed by dragging the time slider"""
        if self.media_player.duration() > 0:
            self.is_seeking = True
            self.media_player.setPosition(position)
            self.is_seeking = False
    
    def _format_time(self, milliseconds):
        """Convert milliseconds to minutes:seconds format"""
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def toggle_play_pause(self):
        """Play/Pause button action"""
        if self.current_song_index >= 0 and self.current_song_index < len(self.current_playlist):
            if self.is_playing:
                self.media_player.pause()
                self.is_playing = False
                self.play_btn.setText("▶ Play")
                self.statusBar.showMessage("Music paused")
            else:
                self.media_player.play()
                self.is_playing = True
                self.play_btn.setText("⏸ Pause")
                self.statusBar.showMessage("Music playing")
        else:
            # If no song is selected, play the first song
            if self.offline_list.count() > 0:
                self.current_song_index = 0
                self.play_current_song()
            else:
                QMessageBox.warning(self, "Warning", "No song to play!")
    
    def play_next(self):
        """Play next song"""
        if len(self.current_playlist) == 0:
            return
        
        if self.is_shuffled:
            # Select a random song in shuffle mode
            import random
            self.current_song_index = random.randint(0, len(self.current_playlist) - 1)
        else:
            # Next song in normal mode
            self.current_song_index = (self.current_song_index + 1) % len(self.current_playlist)
        
        self.play_current_song()
    
    def play_previous(self):
        """Play previous song"""
        if len(self.current_playlist) == 0:
            return
        
        if self.is_shuffled:
            # Select a random song in shuffle mode
            import random
            self.current_song_index = random.randint(0, len(self.current_playlist) - 1)
        else:
            # Previous song in normal mode
            self.current_song_index = (self.current_song_index - 1) % len(self.current_playlist)
        
        self.play_current_song()
    
    def toggle_shuffle(self):
        """Toggle shuffle mode"""
        self.is_shuffled = self.shuffle_btn.isChecked()
        if self.is_shuffled:
            self.shuffle_btn.setStyleSheet("background-color: #4CAF50; color: white;")
            self.statusBar.showMessage("Shuffle mode active")
        else:
            self.shuffle_btn.setStyleSheet("")
            self.statusBar.showMessage("Normal mode active")
    
    def set_volume(self, value):
        """Adjust volume level"""
        self.media_player.setVolume(value)
        self.statusBar.showMessage(f"Volume: {value}%")
    
    def open_music_folder(self):
        """Open music folder"""
        import subprocess
        try:
            if sys.platform == "win32":
                os.startfile(self.download_folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", self.download_folder])
            else:
                subprocess.run(["xdg-open", self.download_folder])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Folder cannot be opened: {str(e)}")
    
    def open_settings(self):
        """Open settings window"""
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec_()
    
    def show_about(self):
        """Show about window"""
        about_text = """
        <h2>YouTube Music Offline Downloader</h2>
        <p><b>Version:</b> 1.0</p>
        <p><b>Description:</b> PyQt5 based application to download music and listen offline using YouTube Music API</p>
        <p><b>Libraries Used:</b></p>
        <ul>
            <li>ytmusicapi - YouTube Music API integration</li>
            <li>pytube - YouTube video download</li>
            <li>mutagen - MP3 metadata operations</li>
            <li>PyQt5 - GUI interface</li>
        </ul>
        <p><i>Note: This application is for educational purposes only. Copyrights must be respected.</i></p>
        """
        
        QMessageBox.about(self, "About", about_text)

class SettingsDialog(QDialog):
    """Settings dialog window"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 400, 300)
        
        layout = QVBoxLayout()
        
        # Music folder setting
        folder_group = QGroupBox("Music Folder")
        folder_layout = QHBoxLayout()
        
        self.folder_input = QLineEdit(parent.download_folder)
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_folder)
        
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(self.browse_btn)
        folder_group.setLayout(folder_layout)
        
        # Other settings
        other_group = QGroupBox("Other Settings")
        other_layout = QFormLayout()
        
        self.auto_download_check = QCheckBox("Auto download")
        self.auto_download_check.setChecked(False)
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["High", "Medium", "Low"])
        self.quality_combo.setCurrentText("High")
        
        self.ffmpeg_path_input = QLineEdit()
        self.ffmpeg_path_input.setPlaceholderText("Enter FFmpeg path here (optional)")
        self.ffmpeg_browse_btn = QPushButton("Browse")
        self.ffmpeg_browse_btn.clicked.connect(self.browse_ffmpeg)
        
        ffmpeg_layout = QHBoxLayout()
        ffmpeg_layout.addWidget(self.ffmpeg_path_input)
        ffmpeg_layout.addWidget(self.ffmpeg_browse_btn)
        
        other_layout.addRow("Download Quality:", self.quality_combo)
        other_layout.addWidget(self.auto_download_check)
        other_layout.addRow("FFmpeg Path:", ffmpeg_layout)
        other_group.setLayout(other_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addWidget(folder_group)
        layout.addWidget(other_group)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def browse_folder(self):
        """Folder selector"""
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if folder:
            self.folder_input.setText(folder)
    
    def browse_ffmpeg(self):
        """FFmpeg file selector"""
        ffmpeg_file, _ = QFileDialog.getOpenFileName(self, "Select FFmpeg File", "", "FFmpeg (ffmpeg.exe ffmpeg ffprobe ffprobe.exe)")
        if ffmpeg_file:
            self.ffmpeg_path_input.setText(ffmpeg_file)
    
    def save_settings(self):
        """Save settings"""
        parent = self.parent()
        parent.download_folder = self.folder_input.text()
        os.makedirs(parent.download_folder, exist_ok=True)
        
        # Save FFmpeg path
        ffmpeg_path = self.ffmpeg_path_input.text().strip()
        if ffmpeg_path:
            # Make FFmpeg path available globally in the application
            os.environ['FFMPEG_PATH'] = ffmpeg_path
        
        QMessageBox.information(self, "Success", "Settings saved!")
        self.accept()

def main():
    """Application Start"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = YouTubeMusicApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()