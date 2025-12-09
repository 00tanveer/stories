# Load the transcript object into memory and study them
# from app.language_models.question_detector.src.infer import InferenceModel
import asyncio
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.db.session import AsyncSessionLocal
from app.db.data_models.episode import Episode
from app.db.data_models.transcript import Transcript
from app.language_models.question_detector.src.infer import InferenceModel

from app.services.podcasts import read_episode_data


async def main():
    results = await extract_questions()
    # await extract_questions()
    await save_question_results(results)
    print("🎉 All questions & answers saved!")

def is_question(text: str, questions_model) -> bool:
    if len(text.split()) > 100:
        return False
    score = questions_model.predict(text)[0]
    if score['label'] == 'LABEL_1':
        return True 
    return False


sem = asyncio.Semaphore(10)
async def questions_from_one_episode(ep, questions_model, i):
    async with sem:
        try:
            print(f"\nNo. {i} TITLE:", ep.title, ep.id)
            transcript = ep.transcript
            if transcript is None:
                print(f"  ❌ No transcript for episode {ep.id}")
                return None
            guest = guest_speaker(transcript)
            host_questions = []
            question_answers = []
            for i,u in enumerate(transcript.utterances):
                if i == len(transcript.utterances) - 1:
                    # print(f"⚠️ Last utterance is a question; skipping answer for episode {ep.id}")
                    continue
                if u.speaker != guest and is_question(u.text, questions_model):
                    question = {
                        "start": u.start,
                        "end": u.end,
                        "confidence": u.confidence,
                        "speaker": u.speaker,
                        "text": u.text
                    }
                    # print("  Q→", question)
                    host_questions.append(question)
                    answer = transcript.utterances[i+1].text
                    question_answers.append(
                        {"question": u.text, "answer": answer}
                    )
                    # print("  A→", answer)
            # ep.host_questions = host_questions
            # ep.question_answers = question_answers

            return {
                "episode_id": ep.id,
                "guest": guest,
                "host_questions": host_questions,
                "question_answers": question_answers
            }
        except Exception as e:
            print(f'❌ Failed extracting questions from episode {ep.title}: {e}')
# Retrieve host question utterances and store them in episodes
async def extract_questions():
    questions_model = InferenceModel()
    async with AsyncSessionLocal() as session:
        episodes = (await session.execute(
            select(Episode)
            .join(Episode.transcript)
            .options(
                selectinload(Episode.transcript)
                .selectinload(Transcript.utterances)
            )
        )).scalars().all()
        print(len(episodes))
        episodes = sorted(episodes, key=lambda e: e.id)
        for ep in episodes:
            print(ep.id)
        tasks = [
            questions_from_one_episode(ep, questions_model, i)
            for i, ep in enumerate(episodes)
        ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if r is not None]
async def save_question_results(results):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for r in results:
                # print("Host questions in r:", r["episode_id"], r["host_questions"][:30])
                if not r["host_questions"]:
                    continue
                ep = await session.get(Episode, r["episode_id"])
                ep.host_questions = r["host_questions"]
                ep.question_answers = r["question_answers"]
# Find speaker with most utterance words
def guest_speaker(transcript: Transcript) -> str:
    speaker_word_count = {}
    for utt in transcript.utterances:
        word_count = len(utt.text.split())
        if utt.speaker in speaker_word_count:
            speaker_word_count[utt.speaker] += word_count
        else:
            speaker_word_count[utt.speaker] = word_count
    # Find speaker with max words
    guest = max(speaker_word_count, key=speaker_word_count.get)
    return guest  

async def get_episode_data():
    results = await read_episode_data()
    for ep, author in results:   # now it unpacks correctly
        print(author)
        print(ep.host_questions)

# # print(f"Extracted a total of host {len(all_questions)} questions from {len(transcript_files[:1])} transcripts.")
if __name__ == "__main__":
    # asyncio.run(get_episode_data())
    asyncio.run(main())


# total questions:  5333
# Questions:
#   total: 5333
#   unique: 1757
#   duplicates: 3576

# QA Pairs:
#   total: 5320
#   unique: 2407
#   duplicates: 2913

# data stream
# 243 episodes
# 121 transcripts

# first 10 episodes w/ trascripts sorted 
# 28356570570
# 29292900154
# 29521002925
# 29522808496
# 29818166796
# 30451431305
# 30831604383
# 31641430512
# 32218939088
# 32568857117