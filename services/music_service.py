import requests

class MusicService:
    def get_recommendations_by_emotion(self, emotion):
        # Map emotions to iTunes search terms
        emotion_map = {
            "happy": "happy pop",
            "sad": "sad acoustic",
            "angry": "energetic rock",
            "calm": "calm ambient",
            "excited": "dance party",
            "neutral": "chill lofi"
        }

        term = emotion_map.get(emotion.lower(), "pop")
        url = f"https://itunes.apple.com/search?term={term}&media=music&limit=15"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"iTunes API Error: {response.status_code}")
                return []
            
            data = response.json()
            tracks = []
            for item in data.get('results', []):
                tracks.append({
                    "id": str(item['trackId']),
                    "title": item['trackName'],
                    "artist": item['artistName'],
                    "emotion": emotion,
                    "coverUrl": item['artworkUrl100'],
                    "duration": self._format_duration(item.get('trackTimeMillis', 0)),
                    "audioUrl": item.get('previewUrl'),
                    "itunesUrl": item.get('trackViewUrl')
                })
            return tracks
        except Exception as e:
            print(f"Error fetching from iTunes: {e}")
            return []

    def _format_duration(self, ms):
        seconds = int((ms / 1000) % 60)
        minutes = int((ms / (1000 * 60)) % 60)
        return f"{minutes}:{seconds:02d}"

music_service = MusicService()
