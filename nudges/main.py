import asyncio
import os
import time
import json
import dotenv
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
)
from groq import AsyncGroq
from rich.console import Console

# Load environment
dotenv.load_dotenv()
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

console = Console()
groq_client = AsyncGroq(api_key=GROQ_API_KEY)

# Global State
latency_tracker = {}
chunk_counter = 0
transcript_buffer = []  # Stores the rolling window of the conversation

class NudgeManager:
    def __init__(self):
        self.history = {} # Tracks: signal_type -> timestamp
        self.cooldown = 60 # Increased to 60 seconds to completely stop duplicates!

    def should_fire(self, signal_type, confidence):
        # 1. False Positive Control: Stricter confidence threshold
        if confidence < 0.7:
            return False 
            
        last_fired = self.history.get(signal_type, 0)
        now = time.time()
        
        # 2. Duplicate Suppression / Cooldown Control
        if now - last_fired > self.cooldown:
            self.history[signal_type] = now
            return True
            
        return False

nudge_manager = NudgeManager()

async def analyze_transcript():
    """Sends the rolling transcript to Groq to extract signals"""
    if len(transcript_buffer) < 2:
        return 

    context = "\n".join(transcript_buffer[-8:])
    start_llm_time = time.time()
    
    prompt = """
    You are an AI analyzing a live business loan sales call. Read the transcript segment and detect ANY of these signals. 
    
    STRICT RULES:
    1. "missed_cross_sell": Fire ONLY if the customer mentions a "second location" AND the agent replies but ignores it.
    2. "rising_frustration": Fire ONLY if the customer explicitly says "bait and switch", "ridiculous", or is angry.
    3. "compliance_gap": Fire ONLY if the agent says "preapproved" or "bye" BUT did NOT mention the "Hard Credit Pull". Do NOT fire at the beginning of the call.
    
    If the text is noisy, or no rule is strictly met, set signal_type to "null".
    
    Output strictly in JSON format. signal_type MUST be one of the exact strings above or "null".
    {"signal_type": "missed_cross_sell" | "rising_frustration" | "compliance_gap" | "null", "confidence": float, "nudge_message": "string"}
    """
    
    try:
        # Using llama-3.1-8b-instant which is Groq's primary fast model
        completion = await groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Transcript:\n{context}"}
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"}
        )
        
        llm_latency = int((time.time() - start_llm_time) * 1000)
        
        result = json.loads(completion.choices[0].message.content)
        signal = result.get("signal_type")
        confidence = result.get("confidence", 0.0)
        msg = result.get("nudge_message")
        
        if signal and signal != "null":
            if nudge_manager.should_fire(signal, confidence):
                console.print(f"\n[bold red on white] 🚨 NUDGE [{signal}] ({llm_latency}ms LLM Latency) [/] [bold yellow]{msg}[/]\n")
                
    except Exception as e:
        # Print error so we can see if Groq fails!
        console.print(f"[bold red]Groq Analysis Error:[/] {e}")


async def main():
    global chunk_counter
    deepgram = DeepgramClient(api_key=DEEPGRAM_API_KEY)
    dg_connection = deepgram.listen.asyncwebsocket.v("1")

    async def on_message(self, result, **kwargs):
        sentence = result.channel.alternatives[0].transcript
        if not sentence:
            return

        time_received = time.time()
        last_sent_time = latency_tracker.get(chunk_counter, time_received)
        latency_ms = int((time_received - last_sent_time) * 1000)

        speaker = result.channel.alternatives[0].words[0].speaker if result.channel.alternatives[0].words else "Unknown"
        
        formatted_line = f"[Speaker {speaker}]: {sentence}"
        print(f"({latency_ms}ms ASR) {formatted_line}")
        
        # Add to rolling buffer
        transcript_buffer.append(formatted_line)
        
        # Fire off the Groq analysis asynchronously so it doesn't block the audio stream!
        asyncio.create_task(analyze_transcript())

    async def on_error(self, error, **kwargs):
        print(f"Deepgram Error: {error}")

    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_connection.on(LiveTranscriptionEvents.Error, on_error)

    options = LiveOptions(
        model="nova-2",
        language="en-US",
        smart_format=True,
        diarize=True, 
        interim_results=False 
    )

    console.print("[bold cyan]Connecting to Deepgram...[/]")
    if await dg_connection.start(options) is False:
        print("Failed to connect to Deepgram")
        return
    console.print("[bold green]Connected! Simulating live call...[/]\n")

    audio_file_path = "test_call.wav" 
    
    try:
        with open(audio_file_path, "rb") as audio:
            chunk_size = 8192 
            while True:
                data = audio.read(chunk_size)
                if not data:
                    break
                
                chunk_counter += 1
                latency_tracker[chunk_counter] = time.time()
                
                await dg_connection.send(data)
                await asyncio.sleep(0.25)
                
    except FileNotFoundError:
        print(f"Error: Could not find '{audio_file_path}'. Please add a test audio file.")

    await asyncio.sleep(3) # Wait for final LLM analysis to finish
    await dg_connection.finish()
    console.print("\nCall Ended.")

if __name__ == "__main__":
    asyncio.run(main())