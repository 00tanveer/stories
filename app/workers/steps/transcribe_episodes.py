import json
from app.services.transcribe import AssemblyAI_API
import os
from tqdm import tqdm

pods = json.load(open('data/podcasts/podcasts_metadata.json', 'r'))
eps_json = json.load(open("data/podcasts/pod_episodes_metadata.json", 'r'))
epidoes_mp3_urls = [ep['enclosureUrl'] for ep in eps_json]

aai = AssemblyAI_API() 

# if transcript doesn't exist in data/podcasts/{podcast_title}/ create it with name {episode_title}_transcript.txt
for pod in pods:
    pod_title = pod.get('title', 'unknown_podcast').replace('/', '_').replace('\\', '_')
    pod_dir = os.path.join('data/podcasts/', pod_title)
    # if {episode_title}_transcript.txt doesn't exist, create it
    for ep in eps_json:
        if ep['feedId'] == pod['id']:
            episode_title = ep.get('title', 'unknown_episode').replace('/', '_').replace('\\', '_')
            transcript_path = os.path.join(pod_dir, f"{episode_title}_transcript.txt")
            if not os.path.exists(transcript_path):
                mp3_url = ep.get('enclosureUrl')
                if mp3_url:
                    print(f"Transcribing episode: {episode_title} from podcast: {pod_title}")
                    transcript_json = aai.transcribe_audio(mp3_url)
                    if transcript_json:
                        with open(transcript_path, 'w') as f:
                            json.dump(transcript_json, f, indent=2)
                        print(f"Saved AssemblyAI transcript request receipt to {transcript_path}")
                    else:
                        print(f"Failed to transcribe episode: {episode_title}")


transcripts = aai.list_transcripts()
filepath = 'data/transcripts/completed_transcripts.json'
print(len(transcripts))
# transcripts = json.load(open('workers/transcripts.json', 'r' ))["transcripts"]
# for t in transcripts:
#     print(f"Transcript ID: {t['id']}, Status: {t['status']}")
#     aai.delete_transcript(t['id'])

for t in tqdm(transcripts, desc="Downloading transcripts"):
    transcription_file = aai.get_transcript(t['id'])
    # print(transcription_file)
    # write to file in data/transcripts/{transcript_id}.json
    with open('data/transcripts/' + t['id'] + '.json', 'w') as f:
        json.dump(transcription_file, f, indent=2)
