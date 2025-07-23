import os
import time
from groq import Groq
from pathlib import Path

import traceback
# Load Groq API key from ../groq_api_key.txt
API_KEY_PATH = Path(__file__).resolve().parent.parent / "groq_api_key.txt"
try:
    with open(API_KEY_PATH, "r") as f:
        groq_api_key = f.read().strip()
except FileNotFoundError:
    raise FileNotFoundError(f"[TTS] API key file not found at {API_KEY_PATH}")
client = Groq(api_key=groq_api_key)


# Configuration
SPEECH_OUTPUT_DIR = os.path.join("stream", "speech")
os.makedirs(SPEECH_OUTPUT_DIR, exist_ok=True)

# Available voices for PlayAI TTS
ENGLISH_VOICES = [
    "Fritz-PlayAI", "Sara-PlayAI", "Kyle-PlayAI", "Madison-PlayAI", 
    "Kai-PlayAI", "Ivy-PlayAI", "Ethan-PlayAI", "Grace-PlayAI",
    "Hazel-PlayAI", "Mason-PlayAI", "Zoe-PlayAI", "Oliver-PlayAI",
    "Ruby-PlayAI", "Leo-PlayAI", "Luna-PlayAI", "Finn-PlayAI",
    "Stella-PlayAI", "Theo-PlayAI", "Iris-PlayAI", "Felix-PlayAI",
    "Sage-PlayAI", "Phoenix-PlayAI", "River-PlayAI", "Quinn-PlayAI",
    "Aria-PlayAI", "Hunter-PlayAI"
]

# For a Victorian-era Darwin character, consider these voices:
DARWIN_SUITABLE_VOICES = [
    "Fritz-PlayAI",    # Deep, distinguished
    "Oliver-PlayAI",   # Classic, refined
    "Theo-PlayAI",     # Intellectual tone
    "Felix-PlayAI",    # Sophisticated
    "Mason-PlayAI"     # Authoritative
]

def run_tts(text, voice="Fritz-PlayAI", model="playai-tts", response_format="wav"):
    """
    Generate speech using Groq's PlayAI TTS model
    
    Args:
        text (str): Text to convert to speech (max 10K characters)
        voice (str): Voice to use for generation
        model (str): Model ID ('playai-tts' or 'playai-tts-arabic')
        response_format (str): Audio format ('wav')
    
    Returns:
        str: Path to the generated audio file
    """
    try:
        # Validate input length
        if len(text) > 10000:
            print(f"[TTS] Warning: Text length ({len(text)}) exceeds 10K limit, truncating...")
            text = text[:10000]
        
        # Generate unique filename with timestamp
        timestamp = int(time.time() * 1000)
        filename = f"darwin_speech_{timestamp}.{response_format}"
        speech_file_path = os.path.join(SPEECH_OUTPUT_DIR, filename)
        
        print(f"[TTS] Generating speech with Groq PlayAI...")
        print(f"[TTS] Model: {model}, Voice: {voice}")
        print(f"[TTS] Text length: {len(text)} characters")
        print(f"[TTS] Output file: {speech_file_path}")
        
        # Generate speech using Groq PlayAI TTS
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format=response_format
        )
        
        # Write the audio data to file
        response.write_to_file(speech_file_path)
        
        print(f"[TTS] Speech generation completed successfully")
        print(f"[TTS] File saved to: {speech_file_path}")
        
        return speech_file_path
        
    
    except Exception as e:
        print(f"[TTS] Error generating speech: {e}")
        traceback.print_exc()
        return None


def run_tts_for_darwin(text):
    """
    Generate speech specifically tuned for Darwin character
    Uses a voice that sounds distinguished and Victorian-era appropriate
    """
    # Choose a voice that suits Darwin's character
    darwin_voice = "Basil-PlayAI"  # Deep, distinguished voice
    return run_tts(text, voice=darwin_voice)

def test_tts():
    """Test function to verify TTS is working"""

    common_words_str = "the.....be.....to.....of.....and.....a.....in.....that.....have.....I" \
                   ".....it.....for.....not.....on.....with.....he.....as.....you.....do.....at" \
                   ".....this.....but.....his.....by.....from.....they.....we.....say.....her.....she" \
                   ".....or.....an.....will.....my.....one.....all.....would.....there.....their.....what" \
                   ".....so.....up.....out.....if.....about.....who.....get.....which.....go.....me" \
                   ".....house.....dog.....car.....book.....apple.....school.....chair.....street.....water.....food"
    pts2 = "time.....year.....people.....way.....day.....man.....thing.....woman.....life.....child" \
       ".....world.....school.....state.....family.....student.....group.....country.....problem.....hand" \
       ".....part.....place.....case.....week.....company.....system.....program.....question.....work" \
       ".....government.....number.....night.....point.....home.....water.....room.....mother.....area.....money" \
       ".....story.....fact.....month.....lot.....right.....study.....book.....eye.....job.....word" \
       ".....business.....issue.....side.....kind.....head.....house.....service.....friend.....father.....power" \
       ".....hour.....game.....line.....end.....member.....law.....car.....city.....community.....name" \
       ".....president.....team.....minute.....idea.....kid.....body.....information.....back.....parent.....face" \
       ".....others.....level.....office.....door.....health.....person.....art.....war.....history.....party" \
       ".....result.....change.....morning.....reason.....research.....girl.....guy.....moment.....air.....teacher"
    pts3 = "force.....education.....foot.....boy.....age.....policy.....everything.....process.....music.....market" \
       ".....sense.....nation.....plan.....college.....interest.....death.....experience.....effect.....use.....class" \
       ".....control.....care.....field.....development.....role.....effort.....rate.....heart.....drug" \
       ".....show.....leader.....light.....voice.....wife.....police.....mind.....price.....report.....decision" \
       ".....son.....view.....relationship.....town.....road.....arm.....difference.....value.....building.....action" \
       ".....model.....season.....society.....tax.....director.....position.....player.....record.....paper.....space" \
       ".....ground.....form.....event.....official.....matter.....center.....couple.....site.....project.....activity" \
       ".....star.....table.....need.....court.....oil.....situation.....cost.....industry.....figure.....street" \
       ".....image.....phone.....data.....picture.....practice.....piece.....land.....product.....doctor.....wall" \
       ".....test.....movie.....north.....love.....support.....technology.....step.....baby.....computer.....type"
    pts4 = "attention.....strategy.....truth.....son.....example.....environment.....camera.....structure.....chance.....energy" \
        ".....period.....course.....summer.....plant.....opportunity.....term.....letter.....choice.....rule.....daughter" \
        ".....administration.....south.....husband.....Congress.....floor.....campaign.....material.....population.....economy.....medical" \
        ".....hospital.....church.....security.....unit.....section.....subject.....officer.....rest.....deal.....performance" \
        ".....fight.....fire.....top.....professor.....cup.....operation.....pressure.....opinion.....style.....adult" \
        ".....machine.....gas.....analysis.....benefit.....sea.....fear.....competition.....camera.....freedom.....dream" \
        ".....note.....responsibility.....behavior.....goal.....soldier.....culture.....trip.....kitchen.....consumer.....shot" \
        ".....painting.....science.....library.....nature.....solution.....damage.....income.....cash.....transport.....region" \
        ".....bar.....strategy.....failure.....weapon.....attempt.....crime.....contract.....attitude.....editor.....magazine"
    pts5 = "newspaper.....aspect.....audience.....attorney.....bag.....battle.....bed.....bill.....birth.....blood" \
       ".....board.....boss.....budget.....cabinet.....campaign.....candidate.....capital.....card.....career.....cell" \
       ".....chance.....character.....charge.....check.....chief.....childhood.....choice.....church.....citizen.....classroom" \
       ".....climate.....clue.....coach.....coalition.....college.....committee.....communication.....community.....company.....comparison" \
       ".....competition.....complaint.....computer.....concept.....concern.....concert.....conclusion.....condition.....conference.....conflict" \
       ".....congress.....connection.....consequence.....construction.....consumer.....contact.....contest.....context.....contract.....contribution" \
       ".....control.....conversation.....cookie.....corner.....costume.....council.....county.....couple.....course.....court" \
       ".....cousin.....crisis.....criticism.....crowd.....culture.....currency.....cycle.....dad.....data.....database" \
       ".....date.....daughter.....day.....dead.....deal.....debate.....debt.....decision.....definition.....degree"
    missing_top_100 = "be....to....an....their....can....come....could....even....find....first....give....here....him....how....into....its....just....know....like....look....make....many....more....new....no....now....only....other....our....over....say....see....some....take....than....them....then....these....they....thing....think....us....use....want....way....well....when....your"





    test_text = "Science can show how the world and body work....Over time, small change can make big difference"    
    print("[TTS] Testing Groq PlayAI TTS...")
    result = run_tts_for_darwin(test_text)
    
    if result:
        print(f"[TTS] Test successful! Audio file generated: {result}")
        return True
    else:
        print("[TTS] Test failed!")
        return False

if __name__ == "__main__":
    # Test the TTS system
    test_tts()