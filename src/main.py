from gui.gui import YouTubeDownloaderGUI

if __name__ == '__main__':
    try:
        app = YouTubeDownloaderGUI()
        app.run()
    except Exception as e:
        print(e)
        input("Press Enter to exit...")