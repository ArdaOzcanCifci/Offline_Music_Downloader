# YouTube Music Offline Downloader

A PyQt5 based application to download music from YouTube Music and listen offline.

## Features

- **YouTube Music Search**: Search for songs, albums, artists and videos
- **Batch Download**: Add multiple tracks to queue and download them sequentially
- **Metadata Support**: Adds title, artist, album and year information to downloaded music
- **Offline Library**: List and manage downloaded music
- **Modern Interface**: User-friendly PyQt5 based graphical interface
- **Progress Tracking**: Real-time monitoring of download process
- **Integrated Music Player**: Advanced music player that can play downloaded music
  - **Sequential Play**: Play songs in order
  - **Shuffle**: Play songs randomly
  - **Previous/Next**: Switch between songs
  - **Volume Control**: Adjust volume level
  - **Play/Pause**: Control the music

## Requirements

- Python 3.8+
- ytmusicapi
- yt-dlp (more powerful alternative to pytube)
- mutagen
- PyQt5

## Installation

1. **Check Python Version**
   ```bash
   python --version
   ```

2. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```

3. **YouTube Music API Authentication**
   
   This application uses the YouTube Music API. You need to perform OAuth authentication to use the API.

   **Step 1: Create a Project in Google Developer Console**
   1. Go to [Google Cloud Console](https://console.developers.google.com/)
   2. Create a new project
   3. Enable "YouTube Data API v3" and "YouTube Analytics API" services
   4. Create OAuth 2.0 credentials

   **Step 2: ytmusicapi Installation**
   ```bash
   pip install ytmusicapi
   ```

   **Step 3: Create Authentication File**
   ```python
   from ytmusicapi import YTMusic
   YTMusic.setup()
   ```
   
   This command will start an OAuth flow in your browser and create a `headers_auth.json` file.

## Usage

### 1. Authentication (Required on First Use)

**Important:** You must authenticate first to use the YouTube Music API.

**Easy Method (Recommended):**
```bash
python setup_auth.py
```

This command will start an OAuth flow in your browser and create the `headers_auth.json` file.

**Manual Method:**
```python
from ytmusicapi import YTMusic
YTMusic.setup()
```

### 2. Start the Application
```bash
python main.py
```

2. **Search for Music**
   - Enter a song, album or artist name in the search box
   - Select the search type (Song, Album, Artist, Video)
   - Click the "Search" button

3. **Add to Download Queue**
   - Select the music you want to download from the results list
   - Click the "Add to Queue" button

4. **Start Download**
   - Click the "Start Download" button
   - Monitor the download status from the progress bar

5. **Manage Offline Music**
   - View downloaded music from the "Offline Music" tab
   - Update the list using the "Refresh" button
   - Access the file location with the "Music Folder" button

## Folder Structure

```
youtube_music_app/
├── main.py              # Main application file
├── requirements.txt     # Python dependencies
├── README.md            # This document
└── music/               # Folder where downloaded music will be saved
    ├── Song Name - Artist.mp3
    └── ...
```

## Notes

- **Copyrights**: This application is for educational purposes only. Copyrights must be respected.
- **Internet Connection**: Internet connection is required for searching and downloading.
- **Storage Space**: Downloaded music takes up space on your computer.
- **API Limitations**: Subject to usage limitations of the YouTube Music API.

## Troubleshooting

### "API Error"
- Make sure the `headers_auth.json` file is in the correct location
- Make sure OAuth authentication was done correctly

### "Download error"
- Make sure the YouTube video URL is valid
- Check your internet connection
- Make sure the yt-dlp library is updated
- Make sure FFmpeg is installed on your system
- For FFmpeg installation: https://ffmpeg.org/download.html
- FFmpeg installation alternative: You can specify the FFmpeg path in the application settings

### "HTTP 400 Bad Request" Error
This error is usually caused by YouTube Music API access issues:
- Authentication file is missing or invalid
- API usage limit reached
- If 2FA is enabled on your Google account, additional configuration might be needed

**Solution:**
1. Re-authenticate using the `python setup_auth.py` command
2. Ensure the `headers_auth.json` file is in the application folder
3. Wait a while and try again

### PyQt5 Errors
- Make sure PyQt5 is installed correctly
- Make sure your Python version is compatible with PyQt5

## Development

This project is open to development. To contribute:

1. Fork the project
2. Create a new branch (`git checkout -b feature/new-feature`)
3. Make your changes
4. Commit (`git commit -am 'Added new feature'`)
5. Push (`git push origin feature/new-feature`)
6. Create a Pull request

## License

The free version of the vscode extension called cline was used in this project. The entire project was written by ai without any intervention. This project was developed for educational purposes. It is strongly requested to be sensitive about copyrights.