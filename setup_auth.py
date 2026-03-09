#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Music API Authentication Setup
This script creates the necessary authentication file for ytmusicapi.
"""

import os
import sys
from ytmusicapi import YTMusic

def setup_authentication():
    """Sets up YouTube Music API authentication"""
    print("YouTube Music API Authentication Setup")
    print("=" * 50)
    
    print("\nAn OAuth flow will start in your browser for this process.")
    print("Please follow the steps below:")
    print("1. Allow 'YouTube Music' app in the opened browser tab")
    print("2. Click the 'Accept' button")
    print("3. Save the generated JSON file to this folder")
    
    try:
        # Create authentication file
        YTMusic.setup()
        
        # Check the existence of headers_auth.json file
        if os.path.exists("headers_auth.json"):
            print("\n✓ Authentication completed successfully!")
            print("✓ headers_auth.json file created.")
            print("\nYou can now run the application.")
        else:
            print("\n✗ Create authentication fileulamadı.")
            print("Please make sure the file is in this folder.")
            
    except Exception as e:
        print(f"\n✗ Authentication error: {str(e)}")
        print("\nPlease follow the steps below:")
        print("1. Create a project in Google Developer Console")
        print("2. Enable YouTube Data API v3 and YouTube Analytics API")
        print("3. Create OAuth 2.0 credentials")
        print("4. Run ytmusicapi.setup() command again")

if __name__ == "__main__":
    setup_authentication()