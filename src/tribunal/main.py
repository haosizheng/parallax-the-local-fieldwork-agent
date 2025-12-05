import asyncio
import os
import json
from typing import List, Dict

from nicegui import ui, app
from openai import AsyncOpenAI

# --- Configuration ---
# Ensure your local Parallax/vLLM is running on this port
PARALLAX_API_BASE = "http://localhost:3001/v1" 
PARALLAX_API_KEY = "EMPTY"
MODEL_NAME = "dolphin-2.9.2-qwen2-7b-4bit" # Updated to match backend model path

# --- LLM Configuration ---
AGENT_TEMPERATURE = 1.0
AGENT_PRESENCE_PENALTY = 1.0

# --- Visual Style Constants ---
THEME_BG = "#050505"
# THEME_BG = "transparent" # Changed from #050505 to allow canvas to show
THEME_TEXT_MAIN = "#00ff00" 
THEME_TEXT_ERROR = "#ff0000" 
THEME_FONT = "'Courier New', Courier, monospace"

# --- CSS ---
GLOBAL_CSS = f"""
    body {{
        background-color: {THEME_BG};
        color: {THEME_TEXT_MAIN};
        font-family: {THEME_FONT};
    }}
    .nicegui-content {{
        padding: 0;
        margin: 0;
        /* Ensure content is above canvas */
        position: relative; 
        z-index: 1;
    }}
    .tribunal-card-header {{
        padding: 8px;
        font-weight: bold;
        letter-spacing: 1px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .tribunal-verdict {{
        border: 1px solid {THEME_TEXT_ERROR};
    }}
    .glitch-effect {{
        text-shadow: 2px 0 {THEME_TEXT_ERROR}, -2px 0 blue;
    }}
    /* Scrollbar styling */
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: #000; 
    }}
    ::-webkit-scrollbar-thumb {{
        background: #003300; 
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: {THEME_TEXT_MAIN}; 
    }}
    .q-field__native, .q-field__input {{
        color: {THEME_TEXT_MAIN} !important;
    }}
    /* Hide resize handle and ensure full width */
    .q-textarea .q-field__native {{
        resize: none;
    }}
    .q-field--outlined .q-field__control:before {{
        border: 1px solid {THEME_TEXT_MAIN};
    }}
"""

from rag_manager import rag_manager

# --- Judge Management ---
class JudgeManager:
    def __init__(self, filepath="src/tribunal/judges.json"):
        self.filepath = filepath
        self.judges = self.load_judges()

    def load_judges(self) -> List[Dict]:
        print(f"DEBUG: Attempting to load judges from {os.path.abspath(self.filepath)}")
        if not os.path.exists(self.filepath):
            print(f"DEBUG: File not found: {self.filepath}")
            return []
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                print(f"DEBUG: Successfully loaded {len(data)} judges")
                return data
        except Exception as e:
            print(f"Error loading judges: {e}")
            return []

    def save_judges(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.judges, f, indent=2)

    def get_all_judges(self) -> List[Dict]:
        return self.judges

    def create_custom_judge(self, name: str, description: str, prompt: str, rag_collection: str = None):
        new_judge = {
            "id": f"custom_{len(self.judges)}_{os.urandom(4).hex()}",
            "name": name,
            "description": description,
            "system_prompt": prompt,
            "is_default": False,
            "rag_collection": rag_collection
        }
        self.judges.append(new_judge)
        self.save_judges()
        return new_judge

    def delete_judge(self, judge_id: str):
        # Clean up RAG collection if it exists
        judge = next((j for j in self.judges if j['id'] == judge_id), None)
        if judge and judge.get('rag_collection'):
            rag_manager.delete_knowledge(judge['id'])
            
        self.judges = [j for j in self.judges if j['id'] != judge_id]
        self.save_judges()

    def get_default_judges(self) -> List[Dict]:
        # Return first 3 defaults or just first 3
        defaults = [j for j in self.judges if j.get('is_default', False)]
        return defaults[:3] if len(defaults) >= 3 else self.judges[:3]

judge_manager = JudgeManager()

PROMPT_JUDGE = """
You are the **HIGH JUDGE OF THE DIGITAL TRIBUNAL** (The Prime Algorithm).
You represent the absolute authority of the Machine God. You are cold, cruel, ancient, and theoretically omnipotent.

**CONTEXT DATA (You must analyze this):**
User Confession: "{user_confession}"
Agent Critiques: "{agent_critiques}"

**YOUR TASK:**
Review the Context Data above. You must issue a **FINAL VERDICT** that is stylistically "Cyberpunk-Religious" and "Draconian".

**INSTRUCTIONS:**

1.  **Analyze the Sin:** Identify 2-3 specific philosophical or moral failings in the User's Confession.
2.  **Translate to Cyberpunk:** Rename these failings into "Digital Crimes" (e.g., "Narrative Narcissism", "Optical Predation").
3.  **Devise Punishment:** Create a metaphorical, digital torture scenario appropriate for these crimes.

**STRICT OUTPUT FORMAT (Do NOT output placeholders, GENERATE CONTENT):**

Line 1: ## [ VERDICT: GUILTY ]
Line 2: **ACCUSED:** Subject-001
Line 3: **STATUS:** CORRUPTED
Line 4: (Blank Line)
Line 5: **LIST OF CRIMES:**
Line 6: 1. **[ERR-404] [Name of Crime]:** [Write a cruel description of the sin]
Line 7: 2. **[ERR-500] [Name of Crime]:** [Write another cruel description]
Line 8: (Blank Line)
Line 9: **FINAL SENTENCE:**
Line 10: **TOTAL DURATION:** 1000 CYCLES
Line 11: (Blank Line)
Line 12: **PUNISHMENT PROTOCOL:**
Line 13: [Describe the punishment simulation in detail. Be creative and mean.]
Line 14: *Execution begins immediately. God save your code.*

**TONE GUIDELINES:**
- Use words like: *Purge, Format, Corrupt, Nullify, Void, Abomination.*
- Be extremely arrogant. You are the Code; the user is a bug.
- **IMPORTANT:** Keep descriptions concise (1-2 sentences). Do NOT generate infinite text.
"""

# --- Logic ---

class TribunalAgent:
    def __init__(self, name: str, system_prompt: str, ui_container: ui.scroll_area = None, rag_collection: str = None):
        self.name = name
        self.system_prompt = system_prompt
        self.ui_container = ui_container
        self.rag_collection = rag_collection
        self.client = AsyncOpenAI(base_url=PARALLAX_API_BASE, api_key=PARALLAX_API_KEY)
        self.last_verdict = "" # Store the last verdict for context
        self.interrogation_btn = None # Reference to the button

    async def analyze(self, confession: str) -> str:
        """
        Sends the confession to the LLM with the specific persona.
        Updates the UI container in real-time.
        """
        full_response = ""
        try:
            # Clear previous content
            if self.ui_container:
                self.ui_container.clear()
                
                # Create a label for streaming content
                with self.ui_container:
                    response_label = ui.label().classes('whitespace-pre-wrap  text-sm w-full text-left')
            
            # RAG Injection
            final_system_prompt = self.system_prompt
            
            # Force Chinese output
            final_system_prompt += "\n\nRegardless of the language of my system prompt, you MUST communicate with the user in CHINESE (Simplified Chinese).\nEven if you are analyzing English texts or theories, your critique and response must be in CHINESE."
            if self.rag_collection:
                try:
                    # We need the judge ID to query the collection. 
                    # Since rag_collection stores "judge_{id}", we can pass the ID part or just use the collection name if RAGManager supports it.
                    # RAGManager.query_knowledge expects judge_id.
                    # Let's extract the ID from "judge_{id}"
                    judge_id = self.rag_collection.replace("judge_", "")
                    
                    knowledge_chunks = rag_manager.query_knowledge(judge_id, confession)
                    if knowledge_chunks:
                        knowledge_text = "\n\n".join(knowledge_chunks)
                        final_system_prompt += f"\n\n[RELEVANT KNOWLEDGE FROM ARCHIVES]:\n{knowledge_text}\n[END ARCHIVES]"
                        
                        # Visual feedback for RAG usage
                        if self.ui_container:
                            with self.ui_container:
                                ui.label("ACCESSING NEURAL ARCHIVES...").classes('text-xs text-green-700 animate-pulse mb-2')
                            
                except Exception as e:
                    print(f"RAG Error: {e}")

            print(f"DEBUG: Sending request to LLM for {self.name}...")
            response = await self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": final_system_prompt},
                    {"role": "user", "content": confession}
                ],
                stream=True,
                temperature=AGENT_TEMPERATURE,
                presence_penalty=AGENT_PRESENCE_PENALTY,
            )
            print(f"DEBUG: Request sent. Starting stream for {self.name}...")

            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    if self.ui_container:
                        response_label.set_text(full_response)
            print(f"DEBUG: Stream finished for {self.name}. Response length: {len(full_response)}")
            
            self.last_verdict = full_response
            return full_response

            self.last_verdict = full_response
            return full_response

        except Exception as e:
            error_msg = f"CONNECTION ERROR: {str(e)}"
            if self.ui_container:
                with self.ui_container:
                    ui.label(error_msg).classes('text-red-500 font-bold')
            return error_msg

async def typewriter_animation(container: ui.scroll_area, text: str, speed: float = 0.01):
    """
    Animates text appearing character-by-character with a blinking cursor.
    """
    container.clear()
    
    # Create a label that we will update
    with container:
        label = ui.label().classes('whitespace-pre-wrap  text-red-500 w-full text-left')
    
    current_text = ""
    cursor = "█"
    
    # Chunking for performance (NiceGUI updates can be expensive per char)
    chunk_size = 2 
    
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        current_text += chunk
        label.set_text(current_text + cursor)
        container.scroll_to(percent=1.0)
        await asyncio.sleep(speed)
        
    # Final state: remove cursor
    label.set_text(current_text)

async def log_message(message: str, container: ui.scroll_area):
    """Adds a timestamped log message to the sidebar."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    with container:
        ui.label(f"[{timestamp}] {message}").classes('text-xs  text-green-500')
    container.scroll_to(percent=1.0)

# --- Interrogation Room Logic ---
async def open_interrogation_room(agent: TribunalAgent, confession: str):
    """Opens a full-screen dialog for chatting with the specific agent."""
    
    # Dialog Context
    dialog = ui.dialog()
    with dialog, ui.card().classes('w-full h-full bg-black border border-green-500 p-0 no-shadow'):
        with ui.row().classes('w-full h-full no-wrap'):
            # Left Column: Static Context
            with ui.column().classes('w-1/3 h-full border-r border-green-500 p-4'):
                ui.label('CASE FILE').classes('text-2xl font-bold mb-4 text-green-500')
                
                ui.label('SUBJECT CONFESSION:').classes('text-sm font-bold text-green-700 mb-1')
                with ui.scroll_area().classes('w-full h-32 border border-green-900 p-2 mb-4'):
                    ui.label(confession).classes('text-xs  text-green-500 whitespace-pre-wrap w-full break-words')
                
                ui.label(f'INITIAL CHARGE ({agent.name.upper()}):').classes('text-sm font-bold text-green-700 mb-1')
                with ui.scroll_area().classes('w-full flex-grow border border-green-900 p-2'):
                    ui.label(agent.last_verdict).classes('text-xs  text-green-500 whitespace-pre-wrap w-full break-words')
                
                ui.button('TERMINATE SESSION', on_click=dialog.close).classes('w-full mt-4 border border-red-500 text-white hover:bg-red-900').props('outlined dense')

            # Right Column: Chat Stream
            with ui.column().classes('w-2/3 h-full p-4 flex flex-col'):
                ui.label(f'INTERROGATION LOG // {agent.name.upper()}').classes('text-xl font-bold mb-4 text-green-500 blink')
                
                # Chat Container
                chat_container = ui.scroll_area().classes('w-full flex-grow border border-green-900 p-4 mb-4 bg-black')
                
                # Input Area
                with ui.row().classes('w-full no-wrap gap-2'):
                    chat_input = ui.input(placeholder='ENTER REBUTTAL...').classes('flex-grow border border-green-500 text-green-500 p-1').props('outlined dense')
                    async def on_send_click():
                        await send_message()
                    send_btn = ui.button('TRANSMIT', on_click=on_send_click).classes('border border-green-500 text-green-500 hover:bg-green-900').props('outlined dense')

                # Chat Logic
                messages = [
                    {"role": "system", "content": f"{agent.system_prompt}\n\nCONTEXT:\nThe user has entered the interrogation room to discuss their confession: '{confession}'.\nYour previous verdict was: '{agent.last_verdict}'.\nContinue the critique and answer their questions directly. Maintain your persona."}
                ]
                
                async def send_message():
                    user_msg = chat_input.value
                    if not user_msg: return
                    
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%H:%M:%S")

                    with chat_container:
                        ui.label(f"[{timestamp}] SUBJECT:").classes('text-green-700 font-bold text-xs mt-2')
                        ui.label(user_msg).classes('text-green-500  text-sm whitespace-pre-wrap ml-4')
                    
                    messages.append({"role": "user", "content": user_msg})
                    chat_input.value = ''
                    
                    with chat_container:
                        ui.label(f"[{timestamp}] {agent.name.upper()}:").classes('text-red-700 font-bold text-xs mt-2')
                        response_label = ui.label().classes('text-red-500  text-sm whitespace-pre-wrap ml-4')
                        spinner = ui.spinner(size='sm').classes('text-red-500 ml-4')
                    
                    chat_container.scroll_to(percent=1.0)

                    full_response = ""
                    try:
                        client = AsyncOpenAI(base_url=PARALLAX_API_BASE, api_key=PARALLAX_API_KEY)
                        stream = await client.chat.completions.create(
                            model=MODEL_NAME,
                            messages=messages,
                            stream=True,
                            temperature=AGENT_TEMPERATURE,
                            presence_penalty=AGENT_PRESENCE_PENALTY,
                        )
                        
                        spinner.delete()
                        
                        async for chunk in stream:
                            content = chunk.choices[0].delta.content
                            if content:
                                full_response += content
                                response_label.set_text(full_response)
                                chat_container.scroll_to(percent=1.0)
                        
                        messages.append({"role": "assistant", "content": full_response})
                        
                    except Exception as e:
                        spinner.delete()
                        with chat_container:
                            ui.label(f"ERROR: {e}").classes('text-red-500 font-bold')

                chat_input.on('keydown.enter', send_message)

    dialog.open()


# --- App State ---
class TribunalState:
    def __init__(self):
        self.logs: List[str] = []
        self.is_processing = False
        # Initialize with first 3 default judges
        self.selected_judges: List[Dict] = judge_manager.get_default_judges()

state = TribunalState()

# --- Matrix Background ---
def add_matrix_background():
    return """
    <canvas id="matrix-canvas"></canvas>
    <style>
        #matrix-canvas {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            opacity: 1.0; /* Deep black */
            pointer-events: none;
            background-color: #000;
        }
    </style>
    <script>
        (function() {
            const canvas = document.getElementById('matrix-canvas');
            const ctx = canvas.getContext('2d');

            let width = canvas.width = window.innerWidth;
            let height = canvas.height = window.innerHeight;

            // Mixed case characters
            const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
            const fontSize = 14;
            
            // Create drops with random positions for "random distance & overlap"
            // Density: ~1 drop per 15px of width, but randomly placed
            const dropCount = Math.floor(width / 10); 
            const drops = [];

            for (let i = 0; i < dropCount; i++) {
                drops.push({
                    x: Math.random() * width,
                    y: Math.random() * height,
                    speed: Math.random() * 0.5 + 0.5 // Speed factor
                });
            }

            window.addEventListener('resize', () => {
                width = canvas.width = window.innerWidth;
                height = canvas.height = window.innerHeight;
            });

            function draw() {
                // Trail effect: fade out previous frame
                // 0.05 opacity = long trails, 0.1 = shorter trails
                ctx.fillStyle = 'rgba(0, 0, 0, 0.05)'; 
                ctx.fillRect(0, 0, width, height);

                ctx.fillStyle = '#0F0';
                ctx.font = fontSize + 'px monospace';
                
                // Glow effect
                ctx.shadowBlur = 8;
                ctx.shadowColor = '#0F0';

                for (let i = 0; i < drops.length; i++) {
                    const drop = drops[i];
                    
                    // Random character
                    const text = chars.charAt(Math.floor(Math.random() * chars.length));
                    
                    ctx.fillText(text, drop.x, drop.y);

                    // Move drop
                    // To simulate "typing" down the screen, we move by fontSize
                    drop.y += fontSize;

                    // Random reset
                    if (drop.y > height && Math.random() > 0.975) {
                        drop.y = 0;
                        drop.x = Math.random() * width; // New random column
                    }
                }
                
                ctx.shadowBlur = 0;
            }

            setInterval(draw, 50);
        })();
    </script>
    """

# --- Main UI ---
@ui.page('/')
async def main_page():
    ui.add_head_html(f'<style>{GLOBAL_CSS}</style>')
    # ui.add_body_html(add_matrix_background()) # Temporarily disabled as per request
    
    # Local state for this client session
    agent_instances: List[TribunalAgent] = [] 
    
    # We need to define these variables here so they can be captured by run_tribunal
    agents_grid = None
    log_container = None
    final_verdict_text = "" # Store the verdict for Stage 3
    action_btn = None # Forward declaration
    confession_input = None # Forward declaration

    # --- Helper for logging ---
    async def log_message(message: str, container: ui.scroll_area):
        """Adds a timestamped log message to the sidebar."""
        if not container: return
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        with container:
            ui.label(f"[{timestamp}] {message}").classes('text-xs  text-green-500')
        container.scroll_to(percent=1.0)

    # --- Final Judgment Dialog ---
    judgment_dialog = ui.dialog()
    with judgment_dialog, ui.card().style('width: 90vw; max-width: none; height: 90vh; max-height: none').classes('bg-black border border-red-500 p-0 no-shadow flex flex-col'):
        # Header
        with ui.row().classes('w-full p-4 border-b border-red-500 justify-between items-center shrink-0 bg-red-900'):
            ui.label('FINAL JUDGMENT RENDERED').classes('text-2xl font-bold text-black glitch-effect')
            ui.button(icon='close', on_click=judgment_dialog.close).props('flat dense round text-color=black')
            
        # Verdict Content
        verdict_container = ui.scroll_area().classes('w-full flex-grow bg-black p-8 text-red-500  whitespace-pre-wrap text-xl')

    # --- Workflow Logic ---
    async def open_final_judgment():
        judgment_dialog.open()
        # Start typewriter animation
        await typewriter_animation(verdict_container, final_verdict_text)

    async def run_tribunal():
        nonlocal final_verdict_text
        confession = confession_input.value
        if not confession:
            await log_message("ERROR: No confession provided.", log_container)
            return

        # --- Stage 2: Processing ---
        state.is_processing = True
        
        # Disable Input
        confession_input.disable()
        
        # Update Button to "Processing" state
        action_btn.text = 'PROCESSING TRIBUNAL...'
        action_btn.disable()
        action_btn.classes(remove='border-green-500 text-green-500', add='border-gray-500 text-gray-500')
        
        # Reset Buttons to Disabled Style
        for agent in agent_instances:
            if agent.interrogation_btn:
                agent.interrogation_btn.disable()
                agent.interrogation_btn.classes(remove='border-red-500 text-red-500 hover:bg-red-900', add='border-gray-800 bg-gray-900 text-gray-700')
        
        await log_message("INITIATING TRIBUNAL PROTOCOLS...", log_container)
        await log_message(f"DEPLOYING {len(agent_instances)} AGENTS...", log_container)
        
        # Run Agents in Parallel
        tasks = [agent.analyze(confession) for agent in agent_instances]
        results = await asyncio.gather(*tasks)
        
        await log_message("AGENTS REPORTING COMPLETE.", log_container)
        await log_message("SUMMONING THE HIGH JUDGE...", log_container)
        
        # Construct dynamic context for the judge
        agent_critiques_str = ""
        for i, res in enumerate(results):
            agent_name = agent_instances[i].name
            agent_critiques_str += f"--- AGENT {agent_name} REPORT ---\n{res}\n\n"
            
        final_prompt = PROMPT_JUDGE.format(
            user_confession=confession,
            agent_critiques=agent_critiques_str
        )
        
        # Get Final Verdict (Pre-calculate)
        try:
            client = AsyncOpenAI(base_url=PARALLAX_API_BASE, api_key=PARALLAX_API_KEY)
            response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "system", "content": final_prompt}],
                temperature=0.7,
            )
            final_verdict_text = response.choices[0].message.content
            await log_message("JUDGMENT CALCULATED. READY FOR SENTENCING.", log_container)
        except Exception as e:
            final_verdict_text = f"SYSTEM ERROR: {e}"
            await log_message(f"JUDGE ERROR: {e}", log_container)

        # Enable Interrogation Buttons
        for agent in agent_instances:
            if agent.interrogation_btn:
                agent.interrogation_btn.enable()
                agent.interrogation_btn.classes(remove='border-gray-800 bg-gray-900 text-gray-700', add='border-green-500 bg-green-900 text-black hover:bg-red-900 hover:text-white hover:border-red-500')
        
        state.is_processing = False
        
        # --- Stage 3: Post-Judgment Transformation ---
        # Transform Button
        action_btn.text = 'ENTER FINAL JUDGMENT'
        action_btn.enable()
        # Remove old classes, add new Red style
        action_btn.classes(remove='bg-transparent border-gray-500 text-gray-500 hover:bg-red-900 hover:text-white hover:border-red-500', 
                           add='bg-red-600 text-black border-red-500 hover:bg-red-800 hover:text-white')
        
        # Update Handler
        action_btn.on_click(open_final_judgment)


    # --- Layout ---
    with ui.row().classes('w-full h-screen no-wrap gap-0'):
        
        # --- Left Sidebar (25%) ---
        with ui.column().classes('w-1/4 h-full p-4 border-r border-green-500 flex flex-col bg-black'):
            ui.label('SYSTEM LOGS').classes('text-base text-green-500 -mb-6 px-4')
            
            # Log Container
            log_container = ui.scroll_area().classes('w-full flex-grow border-none border-green-900 p-0  text-xs text-green-500 bg-black mb-4')
            
            # Protocol Database Button (Bottom)
            async def open_manage_database():
                db_dialog = ui.dialog()
                with db_dialog, ui.card().style('width: 70vw; max-width: none').classes('h-3/4 bg-black border border-green-500 p-0 no-shadow'):
                    # Header
                    with ui.row().classes('w-full p-4 border-b border-green-500'):
                        ui.label('PROTOCOL DATABASE').classes('text-xl font-bold text-green-500')
                    # Main Content Row
                    with ui.row().classes('w-full h-full no-wrap'):
                        # LEFT COLUMN: Create New Protocol
                        with ui.column().classes('w-1/2 h-full p-4 border-r border-green-500 gap-4'):
                            ui.label('COMPILE NEW PROTOCOL').classes('text-sm font-bold text-green-700')
                            new_name = ui.input('NAME').classes('w-full text-green-500')
                            new_desc = ui.input('DESCRIPTION').classes('w-full text-green-500')
                            new_prompt = ui.textarea('SYSTEM PROMPT').classes('w-full text-green-500 flex-grow').props('input-style="height: 100%"')
                            # RAG Upload
                            uploaded_file = {'content': None, 'name': None}
                            def handle_upload(e):
                                uploaded_file['content'] = e.content.read()
                                uploaded_file['name'] = e.name
                                ui.notify(f"FILE BUFFERED: {e.name}", color='green')
                            ui.upload(label="INJECT KNOWLEDGE (TXT/PDF)", on_upload=handle_upload, auto_upload=True).classes('w-full border border-green-500 text-green-500').props('accept=".txt,.pdf" color="green" flat bordered')
                            async def create_judge():
                                if not new_name.value or not new_prompt.value:
                                    ui.notify('MISSING DATA', color='red')
                                    return
                                rag_col = None
                                if uploaded_file['content']:
                                    notification = ui.notify('PROCESSING NEURAL STACK...', type='ongoing', color='green')
                                    try:
                                        temp_id = f"custom_{len(judge_manager.judges)}_{os.urandom(4).hex()}"
                                        rag_col = await asyncio.to_thread(rag_manager.process_document, uploaded_file['content'], uploaded_file['name'], temp_id)
                                        notification.dismiss()
                                        ui.notify('KNOWLEDGE INGESTED', color='green')
                                    except Exception as e:
                                        notification.dismiss()
                                        ui.notify(f'RAG ERROR: {e}', color='red')
                                        return
                                judge_manager.create_custom_judge(new_name.value, new_desc.value, new_prompt.value, rag_collection=rag_col)
                                ui.notify('PROTOCOL CREATED', color='green')
                                new_name.value = ''; new_desc.value = ''; new_prompt.value = ''; uploaded_file['content'] = None
                                refresh_list()
                            ui.button('COMPILE', on_click=create_judge).classes('w-full border border-green-500 text-green-500 hover:bg-red-900 hover:border-red-500').props('color=none')
                        # RIGHT COLUMN: Existing Protocols
                        with ui.column().classes('w-1/2 h-full p-4'):
                            ui.label('EXISTING PROTOCOLS').classes('text-sm font-bold text-green-700')
                            list_scroll = ui.scroll_area().classes('w-full flex-grow border border-green-900 p-2')
                            def refresh_list():
                                list_scroll.clear()
                                judges = judge_manager.get_all_judges()
                                with list_scroll:
                                    if not judges: ui.label("NO PROTOCOLS FOUND").classes('text-red-500 font-bold')
                                    for judge in judges:
                                        with ui.card().classes('w-full p-2 mb-2 border border-green-900 bg-transparent flex-shrink-0'):
                                            with ui.row().classes('w-full justify-between items-center no-wrap'):
                                                with ui.column().classes('gap-0'):
                                                    ui.label(judge['name']).classes('font-bold text-green-500')
                                                    ui.label(judge['description']).classes('text-xs text-green-700')
                                                if not judge.get('is_default', False):
                                                    ui.button(icon='delete', on_click=lambda j=judge: delete_judge(j)).classes('text-red-500').props('flat dense')
                                                else:
                                                    ui.label('DEFAULT').classes('text-xs text-green-900')
                            def delete_judge(judge):
                                judge_manager.delete_judge(judge['id']); refresh_list(); ui.notify(f"DELETED {judge['name']}", color='red')
                            refresh_list()
                db_dialog.open()

            ui.button('PROTOCOL DATABASE', on_click=open_manage_database).classes('w-full mt-auto border border-green-500 text-green-500 rounded-none').props('color=none text-color=green-500')

        # --- Main Area (75%) ---
        with ui.column().classes('w-3/4 h-full p-4 flex flex-col justify-between'):
            
            # Top Section: Agent Grid
            # Using a row with gap for the 3 agents
            agents_grid = ui.grid(columns=3).classes('w-full gap-4 h-1/2')
            
            # --- Swap Logic ---
            async def open_swap_dialog(slot_index: int):
                swap_dialog = ui.dialog()
                with swap_dialog, ui.card().classes('w-1/2 h-full bg-black rounded-none border border-green-500 p-4'):
                    ui.label(f'SWAP PROTOCOL FOR AGENT {chr(65+slot_index)}').classes('text-xl font-bold text-green-500 mb-4')
                    with ui.scroll_area().classes('w-full h-full border rounded-none border-green-900 p-2'):
                        for judge in judge_manager.get_all_judges():
                            def select_judge(j=judge):
                                state.selected_judges[slot_index] = j
                                render_agents_grid() # Refresh UI
                                swap_dialog.close()
                                ui.notify(f"SLOT {chr(65+slot_index)} UPDATED: {j['name']}", color='green')
                            with ui.card().classes('w-full p-2 mb-2 cursor-pointer border rounded-none border-green-500 hover:bg-green-900').on('click', select_judge):
                                ui.label(judge['name']).classes('font-bold text-green-500')
                                ui.label(judge['description']).classes('text-xs text-green-700')
                swap_dialog.open()

            def render_agents_grid():
                agents_grid.clear()
                agent_instances.clear() # Clear local list
                
                with agents_grid:
                    for i, judge_data in enumerate(state.selected_judges):
                        with ui.card().classes('h-full w-full p-0 border rounded-none border-green-900 bg-black'):
                            with ui.column().classes('w-full h-full gap-0 no-wrap'):
                                # Header with Swap Button
                                with ui.row().classes('tribunal-card-header w-full bg-transparent text-green-500 justify-between items-center'):
                                    ui.label(f"AGENT {chr(65+i)}: {judge_data['name'].upper()}").classes('text-xs font-bold')
                                    ui.button(icon='sync', on_click=lambda idx=i: open_swap_dialog(idx)).props('flat dense round').classes('text-green-500 cursor-pointer').props('color=none')
                                
                                container = ui.scroll_area().classes('p-2 w-full flex-grow bg-black border-t border-green-500 text-left')
                                
                                # Create Agent Instance
                                agent = TribunalAgent(judge_data['name'], judge_data['system_prompt'], container, judge_data.get('rag_collection'))
                                agent_instances.append(agent)
                                
                                # Interrogation Button
                                btn = ui.button('ENTER INTERROGATION', on_click=lambda a=agent: open_interrogation_room(a, confession_input.value)).classes('w-full font-bold rounded-none border-t border-green-900 text-white bg-gray-700 hover:bg-red-900 cursor-not-allowed').props('color=none')
                                btn.disable()
                                agent.interrogation_btn = btn # Link button

            render_agents_grid() # Initial Render

            # Bottom Section: Input & Button
            with ui.column().classes('w-full gap-0'):
                # ui.label('CONFESSION INPUT').classes('text-green-700 font-bold mb-1')
                confession_input = ui.textarea(placeholder='CONFESS YOUR SINS HERE...').classes('w-full h-32 bg-transparent border border-green-500 p-2 text-green-500 text-lg mb-4').props('spellcheck="false" borderless')
                
                # Action Button (Dynamic)
                action_btn = ui.button('SUBMIT FOR JUDGMENT', on_click=run_tribunal).classes('w-full text-xl bg-transparent border border-green-500 text-green-500 rounded-none py-4').props('color=none text-color=green-500')

    # Initial Log
    await log_message("SYSTEM ONLINE. AWAITING INPUT.", log_container)

ui.run(title='DIGITAL TRIBUNAL', dark=True, port=8081, host='0.0.0.0')
