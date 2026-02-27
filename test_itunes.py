from services.music_service import music_service

def test_itunes():
    emotions = ["happy", "sad", "angry", "calm", "excited", "neutral"]
    
    for emotion in emotions:
        print(f"\nTesting emotion: {emotion}")
        tracks = music_service.get_recommendations_by_emotion(emotion)
        if tracks:
            print(f"✅ Found {len(tracks)} tracks")
            print(f"   Top track: {tracks[0]['title']} by {tracks[0]['artist']}")
            print(f"   Preview: {tracks[0]['audioUrl']}")
        else:
            print(f"❌ No tracks found for {emotion}")

if __name__ == "__main__":
    test_itunes()
