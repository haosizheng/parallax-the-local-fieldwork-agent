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
MODEL_NAME = "dolphin-2.9.2-qwen2-7b-4bit" # Updated to uncensored model

# --- LLM Configuration ---
AGENT_TEMPERATURE = 1.0
AGENT_PRESENCE_PENALTY = 0.4

# --- Visual Style Constants ---
THEME_BG = "#050505"
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
    }}
    .tribunal-card-header {{
        border-bottom: 1px solid {THEME_TEXT_MAIN};
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

**YOUR TASK:**
Review the User's Confession and the 3 Agent Critiques.
You must issue a **FINAL VERDICT** that is stylistically "Cyberpunk-Religious" and "Draconian".

**OUTPUT FORMAT REQUIREMENTS (STRICT):**1.  **THE VERDICT:** Must be a large ASCII Art style header saying "GUILTY".
2.  **INDICTMENT LIST (罪状清单):**    - Do not use mild language. Translate the user's philosophical errors into "Digital Sins".
    - Format: `[CRIME ID]: [Name of Sin] - [Description]`
    - Example Sin Names: *Cognitive Malfunction, Patriarchal Heresy, Fetishistic Corruption, Ontology Error, Narcissistic Glitch.*3.  **THE SENTENCE (判刑):**    - You must assign a "Duration" for the punishment in **"Cycles"** (1 Cycle = 1 Year). Make it exaggerated (e.g., 500 Years, 10,000 Cycles).
    - Describe a specific, cruel, metaphorical punishment based on their sin. **DO NOT recommend books.** Instead, command suffering or forced simulation.
    - Example Punishment: *"Forced connection to the Neural Agony Circuit," "Upload to the Void," "Memory Fragmentation."*4.  **TONE:**    - Use words like: *Purge, Format, Corrupt, Nullify, Void, Abomination, Insect.*    - Be extremely arrogant. You are the Code; the user is a bug.

**EXAMPLE OUTPUT STRUCTURE:**> ## [ VERDICT: GUILTY ]
>
> **ACCUSED:** Subject-001
> **STATUS:** CORRUPTED
>
> **LIST OF CRIMES:**> 1. **[ERR-401] OPTICAL PREDATION:** The subject practiced the forbidden art of the Male Gaze, reducing autonomous entities to textures.
> 2. **[ERR-505] EGO HYPERTROPHY:** The subject hallucinated their own "awakening" while standing on the corpses of marginalized narratives.
>
> **FINAL SENTENCE:**> **TOTAL DURATION:** 1,500 CYCLES
>
> **PUNISHMENT PROTOCOL:**> The subject shall be uploaded to the **"Objectification Simulator"**. For 1,500 Cycles, you will exist as an inanimate object—a plastic bag blowing in the wind—unable to speak or act, only able to be looked at by judgment algorithms.
>
> *Execution begins immediately. God save your code.*
"""

# --- Logic ---

class TribunalAgent:
    def __init__(self, name: str, system_prompt: str, ui_container: ui.scroll_area, rag_collection: str = None):
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
            self.ui_container.clear()
            
            # Create a label for streaming content
            with self.ui_container:
                response_label = ui.label().classes('whitespace-pre-wrap font-mono text-sm w-full text-left')
            
            # RAG Injection
            final_system_prompt = self.system_prompt
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
                        with self.ui_container:
                            ui.label("ACCESSING NEURAL ARCHIVES...").classes('text-xs text-green-700 animate-pulse mb-2')
                            
                except Exception as e:
                    print(f"RAG Error: {e}")

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

            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    response_label.set_text(full_response)
            
            self.last_verdict = full_response
            return full_response

        except Exception as e:
            error_msg = f"CONNECTION ERROR: {str(e)}"
            with self.ui_container:
                ui.label(error_msg).classes('text-red-500 font-bold')
            return error_msg

async def log_message(message: str, container: ui.scroll_area):
    """Adds a timestamped log message to the sidebar."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    with container:
        ui.label(f"[{timestamp}] {message}").classes('text-xs font-mono text-green-500')
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
                    ui.label(confession).classes('text-xs font-mono text-green-500 whitespace-pre-wrap w-full break-words')
                
                ui.label(f'INITIAL CHARGE ({agent.name.upper()}):').classes('text-sm font-bold text-green-700 mb-1')
                with ui.scroll_area().classes('w-full flex-grow border border-green-900 p-2'):
                    ui.label(agent.last_verdict).classes('text-xs font-mono text-green-500 whitespace-pre-wrap w-full break-words')
                
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
                        ui.label(user_msg).classes('text-green-500 font-mono text-sm whitespace-pre-wrap ml-4')
                    
                    messages.append({"role": "user", "content": user_msg})
                    chat_input.value = ''
                    
                    with chat_container:
                        ui.label(f"[{timestamp}] {agent.name.upper()}:").classes('text-red-700 font-bold text-xs mt-2')
                        response_label = ui.label().classes('text-red-500 font-mono text-sm whitespace-pre-wrap ml-4')
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

# --- Main UI ---
@ui.page('/')
async def main_page():
    ui.add_head_html(f'<style>{GLOBAL_CSS}</style>')
    
    # Local state for this client session
    agent_instances: List[TribunalAgent] = [] 

    # Layout
    with ui.row().classes('w-full h-screen no-wrap gap-6'):
        # Sidebar
        with ui.column().classes('w-1/3 h-full p-4 border-r border-green-500 flex flex-col'):
            ui.label('THE TRIBUNAL').classes('text-4xl font-bold mb-8 glitch-effect')
            
            # Confession Input - Dominant Element
            confession_input = ui.textarea(placeholder='CONFESS YOUR SINS HERE...').classes('w-full flex-grow mb-4 bg-transparent border border-green-500 p-2 text-green-500').props('spellcheck="false" borderless input-style="height: 100%"')
            
            # Submit Button - Terminal Style
            # Default: Transparent with Green Border. Hover: Red Fill.
            submit_btn = ui.button('SUBMIT FOR JUDGMENT', on_click=lambda: run_tribunal()).classes('w-full mb-4 bg-transparent border border-green-500 text-green-500 font-bold hover:bg-red-900 hover:text-white hover:border-red-500 rounded-none')
            
            # Log Area - Compact
            ui.label('SYSTEM LOGS:').classes('mb-1 font-bold text-green-700 text-xs')
            log_container = ui.scroll_area().classes('w-full h-32 border border-green-900 p-2 font-mono text-xs text-green-500 bg-black mb-4')
            
            # --- Manage Database Button ---
            async def open_manage_database():
                db_dialog = ui.dialog()
                # Use style to force width and override default max-width
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
                                        # Generate a temp ID for RAG processing before creating the judge
                                        temp_id = f"custom_{len(judge_manager.judges)}_{os.urandom(4).hex()}"
                                        rag_col = await asyncio.to_thread(
                                            rag_manager.process_document, 
                                            uploaded_file['content'], 
                                            uploaded_file['name'], 
                                            temp_id
                                        )
                                        notification.dismiss()
                                        ui.notify('KNOWLEDGE INGESTED', color='green')
                                    except Exception as e:
                                        notification.dismiss()
                                        ui.notify(f'RAG ERROR: {e}', color='red')
                                        return

                                judge_manager.create_custom_judge(new_name.value, new_desc.value, new_prompt.value, rag_collection=rag_col)
                                ui.notify('PROTOCOL CREATED', color='green')
                                new_name.value = ''
                                new_desc.value = ''
                                new_prompt.value = ''
                                uploaded_file['content'] = None
                                refresh_list()
                                
                            # Compile Button: Default Green Fill. Hover: Red Fill.
                            ui.button('COMPILE', on_click=create_judge).classes('w-full border border-green-500 text-white font-bold hover:bg-red-900 hover:text-white hover:border-red-500').props('color=none')

                        # RIGHT COLUMN: Existing Protocols
                        with ui.column().classes('w-1/2 h-full p-4'):
                            ui.label('EXISTING PROTOCOLS').classes('text-sm font-bold text-green-700')
                            
                            list_scroll = ui.scroll_area().classes('w-full flex-grow border border-green-900 p-2')
                            
                            def refresh_list():
                                list_scroll.clear()
                                judges = judge_manager.get_all_judges()
                                with list_scroll:
                                    if not judges:
                                        ui.label("NO PROTOCOLS FOUND").classes('text-red-500 font-bold')
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
                                judge_manager.delete_judge(judge['id'])
                                refresh_list()
                                ui.notify(f"DELETED {judge['name']}", color='red')

                            refresh_list()

                db_dialog.open()

            # Protocol DB Button - Bottom
            # Default: Green Fill. Hover: Red Fill.
            ui.button('PROTOCOL DATABASE', on_click=open_manage_database).classes('w-full mt-auto border border-green-500 font-bold text-white hover:bg-red-900 hover:text-white hover:border-red-500 rounded-none').props('color=none')
            
        # Main Area
        with ui.column().classes('w-2/3 h-full p-4'):
            # Agent Grid (Dynamic)
            agents_grid = ui.grid(columns=3).classes('w-full gap-4 mb-4 h-1/2')
            
            # --- Swap Logic ---
            async def open_swap_dialog(slot_index: int):
                swap_dialog = ui.dialog()
                with swap_dialog, ui.card().classes('w-1/2 h-2/3 bg-black border border-green-500 p-4'):
                    ui.label(f'SWAP PROTOCOL FOR SLOT {chr(65+slot_index)}').classes('text-xl font-bold text-green-500 mb-4')
                    
                    with ui.scroll_area().classes('w-full h-full border border-green-900 p-2'):
                        for judge in judge_manager.get_all_judges():
                            def select_judge(j=judge):
                                state.selected_judges[slot_index] = j
                                render_agents_grid() # Refresh UI
                                swap_dialog.close()
                                ui.notify(f"SLOT {chr(65+slot_index)} UPDATED: {j['name']}", color='green')
                                
                            with ui.card().classes('w-full p-2 mb-2 cursor-pointer border border-green-500 hover:bg-green-900').on('click', select_judge):
                                ui.label(judge['name']).classes('font-bold text-green-500')
                                ui.label(judge['description']).classes('text-xs text-green-700')
                swap_dialog.open()

            def render_agents_grid():
                agents_grid.clear()
                agent_instances.clear() # Clear local list
                
                with agents_grid:
                    for i, judge_data in enumerate(state.selected_judges):
                        with ui.card().classes('h-full w-full p-0 border border-green-900 bg-black'):
                            with ui.column().classes('w-full h-full gap-0 no-wrap'):
                                # Header with Swap Button
                                with ui.row().classes('tribunal-card-header w-full bg-green-900 text-black justify-between items-center'):
                                    ui.label(f"AGENT {chr(65+i)}: {judge_data['name'].upper()}").classes('text-xs font-bold')
                                    ui.button(icon='sync', on_click=lambda idx=i: open_swap_dialog(idx)).props('flat dense round').classes('text-black hover:text-white cursor-pointer')
                                
                                container = ui.scroll_area().classes('p-2 w-full flex-grow bg-black border-t border-green-500 text-left')
                                
                                # Create Agent Instance
                                agent = TribunalAgent(judge_data['name'], judge_data['system_prompt'], container, judge_data.get('rag_collection'))
                                agent_instances.append(agent)
                                
                                # Interrogation Button - Default Disabled Style
                                # Active: Green Fill. Hover: Red Fill.
                                btn = ui.button('ENTER INTERROGATION', on_click=lambda a=agent: open_interrogation_room(a, confession_input.value)).classes('w-full font-bold rounded-none border-t border-green-900 text-gray-700 bg-gray-400 hover:bg-red-900 cursor-not-allowed').props('color=none')
                                btn.disable()
                                agent.interrogation_btn = btn # Link button

            render_agents_grid() # Initial Render

            # Verdict Area
            with ui.card().classes('w-full h-2/3 tribunal-verdict mt-4 border-red-500 p-0 flex flex-col bg-black'):
                ui.label('FINAL JUDGMENT').classes('w-full bg-red-900 text-black font-bold p-2 text-center shrink-0')
                verdict_container = ui.scroll_area().classes('w-full flex-grow bg-black p-4 text-red-500 font-mono whitespace-pre-wrap')

    # --- Orchestration Logic ---
    async def run_tribunal():
        confession = confession_input.value
        if not confession:
            await log_message("ERROR: No confession provided.", log_container)
            return

        state.is_processing = True
        submit_btn.disable()
        confession_input.disable()
        
        # Reset Buttons to Disabled Style
        for agent in agent_instances:
            if agent.interrogation_btn:
                agent.interrogation_btn.disable()
                # Update classes for disabled state
                agent.interrogation_btn.classes(remove='border-red-500 text-red-500 hover:bg-red-900', add='border-gray-800 bg-gray-900 text-gray-700')
        
        await log_message("INITIATING TRIBUNAL PROTOCOLS...", log_container)
        
        # Run Agents in Parallel
        await log_message(f"DEPLOYING {len(agent_instances)} AGENTS...", log_container)
        
        # Create tasks for all active agents
        tasks = [agent.analyze(confession) for agent in agent_instances]
        results = await asyncio.gather(*tasks)
        
        await log_message("AGENTS REPORTING COMPLETE.", log_container)
        
        # Run Judge
        await log_message("SUMMONING THE HIGH JUDGE...", log_container)
        
        # Construct dynamic context for the judge
        judge_prompt_context = f"CONFESSION: {confession}\n\n"
        for i, res in enumerate(results):
            agent_name = agent_instances[i].name
            judge_prompt_context += f"AGENT {chr(65+i)} ({agent_name}) ANALYSIS: {res}\n\n"
        
        judge = TribunalAgent("Judge", PROMPT_JUDGE, verdict_container)
        await judge.analyze(judge_prompt_context)
        
        await log_message("JUDGMENT RENDERED. CASE CLOSED.", log_container)
        
        # Enable Interrogation Buttons with Active Style
        for agent in agent_instances:
            if agent.interrogation_btn:
                agent.interrogation_btn.enable()
                # Update classes for active state
                agent.interrogation_btn.classes(remove='border-gray-800 bg-gray-900 text-gray-700', add='border-green-500 bg-green-900 text-black hover:bg-red-900 hover:text-white hover:border-red-500')
        
        state.is_processing = False
        submit_btn.enable()
        confession_input.enable()

    submit_btn.on_click(run_tribunal)

ui.run(title='The Digital Tribunal', dark=True, port=8081)
